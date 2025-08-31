# /// script
# dependencies = [
#   "requests",
# ]
# ///

import requests
import base64
import os
import sys
import argparse
import json
import time

# --- 配置 ---
BASE_URL = "http://localhost:8000"
IMAGE_PATH = os.path.join(os.path.dirname(__file__), "image.jpg")
SIMULATED_PUBLIC_IP = "8.8.8.8"

def run_all_tests(image_path: str):
    """对给定的图片路径执行所有API测试。"""
    print(f"--- 开始对图片 {image_path} 进行测试 (服务应已自动初始化) ---")
    
    if not os.path.exists(image_path):
        print(f"错误: 测试图片未找到 at {image_path}")
        return

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        base64_string = base64.b64encode(image_bytes).decode("utf-8")
    except Exception as e:
        print(f"读取或编码图片时出错: {e}")
        return
    
    # 执行所有测试用例
    test_local_requests(base64_string)
    test_remote_unauthenticated(base64_string)
    test_remote_authenticated(base64_string)

def test_local_requests(base64_string):
    """测试无需认证的本地请求"""
    print("\n--- (1/3) 正在测试: 本地请求, 无Token ---")
    print("预期: 成功")
    test_endpoint("/ocr", {"image": base64_string}, expected_status=200)

def test_remote_unauthenticated(base64_string):
    """测试需要认证但未提供Token的远程请求"""
    print("\n--- (2/3) 正在测试: 模拟远程请求, 无Token ---")
    print("预期: 失败 (401 Unauthorized)")
    headers = {"X-Forwarded-For": SIMULATED_PUBLIC_IP}
    test_endpoint("/ocr", {"image": base64_string}, headers=headers, expected_status=401)

def test_remote_authenticated(base64_string):
    """测试提供了Token的远程请求"""
    print("\n--- (3/3) 正在测试: 模拟远程请求, 有Token ---")
    print("预期: 成功")
    headers = {
        "X-Forwarded-For": SIMULATED_PUBLIC_IP,
        "Authorization": "Bearer any-dummy-token-will-work"
    }
    test_endpoint("/ocr", {"image": base64_string}, headers=headers, expected_status=200)

def test_endpoint(path: str, payload: dict, headers: dict = None, expected_status: int = 200):
    """辅助函数，用于测试单个端点并验证状态码"""
    try:
        response = requests.post(f"{BASE_URL}{path}", json=payload, headers=headers, timeout=15)
        print(f"状态码: {response.status_code} (预期: {expected_status})")
        print("响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == expected_status:
            print(f"--- 测试成功！ ---")
        else:
            print(f"--- 测试失败！响应状态码与预期不符。 ---")
            
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        print(f"--- 测试失败！ ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DDDDOCR API 测试脚本")
    parser.add_argument(
        "image_path", 
        nargs="?", 
        default=os.path.join(os.path.dirname(__file__), "image.jpg"),
        help="要测试的图片路径 (默认为: test/image.jpg)"
    )
    args = parser.parse_args()
    
    
    
    run_all_tests(args.image_path)