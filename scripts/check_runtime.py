"""Check the Python, PyTorch, CUDA, GPU, and MiniMind runtime dependencies."""

import importlib
import platform
import sys

import torch


REQUIRED_PACKAGES = (
    "transformers",
    "datasets",
    "accelerate",
    "trl",
    "sentence_transformers",
)


def main() -> None:
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {platform.python_version()}")
    print(f"torch version: {torch.__version__}")
    print(f"CUDA version: {torch.version.cuda or 'not available'}")

    cuda_available = torch.cuda.is_available()
    print(f"cuda available: {cuda_available}")
    print(
        "GPU name: "
        + (torch.cuda.get_device_name(0) if cuda_available else "no cuda")
    )

    failed_imports = []
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
            print(f"{package}: import succeeded")
        except Exception as exc:
            failed_imports.append((package, exc))
            print(f"{package}: import failed ({exc})")

    if not cuda_available:
        raise RuntimeError("CUDA is not available in the current PyTorch runtime.")
    if failed_imports:
        details = "; ".join(
            f"{package}: {error}" for package, error in failed_imports
        )
        raise RuntimeError(f"Required package import failures: {details}")

    print("Runtime check passed.")


if __name__ == "__main__":
    main()
