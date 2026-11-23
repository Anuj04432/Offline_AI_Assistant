"""Hardware diagnostics and capacity tier profiling."""

from typing import Dict, Any, Optional
import platform
import subprocess
import psutil


def get_gpu_info() -> str:
    """Detect primary GPU on Windows/Linux or fallback to integrated."""
    gpu_name = "Integrated Graphics"
    if platform.system() == "Windows":
        try:
            cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join \', \'"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
            out = res.stdout.strip()
            if out:
                gpu_name = out
        except Exception:
            pass
    elif platform.system() == "Linux":
        try:
            res = subprocess.run(["lspci"], capture_output=True, text=True, timeout=3)
            for line in res.stdout.splitlines():
                if "VGA" in line or "3D" in line:
                    gpu_name = line.split(":")[-1].strip()
                    break
        except Exception:
            pass
    return gpu_name


def get_cpu_info() -> Dict[str, Any]:
    """Retrieve CPU model name, physical cores, and logical threads."""
    model_name = platform.processor() or "Unknown CPU"
    if platform.system() == "Windows":
        try:
            cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
            out = res.stdout.strip()
            if out:
                model_name = out
        except Exception:
            pass

    physical_cores = psutil.cpu_count(logical=False) or 2
    logical_cores = psutil.cpu_count(logical=True) or physical_cores

    return {
        "model": model_name,
        "physical_cores": physical_cores,
        "logical_cores": logical_cores,
    }


def determine_hardware_tier(ram_total_gb: float) -> str:
    """
    Categorize user system capacity based on RAM:
    - LIGHT: < 8GB (Ideal for 1B-3B models)
    - MEDIUM: 8GB - 16.5GB (Ideal for 7B-8B models)
    - STRONG: > 16.5GB (Ideal for 14B-32B+ models)
    """
    if ram_total_gb < 7.5:
        return "LIGHT"
    elif ram_total_gb <= 16.5:
        return "MEDIUM"
    else:
        return "STRONG"


def get_system_hardware() -> Dict[str, Any]:
    """Compile comprehensive system diagnostic and capacity information."""
    vmem = psutil.virtual_memory()
    total_ram_gb = round(vmem.total / (1024 ** 3), 2)
    available_ram_gb = round(vmem.available / (1024 ** 3), 2)
    ram_usage_percent = vmem.percent

    cpu = get_cpu_info()
    gpu = get_gpu_info()
    tier = determine_hardware_tier(total_ram_gb)

    return {
        "ram_total_gb": total_ram_gb,
        "ram_available_gb": available_ram_gb,
        "ram_usage_percent": ram_usage_percent,
        "cpu_model": cpu["model"],
        "cpu_physical_cores": cpu["physical_cores"],
        "cpu_logical_cores": cpu["logical_cores"],
        "gpu_name": gpu,
        "hardware_tier": tier,
    }
