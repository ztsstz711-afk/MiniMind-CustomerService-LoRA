"""Download Qwen2.5-1.5B-Instruct from ModelScope to a project-local path.

This script only downloads model files. It does not train and does not modify MiniMind.
"""

import argparse
import json
import os
import shutil
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "models" / "qwen2_5_1_5b_instruct"
DEFAULT_CACHE_DIR = PROJECT_ROOT / "models" / ".modelscope_cache"
DEFAULT_CREDENTIALS_DIR = PROJECT_ROOT / "models" / ".modelscope_credentials"
DOWNLOAD_LOG = PROJECT_ROOT / "experiments" / "qwen_v4_model_download.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Qwen v4 model from ModelScope.")
    parser.add_argument("--model_id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cache_dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--credentials_dir", type=Path, default=DEFAULT_CREDENTIALS_DIR)
    return parser.parse_args()


def has_model_files(path: Path) -> bool:
    has_config = (path / "config.json").is_file()
    has_tokenizer_config = (path / "tokenizer_config.json").is_file()
    has_tokenizer = (path / "tokenizer.json").is_file() or (path / "vocab.json").is_file()
    has_weights = any(path.glob("*.safetensors")) or (path / "model.safetensors").is_file()
    return has_config and has_tokenizer_config and has_tokenizer and has_weights


def file_status(path: Path) -> dict:
    safetensors = sorted(item.name for item in path.glob("*.safetensors"))
    return {
        "config.json": (path / "config.json").is_file(),
        "tokenizer_config.json": (path / "tokenizer_config.json").is_file(),
        "tokenizer.json": (path / "tokenizer.json").is_file(),
        "vocab.json": (path / "vocab.json").is_file(),
        "merges.txt": (path / "merges.txt").is_file(),
        "safetensors": safetensors,
    }


def directory_size_gb(path: Path) -> float:
    total = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
    return total / (1024**3)


def update_log(message: str) -> None:
    DOWNLOAD_LOG.parent.mkdir(parents=True, exist_ok=True)
    existing = DOWNLOAD_LOG.read_text(encoding="utf-8") if DOWNLOAD_LOG.exists() else ""
    DOWNLOAD_LOG.write_text(existing.rstrip() + "\n\n" + message.strip() + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    cache_dir = args.cache_dir
    if not cache_dir.is_absolute():
        cache_dir = PROJECT_ROOT / cache_dir
    credentials_dir = args.credentials_dir
    if not credentials_dir.is_absolute():
        credentials_dir = PROJECT_ROOT / credentials_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    credentials_dir.mkdir(parents=True, exist_ok=True)
    os.environ["MODELSCOPE_CACHE"] = str(cache_dir)
    os.environ["MODELSCOPE_CREDENTIALS_PATH"] = str(credentials_dir / "credentials")

    print(f"ModelScope model id: {args.model_id}")
    print(f"Target local directory: {output_dir}")
    print(f"ModelScope cache directory: {cache_dir}")
    print(f"ModelScope credentials directory: {credentials_dir}")

    if has_model_files(output_dir):
        print("Local model files already exist. Skipping download.")
    else:
        try:
            from modelscope import snapshot_download
            from modelscope.hub.api import ModelScopeConfig

            ModelScopeConfig.path_credential = str(credentials_dir / "credentials")

            downloaded_dir = Path(
                snapshot_download(
                    args.model_id,
                    cache_dir=str(cache_dir),
                    local_dir=str(output_dir),
                )
            )
            print(f"ModelScope snapshot_download returned: {downloaded_dir}")
            if downloaded_dir.resolve() != output_dir.resolve() and downloaded_dir.is_dir():
                for item in downloaded_dir.iterdir():
                    target = output_dir / item.name
                    if target.exists():
                        continue
                    if item.is_dir():
                        shutil.copytree(item, target)
                    else:
                        shutil.copy2(item, target)
        except Exception as exc:
            error_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            update_log(
                f"""## 下载失败

- model_id：`{args.model_id}`
- target_dir：`{output_dir}`
- error：`{type(exc).__name__}: {exc}`

```text
{error_text}
```
"""
            )
            print(f"Download failed: {type(exc).__name__}: {exc}")
            raise

    status = file_status(output_dir)
    print(f"Download directory: {output_dir}")
    print(f"Directory size: {directory_size_gb(output_dir):.3f} GB")
    print("Key file status:")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if not has_model_files(output_dir):
        raise FileNotFoundError(f"Model directory is incomplete: {output_dir}")

    update_log(
        f"""## 下载结果

- model_id：`{args.model_id}`
- local_dir：`{output_dir}`
- status：success
- directory_size_gb：{directory_size_gb(output_dir):.3f}
- key_files：

```json
{json.dumps(status, ensure_ascii=False, indent=2)}
```
"""
    )
    print("Qwen v4 ModelScope download completed.")


if __name__ == "__main__":
    main()
