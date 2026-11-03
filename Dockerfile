# 1. Base image: Official slim Python 3.12 (Debian Linux)
FROM python:3.12-slim

# 2. Prevent Python from buffering stdout/stderr and writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# 3. Install required OS-level C-libraries for FAISS and PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Set container working directory
WORKDIR /app

# 5. Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy application code, static assets, and configurations
COPY . .

# 7. Create persistent runtime storage directories
RUN mkdir -p uploads indexes static

# 8. Expose port 8000
EXPOSE 8000

# 9. Launch Uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
