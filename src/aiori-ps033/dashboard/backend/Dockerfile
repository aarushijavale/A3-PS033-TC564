FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    iputils-tracepath \
    traceroute \
    iproute2 \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

COPY dashboard/backend/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY client /app/client
COPY dashboard/backend /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
