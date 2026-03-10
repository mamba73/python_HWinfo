import platform
import psutil
import wmi

def get_ram_type(type_id):
    """Maps SMBIOS MemoryType IDs to human-readable strings."""
    # Common SMBIOS memory types
    types = {
        0: 'Unknown', 1: 'Other', 20: 'DDR', 21: 'DDR2', 
        22: 'DDR2 FB-DIMM', 24: 'DDR3', 26: 'DDR4', 34: 'DDR5'
    }
    return types.get(type_id, f"DDR{type_id}")

def display_hardware_info():
    c = wmi.WMI()

    # --- CPU Information ---
    # Fetching Name from Win32_Processor provides the marketing name (e.g., i5-6500)
    cpu = c.Win32_Processor()[0]
    cpu_speed = psutil.cpu_freq().current
    print(f"CPU: {cpu.Name.strip()} @ {cpu_speed:.0f} MHz")
    print(f"  - Cores: {psutil.cpu_count(logical=False)}, Threads: {psutil.cpu_count(logical=True)}")

    # --- RAM Information ---
    print("\nRAM:")
    total_ram = 0
    for module in c.Win32_PhysicalMemory():
        cap_gb = int(module.Capacity) / (1024**3)
        total_ram += cap_gb
        mfg = module.Manufacturer if module.Manufacturer else "Unknown"
        # SMBIOSMemoryType identifies DDR generation
        ram_gen = get_ram_type(module.SMBIOSMemoryType)
        print(f"  - {mfg} {module.PartNumber} {module.Speed}MHz {ram_gen} {cap_gb:.2f} GB")
    print(f"  Total: {total_ram:.2f} GB")

    # --- GPU Information ---
    print("\nGPU:")
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
        
        print(f"  - Vendor: {vendor}")
        print(f"  - Model: {gpu.Caption}")

    # --- DISK Information ---
    print("\nDISKS:")
    for i, disk in enumerate(c.Win32_DiskDrive()):
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

        print(f"Disk{i+1}: {disk.Model}")
        print(f"  - Vendor/Type: {vendor} ({drive_type})")

        # Partition mapping
        for partition in disk.references("Win32_DiskDriveToDiskPartition"):
            for logical_disk in partition.Dependent.references("Win32_LogicalDiskToPartition"):
                letter = logical_disk.Dependent.DeviceID
                try:
                    usage = psutil.disk_usage(letter + "\\")
                    print(f"  - Partition {letter} ({logical_disk.Dependent.FileSystem}) - {usage.total / (1024**3):.2f} GB")
                except:
                    print(f"  - Partition {letter} (Access Denied/Ready)")

    # --- Optical Drives ---
    print("\nOPTICAL DRIVES:")
    optical = c.Win32_CDROMDrive()
    if optical:
        for drive in optical:
            print(f"  - {drive.Name} (Mfr: {drive.Manufacturer or 'Unknown'})")
    else:
        print("  - None")

    # --- OS Information ---
    print(f"\nOperating System: {platform.system()} {platform.release()}")
    print(f"  - Arch: {platform.machine()} ({platform.architecture()[0]})")

if __name__ == "__main__":
    display_hardware_info()
