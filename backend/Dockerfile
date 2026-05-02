FROM python:3.13-slim

WORKDIR /app

# System dependencies for psycopg2 and sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install sentence-transformers for embeddings
RUN pip install --no-cache-dir sentence-transformers

COPY src/ ./src/
COPY alembic.ini .
COPY migrations/ ./migrations/

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
