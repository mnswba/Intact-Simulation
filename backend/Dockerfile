FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglu1-mesa libxrender1 libxext6 libsm6 libgomp1 && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY intact_backend ./intact_backend
RUN uv sync --frozen --extra cad --no-dev && useradd --uid 10001 --create-home intact && mkdir /data && chown intact:intact /data
ENV INTACT_STATE_DIR=/data PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER intact
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "intact_backend.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
