#!/usr/bin/env python3
"""
Simple test script to verify HugeGraph Dify plugin structure and basic functionality
"""

import os
import sys
import yaml
import json
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

def test_yaml_files():
    """Test YAML files are valid"""
    print("\nTesting YAML files...")

    yaml_files = [
        "../dify_hugegraph/manifest.yaml",
        "../dify_hugegraph/provider/hugegraph_query.yaml",
        "../dify_hugegraph/tools/hugegraph_query.yaml"
    ]

    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print(f"✓ {yaml_file} is valid YAML")
        except Exception as e:
            print(f"✗ {yaml_file} is invalid: {e}")
            return False

    return True

def test_python_imports():
    """Test that Python files can be imported"""
    print("\nTesting Python imports...")

    # Add the plugin directory to path
    sys.path.insert(0, "../dify_hugegraph")

    try:
        # Test importing the main module
        import main
        print("✓ main.py imports successfully")

        # Test importing provider (might fail due to dify_plugin dependency)
        try:
            from provider import hugegraph_query
            print("✓ provider/hugegraph_query.py imports successfully")
        except ImportError as e:
            print(f"⚠ provider/hugegraph_query.py import warning (expected): {e}")

        # Test importing tool (might fail due to dify_plugin dependency)
        try:
            from tools import hugegraph_query as tool
            print("✓ tools/hugegraph_query.py imports successfully")
        except ImportError as e:
            print(f"⚠ tools/hugegraph_query.py import warning (expected): {e}")

    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

    return True

def test_configuration_completeness():
    """Test that configuration files have required fields"""
    print("\nTesting configuration completeness...")

    # Test manifest.yaml
    try:
        with open("../dify_hugegraph/manifest.yaml", 'r') as f:
            manifest = yaml.safe_load(f)

        required_manifest_fields = ["version", "type", "author", "name", "plugins"]
        for field in required_manifest_fields:
            if field not in manifest:
                print(f"✗ manifest.yaml missing field: {field}")
                return False

        print("✓ manifest.yaml has all required fields")

    except Exception as e:
        print(f"✗ manifest.yaml error: {e}")
        return False

    # Test provider config
    try:
        with open("../dify_hugegraph/provider/hugegraph_query.yaml", 'r') as f:
            provider_config = yaml.safe_load(f)

        if "credentials_for_provider" not in provider_config:
            print("✗ provider config missing credentials_for_provider")
            return False

        required_credentials = ["HOST", "PORT", "GRAPH"]
        for cred in required_credentials:
            if cred not in provider_config["credentials_for_provider"]:
                print(f"✗ provider config missing credential: {cred}")
                return False

        print("✓ provider configuration is complete")

    except Exception as e:
        print(f"✗ provider config error: {e}")
        return False

    return True

def main():
    """Run all tests"""
    print("HugeGraph Dify Plugin Structure Test")
    print("=" * 40)

    tests = [
        test_plugin_structure,
        test_yaml_files,
        test_python_imports,
        test_configuration_completeness
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