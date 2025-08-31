# Enhanced DDDDOcr Service

[简体中文](./README_cn.md)

This project provides a containerized, enhanced version of the `ddddocr` HTTP API, adding a flexible JWT-based authentication layer and other improvements for robust deployment.

## Features

- Provides all core `ddddocr` OCR and detection functionalities.
- Exposes functionalities via a FastAPI-based HTTP API.
- Optional JWT-based authentication middleware with robust client IP detection (handles `X-Forwarded-For`).
- Highly configurable via environment variables.
- Easy to deploy using Docker/Podman Compose.
- Graceful shutdown handling via a dedicated entrypoint script.
- Auto-initialization of models on startup.

## Getting Started

The easiest way to run the service is by using Docker Compose or Podman Compose.

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd py-ocr-service
    ```

2.  **(Optional) Create a `.env` file:**
    You can create a `.env` file in the project root to manage your configuration. See the **Configuration** section below for all available variables.
    ```env
    DDDDOCR_PORT=8080
    AUTH_REMOTE_ENABLED=true
    AUTH_VALIDATION_URL=https://your-auth-server.com/validate
    AUTH_VALIDATION_TIMEOUT=15.0
    ```

3.  **Run the service:**
    ```bash
    # Using Podman
    podman-compose up --build -d
    
    # Or using Docker
    docker compose up --build -d
    ```

4.  The service will be available at `http://localhost:<DDDDOCR_PORT>`. It will be auto-initialized on startup.

## Configuration

The service is configured using environment variables:

| Variable                  | Description                                                                                                                               | Default     |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| `DDDDOCR_PORT`            | The port on which the service will run.                                                                                                   | `8000`      |
| `AUTH_REMOTE_ENABLED`     | If `true`, enables JWT authentication for all requests determined to be from a remote (public) IP address.                                | `true`      |
| `AUTH_LOCAL_ENABLED`      | If `true`, enables JWT authentication for requests determined to be from a local/private IP address.                                      | `false`     |
| `AUTH_VALIDATION_URL`     | **Required if auth is enabled.** The URL of the external authentication service to validate JWTs. See API contract below.                   | `""`        |
| `AUTH_VALIDATION_TIMEOUT` | The timeout in seconds for the request to the authentication service.                                                                     | `20.0`      |

### Authentication Service API Contract

When authentication is triggered, this service will make a `POST` request to the `AUTH_VALIDATION_URL`. Your authentication service is expected to conform to the following contract:

**Request from this OCR service to your Auth Service:**

*   **Method:** `POST`
*   **Headers:** Includes the original `Authorization: Bearer <token>` header received from the client.
*   **Body:** Empty.

**Expected Responses from your Auth Service:**

*   **Success (Token is valid):**
    *   **Status Code:** `200 OK`
    *   The response body can be anything; it is not checked by the OCR service.

*   **Failure (Token is invalid, expired, etc.):**
    *   **Status Code:** Any non-200 status code (e.g., `401 Unauthorized`).
    *   The response from your auth service (including its status code and body) will be passed through to the original client that called the OCR service.

## API Endpoints

This service is fully compatible with the original `ddddocr` HTTP API. Once the service is running, you can access the interactive Swagger UI documentation at `http://localhost:<DDDDOCR_PORT>/docs`.

## Development

This project uses `uv` for package management.

1.  **Initialize Environment:**
    ```bash
    # Create virtual environment
    uv venv

    # Activate environment (Linux/macOS)
    source .venv/bin/activate

    # Install dependencies
    uv sync

    # Install development dependencies (e.g., for running tests)
    uv pip install -e .[dev]
    ```

2.  **Run Locally:**
    ```bash
    # Example of running with local auth disabled
    export AUTH_VALIDATION_URL=https://httpbin.org/post
    uv run python main.py api --port 8000
    ```

## Acknowledgements

This project is based on the excellent open-source project `ddddocr`. Special thanks to the original author [sml2h3](https://github.com/sml2h3) for their hard work and dedication.

-   **Original Project:** [https://github.com/sml2h3/ddddocr](https://github.com/sml2h3/ddddocr)

## License

This project is based on `ddddocr`, which is licensed under the MIT License. This project is also licensed under the **MIT License**.