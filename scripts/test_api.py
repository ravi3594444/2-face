"""Smoke-test and benchmark the deployed llama-server Spaces.

    HF_TOKEN=hf_... LLAMA_API_KEY=sk-... python scripts/test_api.py deer

HF_TOKEN only needs read access; it opens the private Space.
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request

OWNER = "ravi8084"
DOCKER_SPACES = ["deer", "deerflow", "ai-police", "agent11"]


def call(url: str, headers: dict, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, {}


def check(space: str, hf_token: str, api_key: str) -> None:
    base = f"https://{OWNER}-{space}.hf.space"
    hf = {"X-HF-Authorization": f"Bearer {hf_token}"}

    status, _ = call(f"{base}/health", hf)
    print(f"{space}: health {status}")

    status, _ = call(f"{base}/v1/models", {**hf, "Authorization": "Bearer wrong-key"})
    print(f"{space}: wrong key -> {status} (want 401)")

    start = time.time()
    status, resp = call(f"{base}/v1/chat/completions", {**hf, "Authorization": f"Bearer {api_key}"}, {
        "model": "llama-3.2-3b-instruct",
        "messages": [{"role": "user", "content": "In two sentences, what is Docker?"}],
        "max_tokens": 128,
    })
    if status != 200:
        print(f"{space}: chat -> {status}")
        return
    t = resp.get("timings", {})
    print(f"{space}: chat 200 in {time.time() - start:.1f}s | "
          f"prompt {t.get('prompt_per_second', 0):.1f} tok/s | gen {t.get('predicted_per_second', 0):.1f} tok/s")
    print("   ", resp["choices"][0]["message"]["content"].strip()[:300])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("spaces", nargs="*", default=DOCKER_SPACES)
    args = parser.parse_args()
    for space in args.spaces:
        check(space, os.environ["HF_TOKEN"], os.environ["LLAMA_API_KEY"])


if __name__ == "__main__":
    main()
