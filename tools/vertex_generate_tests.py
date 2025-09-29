import os
import argparse
import subprocess
import time

def should_skip_file(file_path):
    """Check if file should be skipped for test generation."""
    skip_patterns = [
        'Test.java',
        'Tests.java',
        'Application.java',
        'Config.java'
    ]
    filename = os.path.basename(file_path)
    return any(pattern in filename for pattern in skip_patterns)

def run_evosuite(target_class, working_dir="backend"):
    """Run EvoSuite test generation for a given class."""
    try:
        print(f"📝 Running EvoSuite for: {target_class}")
        result = subprocess.run(
            ["mvn", "evosuite:generate", f"-Devosuite.targetClass={target_class}"],
            cwd=working_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Success: {target_class}")
            return True
        else:
            print(f"❌ Failed: {target_class}")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running EvoSuite for {target_class}: {e}")
        return False

if _name_ == "_main_":
    parser = argparse.ArgumentParser(description="Generate JUnit tests using EvoSuite")
    parser.add_argument("--source_dir", 
                       default="backend/src/main/java/com/github/yildizmy/service", 
                       help="Directory with source .java files")
    parser.add_argument("--working_dir", 
                       default="backend", 
                       help="Project root directory (where pom.xml is located)")
    args = parser.parse_args()

    if not os.path.exists(args.source_dir):
        print(f"❌ Source directory does not exist: {args.source_dir}")
        exit(1)

    successful, failed = 0, 0

    print(f"🔍 Scanning for Java files in: {args.source_dir}")

    for root, _, files in os.walk(args.source_dir):
        for file in files:
            if file.endswith(".java") and not should_skip_file(file):
                file_path = os.path.join(root, file)
                class_name = file[:-5]  # Remove .java

                # Infer fully qualified class name
                relative_path = os.path.relpath(file_path, "backend/src/main/java")
                target_class = relative_path.replace("/", ".").replace("\\", ".")[:-5]

                if run_evosuite(target_class, args.working_dir):
                    successful += 1
                else:
                    failed += 1
                
                time.sleep(1)  # small delay

    print("\n📊 Test Generation Summary:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")

    if failed > 0:
        exit(1)
