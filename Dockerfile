FROM python:3.11-slim

# Install system dependencies (OpenCV and PyTorch OpenMP dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch CPU-only wheel to keep image small (~500MB instead of ~3GB)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install application requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-cache YOLOv8n model weights for Privacy Blur
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copy application code, database manager, templates, and model weights
COPY main.py database.py privacy.py best.pt test.jpg ./
COPY templates/ ./templates/

# Create directory for local uploads and set permissive permissions for container hosts
RUN mkdir -p static/uploads && chmod -R 777 /app

ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]
