# /// script
# dependencies = [
#   "requests",
#   "PyJWT",
# ]
# ///

import requests
import base64
import os
import sys
import argparse
import json
import time
import jwt

# --- 配置 ---
BASE_URL = os.getenv("OCR_BASE_URL", "http://localhost:8000")
IMAGE_PATH = os.path.join(os.path.dirname(__file__), "image.jpg")
SIMULATED_PUBLIC_IP = "8.8.8.8"

# --- JWT 生成 ---
SECRET_KEY = os.getenv("OCR_SHARED_SECRET")

def generate_jwt():
    """生成一个用于测试的、有效期为60秒的JWT"""
    if not SECRET_KEY:
        print("\n警告: 未设置 OCR_SHARED_SECRET 环境变量，无法生成JWT，跳过需要认证的测试。\n")
        return None
    
    payload = {
        'iss': 'test-script',
        'iat': int(time.time()),
        'exp': int(time.time()) + 60
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# --- 测试主体 ---

def run_all_tests(image_path: str):
    """对给定的图片路径执行所有API测试。"""
    print(f"--- 开始对图片 {image_path} 进行测试 ---")
    print(f"--- 测试目标服务: {BASE_URL} ---")
    
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
    
    # --- 执行初始化 ---
    print("\n--- (0/4) 正在初始化服务, 加载OCR模型 ---")
    init_payload = {"ocr": True}
    test_endpoint("/initialize", init_payload, expected_status=200)

    # --- 执行测试用例 ---
    test_local_unauthenticated(base64_string)
    test_remote_unauthenticated(base64_string)
    test_remote_authenticated(base64_string)
    test_local_authenticated_required(base64_string)

def test_local_unauthenticated(base64_string):
    """测试无需认证的本地请求 (AUTH_LOCAL_ENABLED=false)"""
    print("\n--- (1/4) 正在测试: 本地请求, 无Token (需要 AUTH_LOCAL_ENABLED=false) ---")
    print("预期: 成功")
    test_endpoint("/ocr", {"image": base64_string}, expected_status=200)

def test_remote_unauthenticated(base64_string):
    """测试需要认证但未提供Token的远程请求 (AUTH_REMOTE_ENABLED=true)"""
    print("\n--- (2/4) 正在测试: 模拟远程请求, 无Token (需要 AUTH_REMOTE_ENABLED=true) ---")
    print("预期: 失败 (401 Unauthorized)")
    headers = {"X-Forwarded-For": SIMULATED_PUBLIC_IP}
    test_endpoint("/ocr", {"image": base64_string}, headers=headers, expected_status=401)

def test_remote_authenticated(base64_string):
    """测试提供了有效Token的远程请求 (AUTH_REMOTE_ENABLED=true)"""
    print("\n--- (3/4) 正在测试: 模拟远程请求, 有有效Token (需要 AUTH_REMOTE_ENABLED=true) ---")
    token = generate_jwt()
    if not token:
        print("--- 测试跳过！ ---")
        return
    print("预期: 成功")
    headers = {
        "X-Forwarded-For": SIMULATED_PUBLIC_IP,
        "Authorization": f"Bearer {token}"
    }
    test_endpoint("/ocr", {"image": base64_string}, headers=headers, expected_status=200)

def test_local_authenticated_required(base64_string):
    """测试需要认证的本地请求 (AUTH_LOCAL_ENABLED=true)"""
    print("\n--- (4/4) 正在测试: 本地请求, 有有效Token (需要 AUTH_LOCAL_ENABLED=true) ---")
    print("要运行此测试, 请在启动服务时设置环境变量 AUTH_LOCAL_ENABLED=true")
    token = generate_jwt()
    if not token:
        print("--- 测试跳过！ ---")
        return
    print("预期: 成功")
    headers = {"Authorization": f"Bearer {token}"}
    test_endpoint("/ocr", {"image": base64_string}, headers=headers, expected_status=200)

def test_endpoint(path: str, payload: dict, headers: dict = None, expected_status: int = 200):
    """辅助函数，用于测试单个端点并验证状态码"""
    try:
        response = requests.post(f"{BASE_URL}{path}", json=payload, headers=headers, timeout=15)
        print(f"状态码: {response.status_code} (预期: {expected_status})")
        
        if response.status_code != expected_status:
            print(f"--- 测试失败！响应状态码与预期不符。 ---")
            print("响应内容:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            return

        if path == "/ocr":
            ocr_text = response.json().get("data", {}).get("text")
            print(f"OCR 识别结果: {ocr_text}")
        else:
            print("响应内容:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        print(f"--- 测试成功！ ---")
            
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        print(f"--- 测试失败！ ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DDDDOCR API 测试脚本")
    parser.add_argument(
        "image_path", 
        nargs="?", 
        default=IMAGE_PATH,
        help=f"要测试的图片路径 (默认为: {IMAGE_PATH})"
    )
    args = parser.parse_args()
    
    run_all_tests(args.image_path)
