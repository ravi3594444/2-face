"""Smoke-test and benchmark the deployed Spaces (Llama chat or Laya decisions).

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

    status, models = call(f"{base}/v1/models", {**hf, "Authorization": f"Bearer {api_key}"})
    if status == 200 and models["data"][0]["id"] == "laya":
        check_decision(space, base, {**hf, "Authorization": f"Bearer {api_key}"})
        return

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


TICKET = "Customer message: I was charged twice for my order last week and nobody has replied."
QUESTIONS = {
    "route": {
        "type": "choice",
        "instructions": "Which team should handle this?",
        "criteria": {
            "billing": "payments, charges, refunds, invoices",
            "shipping": "delivery, tracking, lost or late parcels",
            "technical": "bugs, errors, login problems",
        },
    },
    "angry": {"type": "noul", "instructions": "Is the customer angry?"},
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this?",
        "criteria": ["can wait", "this week", "today", "right now"],
    },
}


def check_decision(space: str, base: str, headers: dict, runs: int = 5) -> None:
    pings = []
    for _ in range(runs):
        start = time.time()
        call(f"{base}/health", headers)
        pings.append(time.time() - start)
    print(f"{space}: network baseline (/health) median {sorted(pings)[runs // 2] * 1000:.0f} ms")

    for label, questions in (("1 question", {"route": QUESTIONS["route"]}), ("3 questions", QUESTIONS)):
        times = []
        for _ in range(runs):
            start = time.time()
            status, resp = call(f"{base}/v1/systemone", headers, {"state": TICKET, "questions": questions})
            times.append(time.time() - start)
            if status != 200:
                print(f"{space}: systemone -> {status}")
                return
        times.sort()
        print(f"{space}: systemone {label}: median {times[runs // 2] * 1000:.0f} ms over {runs} runs "
              f"(includes network) | input {resp['usage']['input_tokens']} tokens")
    print("   ", json.dumps(resp["answers"])[:400])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("spaces", nargs="*", default=DOCKER_SPACES)
    args = parser.parse_args()
    for space in args.spaces:
        check(space, os.environ["HF_TOKEN"], os.environ["LLAMA_API_KEY"])


if __name__ == "__main__":
    main()
