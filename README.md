# 2-face

Small LLMs served from free Hugging Face Docker Spaces (2 vCPU, 16 GB RAM each).

`llama-server/` is a Docker Space that runs **Llama 3.2 3B Instruct** (Q4_K_M GGUF) with
[llama.cpp](https://github.com/ggml-org/llama.cpp)'s server. It speaks the OpenAI API
(`/v1/chat/completions`, `/v1/completions`, `/v1/models`) and needs an API key.

## Endpoints

| Space | URL |
|---|---|
| `Ravi8084/deer` | `https://ravi8084-deer.hf.space/v1` |
| `Ravi8084/deerflow` | `https://ravi8084-deerflow.hf.space/v1` |
| `Ravi8084/ai-police` | `https://ravi8084-ai-police.hf.space/v1` |
| `Ravi8084/agent11` | `https://ravi8084-agent11.hf.space/v1` |

The Spaces are private, so every request carries two headers:

- `Authorization: Bearer <LLAMA_API_KEY>`: the API key llama-server checks.
- `X-HF-Authorization: Bearer <HF read token>`: opens the private Space. Use a
  read-only token, not a write token.

## Calling it

```bash
curl https://ravi8084-deer.hf.space/v1/chat/completions \
  -H "Authorization: Bearer $LLAMA_API_KEY" \
  -H "X-HF-Authorization: Bearer $HF_READ_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.2-3b-instruct", "messages": [{"role": "user", "content": "Hello"}]}'
```

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://ravi8084-deer.hf.space/v1",
    api_key=os.environ["LLAMA_API_KEY"],
    default_headers={"X-HF-Authorization": f"Bearer {os.environ['HF_READ_TOKEN']}"},
)
reply = client.chat.completions.create(
    model="llama-3.2-3b-instruct",
    messages=[{"role": "user", "content": "Hello"}],
)
print(reply.choices[0].message.content)
```

## Deploying

```bash
pip install huggingface_hub
export HF_TOKEN=hf_...            # write token
export LLAMA_API_KEY=sk-...       # python -c "import secrets; print('sk-' + secrets.token_urlsafe(32))"
python scripts/deploy.py                 # all Docker Spaces
python scripts/deploy.py deer            # or just some
python scripts/test_api.py deer          # health, auth and speed check
```

`deploy.py` sets the `LLAMA_API_KEY` Space secret and replaces each Space's files with
`llama-server/`, keeping `README.md` (the Space config) and `.gitattributes`.
To rotate the key, run it again with a new `LLAMA_API_KEY`.

## Limits

- **2 vCPU, 16 GB RAM.** The container reports the host's 16 CPUs and ~124 GB, so the
  server is pinned to 2 threads. Don't raise them.
- **Sleeps after 48 h without requests** and restarts cold. Disk is wiped on restart; the
  model is baked into the image so a restart does not re-download it.
- **Outbound traffic** is limited to ports 80, 443 and 8080.
- These are old Docker Spaces: the free plan can't create new ones, so don't delete them.
