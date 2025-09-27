# vertex_generate_tests.py
import os
import argparse
import re
import requests
import google.auth
import google.auth.transport.requests
import time
import subprocess
from pathlib import Path

MODEL_ID = "gemini-pro"
LOCATION = "us-central1"

def get_access_token():
    try:
        credentials, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        project_id = project or os.environ.get('GOOGLE_CLOUD_PROJECT', 'runtime-terror-473409')
        return credentials.token, project_id
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        raise

def validate_java_syntax(java_code):
    if not re.search(r'(class|interface|enum)\s+\w+', java_code):
        return False, "No class/interface/enum declaration found"
    
    open_braces = java_code.count('{')
    close_braces = java_code.count('}')
    
    if open_braces != close_braces:
        return False, f"Brace mismatch: {open_braces} opening, {close_braces} closing"
    
    return True, "Valid"

def fix_common_issues(java_code):
    if 'import org.junit.jupiter.api.Test;' not in java_code:
        java_code = add_missing_imports(java_code)
    
    open_braces = java_code.count('{')
    close_braces = java_code.count('}')
    
    if open_braces > close_braces:
        java_code += '\n' + '}' * (open_braces - close_braces)
    
    java_code = fix_syntax_issues(java_code)
    
    return java_code

def fix_syntax_issues(java_code):
    java_code = re.sub(r'(\w+)\s*\(\s*\)\s*;', r'\1() {\n        // TODO: Implement test\n    }', java_code)
    java_code = re.sub(r'(import\s+[\w\.]+)(?<!;)(\n)', r'\1;\2', java_code)
    java_code = re.sub(r'@(\w+)\s*\n\s*(\w+)', r'@\1\n    \2', java_code)
    return java_code

def add_missing_imports(java_code):
    standard_imports = [
        "import org.junit.jupiter.api.Test;",
        "import org.junit.jupiter.api.BeforeEach;",
        "import org.junit.jupiter.api.DisplayName;",
        "import org.junit.jupiter.api.extension.ExtendWith;",
        "import org.mockito.Mock;",
        "import org.mockito.InjectMocks;",
        "import org.mockito.junit.jupiter.MockitoExtension;",
        "import static org.junit.jupiter.api.Assertions.*;",
        "import static org.mockito.Mockito.*;",
        "import static org.mockito.ArgumentMatchers.*;"
    ]
    
    package_match = re.search(r'package\s+[\w.]+;', java_code)
    if package_match:
        insert_pos = package_match.end()
        imports_to_add = [imp for imp in standard_imports if imp not in java_code]
        if imports_to_add:
            import_block = '\n\n' + '\n'.join(imports_to_add) + '\n'
            java_code = java_code[:insert_pos] + import_block + java_code[insert_pos:]
    
    return java_code

def compile_test_java(java_file_path):
    try:
        result = subprocess.run(['javac', '-cp', '.:*', str(java_file_path)],
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True, "Compilation successful"
        else:
            return False, f"Compilation failed: {result.stderr}"
    except FileNotFoundError:
        return False, "javac not found - skipping compilation check"
    except Exception as e:
        return False, f"Compilation check failed: {str(e)}"

def validate_and_fix_generated_code(generated_code, class_name):
    print(f"🔍 Validating generated code for {class_name}")
    cleaned_code = clean_generated_code(generated_code)
    is_valid, message = validate_java_syntax(cleaned_code)
    
    if is_valid:
        print(f"✅ Validation successful for {class_name}")
        return cleaned_code, True

    print(f"⚠️  Validation failed for {class_name}: {message}")
    cleaned_code = fix_common_issues(cleaned_code)
    return cleaned_code, True

def create_enhanced_prompt(source_code, class_name, package_name):
    return f"""
Generate a comprehensive JUnit 5 test class for the following Java class.

STRICT REQUIREMENTS:
1. Use package declaration: package {package_name};
2. Include ALL necessary imports (JUnit 5, Mockito, assertions)
3. Use @ExtendWith(MockitoExtension.class) for the test class
4. Use @Mock for dependencies and @InjectMocks for the class under test
5. Include @Test annotations for all test methods
6. Test all public methods with positive, negative, and edge cases
7. Use meaningful test method names (shouldDoSomethingWhenCondition)
8. Include proper assertions (assertEquals, assertThrows, assertNotNull, etc.)
9. Ensure ALL braces are balanced and properly closed
10. Generate ONLY valid Java code without explanations or markdown

Class to test: {class_name}
Test class name should be: {class_name}Test

Source code:
{source_code}

Generate the complete test class with proper structure and balanced braces.
"""

def analyze_source_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        if not code.strip():
            return None, "Empty file"
        
        package_name = extract_package_name(code)
        if not package_name:
            print(f"⚠️  No package found in {file_path}, using default")
            package_name = "com.github.yildizmy"
        
        if not re.search(r'(class|interface|enum)\s+\w+', code):
            return None, "No class/interface/enum found"
        
        return {
            'code': code,
            'package': package_name
        }, None
        
    except Exception as e:
        return None, f"Error reading file: {e}"

def clean_generated_code(code_text):
    code_text = re.sub(r'```java\n?', '', code_text)
    code_text = re.sub(r'```\n?', '', code_text)
    lines = code_text.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('package ') or stripped.startswith('import ') or stripped.startswith('@') or stripped.startswith('public class'):
            start_idx = i
            break
    return '\n'.join(lines[start_idx:]).strip()

def extract_package_name(source_code):
    match = re.search(r'package\s+([\w\.]+);', source_code)
    return match.group(1) if match else ""

def generate_tests(access_token: str, project_id: str, source_code: str, class_name: str, package_name: str, out_dir: str, relative_path: str):
    models_to_try = [
        "claude-sonnet-4@20250514",
        "gemini-2.5-pro",
        "gemini-2.5-flash", 
        "gemini-2.0-flash-001",
        "gemini-2.0-flash-lite-001"
    ]
    
    for model_id in models_to_try:
        api_endpoint = (
            f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{project_id}"
            f"/locations/{LOCATION}/publishers/google/models/{model_id}:generateContent"
        )
        if try_generate_with_model(api_endpoint, access_token, source_code, class_name, package_name, out_dir, model_id):
            print(f"✅ Successfully used model: {model_id}")
            return True

    print(f"❌ All models failed for {class_name}")
    return False

def try_generate_with_model(api_endpoint: str, access_token: str, source_code: str, class_name: str, package_name: str, out_dir: str, model_id: str = ""):
    prompt = create_enhanced_prompt(source_code, class_name, package_name)

    request_body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.8,
            "maxOutputTokens": 64000
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_endpoint, headers=headers, json=request_body, timeout=180)

        if response.status_code == 404:
            print(f"⚠️  Model not found or not accessible: {model_id}")
            return False
        elif response.status_code in [403, 429]:
            print(f"⚠️  Error {response.status_code} for model {model_id}, skipping...")
            return False
        elif response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False

        prediction = response.json()
        output_text = prediction["candidates"][0]["content"]["parts"][0]["text"]
        final_code, _ = validate_and_fix_generated_code(output_text, class_name)

        test_file_name = f"{class_name}Test.java"
        test_file_path = Path(out_dir) / test_file_name

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(final_code)
        
        print(f"✅ Test class generated and saved to {test_file_path}")
        return True

    except Exception as e:
        print(f"❌ Exception during generation: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate JUnit 5 test classes using Vertex AI")
    parser.add_argument("--input_dir", type=str, required=True, help="Path to directory containing Java source files")
    parser.add_argument("--output_dir", type=str, required=True, help="Path to directory where test classes will be saved")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    if not os.path.isdir(input_dir):
        print(f"❌ Input directory does not exist: {input_dir}")
        return
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    access_token, project_id = get_access_token()
    java_files = [f for f in Path(input_dir).rglob("*.java") if "Test" not in f.name]

    if not java_files:
        print("⚠️  No Java source files found")
        return

    for file_path in java_files:
        relative_path = os.path.relpath(file_path, input_dir)
        print(f"\n📄 Processing {relative_path}")
        result, error = analyze_source_file(file_path)

        if error:
            print(f"⚠️  Skipping file due to: {error}")
            continue

        class_name_match = re.search(r'public\s+class\s+(\w+)', result['code'])
        if not class_name_match:
            print("⚠️  Could not extract class name")
            continue

        class_name = class_name_match.group(1)
        success = generate_tests(access_token, project_id, result['code'], class_name, result['package'], output_dir, relative_path)

        if not success:
            print(f"❌ Failed to generate test for {class_name}")

if __name__ == "__main__":
    main()
