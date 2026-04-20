from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
import platform
import psutil
import subprocess
import pynvml

# Initialize FastMCP server
mcp = FastMCP("system-info")


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
    )
)
def get_system_info() -> dict:
    """Retrieves basic hardware and operating system identification data.

    Returns:
        dict: A dictionary containing the following platform metrics:
            - 'os' (str): The operating system name.
            - 'version' (str): The system's release version.
            - 'machine' (str): The machine type/architecture.
            - 'processor' (str): The vendor-specific CPU description string.
            - 'hostname' (str): The network name of the computer.
    """
    try:
        return {
            "os": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
    )
)
def get_cpu_info() -> dict:
    """Retrieves current CPU load, core counts, and frequency.

    Returns:
        dict: A dictionary containing CPU hardware and performance metrics:
            - 'percents' (list): CPU load percentage per core.
            - 'cores_physical' (int): The number of physical CPU cores.
            - 'cores_logical' (int): The number of logical CPU cores.
            - 'frequency_mhz' (float or None): Current clock speed in MHz, 
              or None if unavailable.
    """
    try:
        try:
            freq = psutil.cpu_freq()
            frequency_mhz = freq.current if freq else None
        except NotImplementedError:
            frequency_mhz = None

        return {
            "percents": psutil.cpu_percent(interval=1, percpu=True),
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "frequency_mhz": frequency_mhz
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
    )
)
def get_mem_info() -> dict:
    """Retrieves system memory metrics expressed in bytes.

    Returns:
        dict: A dictionary containing the following memory statistics:
            - 'total' (int): Total physical memory available.
            - 'available' (int): The memory that can be given instantly to 
              processes without the system going into swap.
            - 'percent' (float): The percentage usage calculated as 
              (total - available) / total * 100.
            - 'used' (int): Memory used (calculated differently depending on the 
              operating system).
            - 'free' (int): Memory not being used at all that is readily 
              available.
            - 'active' (int or None): Memory currently in use or very recently 
              used (returns None if not available on the platform).
            - 'inactive' (int or None): Memory marked as not used (returns None 
              if not available on the platform).
            - 'buffers' (int or None): Cache for things like file system 
              metadata (returns None if not available on the platform).
            - 'cached' (int or None): Cache for various files (returns None if 
              not available on the platform).
            - 'shared' (int or None): Memory that may be simultaneously 
              accessed by multiple processes (returns None if not available on 
              the platform).
            - 'slab' (int or None): In-kernel data structures cache (returns 
              None if not available on the platform).
            - 'wired' (int or None): Memory that is marked to always stay in 
              RAM; It is never moved to disk. (returns None if not 
              available on the platform).
    """
    try:
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used,
            "free": mem.free,
            "active": getattr(mem, "active", None),
            "inactive": getattr(mem, "inactive", None),
            "buffers": getattr(mem, "buffers", None),
            "cached": getattr(mem, "cached", None),
            "shared": getattr(mem, "shared", None),
            "slab": getattr(mem, "slab", None),
            "wired": getattr(mem, "wired", None)
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
    )
)
def get_disk_info() -> dict:
    """Retrieves disk space usage and properties for all accessible partitions.

    Returns:
        dict: A nested dictionary mapping device names to their properties.
            Each device contains the following keys:
            - 'mountpoint' (str): The directory where the device is mounted.
            - 'fstype' (str): The filesystem type (e.g., ext4, ntfs, hfs).
            - 'opts' (str): Mount options (comma-separated string).
            - 'total' (int): Total storage capacity in bytes.
            - 'used' (int): Used storage space in bytes.
            - 'free' (int): Available storage space in bytes.
            - 'percent' (float): Percentage of storage capacity utilized.
    """
    try:
        disks = {}
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks[part.device] = {
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "opts": part.opts,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                }
            except (PermissionError, OSError):
                continue
        return disks
    except Exception as e:
        return {"error": str(e)}


def _get_gpu_info_windows() -> list:
    gpus = []

    try:
        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        for i in range(count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpus.append({
                "name": pynvml.nvmlDeviceGetName(handle),
                "driver_version": pynvml.nvmlSystemGetDriverVersion(),
                "vram": mem.total
            })
    except pynvml.NVMLError:
        pass

    try:
        import wmi
        w = wmi.WMI()
        for gpu in w.Win32_VideoController():
            if "nvidia" in (gpu.Name or "").lower():
                continue
            gpus.append({
                "name": gpu.Name,
                "driver_version": gpu.DriverVersion,
                "vram": gpu.AdapterRAM if gpu.AdapterRAM >= 0 else gpu.AdapterRAM + 2 ** 32
            })
    except Exception:
        pass

    return gpus


def _get_gpu_info_linux() -> list:
    try:
        result = subprocess.run(
            ["lspci"], capture_output=True, text=True
        )
        return [
            {"name": line.split(":", 2)[-1].strip()}
            for line in result.stdout.splitlines()
            if "VGA" in line or "3D" in line
        ]
    except FileNotFoundError:
        return []


def _get_gpu_info_macos() -> list:
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True, text=True
        )
    except FileNotFoundError:
        return []

    gpus = []
    name, vram = None, None
    for line in result.stdout.splitlines():
        if "Chipset Model" in line:
            name = line.split(":")[1].strip()
        if "VRAM" in line:
            vram = line.split(":")[1].strip()
        if name and vram:
            gpus.append({"name": name, "vram": vram})
            name, vram = None, None
    return gpus


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
    )
)
def get_gpu_info() -> dict:
    """Cross-platform wrapper that delegates GPU data collection to OS-specific handlers.

    Returns:
        dict: A dictionary wrapping the operational outcome:
            - 'gpus' (list of dict): Successfully collected GPU arrays, OR
            - 'error' (str): The exception trace string if an evaluation fails.
    """
    os_name = platform.system()
    try:
        if os_name == "Windows":
            return {"gpus": _get_gpu_info_windows()}
        elif os_name == "Darwin":
            return {"gpus": _get_gpu_info_macos()}
        else:
            return {"gpus": _get_gpu_info_linux()}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
