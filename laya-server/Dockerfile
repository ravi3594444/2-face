# Laya (convaiinnovations/laya) decision model behind llama.cpp's /v1/systemone
# endpoint, sized for a free Hugging Face Space (2 vCPU, 16 GB RAM).
FROM ghcr.io/ggml-org/llama.cpp:server-b11434@sha256:af8c29600d1de84945de13fa7f126d06fdae16c4b19dc7db1c69c74287eae257

ARG MODEL_REPO=ggml-org/Laya-GGUF
ARG MODEL_REV=22265007700297ba9e128297e82540cf28c5d7d4
ARG MODEL_FILE=Laya-Q8_0.gguf
ARG MODEL_SHA256=c06528c5746d3bb8baa72a27938be95abbfd0b226f8471e8a9e365ed0bb066d2

# Bake the model into the image: Space disk is wiped on every restart.
RUN mkdir -p /models \
 && curl -fL --retry 5 -o /models/model.gguf \
      "https://huggingface.co/${MODEL_REPO}/resolve/${MODEL_REV}/${MODEL_FILE}" \
 && echo "${MODEL_SHA256}  /models/model.gguf" | sha256sum -c - \
 && chmod 644 /models/model.gguf

# The container sees the host's 16 CPUs but only 2 are ours, so pin threads.
ENV LLAMA_ARG_MODEL=/models/model.gguf \
    LLAMA_ARG_ALIAS=laya \
    LLAMA_ARG_HOST=0.0.0.0 \
    LLAMA_ARG_PORT=7860 \
    LLAMA_ARG_THREADS=2

EXPOSE 7860
HEALTHCHECK CMD ["curl", "-f", "http://localhost:7860/health"]

# LLAMA_API_KEY comes from the Space secret. Refuse to start without it so
# the endpoint is never served unauthenticated.
ENTRYPOINT ["/bin/sh", "-c", "if [ -z \"$LLAMA_API_KEY\" ]; then echo 'LLAMA_API_KEY is not set; refusing to start.' >&2; exit 1; fi; exec /app/llama-server --threads-batch 2 --no-webui \"$@\"", "--"]
