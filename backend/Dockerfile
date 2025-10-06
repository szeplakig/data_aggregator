FROM python:3.12-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and package structure
COPY pyproject.toml README.md ./backend/
COPY app/__init__.py ./backend/app/__init__.py

# Install Python dependencies
WORKDIR /workspace/backend
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy rest of application code
COPY app ./app

# Expose port
EXPOSE 8000

# Set Python path to include workspace
ENV PYTHONPATH=/workspace

# Run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
