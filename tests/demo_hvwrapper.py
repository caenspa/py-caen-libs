from caen_libs import caenhvwrapper as hv


connection_type = hv.SystemType.N1470
link_type = hv.LinkType.USB_VCP

with hv.Device.open(connection_type, link_type, 'COM4_9600_8_1_0_0', '', '') as device:

    slots = device.get_crate_map()  # initialize internal stuff

    comm_list = device.get_exec_comm_list()
    print('EXEC_COMM_LIST', comm_list)

    sys_props = device.get_sys_prop_list()
    for prop_name in sys_props:
        prop_info = device.get_sys_prop_info(prop_name)
        print('SYSPROP', prop_name, prop_info.type.name)
        if prop_info.mode != hv.SysPropMode.WRONLY:
            prop_value = device.get_sys_prop(prop_name)
            print('VALUE', prop_value)
    #device.subscribe_system_params(sys_props)

    for slot, board in enumerate(slots):
        if board.model != '':
            bd_params = device.get_bd_param_info(slot)
            for param_name in bd_params:
                param_prop = device.get_bd_param_prop(slot, param_name)
                print('BD_PARAM', slot, param_name, param_prop.type.name)
                if param_prop.mode != hv.ParamMode.WRONLY:
                    param_value = device.get_bd_param([slot], param_name)
                    print('VALUE', param_value)
            #device.subscribe_board_params(slot, bd_params)
            for ch in range(board.n_channel):
                ch_params = device.get_ch_param_info(slot, ch)
                for param_name in ch_params:
                    param_prop = device.get_ch_param_prop(slot, ch, param_name)
                    print('CH_PARAM', slot, ch, param_name, param_prop.type.name)
                    if param_prop.mode != hv.ParamMode.WRONLY:
                        param_value = device.get_ch_param(slot, [ch], param_name)
                        print('VALUE', param_value)
                #device.subscribe_channel_params(slot, ch, ch_params)

    while True:
        evt_list, _ = device.get_event_data()
        for evt in evt_list:
            if evt.type != hv.EventType.KEEPALIVE:
                print(evt)
