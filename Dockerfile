FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System packages needed for metadata processing and image libraries
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       ca-certificates \
       ffmpeg \
       libmagic1 \
       libjpeg-dev \
       zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements early for layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Create a non-root user for running the app
RUN groupadd -r app && useradd -r -g app -d /home/app -s /sbin/nologin app \
    && mkdir -p /home/app && chown -R app:app /home/app /app

USER app

# Expose a production port for gunicorn
EXPOSE 8000

# Use gunicorn to run the Flask WSGI app (bind to 8000)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
FROM python:3.11-slim
