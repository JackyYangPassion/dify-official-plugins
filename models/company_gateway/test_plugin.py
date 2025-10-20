#!/usr/bin/env python3
"""
Simple test script to validate plugin structure and configuration
"""

import os
import yaml
import json
from pathlib import Path

def test_plugin_structure():
    """Test plugin directory structure"""
    print("🔍 Testing plugin structure...")
    
    plugin_dir = Path(__file__).parent
    required_files = [
        "manifest.yaml",
        "requirements.txt",
        "main.py",
        "README.md",
        "_assets/icon.svg",
        "provider/company_gateway.yaml",
        "provider/company_gateway.py",
        "models/common_gateway.py",
        "models/llm/llm.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (plugin_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_yaml_files():
    """Test YAML file validity"""
    print("\n🔍 Testing YAML files...")
    
    plugin_dir = Path(__file__).parent
    yaml_files = [
        "manifest.yaml",
        "provider/company_gateway.yaml",
        "models/llm/gpt4-128k.yaml",
        "models/llm/qwen-plus.yaml",
        "models/llm/qwen-turbo.yaml",
        "models/llm/deepseek-chat.yaml",
        "models/llm/deepseek-coder.yaml",
        "models/llm/doubao-pro.yaml",
        "models/llm/doubao-lite.yaml",
    ]
    
    for yaml_file in yaml_files:
        file_path = plugin_dir / yaml_file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print(f"✅ {yaml_file} - Valid YAML")
        except Exception as e:
            print(f"❌ {yaml_file} - Invalid YAML: {e}")
            return False
    
    return True

def test_manifest():
    """Test manifest.yaml content"""
    print("\n🔍 Testing manifest.yaml...")
    
    plugin_dir = Path(__file__).parent
    manifest_path = plugin_dir / "manifest.yaml"
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = yaml.safe_load(f)
        
        required_fields = ['version', 'type', 'author', 'name', 'description', 'label', 'created_at']
        missing_fields = [field for field in required_fields if field not in manifest]
        
        if missing_fields:
            print(f"❌ Missing manifest fields: {missing_fields}")
            return False
        
        print("✅ Manifest structure valid")
        print(f"   Plugin: {manifest['name']} v{manifest['version']}")
        print(f"   Author: {manifest['author']}")
        return True
        
    except Exception as e:
        print(f"❌ Manifest error: {e}")
        return False

def test_provider_config():
    """Test provider configuration"""
    print("\n🔍 Testing provider configuration...")
    
    plugin_dir = Path(__file__).parent
    provider_path = plugin_dir / "provider/company_gateway.yaml"
    
    try:
        with open(provider_path, 'r', encoding='utf-8') as f:
            provider = yaml.safe_load(f)
        
        required_fields = ['provider', 'label', 'description', 'supported_model_types']
        missing_fields = [field for field in required_fields if field not in provider]
        
        if missing_fields:
            print(f"❌ Missing provider fields: {missing_fields}")
            return False
        
        if 'llm' not in provider['supported_model_types']:
            print("❌ LLM model type not supported")
            return False
        
        print("✅ Provider configuration valid")
        print(f"   Provider: {provider['provider']}")
        print(f"   Supported types: {provider['supported_model_types']}")
        return True
        
    except Exception as e:
        print(f"❌ Provider config error: {e}")
        return False

def test_model_configs():
    """Test model configuration files"""
    print("\n🔍 Testing model configurations...")
    
    plugin_dir = Path(__file__).parent
    model_files = list((plugin_dir / "models/llm").glob("*.yaml"))
    
    if not model_files:
        print("❌ No model configuration files found")
        return False
    
    for model_file in model_files:
        try:
            with open(model_file, 'r', encoding='utf-8') as f:
                model_config = yaml.safe_load(f)
            
            required_fields = ['model', 'label', 'model_type', 'model_properties']
            missing_fields = [field for field in required_fields if field not in model_config]
            
            if missing_fields:
                print(f"❌ {model_file.name} missing fields: {missing_fields}")
                return False
            
            print(f"✅ {model_file.name} - Valid model config")
            
        except Exception as e:
            print(f"❌ {model_file.name} error: {e}")
            return False
    
    print(f"✅ All {len(model_files)} model configs valid")
    return True

def test_python_syntax():
    """Test Python file syntax"""
    print("\n🔍 Testing Python syntax...")
    
    plugin_dir = Path(__file__).parent
    python_files = [
        "main.py",
        "provider/company_gateway.py",
        "models/common_gateway.py",
        "models/llm/llm.py",
    ]
    
    for py_file in python_files:
        file_path = plugin_dir / py_file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Basic syntax check
            compile(code, file_path, 'exec')
            print(f"✅ {py_file} - Valid Python syntax")
            
        except Exception as e:
            print(f"❌ {py_file} syntax error: {e}")
            return False
    
    return True

def generate_summary():
    """Generate plugin summary"""
    print("\n📋 Plugin Summary:")
    print("=" * 50)
    
    plugin_dir = Path(__file__).parent
    
    # Read manifest
    with open(plugin_dir / "manifest.yaml", 'r', encoding='utf-8') as f:
        manifest = yaml.safe_load(f)
    
    print(f"Plugin Name: {manifest['name']}")
    print(f"Version: {manifest['version']}")
    print(f"Author: {manifest['author']}")
    print(f"Type: {manifest['type']}")
    
    # Count models
    model_files = list((plugin_dir / "models/llm").glob("*.yaml"))
    print(f"Supported Models: {len(model_files)}")
    
    for model_file in model_files:
        with open(model_file, 'r', encoding='utf-8') as f:
            model_config = yaml.safe_load(f)
        print(f"  - {model_config['model']}: {model_config['label']['en_US']}")
    
    print(f"\nPlugin Size: {sum(f.stat().st_size for f in plugin_dir.rglob('*') if f.is_file()) / 1024:.1f} KB")

def main():
    """Run all tests"""
    print("🚀 Company Gateway Plugin Test Suite")
    print("=" * 50)
    
    tests = [
        test_plugin_structure,
        test_yaml_files,
        test_manifest,
        test_provider_config,
        test_model_configs,
        test_python_syntax,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Plugin is ready for deployment.")
        generate_summary()
        return True
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    main()
