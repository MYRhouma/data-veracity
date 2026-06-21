FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY src/ ./src/
COPY static/ ./static/

RUN mkdir -p /data/keys

ENV DVA_VC_KEY_PATH=/data/keys/private_key.pem

EXPOSE 8050

CMD ["python", "-m", "dva_vc_issuer.main"]