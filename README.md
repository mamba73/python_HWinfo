# Hardware Info Script

A Python-based utility to retrieve detailed hardware specifications on Windows systems, including CPU, RAM modules, GPU, Disk types (NVMe/SSD/HDD/USB) with correct partition mapping, and Optical drives.

## 🛠️ Requirements

- **Python 3.x**
- **Windows OS** (WMI dependency)

## 📦 Installation

Install the required Python libraries using pip:

```
pip install psutil wmi GPUtil
```

## 🚀 Usage

Simply run the script from your terminal or command prompt:

```
python hardware_info.py
```

## 📝 Features
- **Accurate Partition Mapping:** Shows only partitions belonging to the specific physical disk.
- **USB Vendor Detection:** Identifies the manufacturer of external USB drives via PNPDeviceID.
- **Smart Disk Classification:** Automatically detects if a drive is NVMe, SSD, HDD, or USB.
- **System Architecture:** Clearly displays if the OS is 32-bit or 64-bit.

---
## ☕ Support
If you like this project and want to support development:
[Buy Me a Coffee ☕](https://buymeacoffee.com/mamba73)

*Project is currently under active development.*
*Developed by mamba*
