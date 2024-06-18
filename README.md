# caen_libs
Official Python binding for CAEN VMELib, CAEN Comm, CAEN PLU and CAEN HV Wrapper libraries.

## Install
You need to install the latest version of the libraries from [the CAEN website](https://www.caen.it/subfamilies/software-libraries/).

Then, install this module and have fun.

## Examples
This example show the simplest way to read some registers using the CAEN Comm:

```python
from caen_libs import caencomm as comm


print(f'CAEN Comm binding loaded (lib version {comm.lib.sw_release()})')

conn_type = comm.ConnectionType.USB
link_number = 0
conet_node = 0
vme_ba = 0

with comm.Device.open(conn_type, link_number, conet_node, vme_ba) as device:
    # Assuming to be connected to a CAEN Digitizer 1.0
    serial_byte_1 = device.read32(0xF080) & 0xFF
    serial_byte_0 = device.read32(0xF084) & 0xFF
    serial_number = (serial_byte_1 << 8) | serial_byte_0
    print(f'Connected to device with serial number {serial_number}')
```

## References
Requirements and documentation can be found at 
https://www.caen.it/subfamilies/software-libraries/.
