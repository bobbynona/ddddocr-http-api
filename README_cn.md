# 增强版 DDDDOcr 服务

[English](./README.md)

本项目提供一个容器化的、功能增强的 `ddddocr` HTTP API 服务，为其增加了灵活的、基于 JWT 的身份验证层以及其他用于稳健部署的改进。

## 架构设计

本服务采用了一种**“猴子补丁” (Monkey Patching)** 的非侵入式设计思路：

1.  **依赖原始库**: 项目将原始的 `ddddocr` 作为一个库依赖，而不是直接修改其源代码。
2.  **动态替换**: 在运行时，我们自己的 `main.py` 脚本会导入原始的 `ddddocr` 服务，并在其启动前，动态地将其中的 `run_server` 函数替换为我们自定义的实现 (`our_custom_run_server`)。
3.  **注入逻辑**: 在我们自定义的 `our_custom_run_server` 函数中，我们得以在不修改原库任何文件的情况下，实现以下增强功能：
    *   **注入认证中间件**: 为 FastAPI 应用实例添加了 `AuthMiddleware`。
    *   **程序化自动初始化**: 在启动 Uvicorn 服务器**之前**，以编程方式调用 `ddddocr` 的内部初始化方法，彻底解决了容器环境中的启动时序和竞争条件问题。

这种设计确保了我们可以轻松地跟进上游 `ddddocr` 库的更新，同时保持我们自定义功能的独立性和稳定性。

## 功能特性

- 提供 `ddddocr` 全部的核心 OCR 与目标检测功能。
- 通过基于 FastAPI 的 HTTP API 暴露服务。
- **基于 JWT 共享密钥的身份验证**: 通过 `AuthMiddleware` 实现，安全、高效。
- **程序化自动初始化**: 服务在启动时自动加载模型，无需外部脚本或API调用。
- 通过环境变量进行高度配置。
- 使用 Docker/Podman Compose，易于部署。

## 快速开始

运行此服务最推荐、最安全的方式是使用 Docker Compose 或 Podman Compose 配合其 `secrets` 功能。

1.  **克隆仓库:**
    ```bash
    git clone <repository_url>
    cd py-ocr-service/ddddocr-http-api
    ```

2.  **创建并管理密钥:**
    我们强烈建议使用 `podman secret` 或 `docker secret` 来管理你的 `OCR_SHARED_SECRET`，而不是将其作为明文环境变量。
    ```bash
    # 生成一个256位的强密钥并将其存入名为 ocr_shared_secret 的 Podman secret 中
    openssl rand -base64 32 | podman secret create ocr_shared_secret -
    ```
    对于本地开发，你也可以将密钥存放在一个名为 `ocr_secret.txt` 的文件中。

3.  **配置 `compose.yml` (如果需要):**
    默认的 `compose.yml` 文件已配置为使用名为 `ocr_shared_secret` 的 secret。你也可以按需调整其他环境变量，如 `DET_ENABLED`。

4.  **运行服务:**
    ```bash
    # 使用 Podman
    podman-compose up --build -d
    
    # 或使用 Docker
    docker compose up --build -d
    ```

5.  服务将运行在 `http://localhost:8000`，并在启动时自动初始化。

## 配置

服务通过环境变量进行配置。对于生产环境，`OCR_SHARED_SECRET` 应通过 `secrets` 注入。

| 变量名                   | 注入方式                               | 描述                                                                                             | 默认值    |
| ------------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------------ | --------- |
| `DDDDOCR_LISTEN_ADDRESS` | 环境变量                               | 服务监听的地址和端口，格式为 `host:port` 或仅 `port`。也支持Unix套接字路径。                         | `8000`    |
| `AUTH_REMOTE_ENABLED`    | 环境变量                               | 如果为 `true`，则对所有被判定为来自远程（公网）IP地址的请求启用 JWT 身份验证。                       | `true`    |
| `AUTH_LOCAL_ENABLED`     | 环境变量                               | 如果为 `true`，则对所有被判定为来自本地/私网 IP地址的请求启用 JWT 身份验证。                         | `false`   |
| `OCR_SHARED_SECRET_FILE` | 由 `compose.yml` 的 `secrets` 自动创建 | 指向包含共享密钥的文件的路径 (例如 `/run/secrets/ocr_shared_secret`)。代码会优先使用此项。         | `null`    |
| `OCR_SHARED_SECRET`      | 环境变量 (本地开发备用)                | 用于签发和验证 JWT 的共享密钥。如果 `_FILE` 版本不存在，则会使用此变量。                           | `null`    |
| `DET_ENABLED`            | 环境变量                               | 如果为 `true`，则在启动时初始化并加载目标检测（det）模型。                                         | `false`   |

## API 端点

本服务与原始的 `ddddocr` HTTP API 完全兼容。当服务运行时，你可以通过 `http://localhost:<port>/docs` 访问交互式的 Swagger UI 文档。

## 本地开发

本项目使用 `uv` 进行包管理。

1.  **初始化环境:**
    ```bash
    # 进入项目目录
    cd py-ocr-service/ddddocr-http-api

    # 创建虚拟环境
    uv venv

    # 激活环境 (Linux/macOS)
    source .venv/bin/activate

    # 安装依赖
    uv sync
    ```

2.  **本地运行:**
    ```bash
    # 这是一个禁用了本地验证，并设置了共享密钥的运行示例
    export AUTH_LOCAL_ENABLED=false
    export OCR_SHARED_SECRET="a-local-secret-key"
    uv run python main.py api --port 8000
    ```

## 鸣谢

本项目基于优秀的 `ddddocr` 开源项目。特别感谢原作者 [sml2h3](https://github.com/sml2h3) 的辛勤工作和无私奉献。

-   **原始项目地址:** [https://github.com/sml2h3/ddddocr](https://github.com/sml2h3/ddddocr)

## 开源许可

本项目基于 `ddddocr`，它使用 MIT 许可。因此，本项目同样在 **MIT 许可**下开源。