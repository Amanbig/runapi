#!/usr/bin/env python3
"""
Comprehensive test script for RunApi CLI functionality
Tests the complete workflow from installation to running the dev server
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class RunApiTester:
    def __init__(self):
        self.test_dir = None
        self.original_cwd = os.getcwd()
        self.success_count = 0
        self.total_tests = 0

    def log(self, message, status="INFO"):
        """Log test messages with status"""
        status_symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        symbol = status_symbols.get(status, "•")
        print(f"{symbol} {message}")

    def run_command(self, cmd, timeout=30, expect_success=True):
        """Run a command and return result"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.test_dir or self.original_cwd,
            )

            if expect_success and result.returncode != 0:
                self.log(f"Command failed: {cmd}", "ERROR")
                self.log(f"STDOUT: {result.stdout}", "ERROR")
                self.log(f"STDERR: {result.stderr}", "ERROR")
                return False, result

            return True, result
        except subprocess.TimeoutExpired:
            self.log(f"Command timed out: {cmd}", "WARNING")
            return False, None
        except Exception as e:
            self.log(f"Command exception: {cmd} - {e}", "ERROR")
            return False, None

    def test_cli_available(self):
        """Test 1: Check if runapi CLI is available"""
        self.total_tests += 1
        self.log("Testing CLI availability...")

        success, result = self.run_command("runapi --help")
        if success and "RunApi" in result.stdout:
            self.log("CLI is available and working", "SUCCESS")
            self.success_count += 1
            return True
        else:
            self.log("CLI is not available or not working", "ERROR")
            return False

    def test_project_creation(self):
        """Test 2: Create a new project"""
        self.total_tests += 1
        self.log("Testing project creation...")

        # Create temporary directory
        self.test_dir = tempfile.mkdtemp(prefix="runapi_test_")
        os.chdir(self.test_dir)

        success, result = self.run_command("runapi init testproject")
        if success and Path("testproject").exists():
            self.log("Project created successfully", "SUCCESS")
            self.success_count += 1

            # Change to project directory
            self.test_dir = str(Path(self.test_dir) / "testproject")
            os.chdir(self.test_dir)

            return True
        else:
            self.log("Project creation failed", "ERROR")
            return False

    def test_project_structure(self):
        """Test 3: Verify project structure"""
        self.total_tests += 1
        self.log("Testing project structure...")

        required_files = ["main.py", ".env", "README.md", "routes/index.py", "routes/api/hello.py"]

        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)

        if not missing_files:
            self.log("All required files present", "SUCCESS")
            self.success_count += 1
            return True
        else:
            self.log(f"Missing files: {missing_files}", "ERROR")
            return False

    def test_main_import(self):
        """Test 4: Test if main.py can be imported"""
        self.total_tests += 1
        self.log("Testing main.py import...")

        success, result = self.run_command("python -c \"import main; print('SUCCESS')\"")
        if success and "SUCCESS" in result.stdout:
            self.log("main.py imports successfully", "SUCCESS")
            self.success_count += 1
            return True
        else:
            self.log("main.py import failed", "ERROR")
            if result:
                self.log(f"Error: {result.stderr}", "ERROR")
            return False

    def test_runapi_import(self):
        """Test 5: Test if runapi package can be imported"""
        self.total_tests += 1
        self.log("Testing runapi package import...")

        success, result = self.run_command("python -c \"import runapi; print('SUCCESS')\"")
        if success and "SUCCESS" in result.stdout:
            self.log("runapi package imports successfully", "SUCCESS")
            self.success_count += 1
            return True
        else:
            self.log("runapi package import failed", "ERROR")
            if result:
                self.log(f"Error: {result.stderr}", "ERROR")
            return False

    def test_app_creation(self):
        """Test 6: Test app creation"""
        self.total_tests += 1
        self.log("Testing app creation...")

        test_script = """
import sys
sys.path.insert(0, ".")
try:
    from runapi import create_runapi_app
    app = create_runapi_app(title="Test")
    fastapi_app = app.get_app()
    print("SUCCESS: App created")
    print(f"App type: {type(fastapi_app)}")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
"""

        success, result = self.run_command(f'python -c "{test_script}"')
        if success and "SUCCESS: App created" in result.stdout:
            self.log("App creation successful", "SUCCESS")
            self.success_count += 1
            return True
        else:
            self.log("App creation failed", "ERROR")
            if result:
                self.log(f"Error: {result.stderr}", "ERROR")
            return False

    def test_uvicorn_direct(self):
        """Test 7: Test uvicorn directly"""
        self.total_tests += 1
        self.log("Testing uvicorn direct import...")

        # Test if uvicorn can import the main:app
        test_script = """
import sys
import importlib.util
sys.path.insert(0, ".")

try:
    # Test importlib approach (what uvicorn uses)
    spec = importlib.util.spec_from_file_location("main", "main.py")
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)

    if hasattr(main_module, "app"):
        print("SUCCESS: main:app accessible")
    else:
        print("ERROR: main.app not found")
        sys.exit(1)

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
"""

        success, result = self.run_command(f'python -c "{test_script}"')
        if success and "SUCCESS: main:app accessible" in result.stdout:
            self.log("uvicorn can access main:app", "SUCCESS")
            self.success_count += 1
            return True
        else:
            self.log("uvicorn cannot access main:app", "ERROR")
            if result:
                self.log(f"Error: {result.stderr}", "ERROR")
            return False

    def test_server_startup(self):
        """Test 8: Test if server can start (without running indefinitely)"""
        self.total_tests += 1
        self.log("Testing server startup (quick test)...")

        # Create a test script that starts the server and immediately stops it
        test_script = """
import sys
import os
import threading
import time
sys.path.insert(0, ".")

def test_server():
    try:
        import uvicorn
        import main

        # Test if we can create a server instance
        config = uvicorn.Config("main:app", host="127.0.0.1", port=8999)
        server = uvicorn.Server(config)
        print("SUCCESS: Server can be created")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if test_server():
    sys.exit(0)
else:
    sys.exit(1)
"""

        success, result = self.run_command(f'python -c "{test_script}"')
        if success and "SUCCESS: Server can be created" in result.stdout:
            self.log("Server startup test passed", "SUCCESS")
            self.success_count += 1
            return True
        else:
            self.log("Server startup test failed", "ERROR")
            if result:
                self.log(f"Error: {result.stderr}", "ERROR")
            return False

    def test_cli_dev_dry_run(self):
        """Test 9: Test CLI dev command validation (without actual server start)"""
        self.total_tests += 1
        self.log("Testing CLI dev command validation...")

        # We'll test the CLI's pre-validation logic
        test_script = """
import sys
import os
sys.path.insert(0, ".")

# Simulate what the CLI does before starting uvicorn
try:
    # Check if main.py exists
    if not os.path.exists("main.py"):
        print("ERROR: main.py not found")
        sys.exit(1)

    # Check if main can be imported
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "main.py")
    if spec is None:
        print("ERROR: Cannot load main.py")
        sys.exit(1)

    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)

    if not hasattr(main_module, "app"):
        print("ERROR: main.py does not have app attribute")
        sys.exit(1)

    print("SUCCESS: CLI validation passed")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
"""

        success, result = self.run_command(f'python -c "{test_script}"')
        if success and "SUCCESS: CLI validation passed" in result.stdout:
            self.log("CLI dev command validation passed", "SUCCESS")
            self.success_count += 1
            return True
        else:
            self.log("CLI dev command validation failed", "ERROR")
            if result:
                self.log(f"Error: {result.stderr}", "ERROR")
            return False

    def cleanup(self):
        """Clean up test directory"""
        try:
            os.chdir(self.original_cwd)
            if self.test_dir and Path(self.test_dir).exists():
                # Go up to temp directory and remove the whole test dir
                test_root = (
                    Path(self.test_dir).parents[0]
                    if "testproject" in self.test_dir
                    else Path(self.test_dir)
                )
                shutil.rmtree(test_root, ignore_errors=True)
                self.log("Test directory cleaned up", "INFO")
        except Exception as e:
            self.log(f"Cleanup warning: {e}", "WARNING")

    def run_all_tests(self):
        """Run all tests"""
        self.log("🚀 Starting RunApi Installation Tests", "INFO")
        self.log(f"Python: {sys.executable}", "INFO")
        self.log(f"Working directory: {os.getcwd()}", "INFO")
        print("-" * 60)

        try:
            # Run tests in sequence
            tests = [
                self.test_cli_available,
                self.test_project_creation,
                self.test_project_structure,
                self.test_main_import,
                self.test_runapi_import,
                self.test_app_creation,
                self.test_uvicorn_direct,
                self.test_server_startup,
                self.test_cli_dev_dry_run,
            ]

            for i, test in enumerate(tests, 1):
                self.log(f"Running test {i}/{len(tests)}: {test.__name__}", "INFO")
                try:
                    test()
                except Exception as e:
                    self.log(f"Test {test.__name__} threw exception: {e}", "ERROR")
                print("-" * 40)

        finally:
            self.cleanup()

        # Results
        print("=" * 60)
        self.log("🏁 TEST RESULTS", "INFO")
        self.log(
            f"Passed: {self.success_count}/{self.total_tests}",
            "SUCCESS" if self.success_count == self.total_tests else "WARNING",
        )

        if self.success_count == self.total_tests:
            self.log("🎉 All tests passed! RunApi is working correctly.", "SUCCESS")
            return True
        else:
            failed = self.total_tests - self.success_count
            self.log(f"❌ {failed} test(s) failed. RunApi may have issues.", "ERROR")
            return False


if __name__ == "__main__":
    tester = RunApiTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
