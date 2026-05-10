FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HLAS_DATA_DIR=/data

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt


# Copy backend code
COPY backend /app
# Ensure field_order.json is present at /app/field_order.json for the API
COPY backend/field_order.json /app/field_order.json

RUN mkdir -p /data /data/club_logos /data/ID_photos \
    && cp -n /app/clubs.config.json /data/clubs.config.json || true \
    && cp -n /app/server.config.json /data/server.config.json || true

EXPOSE 5050

CMD ["sh", "-c", "alembic upgrade head && gunicorn -w 2 --threads 4 -b 0.0.0.0:5050 --log-level debug app:app"]
