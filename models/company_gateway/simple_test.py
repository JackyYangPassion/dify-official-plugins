#!/usr/bin/env python3
"""
Simple test script to validate plugin structure (no external dependencies)
"""

import os
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

def test_model_files():
    """Test model configuration files exist"""
    print("\n🔍 Testing model files...")
    
    plugin_dir = Path(__file__).parent
    model_dir = plugin_dir / "models/llm"
    
    expected_models = [
        "gpt4-128k.yaml",
        "qwen-plus.yaml", 
        "qwen-turbo.yaml",
        "deepseek-chat.yaml",
        "deepseek-coder.yaml",
        "doubao-pro.yaml",
        "doubao-lite.yaml"
    ]
    
    missing_models = []
    for model_file in expected_models:
        if not (model_dir / model_file).exists():
            missing_models.append(model_file)
    
    if missing_models:
        print(f"❌ Missing model files: {missing_models}")
        return False
    else:
        print(f"✅ All {len(expected_models)} model files present")
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

def test_file_sizes():
    """Test reasonable file sizes"""
    print("\n🔍 Testing file sizes...")
    
    plugin_dir = Path(__file__).parent
    
    # Check main implementation files are not empty
    important_files = [
        "models/llm/llm.py",
        "models/common_gateway.py",
        "provider/company_gateway.py"
    ]
    
    for file_path in important_files:
        full_path = plugin_dir / file_path
        size = full_path.stat().st_size
        if size < 100:  # Too small
            print(f"❌ {file_path} seems too small ({size} bytes)")
            return False
        elif size > 100000:  # Too large 
            print(f"⚠️  {file_path} seems large ({size} bytes)")
        else:
            print(f"✅ {file_path} - {size} bytes")
    
    return True

def generate_plugin_info():
    """Generate plugin information"""
    print("\n📋 Plugin Information:")
    print("=" * 50)
    
    plugin_dir = Path(__file__).parent
    
    # Count files
    all_files = list(plugin_dir.rglob('*'))
    file_count = len([f for f in all_files if f.is_file()])
    total_size = sum(f.stat().st_size for f in all_files if f.is_file())
    
    print(f"Plugin Directory: {plugin_dir.name}")
    print(f"Total Files: {file_count}")
    print(f"Total Size: {total_size / 1024:.1f} KB")
    
    # List model files
    model_files = list((plugin_dir / "models/llm").glob("*.yaml"))
    print(f"\nSupported Models ({len(model_files)}):")
    for model_file in sorted(model_files):
        model_name = model_file.stem
        print(f"  - {model_name}")
    
    print(f"\nKey Files:")
    key_files = [
        "manifest.yaml",
        "provider/company_gateway.yaml", 
        "models/llm/llm.py",
        "README.md"
    ]
    
    for key_file in key_files:
        file_path = plugin_dir / key_file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  - {key_file}: {size} bytes")

def main():
    """Run all tests"""
    print("🚀 Company Gateway Plugin Simple Test")
    print("=" * 50)
    
    tests = [
        test_plugin_structure,
        test_model_files,
        test_python_syntax,
        test_file_sizes,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 Plugin structure validation passed!")
        generate_plugin_info()
        
        print(f"\n🚀 Next Steps:")
        print("1. Install the plugin in your Dify instance")
        print("2. Configure gateway URL and API credentials")
        print("3. Test model connectivity")
        print("4. Start using the models in your applications")
        
        return True
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    main()
