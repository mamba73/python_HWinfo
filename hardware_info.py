SCRIPT_VERSION = "0.0.3"

# --- Terminal Colors ---
CLR_YELLOW = "\033[93m"
CLR_GREEN  = "\033[92m"
CLR_RED    = "\033[91m"
CLR_DEBUG  = "\033[94m"
CLR_RESET  = "\033[0m"

import platform
import psutil
import wmi
import subprocess
import winreg

def get_ram_type(type_id):
    """Maps SMBIOS MemoryType IDs to human-readable strings."""
    # Common SMBIOS memory types
    types = {
        0: 'Unknown', 1: 'Other', 20: 'DDR', 21: 'DDR2',
        22: 'DDR2 FB-DIMM', 24: 'DDR3', 26: 'DDR4', 34: 'DDR5'
    }
    return types.get(type_id, f"DDR{type_id}")

def get_nvidia_vram():
    """Get VRAM for NVIDIA GPUs using nvidia-smi"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            vram_mb = int(result.stdout.strip())
            return f"{vram_mb / 1024:.2f} GB"
    except:
        pass
    return None

def get_gpu_vram_registry(gpu_name):
    """Get VRAM from Windows Registry (works for all vendors)"""
    try:
        key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                
                try:
                    driver_desc, _ = winreg.QueryValueEx(subkey, "DriverDesc")
                    if gpu_name.lower() in driver_desc.lower():
                        try:
                            memory_size, _ = winreg.QueryValueEx(subkey, "HardwareInformation.MemorySize")
                            vram_gb = memory_size / (1024**3)
                            winreg.CloseKey(subkey)
                            winreg.CloseKey(key)
                            return f"{vram_gb:.2f} GB"
                        except:
                            pass
                except:
                    pass
                
                winreg.CloseKey(subkey)
                i += 1
            except OSError:
                break
        
        winreg.CloseKey(key)
    except:
        pass
    
    return None

def get_gpu_vram(gpu_name, vendor):
    """Get VRAM using multiple methods with fallback"""
    # 1. For NVIDIA - try nvidia-smi first (most reliable)
    if vendor == "NVIDIA":
        vram = get_nvidia_vram()
        if vram:
            return vram
    
    # 2. Registry approach (works for all vendors)
    vram = get_gpu_vram_registry(gpu_name)
    if vram:
        return vram
    
    # 3. WMI fallback (has 32-bit bug for >4GB)
    try:
        c = wmi.WMI()
        for gpu in c.Win32_VideoController():
            if gpu_name.lower() in gpu.Caption.lower():
                vram_bytes = int(gpu.AdapterRAM)
                vram_gb = vram_bytes / (1024**3)
                if vram_gb > 0 and vram_gb < 100:
                    return f"{vram_gb:.2f} GB"
    except:
        pass
    
    return "N/A"

def display_hardware_info():
    # Initial Banner
    print(f"\n{CLR_YELLOW}====================================================")
    print(f"   HARDWARE INFO SCANNER v{SCRIPT_VERSION}")
    print(f"   System Hardware Detection Tool")
    print(f"===================================================={CLR_RESET}\n")
    
    c = wmi.WMI()
    
    # --- CPU Information ---
    print(f"{CLR_GREEN}[CPU]{CLR_RESET}")
    cpu = c.Win32_Processor()[0]
    cpu_speed = psutil.cpu_freq().current
    print(f"  Model: {cpu.Name.strip()} @ {cpu_speed:.0f} MHz")
    print(f"  Cores: {psutil.cpu_count(logical=False)} | Threads: {psutil.cpu_count(logical=True)}")
    
    # --- RAM Information ---
    print(f"\n{CLR_GREEN}[RAM]{CLR_RESET}")
    total_ram = 0
    for module in c.Win32_PhysicalMemory():
        cap_gb = int(module.Capacity) / (1024**3)
        total_ram += cap_gb
        mfg = module.Manufacturer if module.Manufacturer else "Unknown"
        ram_gen = get_ram_type(module.SMBIOSMemoryType)
        print(f"  {mfg} {module.PartNumber} {module.Speed}MHz {ram_gen} {cap_gb:.2f} GB")
    print(f"  {CLR_YELLOW}Total: {total_ram:.2f} GB{CLR_RESET}")
    
    # --- GPU Information ---
    print(f"\n{CLR_GREEN}[GPU]{CLR_RESET}")
    for gpu in c.Win32_VideoController():
        name_upper = gpu.Caption.upper()
        
        # Identify vendor based on device caption
        if "NVIDIA" in name_upper:
            vendor = "NVIDIA"
        elif "AMD" in name_upper or "RADEON" in name_upper:
            vendor = "AMD"
        elif "INTEL" in name_upper:
            vendor = "Intel"
        else:
            vendor = "Unknown Vendor"
        
        print(f"  Vendor: {vendor}")
        print(f"  Model: {gpu.Caption}")
        
        # Get VRAM using multiple methods
        vram = get_gpu_vram(gpu.Caption, vendor)
        print(f"  VRAM: {vram}")
    
    # --- DISK Information ---
    print(f"\n{CLR_GREEN}[DISKS]{CLR_RESET}")
    for i, disk in enumerate(c.Win32_DiskDrive(), 1):
        model = disk.Model.upper()
        vendor = disk.Manufacturer
        
        # Determine Drive Type and refined Vendor for USBs
        if "USBSTOR" in disk.PNPDeviceID or "USB" in disk.InterfaceType:
            drive_type = "USB External"
            try:
                vendor = disk.PNPDeviceID.split("VEN_")[1].split("&")[0].replace("_", " ")
            except:
                pass
        elif "NVME" in model:
            drive_type = "NVMe SSD"
        elif "SSD" in model:
            drive_type = "SSD"
        else:
            drive_type = "HDD"
        
        print(f"  Disk{i}: {disk.Model}")
        print(f"    Vendor/Type: {vendor} ({drive_type})")
        
        # Partition mapping
        for partition in disk.references("Win32_DiskDriveToDiskPartition"):
            for logical_disk in partition.Dependent.references("Win32_LogicalDiskToPartition"):
                letter = logical_disk.Dependent.DeviceID
                try:
                    usage = psutil.disk_usage(letter + "\\")
                    print(f"    Partition {letter} ({logical_disk.Dependent.FileSystem}) - {usage.total / (1024**3):.2f} GB")
                except:
                    print(f"    Partition {letter} (Access Denied/Ready)")
    
    # --- Optical Drives ---
    print(f"\n{CLR_GREEN}[OPTICAL DRIVES]{CLR_RESET}")
    optical = c.Win32_CDROMDrive()
    if optical:
        for drive in optical:
            print(f"  {drive.Name} (Mfr: {drive.Manufacturer or 'Unknown'})")
    else:
        print(f"  {CLR_DEBUG}None{CLR_RESET}")
    
    # --- OS Information ---
    print(f"\n{CLR_GREEN}[OPERATING SYSTEM]{CLR_RESET}")
    print(f"  {platform.system()} {platform.release()}")
    print(f"  Architecture: {platform.machine()} ({platform.architecture()[0]})")
    
    print(f"\n{CLR_YELLOW}====================================================")
    print(f"   Scan Complete")
    print(f"===================================================={CLR_RESET}\n")

if __name__ == "__main__":
    display_hardware_info()