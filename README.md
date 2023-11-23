# virtual-usbip-py3
A simple rewrite of USBIP-Virtual-USB-Device to python3 for my personal experiments. Supports multiple interfaces.
Very barebones. May or may not work for you. For more information check original USBIP-Virtual-USB-Device.

Depends on python-construct

Start a server with:
```
python example.py
```

And attach device:
```
sudo modprobe vhci-hcd
sudo usbip attach -r 127.0.0.1 -b "1-1"
```
