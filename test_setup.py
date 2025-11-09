#!/usr/bin/env python3
"""
Quick setup test script to verify the code generator is ready to run
"""
import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from dotenv import load_dotenv
        print("  [OK] python-dotenv")
    except ImportError:
        print("  [FAIL] python-dotenv - Install with: pip install python-dotenv")
        return False
    
    try:
        from langchain_anthropic import ChatAnthropic
        print("  [OK] langchain-anthropic")
    except ImportError:
        print("  [FAIL] langchain-anthropic - Install with: pip install langchain-anthropic")
        return False
    
    try:
        from langgraph.graph import StateGraph
        print("  [OK] langgraph")
    except ImportError:
        print("  [FAIL] langgraph - Install with: pip install langgraph")
        return False
    
    try:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        print("  [OK] langgraph-checkpoint-sqlite")
    except ImportError:
        print("  [FAIL] langgraph-checkpoint-sqlite - Install with: pip install langgraph-checkpoint-sqlite")
        return False
    
    try:
        from rich.console import Console
        print("  [OK] rich")
    except ImportError:
        print("  [FAIL] rich - Install with: pip install rich")
        return False
    
    return True

def test_env():
    """Test if .env file exists and has API key"""
    print("\nTesting environment...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"  [OK] ANTHROPIC_API_KEY is set (length: {len(api_key)})")
        return True
    else:
        print("  [FAIL] ANTHROPIC_API_KEY not found in .env file")
        print("     Create a .env file with: ANTHROPIC_API_KEY=your_key_here")
        return False

def test_agent_import():
    """Test if agent module can be imported"""
    print("\nTesting agent module...")
    
    try:
        from agent import CodeGeneratorAgent
        print("  [OK] CodeGeneratorAgent can be imported")
        return True
    except ImportError as e:
        print(f"  [FAIL] Cannot import CodeGeneratorAgent: {e}")
        return False
    except Exception as e:
        print(f"  [WARN] Import succeeded but error occurred: {e}")
        return True  # Import worked, other error

def main():
    """Run all tests"""
    import io
    import sys
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 60)
    print("Code Generator Setup Test")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test environment
    results.append(("Environment", test_env()))
    
    # Test agent import
    results.append(("Agent Module", test_agent_import()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed! You're ready to run the code generator.")
        print("\n   Run: python main.py")
    else:
        print("Some tests failed. Please fix the issues above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

