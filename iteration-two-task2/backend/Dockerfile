FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

WORKDIR /app

# Debian 镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# devcontainers 基础镜像里可能带有 yarn 源；该源在当前网络下会触发 GPG 校验失败
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn.list.save || true

# 安装基础依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# pip 网络配置（当前环境下 HTTPS/TLS 握手不稳定，默认走 HTTP 镜像）
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DEFAULT_TIMEOUT=120

ARG INSTALL_ADVANCED=false
ARG PIP_INDEX_URL=http://mirrors.aliyun.com/pypi/simple/
ARG PIP_TRUSTED_HOST=mirrors.aliyun.com

ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}
ENV PIP_EXTRA_INDEX_URL=

COPY requirements.txt /app/requirements.txt
COPY requirements-advanced.txt /app/requirements-advanced.txt

# 安装基础依赖（严格使用镜像和 trusted-host，避免 TLS EOF）
RUN pip install --retries 3 --trusted-host ${PIP_TRUSTED_HOST} \
    -i ${PIP_INDEX_URL} -r /app/requirements.txt

# 安装高级依赖（可选）
RUN if [ "$INSTALL_ADVANCED" = "true" ]; then \
    pip install --retries 3 --trusted-host ${PIP_TRUSTED_HOST} \
    -i ${PIP_INDEX_URL} -r /app/requirements-advanced.txt; \
    fi

COPY app /app/app
COPY tests /app/tests
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY pytest.ini /app/pytest.ini
COPY .env.example /app/.env

EXPOSE 8000

# 从 SQLAlchemy 模型直接建表，绕过因迁移文件顺序出错导致的 alembic 失败
CMD sh -c "sleep 5 && python -c 'from app.core.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)' && uvicorn app.main:app --host 0.0.0.0 --port 8000"
