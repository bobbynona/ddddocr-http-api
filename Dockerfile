# 阶段 1: 基础构建器 - 仅安装第三方依赖
# 这一层的目的是创建一个包含所有重量级依赖的缓存层
FROM python:3.12-slim as builder-deps

# 安装 uv
RUN pip install -U --no-cache-dir uv

WORKDIR /app

# 复制项目依赖定义文件
COPY pyproject.toml uv.lock* ./

# 使用 --frozen 标志，uv 将使用 lockfile 作为唯一信源，且不会尝试更新它
# 使用 --no-install-project 标志，只安装第三方依赖，为 Docker 提供完美的缓存层
RUN uv sync --frozen --no-install-project

# 阶段 2: 应用构建器 - 添加应用代码
# 这一层基于上一层，只添加轻量的、经常变动的应用代码
FROM builder-deps as builder-app

WORKDIR /app

# 复制应用代码
COPY api/ ./api/
COPY main.py ./

# 阶段 3: 最终镜像
# 从一个全新的、干净的基础镜像开始，保证最小体积
FROM python:3.12-slim

WORKDIR /app

# 从 builder-base 阶段复制 uv 可执行文件，确保最终镜像中有 uv 命令
COPY --from=builder-deps /usr/local/bin/uv /usr/local/bin/uv

# 从最终的构建器阶段 (builder-app) 精确复制所需的一切
COPY --from=builder-app /app/.venv ./.venv
COPY --from=builder-app /app/pyproject.toml /app/uv.lock* ./
COPY --from=builder-app /app/api/ ./api/
COPY --from=builder-app /app/main.py ./

# 暴露端口
EXPOSE 8000

# 设置环境变量，让 shell 和 uv 自动找到并使用项目内的 .venv
# 注意：虽然 uv run 会自动激活 .venv，但显式设置 PATH 是一个最佳实践，
# 它极大地简化了通过 `docker exec` 进入容器进行手动调试的过程。
ENV PATH="/app/.venv/bin:$PATH"

# 最终的入口点和命令
ENTRYPOINT ["uv", "run", "python", "main.py"]
CMD ["api"]
