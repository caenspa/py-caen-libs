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
