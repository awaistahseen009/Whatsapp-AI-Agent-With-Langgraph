#!/usr/bin/env python3
"""
Script to run all tests with proper environment setup
"""
import subprocess
import sys
import os

def run_command(cmd, cwd=None):
    """Run command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=600)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def main():
    print("=" * 80)
    print("RUNNING ALL TESTS WITH AGENT RESPONSE TESTING")
    print("=" * 80)
    
    backend_dir = "backend"
    
    if not os.path.exists(backend_dir):
        print("❌ Backend directory not found")
        return
    
    print(f"📁 Directory: {os.path.abspath(backend_dir)}")
    print("🔧 Running comprehensive test suite...")
    
    # Set environment variables for testing (CI pipeline)
    env_vars = {
        "GROQ_API_KEY": "test_groq_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key", 
        "ELEVEN_LABS_API_KEY": "test_eleven_key",
        "OPENAI_API_KEY": "test_openai_key"
    }
    
    # Export environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"🔑 Setting {key}=***")
    
    # Activate virtual environment and run tests
    activate_cmd = "venv\\Scripts\\Activate.ps1"
    test_cmd = "python -m pytest tests/ -v --tb=short --maxfail=20"
    
    print(f"\n🧪 Running: {test_cmd}")
    print("📊 Expected test coverage:")
    print("   ✅ Auth Routes (8 tests)")
    print("   ✅ Chat Routes (3 tests)")
    print("   ✅ Client Routes (2 tests)")
    print("   ✅ Property Routes (4 tests)")
    print("   ✅ Agent Response (10 tests)")
    print("   ✅ Agent Multimedia (9 tests)")
    print("   ✅ Utils Tests (1 test)")
    print("   ✅ Escalation Tests (1 test)")
    print("   ✅ Log Routes (1 test)")
    print("   ✅ Meeting Routes (1 test)")
    print("   📈 Total: ~40 tests")
    
    print("\n" + "=" * 80)
    
    # Run tests
    returncode, stdout, stderr = run_command(f"{activate_cmd} && {test_cmd}", cwd=backend_dir)
    
    if returncode == 0:
        print("✅ All tests completed successfully!")
    else:
        print(f"❌ Tests failed with exit code: {returncode}")
    
    print("\n📋 TEST OUTPUT:")
    print("-" * 40)
    if stdout:
        print(stdout)
    if stderr:
        print("STDERR:", stderr)
    
    print("\n" + "=" * 80)
    print("TEST EXECUTION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
