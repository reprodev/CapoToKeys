FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
  python3 \
  python3-pip \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY transpose_chords.py /app/transpose_chords.py
COPY entrypoint.py /app/entrypoint.py
COPY webui.py /app/webui.py
COPY utils.py /app/utils.py
COPY static/ /app/static/
COPY templates/ /app/templates/

# Application data directory
# All generated files are written to: /data/outputs
ENV DATA_DIR=/data \
  WEB_HOST=0.0.0.0 \
  WEB_PORT=4506

# Declare persistent volume for outputs
VOLUME ["/data"]

EXPOSE 4506

CMD ["python3", "/app/webui.py"]
