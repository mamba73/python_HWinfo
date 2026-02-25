import platform
import psutil
import wmi
import GPUtil

def display_hardware_info():
    c = wmi.WMI()

    # --- CPU Information ---
    cpu_speed = psutil.cpu_freq().current
    print(f"CPU: {platform.processor()} {cpu_speed:.0f} MHz")
    print(f"  - Cores: {psutil.cpu_count(logical=False)}, Threads: {psutil.cpu_count(logical=True)}")

    # --- RAM Information ---
    print("\nRAM:")
    total_ram = 0
    for module in c.Win32_PhysicalMemory():
        cap = int(module.Capacity) / (1024**3)
        total_ram += cap
        manufacturer = module.Manufacturer if module.Manufacturer else "Unknown"
        print(f"  - {manufacturer} {module.PartNumber} {module.Speed}MHz {cap:.2f} GB")
    print(f"  Total: {total_ram:.2f} GB")

    # --- GPU Information ---
    print("\nGPU:")
    gpus = GPUtil.getGPUs()
    if gpus:
        for gpu in gpus:
            print(f"  - {gpu.name} ({gpu.memoryTotal} MB)")
    else:
        print("  - Not detected")

    # --- DISK Information (HDD/SSD/USB) ---
    print("\nDISKS:")
    for i, disk in enumerate(c.Win32_DiskDrive()):
        model = disk.Model.upper()
        
        # Detect USB Manufacturer from PNPDeviceID if standard Manufacturer field is generic
        vendor = disk.Manufacturer
        if "USBSTOR" in disk.PNPDeviceID or "USB" in disk.InterfaceType:
            try:
                # Extracts vendor name from string like 'USBSTOR\DISK&VEN_SAMSUNG&PROD_...'
                vendor_part = disk.PNPDeviceID.split("VEN_")[1].split("&")[0]
                vendor = vendor_part.replace("_", " ")
            except:
                vendor = "USB Device"

        # Determine Drive Type
        if "USB" in disk.InterfaceType or "USB" in model:
            drive_type = f"USB External ({vendor})"
        elif "NVME" in model:
            drive_type = "NVMe SSD"
        elif "SSD" in model:
            drive_type = "SSD"
        else:
            drive_type = "HDD"

        print(f"Disk{i+1}: {disk.Model}")
        print(f"  - Manufacturer: {vendor}")
        print(f"  - Type: {drive_type}")

        # Correctly associate partitions ONLY with this physical drive
        for partition in disk.references("Win32_DiskDriveToDiskPartition"):
            for logical_disk in partition.Dependent.references("Win32_LogicalDiskToPartition"):
                drive_letter = logical_disk.Dependent.DeviceID
                try:
                    usage = psutil.disk_usage(drive_letter + "\\")
                    print(f"  - Partition {drive_letter} ({logical_disk.Dependent.FileSystem}) - {usage.total / (1024**3):.2f} GB")
                except:
                    print(f"  - Partition {drive_letter} (Media not ready)")

    # --- Optical Drives (CD/DVD) ---
    print("\nOPTICAL DRIVES:")
    drives = c.Win32_CDROMDrive()
    if drives:
        for dvd in drives:
            print(f"  - {dvd.Name} (Manufacturer: {dvd.Manufacturer or 'Unknown'})")
    else:
        print("  - No CD/DVD drive detected")

    # --- Operating System Information ---
    os_bit = platform.architecture()[0] # Returns '64bit' or '32bit'
    print(f"\nOperating System: {platform.system()} {platform.release()}")
    print(f"  - Architecture: {platform.machine()}")
    print(f"  - Version: {os_bit}")

if __name__ == "__main__":
    display_hardware_info()