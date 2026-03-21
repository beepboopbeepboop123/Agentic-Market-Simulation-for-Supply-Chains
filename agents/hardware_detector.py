import subprocess
import sys
import os
import json

# ─────────────────────────────────────────
# 1. DETECT GPU SPECIFICATIONS
# ─────────────────────────────────────────

def get_gpu_info():
    """
    Detect GPU specs using multiple methods.
    Returns a dict with GPU information.
    """
    gpu_info = {
        "has_gpu":        False,
        "gpu_name":       "None",
        "vram_mb":        0,
        "vram_gb":        0,
        "cuda_available": False,
        "driver_version": "Unknown",
    }

    # Method 1 — Try nvidia-smi (most reliable)
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits"
            ],
            capture_output = True,
            text           = True,
            timeout        = 10
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if lines:
                parts = lines[0].split(",")
                if len(parts) >= 2:
                    gpu_info["has_gpu"]        = True
                    gpu_info["gpu_name"]       = parts[0].strip()
                    gpu_info["vram_mb"]        = int(parts[1].strip())
                    gpu_info["vram_gb"]        = round(
                        int(parts[1].strip()) / 1024, 1
                    )
                    gpu_info["cuda_available"] = True
                    if len(parts) >= 3:
                        gpu_info["driver_version"] = parts[2].strip()

    except Exception:
        pass

    # Method 2 — Try torch if nvidia-smi fails
    if not gpu_info["has_gpu"]:
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info["has_gpu"]        = True
                gpu_info["cuda_available"] = True
                gpu_info["gpu_name"]       = torch.cuda.get_device_name(0)
                vram_bytes                 = torch.cuda.get_device_properties(0).total_memory
                gpu_info["vram_mb"]        = round(vram_bytes / 1024 / 1024)
                gpu_info["vram_gb"]        = round(vram_bytes / 1024 / 1024 / 1024, 1)
        except Exception:
            pass

    return gpu_info


# ─────────────────────────────────────────
# 2. GET RAM INFO
# ─────────────────────────────────────────

def get_ram_info():
    """Get total and available system RAM."""
    ram_info = {
        "total_gb":     0,
        "available_gb": 0,
    }

    try:
        import psutil
        mem                    = psutil.virtual_memory()
        ram_info["total_gb"]   = round(mem.total / 1024**3, 1)
        ram_info["available_gb"] = round(mem.available / 1024**3, 1)
    except Exception:
        # Fallback if psutil not installed
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulong  = ctypes.c_ulong

            class MEMORYSTATUS(ctypes.Structure):
                _fields_ = [
                    ("dwLength",                c_ulong),
                    ("dwMemoryLoad",            c_ulong),
                    ("dwTotalPhys",             c_ulong),
                    ("dwAvailPhys",             c_ulong),
                    ("dwTotalPageFile",         c_ulong),
                    ("dwAvailPageFile",         c_ulong),
                    ("dwTotalVirtual",          c_ulong),
                    ("dwAvailVirtual",          c_ulong),
                ]

            memory_status             = MEMORYSTATUS()
            memory_status.dwLength    = ctypes.sizeof(MEMORYSTATUS)
            kernel32.GlobalMemoryStatus(ctypes.byref(memory_status))
            ram_info["total_gb"]      = round(
                memory_status.dwTotalPhys / 1024**3, 1
            )
            ram_info["available_gb"]  = round(
                memory_status.dwAvailPhys / 1024**3, 1
            )
        except Exception:
            pass

    return ram_info


# ─────────────────────────────────────────
# 3. DETERMINE HARDWARE TIER
# ─────────────────────────────────────────

def get_hardware_tier(gpu_info, ram_info):
    """
    Classify the machine into a tier based
    on its actual hardware capabilities.

    TIER 4 — High end  (8GB+ VRAM)
    TIER 3 — Mid range (4-8GB VRAM)
    TIER 2 — Low end   (2-4GB VRAM or no GPU)
    TIER 1 — CPU only  (no GPU at all)
    """

    vram = gpu_info["vram_gb"]
    ram  = ram_info["total_gb"]

    if not gpu_info["has_gpu"]:
        return "TIER_1"
    elif vram >= 8:
        return "TIER_4"
    elif vram >= 4:
        return "TIER_3"
    elif vram >= 2:
        return "TIER_2"
    else:
        return "TIER_1"


# ─────────────────────────────────────────
# 4. MODEL RECOMMENDATIONS PER TIER
# ─────────────────────────────────────────

TIER_CONFIG = {
    "TIER_4": {
        "label":           "High End GPU (8GB+ VRAM)",
        "recommended_model": "mistral",
        "fallback_model":  "phi3",
        "context_length":  8192,
        "max_tokens":      2000,
        "num_gpu_layers":  35,
        "description":     "Full Mistral-7B on GPU. Best quality output.",
        "emoji":           "🚀"
    },
    "TIER_3": {
        "label":           "Mid Range GPU (4-8GB VRAM)",
        "recommended_model": "phi3",
        "fallback_model":  "phi3:mini",
        "context_length":  4096,
        "max_tokens":      1500,
        "num_gpu_layers":  20,
        "description":     "Phi-3 on GPU. Good quality, faster speed.",
        "emoji":           "⚡"
    },
    "TIER_2": {
        "label":           "Low End GPU (2-4GB VRAM)",
        "recommended_model": "phi3:mini",
        "fallback_model":  "tinyllama",
        "context_length":  2048,
        "max_tokens":      1000,
        "num_gpu_layers":  10,
        "description":     "Phi-3 Mini. Reduced context, still functional.",
        "emoji":           "🔋"
    },
    "TIER_1": {
        "label":           "CPU Only (No GPU)",
        "recommended_model": "tinyllama",
        "fallback_model":  "tinyllama",
        "context_length":  1024,
        "max_tokens":      500,
        "num_gpu_layers":  0,
        "description":     "TinyLlama on CPU. Slower but works anywhere.",
        "emoji":           "🐢"
    },
}


# ─────────────────────────────────────────
# 5. FULL SYSTEM SCAN
# ─────────────────────────────────────────

def scan_hardware():
    """
    Full hardware scan. Returns everything
    needed to configure Ollama correctly.
    """
    gpu_info = get_gpu_info()
    ram_info = get_ram_info()
    tier     = get_hardware_tier(gpu_info, ram_info)
    config   = TIER_CONFIG[tier]

    result = {
        "gpu":    gpu_info,
        "ram":    ram_info,
        "tier":   tier,
        "config": config,
    }

    return result


# ─────────────────────────────────────────
# 6. GET OLLAMA OPTIONS FOR THIS MACHINE
# ─────────────────────────────────────────

def get_ollama_options(tier=None):
    """
    Returns Ollama options dict tuned for
    this machine's hardware tier.
    Use this when calling ollama.chat()
    """
    if tier is None:
        hardware = scan_hardware()
        tier     = hardware["tier"]

    config = TIER_CONFIG[tier]

    return {
        "num_gpu":     config["num_gpu_layers"],
        "num_ctx":     config["context_length"],
        "num_predict": config["max_tokens"],
    }


# ─────────────────────────────────────────
# 7. PRINT HARDWARE REPORT
# ─────────────────────────────────────────

def print_hardware_report(hardware=None):
    if hardware is None:
        hardware = scan_hardware()

    gpu    = hardware["gpu"]
    ram    = hardware["ram"]
    tier   = hardware["tier"]
    config = hardware["config"]

    print("\n" + "="*55)
    print("  🖥️  HARDWARE DETECTION REPORT")
    print("="*55)

    print(f"\n  GPU")
    print(f"  Has GPU      : {gpu['has_gpu']}")
    print(f"  GPU Name     : {gpu['gpu_name']}")
    print(f"  VRAM         : {gpu['vram_gb']} GB")
    print(f"  CUDA         : {gpu['cuda_available']}")
    print(f"  Driver       : {gpu['driver_version']}")

    print(f"\n  RAM")
    print(f"  Total RAM    : {ram['total_gb']} GB")
    print(f"  Available    : {ram['available_gb']} GB")

    print(f"\n  {config['emoji']} HARDWARE TIER: {tier}")
    print(f"  {config['label']}")
    print(f"  {config['description']}")

    print(f"\n  AI CONFIGURATION")
    print(f"  Recommended  : {config['recommended_model']}")
    print(f"  Fallback     : {config['fallback_model']}")
    print(f"  Context len  : {config['context_length']} tokens")
    print(f"  Max tokens   : {config['max_tokens']} tokens")
    print(f"  GPU layers   : {config['num_gpu_layers']}")
    print("="*55)

    return hardware


# ─────────────────────────────────────────
# 8. SAVE CONFIG FOR OTHER FILES TO USE
# ─────────────────────────────────────────

def save_hardware_config():
    """Save hardware config to data folder."""
    hardware = scan_hardware()

    with open("data/hardware_config.json", "w") as f:
        json.dump(hardware, f, indent=2)

    return hardware


# ─────────────────────────────────────────
# 9. RUN IT
# ─────────────────────────────────────────

if __name__ == "__main__":
    hardware = print_hardware_report()
    save_hardware_config()
    print(f"\n✅ Config saved to data/hardware_config.json")