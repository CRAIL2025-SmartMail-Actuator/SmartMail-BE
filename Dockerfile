# Use official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./


RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu


# Install other ML dependencies from PyPI
RUN pip install --no-cache-dir \
    transformers \
    safetensors \
    tokenizers \
    huggingface-hub \
    sentence-transformers

RUN pip install --no-cache-dir \
    xxhash \
    langgraph \
    langchain \
    langchain-core \
    langchain-community
    
# Install dependencies system-wide
RUN uv pip install --system --no-deps -r pyproject.toml || \
    uv pip install --system fastapi uvicorn python-multipart python-dotenv sqlalchemy alembic psycopg2-binary qdrant-client

# Copy source code
COPY . ./

# Remove any .venv that might have been copied
RUN rm -rf .venv

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]