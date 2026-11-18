
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    docker==7.1.0 \
    requests==2.32.3

COPY monitoring/auto_recovery.py /app/auto_recovery.py

CMD ["python", "-u", "/app/auto_recovery.py"]
