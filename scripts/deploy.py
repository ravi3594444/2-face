"""Deploy an app folder (llama-server/ or laya-server/) to Hugging Face Docker Spaces.

Sets the LLAMA_API_KEY Space secret, then replaces the Space's files with
the contents of the app folder (README.md and .gitattributes are kept, since
README.md holds the Space config).

    HF_TOKEN=hf_... LLAMA_API_KEY=sk-... python scripts/deploy.py --app laya-server ai-police
"""
import argparse
import os
from pathlib import Path

from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi

OWNER = "Ravi8084"
DOCKER_SPACES = ["deer", "deerflow", "ai-police", "agent11"]
KEEP = {"README.md", ".gitattributes"}
ROOT = Path(__file__).resolve().parent.parent
APPS = ["llama-server", "laya-server"]


def deploy(api: HfApi, space: str, app: str, api_key: str) -> None:
    repo_id = f"{OWNER}/{space}"
    src = ROOT / app
    api.add_space_secret(repo_id, "LLAMA_API_KEY", api_key)

    local = {p.relative_to(src).as_posix(): p for p in src.rglob("*") if p.is_file()}
    remote = api.list_repo_files(repo_id, repo_type="space")
    ops = [CommitOperationAdd(path_in_repo=name, path_or_fileobj=str(path)) for name, path in local.items()]
    ops += [CommitOperationDelete(path_in_repo=f) for f in remote if f not in KEEP and f not in local]

    commit = api.create_commit(repo_id, repo_type="space", operations=ops, commit_message=f"Deploy {app}")
    print(f"{repo_id}: {app} {commit.oid[:10]} -> https://{OWNER.lower()}-{space}.hf.space")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app", choices=APPS, default="llama-server", help="App folder to deploy")
    parser.add_argument("spaces", nargs="*", default=DOCKER_SPACES, help="Space names (default: all Docker Spaces)")
    args = parser.parse_args()

    api = HfApi(token=os.environ["HF_TOKEN"])
    api_key = os.environ["LLAMA_API_KEY"]
    for space in args.spaces:
        deploy(api, space, args.app, api_key)


if __name__ == "__main__":
    main()
