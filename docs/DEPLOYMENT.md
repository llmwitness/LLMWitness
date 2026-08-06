# AgentTrace Production Deployment Guide

This guide details bare-metal, systemd, containerized, and reverse proxy deployment strategies for AgentTrace microservices.

---

## 1. Systemd Service Deployment

Create systemd unit files for `ingest.service` and `gateway.service`:

### `/etc/systemd/system/agenttrace-ingest.service`
```ini
[Unit]
Description=AgentTrace Ingestion Service
After=network.target

[Service]
User=agenttrace
WorkingDirectory=/opt/agenttrace
Environment="AGENTTRACE_SECRET_KEY=production-secret-key-change-me"
ExecStart=/opt/agenttrace/venv/bin/uvicorn ingest:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### `/etc/systemd/system/agenttrace-gateway.service`
```ini
[Unit]
Description=AgentTrace Gateway Proxy Service
After=network.target agenttrace-ingest.service

[Service]
User=agenttrace
WorkingDirectory=/opt/agenttrace
Environment="INGESTION_SERVER_URL=http://127.0.0.1:8000"
Environment="AGENTTRACE_SECRET_KEY=production-secret-key-change-me"
ExecStart=/opt/agenttrace/venv/bin/uvicorn gateway:app --host 127.0.0.1 --port 8011 --workers 8
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 2. Nginx Reverse Proxy Integration

Example Nginx configuration terminating TLS and forwarding traffic to Gateway Proxy:

```nginx
server {
    listen 443 ssl http2;
    server_name gateway.agenttrace.internal;

    ssl_certificate /etc/ssl/certs/agenttrace.crt;
    ssl_certificate_key /etc/ssl/private/agenttrace.key;

    location / {
        proxy_pass http://127.0.0.1:8011;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
