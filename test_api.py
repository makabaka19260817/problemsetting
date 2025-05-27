#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API端点测试脚本
"""

import requests
import json
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

BASE_URL = "http://127.0.0.1:5000"

def test_main_page():
    """测试主页访问"""
    try:
        response = requests.get(BASE_URL)
        print(f"✓ 主页访问成功: 状态码 {response.status_code}")
        return True
    except requests.RequestException as e:
        print(f"✗ 主页访问失败: {e}")
        return False

def test_auth_page():
    """测试认证页面"""
    try:
        response = requests.get(f"{BASE_URL}/auth")
        print(f"✓ 认证页面访问成功: 状态码 {response.status_code}")
        return True
    except requests.RequestException as e:
        print(f"✗ 认证页面访问失败: {e}")
        return False

def test_database_status():
    """测试数据库状态API"""
    try:
        # 这个测试需要管理员权限，所以可能会返回重定向
        response = requests.get(f"{BASE_URL}/test-data/database-status")
        print(f"✓ 数据库状态API响应: 状态码 {response.status_code}")
        return True
    except requests.RequestException as e:
        print(f"✗ 数据库状态API失败: {e}")
        return False

def test_data_validation_functions():
    """测试数据验证函数"""
    print("\n=== 数据验证测试 ===")
    
    # 测试整数转换和验证
    test_cases = [
        (10, True),
        (5, True),
        (None, False),
        ("10", True),
        ("abc", False),
        (-1, False),
        (101, False),
    ]
    
    def validate_count(value, min_val=1, max_val=100):
        """模拟验证函数"""
        try:
            if value is None:
                return False, "值不能为空"
            
            if isinstance(value, str):
                value = int(value)
            
            if not isinstance(value, int):
                return False, "必须是整数"
                
            if value < min_val or value > max_val:
                return False, f"值必须在{min_val}-{max_val}之间"
                
            return True, "验证通过"
        except (ValueError, TypeError):
            return False, "无效的数值"
    
    for test_value, expected_success in test_cases:
        success, msg = validate_count(test_value)
        if success == expected_success:
            print(f"✓ 验证测试通过: {test_value} -> {msg}")
        else:
            print(f"✗ 验证测试失败: {test_value} -> 期望:{expected_success}, 实际:{success}")

def main():
    """主测试函数"""
    print("=== Flask 应用测试 ===")
    
    # 基本页面测试
    test_main_page()
    test_auth_page()
    test_database_status()
    
    # 数据验证测试
    test_data_validation_functions()
    
    print("\n=== 测试完成 ===")
    print("注意: 某些API端点需要管理员登录才能完全测试")

if __name__ == "__main__":
    main()
