# 增强版 DDDDOcr 服务

[English](./README.md)

本项目提供一个容器化的、功能增强的 `ddddocr` HTTP API 服务，为其增加了灵活的、基于 JWT 的身份验证层以及其他用于稳健部署的改进。

## 功能特性

- 提供 `ddddocr` 全部的核心 OCR 与目标检测功能。
- 通过基于 FastAPI 的 HTTP API 暴露服务。
- 可选的、基于 JWT 的身份验证中间件，具有健壮的客户端IP识别能力（可处理 `X-Forwarded-For`）。
- 通过环境变量进行高度配置。
- 使用 Docker/Podman Compose，易于部署。
- 通过专用的入口点脚本，实现优雅停机。
- 启动时自动初始化模型。

## 快速开始

运行此服务最简单的方式是使用 Docker Compose 或 Podman Compose。

1.  **克隆仓库:**
    ```bash
    git clone <repository_url>
    cd py-ocr-service
    ```

2.  **(可选) 创建 `.env` 文件:**
    你可以在项目根目录创建一个 `.env` 文件来管理你的配置。所有可用的变量请参见下方的 **配置** 部分。
    ```env
    DDDDOCR_PORT=8080
    AUTH_REMOTE_ENABLED=true
    AUTH_VALIDATION_URL=https://your-auth-server.com/validate
    AUTH_VALIDATION_TIMEOUT=15.0
    ```

3.  **运行服务:**
    ```bash
    # 使用 Podman
    podman-compose up --build -d
    
    # 或使用 Docker
    docker compose up --build -d
    ```

4.  服务将运行在 `http://localhost:<DDDDOCR_PORT>`，并在启动时自动初始化。

## 配置

服务通过环境变量进行配置：

| 变量名                    | 描述                                                                                                                            | 默认值      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| `DDDDOCR_PORT`            | 服务运行的端口。                                                                                                                | `8000`      |
| `AUTH_REMOTE_ENABLED`     | 如果为 `true`，则对所有被判定为来自远程（公网）IP地址的请求启用 JWT 身份验证。                                                    | `true`      |
| `AUTH_LOCAL_ENABLED`      | 如果为 `true`，则对所有被判定为来自本地/私网 IP地址的请求启用 JWT 身份验证。                                                      | `false`     |
| `AUTH_VALIDATION_URL`     | **如果启用了任一验证，此项为必需。** 用于验证 JWT 的外部身份验证服务的 URL。详见下方的 API 规范。                               | `""`        |
| `AUTH_VALIDATION_TIMEOUT` | 调用身份验证服务时的超时时间（秒）。                                                                                            | `20.0`      |

### 认证服务 API 规范

当身份验证被触发时，本服务会向 `AUTH_VALIDATION_URL` 发起一个 `POST` 请求。你的认证服务需要遵循以下接口规范：

**OCR服务 -> 你的认证服务 的请求:**

*   **方法:** `POST`
*   **头部 (Headers):** 包含从原始客户端收到的 `Authorization: Bearer <token>` 头。
*   **请求体 (Body):** 空。

**你的认证服务 -> OCR服务 的预期响应:**

*   **成功 (Token 有效):**
    *   **状态码:** `200 OK`
    *   响应体可以为任意内容，OCR服务不会检查。

*   **失败 (Token 无效、过期等):**
    *   **状态码:** 任意非 200 状态码 (例如 `401 Unauthorized`)。
    *   你的认证服务的响应（包括状态码和响应体）将被直接透传给最初调用OCR服务的客户端。

## API 端点

本服务与原始的 `ddddocr` HTTP API 完全兼容。当服务运行时，你可以通过 `http://localhost:<DDDDOCR_PORT>/docs` 访问交互式的 Swagger UI 文档。

## 本地开发

本项目使用 `uv` 进行包管理。

1.  **初始化环境:**
    ```bash
    # 创建虚拟环境
    uv venv

    # 激活环境 (Linux/macOS)
    source .venv/bin/activate

    # 安装依赖
    uv sync

    # 安装开发依赖 (例如，用于运行测试脚本)
    uv pip install -e .[dev]
    ```

2.  **本地运行:**
    ```bash
    # 这是一个禁用了本地验证的运行示例
    export AUTH_VALIDATION_URL=https://httpbin.org/post
    uv run python main.py api --port 8000
    ```

## 鸣谢

本项目基于优秀的 `ddddocr` 开源项目。特别感谢原作者 [sml2h3](https://github.com/sml2h3) 的辛勤工作和无私奉献。

-   **原始项目地址:** [https://github.com/sml2h3/ddddocr](https://github.com/sml2h3/ddddocr)

## 开源许可

本项目基于 `ddddocr`，它使用 MIT 许可。因此，本项目同样在 **MIT 许可**下开源。