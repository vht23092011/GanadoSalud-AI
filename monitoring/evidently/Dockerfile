
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    evidently==0.7.23 \
    pandas==2.2.3

CMD ["python", "monitoring/drift_detection.py"]