# 阶段 1: 构建器 (Builder)
FROM python:3.12-slim as builder

RUN pip install --no-cache-dir -U pip uv
ENV UV_PROJECT_ENVIRONMENT=/usr/local
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 仅复制依赖定义文件
COPY pyproject.toml uv.lock* ./

# 安装所有依赖项到系统 Python 环境中
RUN uv sync --frozen

# 阶段 2: 最终镜像 (Final Image)
FROM python:3.12-slim as final

# 安装curl，以便入口点脚本可以使用它
RUN apt-get update && apt-get install -y curl --no-install-recommends && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
COPY --from=builder /usr/local /usr/local
WORKDIR /app

# 复制应用源代码
COPY main.py ./
COPY app/ ./app/

# 复制并设置入口点脚本
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8000

# 将入口点设置为我们的脚本
ENTRYPOINT ["./entrypoint.sh"]
