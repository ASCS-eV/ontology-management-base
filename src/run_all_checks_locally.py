import os
import subprocess
import sys

# Define the root directory of the repository and the source folder for scripts
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")

# Explicitly excluded folders
EXCLUDED_FOLDERS = {"src"}


def get_ontology_dirs():
    """Return non-hidden directories in ROOT_DIR that are not explicitly excluded."""
    return [
        folder
        for folder in os.listdir(ROOT_DIR)
        if os.path.isdir(os.path.join(ROOT_DIR, folder))
        and folder not in EXCLUDED_FOLDERS
        and not folder.startswith(".")
    ]


ONTOLOGY_DIRS = get_ontology_dirs()
print(f"Detected ontology directories: {ONTOLOGY_DIRS}")
print("\n🚀 Running all ontology validation checks...")


def run_command(command, description):
    """Execute a command and print its raw output."""
    print(f"\n🔍 {description}")
    try:
        result = subprocess.run(
            command, shell=False, capture_output=True, text=True, check=True
        )
        output = result.stdout.strip() + "\n" + result.stderr.strip()
        print(output)
        return result.returncode, output
    except subprocess.CalledProcessError as e:
        output = e.stdout.strip() + "\n" + e.stderr.strip()
        print(f"❌ Error during {description}:\n{output}", file=sys.stderr)
        sys.exit(1)


def check_ttl_syntax():
    """Check the syntax of all Turtle (.ttl) files in each ontology folder."""
    print("\n=== Checking TTL syntax ===")
    for ontology in ONTOLOGY_DIRS:
        folder_path = os.path.join(ROOT_DIR, ontology)
        print(f"\n🔍 Starting TTL syntax tests for folder: {ontology}")
        ttl_files = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.endswith(".ttl")
        ]
        if not ttl_files:
            print(f"⚠️  No .ttl files found in folder: {ontology}")
        for ttl_file in ttl_files:
            print(f"🔍 Checking syntax of {ttl_file}...")
            returncode, _ = run_command(
                [
                    sys.executable,
                    os.path.join(SRC_DIR, "check_ttl_syntax.py"),
                    ttl_file,
                ],
                f"TTL syntax check for {ttl_file}",
            )
            if returncode != 0:
                print(f"❌ {ttl_file} failed syntax check!")
                sys.exit(1)
            else:
                print(f"✅ {ttl_file} passed syntax check.")
        print(f"📌 Completed TTL syntax tests for folder: {ontology}")


def check_jsonld_against_shacl():
    """Validate JSON-LD files against SHACL schemas for each ontology folder."""
    print("\n=== Checking JSON-LD against SHACL ===")
    for ontology in ONTOLOGY_DIRS:
        folder_path = os.path.join(ROOT_DIR, ontology)
        print(f"\n🔍 Starting JSON-LD SHACL validation for folder: {ontology}")
        returncode, output = run_command(
            [
                sys.executable,
                os.path.join(SRC_DIR, "check_jsonld_against_shacl_schema.py"),
                folder_path,
            ],
            f"JSON-LD SHACL validation for {folder_path}",
        )
        if returncode != 0:
            print(f"❌ JSON-LD SHACL validation failed for folder: {ontology}.")
            sys.exit(1)
        else:
            print(f"✅ {ontology} conforms to SHACL constraints.")
        print(f"📌 Completed JSON-LD SHACL validation for folder: {ontology}")


def check_failing_tests():
    """Run failing test cases in the tests/ subfolder of each ontology."""
    print("\n=== Running failing tests ===")
    for ontology in ONTOLOGY_DIRS:
        folder_path = os.path.join(ROOT_DIR, ontology)
        test_folder = os.path.join(folder_path, "tests")
        if not os.path.exists(test_folder):
            print(f"⚠️  No tests folder found in {ontology}, skipping failing tests.")
            continue

        print(f"\n🔍 Running failing tests in folder: {ontology}")
        # Select test files starting with "fail" and ending with ".json"
        fail_tests = [
            f
            for f in os.listdir(test_folder)
            if f.startswith("fail") and f.endswith(".json")
        ]
        if not fail_tests:
            print(f"⚠️  No failing test files found in {ontology}.")
        for test in fail_tests:
            test_path = os.path.join(test_folder, test)
            print(f"🔍 Running failing test: {test_path} in folder: {ontology}")
            returncode, _ = run_command(
                [
                    sys.executable,
                    os.path.join(SRC_DIR, "check_jsonld_against_shacl_schema.py"),
                    test_path,
                ],
                f"Failing test validation for {test_path}",
            )
            # Failing tests should have a non-zero exit code.
            if returncode == 0:
                print(f"❌ Test {test} in folder {ontology} should fail but passed!")
                sys.exit(1)
            else:
                print(f"✅ Test {test} in folder {ontology} failed as expected.")
        print(f"📌 Completed failing tests for folder: {ontology}")


def main():
    """Run all three checks sequentially."""
    check_ttl_syntax()
    check_jsonld_against_shacl()
    check_failing_tests()
    print("\n✅ All checks completed successfully!")


if __name__ == "__main__":
    main()
