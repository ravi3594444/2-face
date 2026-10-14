# Llama 3.2 3B Instruct behind llama.cpp's OpenAI-compatible server,
# sized for a free Hugging Face Space (2 vCPU, 16 GB RAM).
FROM ghcr.io/ggml-org/llama.cpp:server-b11223@sha256:8fdfad183be053cdb72d4b6a5930c3a2475730f932855ee9260193422c2564ed

ARG MODEL_REPO=bartowski/Llama-3.2-3B-Instruct-GGUF
ARG MODEL_REV=5ab33fa94d1d04e903623ae72c95d1696f09f9e8
ARG MODEL_FILE=Llama-3.2-3B-Instruct-Q4_K_M.gguf
ARG MODEL_SHA256=6c1a2b41161032677be168d354123594c0e6e67d2b9227c84f296ad037c728ff

# Bake the model into the image: Space disk is wiped on every restart.
RUN mkdir -p /models \
 && curl -fL --retry 5 -o /models/model.gguf \
      "https://huggingface.co/${MODEL_REPO}/resolve/${MODEL_REV}/${MODEL_FILE}" \
 && echo "${MODEL_SHA256}  /models/model.gguf" | sha256sum -c - \
 && chmod 644 /models/model.gguf

# The container sees the host's 16 CPUs but only 2 are ours, so pin threads.
ENV LLAMA_ARG_MODEL=/models/model.gguf \
    LLAMA_ARG_ALIAS=llama-3.2-3b-instruct \
    LLAMA_ARG_HOST=0.0.0.0 \
    LLAMA_ARG_PORT=7860 \
    LLAMA_ARG_THREADS=2 \
    LLAMA_ARG_CTX_SIZE=16384 \
    LLAMA_ARG_N_PARALLEL=2

EXPOSE 7860
HEALTHCHECK CMD ["curl", "-f", "http://localhost:7860/health"]

# LLAMA_API_KEY comes from the Space secret. Refuse to start without it so
# the endpoint is never served unauthenticated.
ENTRYPOINT ["/bin/sh", "-c", "if [ -z \"$LLAMA_API_KEY\" ]; then echo 'LLAMA_API_KEY is not set; refusing to start.' >&2; exit 1; fi; exec /app/llama-server --threads-batch 2 --no-webui --jinja \"$@\"", "--"]
