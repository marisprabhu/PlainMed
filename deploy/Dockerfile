# PlainMed GPU serving image.
#
# Base is CUDA runtime rather than devel: nothing is compiled at runtime, and
# a smaller image means less to patch and a faster cold start when a GPU node
# scales up.
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    # Never phone home from a container holding patient data.
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    PLAINMED_MODEL_DIR=/models/medgemma-1.5-4b-it \
    PLAINMED_BACKEND=medgemma \
    PLAINMED_OCR_BACKEND=paddle

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3-pip python3.11-venv \
        libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.11 /usr/local/bin/python

WORKDIR /app

# Dependencies first so code edits do not invalidate the layer.
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --upgrade pip \
    && python -m pip install ".[gpu]" \
    && python -m pip install "uvicorn[standard]" gunicorn

COPY app ./app
COPY samples ./samples

# Run unprivileged. The app writes nothing, so no writable volume is needed.
RUN useradd --create-home --uid 10001 plainmed \
    && chown -R plainmed:plainmed /app
USER plainmed

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/v1/health || exit 1

# One worker per GPU: workers do not share a device safely, so scale with
# replicas (each with its own GPU), not with worker count.
CMD ["gunicorn", "plainmed.api.app:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "1", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-"]
