# Enhanced DDDDOcr Service

[简体中文](./README_cn.md)

This project provides a containerized, enhanced `ddddocr` HTTP API service. It adds a flexible, JWT-based authentication layer and other improvements for robust deployment.

## Architecture Design

This service uses a **"Monkey Patching"** non-intrusive design:

1.  **Library Dependency**: The project depends on the original `ddddocr` as a library, without modifying its source code.
2.  **Dynamic Replacement**: At runtime, our `main.py` script imports the original `ddddocr` service and dynamically replaces its `run_server` function with our custom implementation (`our_custom_run_server`) before startup.
3.  **Logic Injection**: In our custom `our_custom_run_server` function, we can inject enhanced features without altering the original library files:
    *   **Auth Middleware**: Adds `AuthMiddleware` to the FastAPI application instance.
    *   **Programmatic Auto-Initialization**: Programmatically calls the internal initialization method of `ddddocr` **before** starting the Uvicorn server, completely resolving startup timing and race condition issues in containerized environments.

This design ensures that we can easily keep up with upstream `ddddocr` library updates while maintaining the stability and independence of our custom features.

## Features

-   Provides all core OCR and object detection features of `ddddocr`.
-   Exposes services via a FastAPI-based HTTP API.
-   **JWT Shared-Secret Authentication**: Secure and high-performance auth via `AuthMiddleware`.
-   **Programmatic Auto-Initialization**: The service automatically loads models on startup, no external scripts or API calls needed.
-   Highly configurable via environment variables.
-   Easy to deploy using Docker/Podman Compose.

## Getting Started

The most recommended and secure way to run this service is with Docker Compose or Podman Compose, using their `secrets` feature.

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd py-ocr-service/ddddocr-http-api
    ```

2.  **Create and Manage the Secret:**
    We strongly advise using `podman secret` or `docker secret` to manage your `OCR_SHARED_SECRET` instead of using plaintext environment variables.
    ```bash
    # Generate a strong 256-bit key and store it in a Podman secret named ocr_shared_secret
    openssl rand -base64 32 | podman secret create ocr_shared_secret -
    ```
    For local development, you can also place the secret in a file named `ocr_secret.txt`.

3.  **(Optional) Configure `compose.yml`:**
    The default `compose.yml` is already configured to use a secret named `ocr_shared_secret`. You can adjust other environment variables like `DET_ENABLED` as needed.

4.  **Run the service:**
    ```bash
    # Using Podman
    podman-compose up --build -d
    
    # Or using Docker
    docker compose up --build -d
    ```

5.  The service will be available at `http://localhost:8000` and initializes automatically on startup.

## Configuration

The service is configured via environment variables. For production, `OCR_SHARED_SECRET` should be injected via `secrets`.

| Variable                 | Injection Method        | Description                                                                                             | Default   |
| ------------------------ | ----------------------- | -------------------------------------------------------------------------------------------------------- | --------- |
| `DDDDOCR_LISTEN_ADDRESS` | Environment Variable    | The address and port for the service to listen on, e.g., `host:port` or just `port`. Also supports Unix socket paths. | `8000`    |
| `AUTH_REMOTE_ENABLED`    | Environment Variable    | If `true`, enables JWT authentication for all requests determined to be from remote (public) IP addresses. | `true`    |
| `AUTH_LOCAL_ENABLED`     | Environment Variable    | If `true`, enables JWT authentication for all requests determined to be from local/private IP addresses.   | `false`   |
| `OCR_SHARED_SECRET_FILE` | From `compose.yml` secrets | Path to the file containing the shared secret (e.g., `/run/secrets/ocr_shared_secret`). The code prioritizes this. | `null`    |
| `OCR_SHARED_SECRET`      | Env Var (local fallback) | The shared secret for signing/verifying JWTs. Used if the `_FILE` version is not present.              | `null`    |
| `DET_ENABLED`            | Environment Variable    | If `true`, initializes and loads the object detection (det) model on startup.                            | `false`   |

## API Endpoints

This service is fully compatible with the original `ddddocr` HTTP API. While the service is running, you can access the interactive Swagger UI documentation at `http://localhost:<port>/docs`.

## Local Development

This project uses `uv` for package management.

1.  **Initialize Environment:**
    ```bash
    # cd into the project directory
    cd py-ocr-service/ddddocr-http-api

    # Create virtual environment
    uv venv

    # Activate environment (Linux/macOS)
    source .venv/bin/activate

    # Install dependencies
    uv sync
    ```

2.  **Run Locally:**
    ```bash
    # Example run with local auth disabled and a shared secret set
    export AUTH_LOCAL_ENABLED=false
    export OCR_SHARED_SECRET="a-local-secret-key"
    uv run python main.py api --port 8000
    ```

## Acknowledgements

This project is based on the excellent open-source project `ddddocr`. Special thanks to the original author [sml2h3](https://github.com/sml2h3) for their hard work and dedication.

-   **Original Project:** [https://github.com/sml2h3/ddddocr](https://github.com/sml2h3/ddddocr)

## License

This project is based on `ddddocr`, which is licensed under the MIT License. This project is also licensed under the **MIT License**.
