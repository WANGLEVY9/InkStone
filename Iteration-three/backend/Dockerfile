FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv -i https://mirror.nju.edu.cn/pypi/web/simple

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
ENV UV_DEFAULT_INDEX=https://mirror.nju.edu.cn/pypi/web/simple
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
