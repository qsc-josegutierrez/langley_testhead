import ctypes
import os
import sys

def find_dll():
    """
    Search for AIOUSB.dll in multiple locations:
    1. Next to the executable (for PyInstaller bundles)
    2. drivers/ subdirectory (for portable deployment)
    3. C:\Windows\System32 (for system-installed DLL)
    4. Current working directory
    """
    # Get the directory where the executable/script is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    search_paths = [
        os.path.join(app_dir, "AIOUSB.dll"),                    # Next to exe
        os.path.join(app_dir, "drivers", "AIOUSB.dll"),         # drivers/ subfolder
        os.path.join(os.path.dirname(app_dir), "drivers", "AIOUSB.dll"),  # Parent/drivers/
        r"C:\Windows\System32\AIOUSB.dll",                      # System directory
        os.path.join(os.getcwd(), "AIOUSB.dll"),                # Current directory
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return path
    
    return None

class AccesDIO:
    def __init__(self, dio_model="ACCESSIO_96", dll_path=None):
        # Allow manual DLL path override, otherwise search automatically
        if dll_path is None:
            dll_path = find_dll()
        
        if dll_path is None:
            raise FileNotFoundError(
                "AIOUSB.dll not found. Searched locations:\n"
                "  - Next to executable\n"
                "  - drivers/ subdirectory\n"
                "  - C:\\Windows\\System32\n"
                "  - Current working directory"
            )
        
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"AIOUSB.dll not found at {dll_path}")
        
        print(f"Loading AIOUSB.dll from: {dll_path}")
        self.dll = ctypes.windll.LoadLibrary(dll_path)
        self._bind_functions()

        self.dio_model = dio_model.upper()
        self.model_line_map = {
            "ACCESSIO_16": 16,
            "ACCESSIO_48": 48,
            "ACCESSIO_96": 96
        }
        self.max_lines = self.model_line_map.get(self.dio_model, 96)
        self.port_count = self.max_lines // 8

        self.dll.DIO_Configure.argtypes = [
            ctypes.c_uint32,    # DeviceIndex
            ctypes.c_ubyte,     # Tristate (0 = active, 1 = tristate)
            ctypes.POINTER(ctypes.c_ushort),    # OutMask
            ctypes.POINTER(ctypes.c_ubyte)      # Data
        ]
        self.dll.DIO_Configure.restype = ctypes.c_uint32

    def _bind_functions(self):
        self.dll.GetDeviceByEEPROMByte.restype = ctypes.c_uint32
        self.dll.GetDeviceByEEPROMByte.argtypes = [ctypes.c_ubyte]

        self.dll.GetDeviceByEEPROMData.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte]
        self.dll.GetDeviceByEEPROMData.restype = ctypes.c_uint32

        self.dll.DIO_Write1.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_ubyte]
        self.dll.DIO_Write1.restype = ctypes.c_uint32

        self.dll.DIO_ReadAll.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte)]
        self.dll.DIO_ReadAll.restype = ctypes.c_uint32

    def get_device_by_eeprom_byte(self, board_id):
        """
        Retrieves the device index of the device with the specified EEPROM byte at address 0x00.

        Args:
            board_id (int): The user-defined board ID byte (0–255) programmed into EEPROM at address 0x00.

        Returns:
            int: The device index if found.

        Raises:
            ValueError: If board_id is out of range.
            RuntimeError: If no matching device is found.
        """
        if not (0 <= board_id <= 255):
            raise ValueError("board_id must be an integer between 0 and 255.")
        device_index = self.dll.GetDeviceByEEPROMByte(ctypes.c_ubyte(board_id))
        if device_index in (0xFFFFFFFF, -1):
            raise RuntimeError(f"No device found with EEPROM byte 0x{board_id:02X} at address 0x00.")
        return device_index

    def configure_output(self, device_index, pin_values, default_low=True):
        """
        Configure specified pins as outputs and set their values.

        Args:
            device_index (int): Index of the target device.
            pin_values (dict): Dictionary where keys are line numbers (0 to max lines) and values are 0 or 1.
            default_low (bool): If True, sets unspecified pins to low (0); otherwise, high (1).
        """
        out_mask = ctypes.c_ushort(0x0000)
        data = (ctypes.c_ubyte * self.port_count)(*([0x00 if default_low else 0xFF] * self.port_count))

        for line, value in pin_values.items():
            if not (0 <= line < self.max_lines):
                raise ValueError(f"Invalid line number: {line}")
            port = line // 8
            bit = line % 8
            if value:
                data[port] |= (1 << bit)
            else:
                data[port] &= ~(1 << bit)
            out_mask.value |= (1 << port)

        result = self.dll.DIO_Configure(device_index, 0, ctypes.byref(out_mask), data)
        if result != 0:
            raise RuntimeError(f"DIO_Configure failed with code {result}")

    # line_number is 1-based and starts at 1. The code adjust for 0-based indexing.
    def write_line(self, device_index, line_number, value):
        line_number -= 1
        if not (0 <= line_number < self.max_lines):
            raise ValueError("line_number out of range")
        result = self.dll.DIO_Write1(device_index, line_number, value)
        if result != 0:
            raise RuntimeError(f"DIO_Write1 failed for line {line_number}, value {value}, code={result}")

    def read_all_lines(self, device_index):
        """
        Reads the current state of all digital lines (inputs and outputs).

        Args:
            device_index (int): Index of the device.

        Returns:
            list: A list of integers representing the state of each line (0 or 1).
        """        
        buffer = (ctypes.c_ubyte * self.port_count)()
        #result = self.dll.DIO_ReadAll(ctypes.c_uint32(device_index), ctypes.byref(buffer))
        result = self.dll.DIO_ReadAll(ctypes.c_uint32(device_index), buffer)
        if result != 0:
            raise RuntimeError(f"DIO_ReadAll failed with code {result}")
        return list(buffer)

    # Convert GroupPortBit to line number (1-based)
    # There are 4 Groups: 0-3, one for each connector
    # Each Group has 3 Ports: A, B, C
    # Each Port has 8 Bits: 0-7
    # For example: 0A0 is pin 1 and 0B5 is pin 14. 0C7 is pin 24 etc.
    def groupportbit_to_line_number(self, groupportbit):
        """
        Converts a GroupPortBit string to a line number (1-based).

        Args:
            groupportbit (str): A string in the format '0A0', '1B5', etc.

        Returns:
            int: The corresponding line number (1 to max lines).

        Raises:
            ValueError: If the input format is invalid. Exceeds max line count for the model.
        """
        if len(groupportbit) != 3 or groupportbit[0] not in '0123' or groupportbit[1] not in 'ABC' or not groupportbit[2].isdigit():
            raise ValueError("Invalid GroupPortBit format. Expected format like '0A0', '1B5', etc.")
        group = int(groupportbit[0])
        port = ord(groupportbit[1]) - ord('A')
        bit = int(groupportbit[2])
        line_number = (group * 24) + (port * 8) + (bit + 1)
        if line_number > self.max_lines:
            raise ValueError(f"GroupPortBit {groupportbit} exceeds max line count for {self.dio_model}")
        return line_number

    def write_groupportbit_preserve(self, device_index, groupportbit, value):
        """
        Writes a value to a specific GroupPortBit while preserving the state of other lines.

        Args:
            device_index (int): Index of the device.
            groupportbit (str): A string in the format '0A0', '1B5', etc.
            value (int): The value to write (0 or 1).

        Raises:
            ValueError: If groupportbit format is invalid or value is not 0 or 1.
            RuntimeError: If the DIO_Configure operation fails.
        """

        line_number = self.groupportbit_to_line_number(groupportbit)
        if not (0 <= line_number < self.max_lines):
            raise ValueError(f"Line number {line_number} exceeds max for model {self.dio_model}")
        if value not in (0, 1):
            raise ValueError("value must be 0 or 1")
        self.write_line_preserve(device_index, line_number, value)

    # line_number is 1-based and starts at 1. The code adjust for 0-based indexing.
    def write_line_preserve(self, device_index, line_number, value):
        line_number -= 1
        if not (0 <= line_number < self.max_lines):
            raise ValueError("line_number out of range")
        if value not in (0, 1):
            raise ValueError("value must be 0 or 1")

        # Read current state of all ports
        buffer = (ctypes.c_ubyte * self.port_count)()
        #result = self.dll.DIO_ReadAll(ctypes.c_uint32(device_index), ctypes.byref(buffer))  # byref doesn't work with model-specific ctypes array
        result = self.dll.DIO_ReadAll(ctypes.c_uint32(device_index), buffer)
        if result != 0:
            raise RuntimeError(f"DIO_ReadAll failed with code {result}")

        # Identify port and bit
        port = line_number // 8
        bit = line_number % 8

        # Modify only the target bit in the buffer
        if value:
            buffer[port] |= (1 << bit)
        else:
            buffer[port] &= ~(1 << bit)

        # Set out_mask to enable output on all ports
        out_mask = ctypes.c_ushort((1 << self.port_count) - 1)
        # Write back the full buffer to preserve all states
        result = self.dll.DIO_Configure(device_index, 0, ctypes.byref(out_mask), buffer)
        if result != 0:
            raise RuntimeError(f"DIO_Configure failed with code {result}")

    def reset_all_lines_low(self, device_index):
        """
        Resets all (max) digital lines (ports) to low (0) in a single operation.

        Args:
            device_index (int): Index of the device.
        """
        data = (ctypes.c_ubyte * self.port_count)(*([0x00] * self.port_count))
        out_mask = ctypes.c_ushort((1 << self.port_count) - 1)
        result = self.dll.DIO_Configure(device_index, 0, ctypes.byref(out_mask), data)
        if result != 0:
            raise RuntimeError(f"DIO_Configure failed while resetting all lines: code {result}")
