FROM python:3.10-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files first (better caching)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies (without installing the project itself yet)
RUN uv sync --frozen --no-install-project

# Copy application code
COPY app/ ./app/

# Install the project
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Run with uvicorn via uv
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
