import os
import argparse
import re
import requests
import google.auth
import google.auth.transport.requests
import time
from pathlib import Path

# --- Configuration ---
LOCATION = "us-central1"

def get_access_token():
    """Gets the default access token to authenticate to the Google Cloud API."""
    try:
        credentials, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        
        # Get project ID from environment or credentials
        project_id = project or os.environ.get('GOOGLE_CLOUD_PROJECT', 'runtime-terror-473409')
        
        return credentials.token, project_id
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        raise

def clean_generated_code(code_text):
    """Clean the generated code by removing markdown formatting and extra text."""
    # Remove markdown code blocks
    code_text = re.sub(r'```java\n?', '', code_text)
    code_text = re.sub(r'```\n?', '', code_text)
    
    # Remove any introductory text before the first import or package statement
    lines = code_text.split('\n')
    start_idx = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('package ') or stripped.startswith('import ') or stripped.startswith('@') or stripped.startswith('public class'):
            start_idx = i
            break
    
    return '\n'.join(lines[start_idx:]).strip()

def extract_package_name(source_code):
    """Extract package name from source code."""
    match = re.search(r'package\s+([\w\.]+);', source_code)
    return match.group(1) if match else ""

def generate_tests(access_token: str, project_id: str, source_code: str, class_name: str, package_name: str, out_dir: str, relative_path: str):
    """Generates tests by calling the Vertex AI REST API."""
    
    # Updated with current available models
    models_to_try = [
        "gemini-2.5-pro",
        "qwen2.5",
        "gemini-2.5-flash",
        "gemini-2.0-flash-001"
    ]
    
    for model_id in models_to_try:
        api_endpoint = (
            f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{project_id}"
            f"/locations/{LOCATION}/publishers/google/models/{model_id}:generateContent"
        )
        
        if try_generate_with_model(api_endpoint, access_token, source_code, class_name, package_name, out_dir):
            print(f"✅ Successfully used model: {model_id}")
            return True
    
    print(f"❌ All models failed for {class_name}")
    return False


def try_generate_with_model(api_endpoint: str, access_token: str, source_code: str, class_name: str, package_name: str, out_dir: str):
    """Try to generate tests using a specific model endpoint."""
    
    prompt = f"""
Generate comprehensive JUnit 5 test cases for the following Spring Boot service class.

REQUIREMENTS:
1. Package declaration: package {package_name};
2. Import statements must include:
   - org.junit.jupiter.api.*
   - org.mockito.*
   - org.springframework.boot.test.context.SpringBootTest
   - org.springframework.test.context.junit.jupiter.SpringJUnitConfig
   - All necessary domain classes and dependencies

3. Class structure:
   - @ExtendWith(MockitoExtension.class) 
   - @SpringBootTest (if testing Spring components)
   - Private @Mock fields for dependencies
   - Private @InjectMocks field for the class under test
   - @BeforeEach setup method if needed

4. Test methods should:
   - Use @Test annotation
   - Follow naming convention: methodName_condition_expectedResult
   - Test positive cases, negative cases, and edge cases
   - Use proper assertions (assertEquals, assertThrows, assertNotNull, etc.)
   - Mock external dependencies properly
   - Include @DisplayName annotations for clarity

5. Handle common Spring Boot patterns:
   - Repository mocking
   - Service layer testing
   - Exception handling
   - Validation testing
   - Security context if needed

6. Use realistic test data and avoid hardcoded values where possible

7. Ensure all imports are valid and the code compiles without errors

8. Do NOT include:
   - Markdown formatting
   - Explanatory text
   - Comments about what the test does
   - Package-info or module declarations

Source code to test:
{source_code}

Generate ONLY the Java test class code:
"""
    
    request_body = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2,  # Reduced for more consistent output
            "topP": 0.9,
            "maxOutputTokens": 8192,
            "candidateCount": 1
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_endpoint, headers=headers, json=request_body, timeout=180)
        
        # Enhanced error handling
        if response.status_code == 404:
            print(f"⚠️  Model not found or not accessible: {api_endpoint.split('/')[-1].split(':')[0]}")
            return False
        elif response.status_code == 403:
            print(f"⚠️  Permission denied for model: {api_endpoint.split('/')[-1].split(':')[0]}")
            return False
        elif response.status_code == 429:
            print(f"⚠️  Rate limit exceeded, waiting...")
            time.sleep(5)  # Wait longer for rate limits
            return False
            
        response.raise_for_status()
        
        response_json = response.json()
        
        if 'candidates' not in response_json or not response_json['candidates']:
            print(f"⚠️  No candidates returned from model")
            return False
        
        test_code = response_json['candidates'][0]['content']['parts'][0]['text']
        test_code = clean_generated_code(test_code)
        
        # Validate the generated code has basic structure
        if not validate_generated_test(test_code, class_name):
            print(f"⚠️  Generated test for {class_name} failed validation")
            return False
        
        # Create output directory structure matching the package structure
        package_path = package_name.replace('.', '/')
        full_out_dir = os.path.join(out_dir, package_path)
        os.makedirs(full_out_dir, exist_ok=True)
        
        test_file = os.path.join(full_out_dir, f"{class_name}Test.java")
        
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)
        
        print(f"✅ Generated: {test_file}")
        return True
        
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            if e.response.status_code == 404:
                return False  # Model not available, try next one
            print(f"❌ HTTP error {e.response.status_code} for {class_name}: {e.response.text}")
        else:
            print(f"❌ Network error for {class_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error for {class_name}: {e}")
        return False
    
def validate_generated_test(test_code: str, class_name: str) -> bool:
    """Validate that the generated test has basic required structure."""
    required_elements = [
        f"class {class_name}Test",
        "@Test",
        "import org.junit.jupiter.api",
        f"package "
    ]
    
    for element in required_elements:
        if element not in test_code:
            print(f"❌ Missing required element: {element}")
            return False
    
    # Check for basic Java syntax
    if test_code.count('{') != test_code.count('}'):
        print(f"❌ Unbalanced braces in generated test")
        return False
        
    return True