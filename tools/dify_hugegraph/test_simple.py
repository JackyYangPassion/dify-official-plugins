#!/usr/bin/env python3
"""
Simple test script to verify HugeGraph Dify plugin structure
"""

import os
import sys
from pathlib import Path

def test_plugin_structure():
    """Test that all required files exist"""
    print("Testing plugin structure...")

    required_files = [
        "manifest.yaml",
        "main.py",
        "requirements.txt",
        "README.md",
        "PRIVACY.md",
        "_assets/icon.svg",
        "provider/hugegraph_query.py",
        "provider/hugegraph_query.yaml",
        "tools/hugegraph_query.py",
        "tools/hugegraph_query.yaml"
    ]

    base_path = Path("../dify_hugegraph")
    missing_files = []

    for file in required_files:
        file_path = base_path / file
        if not file_path.exists():
            missing_files.append(file)
        else:
            print(f"✓ {file}")

    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False

    print("✓ All required files exist")
    return True

def test_file_sizes():
    """Test that files have reasonable content"""
    print("\nTesting file sizes...")

    base_path = Path("../dify_hugegraph")

    # Check that Python files are not empty
    python_files = [
        "main.py",
        "provider/hugegraph_query.py",
        "tools/hugegraph_query.py"
    ]

    for file in python_files:
        file_path = base_path / file
        if file_path.stat().st_size < 100:  # At least 100 bytes
            print(f"✗ {file} seems too small")
            return False
        else:
            print(f"✓ {file} has reasonable size ({file_path.stat().st_size} bytes)")

    # Check YAML files
    yaml_files = [
        "manifest.yaml",
        "provider/hugegraph_query.yaml",
        "tools/hugegraph_query.yaml"
    ]

    for file in yaml_files:
        file_path = base_path / file
        if file_path.stat().st_size < 50:  # At least 50 bytes
            print(f"✗ {file} seems too small")
            return False
        else:
            print(f"✓ {file} has reasonable size ({file_path.stat().st_size} bytes)")

    return True

def test_basic_content():
    """Test basic content patterns"""
    print("\nTesting basic content...")

    base_path = Path("../dify_hugegraph")

    # Check manifest has basic structure
    manifest_path = base_path / "manifest.yaml"
    with open(manifest_path, 'r') as f:
        manifest_content = f.read()

    if "hugegraph_query" not in manifest_content:
        print("✗ manifest.yaml doesn't contain 'hugegraph_query'")
        return False

    if "version:" not in manifest_content:
        print("✗ manifest.yaml doesn't contain 'version:'")
        return False

    print("✓ manifest.yaml has basic content")

    # Check tools have required classes
    tools_path = base_path / "tools/hugegraph_query.py"
    with open(tools_path, 'r') as f:
        tools_content = f.read()

    if "class HugeGraphQueryTool" not in tools_content:
        print("✗ tools/hugegraph_query.py doesn't contain HugeGraphQueryTool class")
        return False

    if "_invoke" not in tools_content:
        print("✗ tools/hugegraph_query.py doesn't contain _invoke method")
        return False

    print("✓ tools/hugegraph_query.py has required content")

    # Check provider has required class
    provider_path = base_path / "provider/hugegraph_query.py"
    with open(provider_path, 'r') as f:
        provider_content = f.read()

    if "class HugeGraphQueryProvider" not in provider_content:
        print("✗ provider/hugegraph_query.py doesn't contain HugeGraphQueryProvider class")
        return False

    if "_validate_credentials" not in provider_content:
        print("✗ provider/hugegraph_query.py doesn't contain _validate_credentials method")
        return False

    print("✓ provider/hugegraph_query.py has required content")

    return True

def main():
    """Run all tests"""
    print("HugeGraph Dify Plugin Structure Test")
    print("=" * 40)

    tests = [
        test_plugin_structure,
        test_file_sizes,
        test_basic_content
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All tests passed! Plugin structure is valid.")
    else:
        print("✗ Some tests failed. Please review the issues above.")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)