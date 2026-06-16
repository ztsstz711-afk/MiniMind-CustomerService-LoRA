"""Check local runtime readiness for Qwen v4 experiments.

This script does not download models and does not start training.
"""

import importlib
import sys


def check_import(package_name: str, import_name: str | None = None, required: bool = True) -> bool:
    module_name = import_name or package_name
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        status = "unavailable"
        print(f"{package_name}: {status} ({type(exc).__name__}: {exc})")
        if required:
            return False
        return False
    version = getattr(module, "__version__", "unknown")
    print(f"{package_name}: available ({version})")
    return True


def main() -> None:
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.replace(chr(10), ' ')}")

    torch_ok = check_import("torch")
    cuda_available = False
    if torch_ok:
        import torch

        cuda_available = torch.cuda.is_available()
        print(f"torch version: {torch.__version__}")
        print(f"CUDA available: {cuda_available}")
        print(f"CUDA version: {getattr(torch.version, 'cuda', None)}")
        print(
            "GPU name: "
            + (torch.cuda.get_device_name(0) if cuda_available else "no cuda")
        )

    required_ok = True
    required_ok &= check_import("transformers")
    required_ok &= check_import("datasets")
    required_ok &= check_import("peft")
    required_ok &= check_import("accelerate")
    required_ok &= check_import("trl")
    bnb_ok = check_import("bitsandbytes", required=False)

    print("Recommendation:")
    if cuda_available:
        print("- CUDA is available. Start with Qwen2.5-1.5B-Instruct bf16/fp16 LoRA.")
    else:
        print("- CUDA is not available. Do not start Qwen LoRA training in this environment.")
    if not bnb_ok:
        print("- bitsandbytes is unavailable. Do not start with 4bit QLoRA on Windows.")
    else:
        print("- bitsandbytes is available, but still validate 4bit QLoRA with a smoke test first.")

    if not required_ok:
        raise RuntimeError("One or more required Qwen v4 packages are unavailable.")
    print("Qwen v4 environment check completed.")


if __name__ == "__main__":
    main()
