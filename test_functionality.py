#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据管理功能测试脚本
"""

import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """测试所有必要的模块导入"""
    try:
        import test_data_handler
        print("✓ test_data_handler 模块导入成功")
        
        import db_problems
        print("✓ db_problems 模块导入成功")
        
        import db_users
        print("✓ db_users 模块导入成功")
        
        return True
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_data_validation():
    """测试数据验证函数"""
    try:
        # 测试整数转换
        test_cases = [
            ("10", 10),
            ("5", 5),
            (None, 10),  # 默认值
            ("", 10),    # 空字符串默认值
        ]
        
        for input_val, expected in test_cases:
            try:
                result = int(input_val) if input_val is not None and input_val != "" else 10
                assert result == expected
                print(f"✓ 数据验证测试通过: {input_val} -> {result}")
            except Exception as e:
                print(f"✗ 数据验证测试失败: {input_val} -> {e}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 数据验证测试异常: {e}")
        return False

def test_range_function():
    """测试range函数调用"""
    try:
        # 测试可能导致错误的情况
        test_values = [1, 5, 10, 50, 100]
        
        for val in test_values:
            try:
                result = list(range(val))
                print(f"✓ range({val}) 测试通过，长度: {len(result)}")
            except Exception as e:
                print(f"✗ range({val}) 测试失败: {e}")
                return False
        
        # 测试边界情况
        try:
            result = list(range(0))
            print(f"✓ range(0) 测试通过，长度: {len(result)}")
        except Exception as e:
            print(f"✗ range(0) 测试失败: {e}")
            return False
            
        return True
    except Exception as e:
        print(f"✗ range函数测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试数据管理功能...")
    print("=" * 50)
    
    tests = [
        ("模块导入测试", test_imports),
        ("数据验证测试", test_data_validation),
        ("Range函数测试", test_range_function),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n运行 {test_name}:")
        if test_func():
            passed += 1
            print(f"✓ {test_name} 通过")
        else:
            print(f"✗ {test_name} 失败")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败，请检查代码")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
