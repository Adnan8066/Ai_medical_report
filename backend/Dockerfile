FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System packages: Tesseract for OCR, libgl for OpenCV.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        tesseract-ocr \
        libglib2.0-0 \
        libgl1 \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py seed_demo_data --skip-documents && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]
