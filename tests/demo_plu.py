from caen_libs import caenplu as plu


print('CAEN PLU binding loaded')

for board in plu.lib.usb_enumerate():
    print(board)
