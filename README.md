# 2-face

Small models served from free Hugging Face Docker Spaces (2 vCPU, 16 GB RAM each), all
through [llama.cpp](https://github.com/ggml-org/llama.cpp)'s server and an API key.

| App | Model | What it does | API |
|---|---|---|---|
| `laya-server/` | [Laya](https://huggingface.co/convaiinnovations/laya) 421M (Q8_0 GGUF) | Decisions: picks an option, scores, or answers yes/no with probabilities. Does not write text. English. | `POST /v1/systemone` |
| `llama-server/` | Llama 3.2 3B Instruct (Q4_K_M GGUF) | Chat: writes text. | OpenAI: `/v1/chat/completions` |

## Endpoints

| Space | App | URL |
|---|---|---|
| `Ravi8084/ai-police` | Laya | `https://ravi8084-ai-police.hf.space` |
| `Ravi8084/deer` | Llama | `https://ravi8084-deer.hf.space` |
| `Ravi8084/deerflow` | Llama | `https://ravi8084-deerflow.hf.space` |
| `Ravi8084/agent11` | Llama | `https://ravi8084-agent11.hf.space` (standby, see Limits) |

The Spaces are private, so every request carries two headers:

- `Authorization: Bearer <LLAMA_API_KEY>`: the API key llama-server checks.
- `X-HF-Authorization: Bearer <HF read token>`: opens the private Space. Use a
  read-only token, not a write token.

## Speed (measured, per Space)

| Model | Request | Time |
|---|---|---|
| Laya | 1 question | ~0.5 s |
| Laya | 3 questions | ~1.2 s |
| Llama 3.2 3B | reading the prompt | ~25 tokens/s |
| Llama 3.2 3B | writing the answer | ~7 tokens/s (a 128-token answer takes ~12 s) |

Laya times exclude ~0.18 s of network from the test machine. Each Laya question is one
pass over the input, so time grows with the number of questions.

## Calling Laya

```bash
curl https://ravi8084-ai-police.hf.space/v1/systemone \
  -H "Authorization: Bearer $LLAMA_API_KEY" \
  -H "X-HF-Authorization: Bearer $HF_READ_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "state": "Customer message: I was charged twice for my order last week and nobody has replied.",
    "questions": {
      "route":   {"type": "choice", "instructions": "Which team should handle this?",
                  "criteria": {"billing": "payments, refunds", "shipping": "delivery, tracking", "technical": "bugs, login"}},
      "angry":   {"type": "noul",   "instructions": "Is the customer angry?"},
      "urgency": {"type": "score",  "instructions": "How urgent is this?",
                  "criteria": ["can wait", "this week", "today", "right now"]}
    }
  }'
```

Question types: `choice` returns the top option and a probability per option; `score`
returns the expected level on a 2 to 10 step scale; `noul` returns the probability of yes.

## Calling Llama

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
python scripts/deploy.py --app laya-server ai-police
python scripts/deploy.py --app llama-server deer deerflow
python scripts/test_api.py ai-police deer   # health, auth and speed check
```

`deploy.py` sets the `LLAMA_API_KEY` Space secret and replaces each Space's files with
the app folder, keeping `README.md` (the Space config) and `.gitattributes`.
To rotate the key, run it again with a new `LLAMA_API_KEY`.

## Limits

- **Only 3 Spaces can run at once.** The free account's `cpu-basic` quota is 3, so a 4th
  Space is paused with `Quota exceeded for flavor cpu-basic`. `agent11` is deployed but
  paused; restart it from its Settings page after pausing one of the others.
- **2 vCPU, 16 GB RAM.** The container reports the host's 16 CPUs and ~124 GB, so the
  servers are pinned to 2 threads. Don't raise them.
- **Llama is slow on long prompts.** A 2,000-token prompt takes over a minute before the
  first output token.
- **Sleeps after 48 h without requests** and restarts cold. Disk is wiped on restart; the
  models are baked into the images so a restart does not re-download them.
- **Outbound traffic** is limited to ports 80, 443 and 8080.
- These are old Docker Spaces: the free plan can't create new ones, so don't delete them.
