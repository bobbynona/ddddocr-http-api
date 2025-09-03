# coding=utf-8
"""
项目主入口 (独立自包含方案)

此脚本复刻了原始 ddddocr.__main__ 的所有功能，
并集成了服务自动初始化、中间件注入等增强逻辑。
"""

import os
import sys
import json
import argparse
from pathlib import Path
import uvicorn

# 导入我们自己的服务和中间件
from api.middleware import AuthMiddleware
from api.server import create_app, service, InitializeRequest

def main():
    """主入口函数，负责解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="DDDDOCR API Service (Enhanced)",
        prog="python main.py"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available Commands")
    
    # API服务命令
    api_parser = subparsers.add_parser("api", help="启动HTTP API服务")
    api_parser.add_argument("--host", help="服务器主机地址 (将被 DDDDOCR_LISTEN_ADDRESS 覆盖)")
    api_parser.add_argument("--port", type=int, help="服务器端口 (将被 DDDDOCR_LISTEN_ADDRESS 覆盖)")
    api_parser.add_argument("--workers", type=int, default=1, help="工作进程数 (默认: 1)")
    api_parser.add_argument("--reload", action="store_true", help="启用自动重载 (开发模式)")
    api_parser.add_argument("--config", help="配置文件路径 (JSON格式)")
    api_parser.add_argument("--log-level", default="info", 
                           choices=["critical", "error", "warning", "info", "debug", "trace"],
                           help="日志级别 (默认: info)")

    # 其他辅助命令
    subparsers.add_parser("colors", help="显示可用的颜色过滤器预设")
    subparsers.add_parser("version", help="显示版本信息")
    subparsers.add_parser("example", help="显示使用示例")
    
    args = parser.parse_args()
    
    if args.command == "api":
        start_api_server(args)
    elif args.command == "colors":
        show_color_presets()
    elif args.command == "version":
        show_version()
    elif args.command == "example":
        show_examples()
    else:
        parser.print_help()

def start_api_server(args):
    """配置并启动API服务器"""
    try:
        # 1. 加载配置文件 (逻辑与原版一致)
        config = {}
        if args.config:
            config_path = Path(args.config)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"Configuration loaded from: {config_path}")
            else:
                print(f"Warning: Config file not found: {config_path}")

        # 2. 确定监听地址 (优先级: 环境变量 > 命令行 > 配置文件 > 默认值)
        listen_address = os.getenv("DDDDOCR_LISTEN_ADDRESS")
        uvicorn_kwargs = {}

        if listen_address:
            print(f"[Info] Using DDDDOCR_LISTEN_ADDRESS env var: {listen_address}")
            if listen_address.startswith("/") or listen_address.startswith("./"):
                uvicorn_kwargs["uds"] = listen_address
            elif ":" in listen_address:
                host, port_str = listen_address.split(":")
                uvicorn_kwargs["host"] = host
                uvicorn_kwargs["port"] = int(port_str)
            else:
                uvicorn_kwargs["host"] = "0.0.0.0"
                uvicorn_kwargs["port"] = int(listen_address)
        else:
            # 如果环境变量不存在，则使用命令行或配置文件
            uvicorn_kwargs["host"] = args.host or config.get("host", "0.0.0.0")
            uvicorn_kwargs["port"] = args.port or config.get("port", 8000)

        # 3. 合并其他配置 (命令行优先)
        uvicorn_kwargs["workers"] = args.workers or config.get("workers", 1)
        uvicorn_kwargs["reload"] = args.reload or config.get("reload", False)
        uvicorn_kwargs["log_level"] = args.log_level or config.get("log_level", "info")

        # 4. 创建FastAPI应用并注入中间件
        app = create_app()
        app.add_middleware(AuthMiddleware)

        # 5. 程序化自动初始化
        print("=" * 60)
        print("Performing programmatic auto-initialization...")
        try:
            det_enabled = os.getenv("DET_ENABLED", "false").lower() == "true"
            init_config = InitializeRequest(ocr=True, det=det_enabled)
            result = service.initialize(init_config)
            print(f"[Initialization Success] {result['message']}")
            print(f"[Initialization Success] Loaded models: {result['loaded_models']}")
        except Exception as e:
            print(f"[Initialization Failed] Error: {e}", file=sys.stderr)
        print("=" * 60)

        # 6. 启动服务器
        print("Starting DDDOCR API Service (Standalone Mode)...")
        for key, value in uvicorn_kwargs.items():
            if value is not None: print(f"  - {key}: {value}")
        print("=" * 60)
        
        uvicorn_kwargs["proxy_headers"] = True
        uvicorn_kwargs["forwarded_allow_ips"] = '*'

        uvicorn.run(app, **uvicorn_kwargs)
        
    except Exception as e:
        print(f"Failed to start API server: {e}", file=sys.stderr)
        sys.exit(1)

def show_color_presets():
    """显示颜色过滤器预设 (来自原版)"""
    try:
        from ddddocr import ColorFilter
        print("DDDDOCR 颜色过滤器预设")
        print("=" * 40)
        colors = ColorFilter.get_available_colors()
        for i, color in enumerate(colors, 1):
            ranges = ColorFilter.COLOR_PRESETS[color]
            print(f"{i:2d}. {color:8s} - HSV范围: {ranges}")
        print("\n使用示例:")
        print("  ocr.classification(image, color_filter_colors=['red', 'blue'])")
    except ImportError as e:
        print(f"错误: 无法导入 ddddocr.ColorFilter: {e}")

def show_version():
    """显示版本信息 (来自原版)"""
    try:
        import ddddocr
        print("DDDDOCR 版本信息")
        print("=" * 30)
        # 注意：版本号是硬编码的，因为我们不再是ddddocr包的一部分
        print(f"API 版本: 1.6.0 (增强版)")
        print(f"原作者: sml2h3")
        print(f"项目地址: https://github.com/sml2h3/ddddocr")
    except Exception as e:
        print(f"获取版本信息失败: {e}")

def show_examples():
    """显示使用示例 (来自原版)"""
    # 此功能为纯文本打印，直接保留
    examples = """
    DDDDOCR 使用示例 (此为静态文本)
    ===============================
    1. 启动API服务:
       python main.py api --port 8000

    2. 查看可用颜色:
       python main.py colors

    3. 查看版本:
       python main.py version
    """
    print(examples)

if __name__ == "__main__":
    main()