from caen_libs import caenvme as vme


print(f'CAEN VME wrapper loaded (lib version {vme.lib.sw_release()})')

board_type = vme.BoardType.USB_V4718
link_number = 0
conet_node = 0

with vme.Device.open(board_type, link_number, conet_node) as device:
    # Assuming to be connected to a CAEN Digitizer 1.0
    serial_byte_1 = device.read_cycle(0xF080, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32) & 0xFF
    serial_byte_0 = device.read_cycle(0xF084, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32) & 0xFF
    serial_number = (serial_byte_1 << 8) | serial_byte_0
    print(f'Connected to device with serial number {serial_number}')
