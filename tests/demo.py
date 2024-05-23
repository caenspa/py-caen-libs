from caen_libs import caencomm as comm

with comm.Device.open(comm.ConnectionType.USB, 0, 0, 0) as device:
    serial_byte_1 = device.read32(0xF080) & 0xFF
    serial_byte_0 = device.read32(0xF084) & 0xFF
    serial_number = (serial_byte_1 << 8) | serial_byte_0
    print(f'Connected to devive with serial number {serial_number}')
