from caen_libs import _utils
from enum import Flag, IntEnum
from typing import Any, List, Sequence, Type, Union

class ErrorCode(IntEnum):
    SUCCESS: int = ...
    VME_BUS_ERROR: int = ...
    COMM_ERROR: int = ...
    GENERIC_ERROR: int = ...
    INVALID_PARAM: int = ...
    INVALID_LINK_TYPE: int = ...
    INVALID_HANDLER: int = ...
    COMM_TIMEOUT: int = ...
    DEVICE_NOT_FOUND: int = ...
    MAX_DEVICES_ERROR: int = ...
    DEVICE_ALREADY_OPEN: int = ...
    NOT_SUPPORTED: int = ...
    UNUSED_BRIDGE: int = ...
    TERMINATED: int = ...
    UNSUPPORTED_BASE_ADDRESS: int = ...

class ConnectionType(IntEnum):
    USB: int = ...
    OPTICAL_LINK: int = ...
    USB_A4818: int = ...
    ETH_V4718: int = ...
    USB_V4718: int = ...

class Info(IntEnum):
    PCI_BOARD_SN: int = ...
    PCI_BOARD_FW_REL: int = ...
    VME_BRIDGE_SN: int = ...
    VME_BRIDGE_FW_REL_1: int = ...
    VME_BRIDGE_FW_REL_2: int = ...

class IRQLevels(Flag):
    L1: int = ...
    L2: int = ...
    L3: int = ...
    L4: int = ...
    L5: int = ...
    L6: int = ...
    L7: int = ...

class Error(RuntimeError):
    code: ErrorCode
    message: str
    func: str
    def __init__(self, message: str, res: int, func: str) -> None: ...

class _Lib(_utils.Lib):
    def __init__(self, name: str) -> None: ...
    def decode_error(self, error_code: int) -> str: ...
    def sw_release(self) -> str: ...
    def vme_irq_check(self, vme_handle: int) -> IRQLevels: ...
    def vme_iack_cycle16(self, vme_handle: int, levels: IRQLevels) -> int: ...
    def vme_iack_cycle32(self, vme_handle: int, levels: IRQLevels) -> int: ...
    def vme_irq_wait(self, connection_type: ConnectionType, link_num: int, conet_node: int, irq_mask: IRQLevels, timeout: int) -> int: ...
    def reboot_device(self, link_number: int, use_backup: bool) -> None: ...

lib: _Lib

class Device:
    handle: int
    opened: bool = ...
    connection_type: ConnectionType = ...
    arg: Union[int, str] = ...
    conet_node: int = ...
    vme_base_address: int = ...
    def __del__(self) -> None: ...
    @classmethod
    def open(cls: Type[_T], connection_type: ConnectionType, arg: Union[int, str], conet_node: int, vme_base_address: int) -> _T: ...
    def connect(self) -> None: ...
    def close(self) -> None: ...
    def write32(self, address: int, value: int) -> None: ...
    def write16(self, address: int, value: int) -> None: ...
    def read32(self, address: int) -> int: ...
    def read16(self, address: int) -> int: ...
    def multi_write32(self, address: Sequence[int], data: Sequence[int]) -> None: ...
    def multi_write16(self, address: Sequence[int], data: Sequence[int]) -> None: ...
    def multi_read32(self, address: Sequence[int]) -> List[int]: ...
    def multi_read16(self, address: Sequence[int]) -> List[int]: ...
    def blt_read(self, address: int, blt_size: int) -> List[int]: ...
    def mblt_read(self, address: int, blt_size: int) -> List[int]: ...
    def irq_disable(self, mask: int) -> None: ...
    def irq_enable(self, mask: int) -> None: ...
    def iack_cycle(self, levels: IRQLevels) -> int: ...
    def irq_wait(self, timeout: int) -> None: ...
    def info(self, info_type: Info) -> str: ...
    def vme_handle(self) -> int: ...
    def device_closed(self) -> None: ...
    def __enter__(self) -> None: ...
    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None: ...
    def __init__(self, handle: Any, opened: Any, connection_type: Any, arg: Any, conet_node: Any, vme_base_address: Any) -> None: ...