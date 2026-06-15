"""Download the official MiniMind baseline checkpoint from ModelScope."""

import shutil
import sys
from pathlib import Path

from modelscope import snapshot_download


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "gongjy/minimind-3-pytorch"
CHECKPOINT_NAME = "full_sft_768.pth"
STAGING_DIR = PROJECT_ROOT / "outputs" / "minimind-checkpoint-download"
FINAL_PATH = PROJECT_ROOT / "minimind" / "out" / CHECKPOINT_NAME


def find_checkpoint(snapshot_path: Path) -> Path:
    """Locate the requested checkpoint in the downloaded snapshot."""
    matches = [path for path in snapshot_path.rglob(CHECKPOINT_NAME) if path.is_file()]
    if not matches:
        raise FileNotFoundError(
            f"ModelScope snapshot does not contain {CHECKPOINT_NAME}: {snapshot_path}"
        )
    if len(matches) > 1:
        rendered = ", ".join(str(path) for path in matches)
        raise RuntimeError(f"Multiple matching checkpoints found: {rendered}")
    return matches[0]


def main() -> None:
    print(f"Download source: ModelScope ({MODEL_ID})")
    print(f"Requested file: {CHECKPOINT_NAME}")

    if FINAL_PATH.is_file():
        size_mb = FINAL_PATH.stat().st_size / (1024 * 1024)
        print(f"Checkpoint already exists: {FINAL_PATH}")
        print(f"File size: {size_mb:.2f} MB")
        return

    try:
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_dir = Path(
            snapshot_download(
                MODEL_ID,
                local_dir=str(STAGING_DIR),
                allow_file_pattern=CHECKPOINT_NAME,
                max_workers=1,
            )
        )
        downloaded_path = find_checkpoint(snapshot_dir)

        FINAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(downloaded_path, FINAL_PATH)
        if not FINAL_PATH.is_file() or FINAL_PATH.stat().st_size == 0:
            raise RuntimeError(f"Checkpoint copy validation failed: {FINAL_PATH}")

        size_mb = FINAL_PATH.stat().st_size / (1024 * 1024)
        print(f"Downloaded file: {downloaded_path}")
        print(f"Final checkpoint path: {FINAL_PATH}")
        print(f"File size: {size_mb:.2f} MB")
    except Exception as exc:
        print(f"Checkpoint download failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
