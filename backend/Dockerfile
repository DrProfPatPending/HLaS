FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HLAS_DATA_DIR=/data

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt gunicorn

COPY backend /app

RUN mkdir -p /data /data/club_logos /data/ID_photos \
    && cp -n /app/clubs.config.json /data/clubs.config.json || true \
    && cp -n /app/server.config.json /data/server.config.json || true

EXPOSE 5050

CMD ["gunicorn", "-w", "2", "--threads", "4", "-b", "0.0.0.0:5050", "app:app"]
