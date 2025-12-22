from accesio import accesio_dio as dio
import os
#This script also requires openpyxl "pip install openpyxl"
import pandas as pd
import sys # for command line arguments
from config_loader import ConfigLoader


def get_config_path(filename):
    """
    Find configuration file in multiple locations:
    1. Absolute path if provided
    2. Relative to executable (for PyInstaller bundles)
    3. config/ subdirectory next to executable
    4. config/ subdirectory in current working directory
    """
    # If absolute path provided and exists, use it
    if os.path.isabs(filename) and os.path.exists(filename):
        return filename
    
    # Get the directory where the executable/script is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    search_paths = [
        filename,                                           # Relative to current dir
        os.path.join(app_dir, filename),                   # Next to exe
        os.path.join(app_dir, "config", filename),         # config/ subfolder
        os.path.join(os.getcwd(), "config", filename),     # cwd/config/
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return path
    
    # If not found, return the config/ path as default (will fail with clear error)
    return os.path.join(app_dir, "config", filename)


class Testhead_Control:
    def __init__(self):
        """Initialize instance variables"""
        self.command_success = False
        self.dio_model = None
        self.dio = None
        self.device_index = None
    
    def run(self, testhead_lookup_xlsx="", dio_name="TestHead", dio_pathname="", sheet_name="Model_Common"):
        """Execute the testhead control sequence"""
        self.command_success = False  # Initialize command success status
        
        # Resolve config file path - use get_config_path to search multiple locations
        if not testhead_lookup_xlsx:
            # Default to the standard config file if none provided
            testhead_lookup_xlsx = "Amplifier_Testhead Switch Path Configuration.xlsx"
        
        testhead_lookup_xlsx = get_config_path(testhead_lookup_xlsx)
        print(f"Using config file: {testhead_lookup_xlsx}")
        
        # Use ConfigLoader to handle both Excel and JSON formats
        config_loader = ConfigLoader(testhead_lookup_xlsx)
        
        # Load DIO List
        dio_list_df = config_loader.load_dio_list()
        
        # Print preview of the DIO List
        print("DIO List loaded:")
        if config_loader.file_format == 'excel':
            print(dio_list_df.head())
        else:
            print(f"Found {len(dio_list_df)} DIO devices")

        # Get the MODEL and HEXADDRESS for the dio_name
        dio_model, dio_hexaddress = config_loader.get_device_info(dio_name)
        self.dio_model = dio_model.upper()  # Ensure model is uppercase (needed for set_line method)

        # Load Command List
        dio_cmdlist_df = config_loader.load_command_list(sheet_name)
        
        # Print preview of the Command List
        print("Command List loaded:")
        if config_loader.file_format == 'excel':
            print(dio_cmdlist_df.head())
        else:
            print(f"Found {len(dio_cmdlist_df)} commands for {sheet_name}")

        # Get the Switch Driver Command for the pathname
        switch_driver_command = config_loader.get_switch_command(dio_pathname, sheet_name)

        # Convert to int
        device_board_id = int(dio_hexaddress, 16)
        
        # Initialize the DIO object with the specified model (needed for all DIO operations)
        self.dio = dio.AccesDIO(dio_model=self.dio_model)
        
        # get the custom programmed board ID from EEPROM at address 0 (needed for all DIO operations)
        self.device_index = self.dio.get_device_by_eeprom_byte(device_board_id)

        if self.device_index is None:
            raise RuntimeError(f"Device with board ID {device_board_id} not found.")
        
        print(f"Board ID: {device_board_id} found with Device Index: {self.device_index}")
        
        # Process the Switch Driver Command
        print(f"Processing Switch Driver Command: {switch_driver_command}")
        self.process_switch_driver_command(switch_driver_command)

        # No raise exception here, print success message and set command_success to True
        self.command_success = True
        print(f"command_success: {self.command_success}")

    # ***********************************
    # Excel and Dataframe Related Functions
    # ***********************************
    def read_excelfile_sheet_to_df(self, excel_file_path, excel_sheet_name, header_row_num=0):
        if not os.path.exists(excel_file_path):
            print(f"Excel file not found at {excel_file_path}")
            raise FileNotFoundError(f"Excel file not found at {excel_file_path}")
        else:
            print(f"Excel file found at {excel_file_path}")
        #Check if Sheet exists
        xl = pd.ExcelFile(excel_file_path)
        if excel_sheet_name not in xl.sheet_names:
            print(f"Sheet {excel_sheet_name} not found in {excel_file_path}")
            raise ValueError(f"Sheet {excel_sheet_name} not found in {excel_file_path}")
        else:
            print(f"Sheet '{excel_sheet_name}' found")
        #Read Excel file to DataFrame
        #Read all data as string
        print(f"Reading Excel file to DataFrame with header row at: {header_row_num}")
        df = pd.read_excel(excel_file_path, sheet_name=excel_sheet_name, dtype=str, header=header_row_num, keep_default_na=False)
        return df

    def dio_list_validate_column_names(self):
        #Check if all required columns are present
        required_columns = [
            self.DIO_List_MODEL_Columnname,
            self.DIO_List_NAME_Columnname,
            self.DIO_List_HEXADDRESS_Columnname
        ]
        for col in required_columns:
            if col not in self.dio_list_df.columns:
                print(f"Column '{col}' not found in the DataFrame")
                raise ValueError(f"Column '{col}' not found in the DataFrame")
                sys.exit(1)
        print(f"All required columns found in the DataFrame")

    def dio_cmdlist_validate_column_names(self):
        #Check if all required columns are present
        required_columns = [
            self.DIO_CmdList_PathName_Columnname,
            self.DIO_CmdList_SwitchDriverCommand_Columnname
        ]
        for col in required_columns:
            if col not in self.dio_cmdlist_df.columns:
                print(f"Column '{col}' not found in the DataFrame")
                raise ValueError(f"Column '{col}' not found in the DataFrame")
                sys.exit(1)
        print(f"All required columns found in the DataFrame")

    # Lookup NAME to MODEL and HEXADDRESS in dio_list_df
    def dio_name_to_model_and_address(self, dio_name):
        """Get the MODEL and HEXADDRESS for a given dio_name from the dio_list_df DataFrame."""
        if dio_name not in self.dio_list_df[self.DIO_List_NAME_Columnname].values:
            raise ValueError(f"DIO name '{dio_name}' not found in the DIO list.")
        
        model = self.dio_list_df.loc[self.dio_list_df[self.DIO_List_NAME_Columnname] == dio_name,
                                     self.DIO_List_MODEL_Columnname].values[0]
        print(f"DIO name '{dio_name}' corresponds to MODEL '{model}'")

        address = self.dio_list_df.loc[self.dio_list_df[self.DIO_List_NAME_Columnname] == dio_name, 
                                       self.DIO_List_HEXADDRESS_Columnname].values[0]
        print(f"DIO name '{dio_name}' corresponds to HEXADDRESS '{address}'")
        return model, address

    # Lookup PathName to SwitchDriverCommand in dio_cmdlist_df
    def dio_pathname_to_switchdrivercommand(self, dio_pathname):
        """Get the SwitchDriverCommand for a given dio_pathname from the dio_cmdlist_df DataFrame."""
        if dio_pathname not in self.dio_cmdlist_df[self.DIO_CmdList_PathName_Columnname].values:
            raise ValueError(f"DIO pathname '{dio_pathname}' not found in the DIO command list.")
        
        command = self.dio_cmdlist_df.loc[self.dio_cmdlist_df[self.DIO_CmdList_PathName_Columnname] == dio_pathname, 
                                          self.DIO_CmdList_SwitchDriverCommand_Columnname].values[0]
        print(f"DIO pathname '{dio_pathname}' corresponds to SwitchDriverCommand '{command}'")
        return command

    # ***********************************
    # DIO Related Functions
    # ***********************************
    def set_line(self, line_number, value):
        """Set a digital output line to a specific value. This resets other pin states"""
        if not (0 <= line_number < self.dio.max_lines):
            raise ValueError(f"Line number {line_number} exceeds max for model {self.dio_model}")
        self.dio.write_line(self.device_index, line_number, value)
        print(f"Line {line_number} set to {value}")

    def set_groupportbit_preserve(self, groupportbit, value):
        """Set a group port bit to a specific value without affecting other bits."""
        self.dio.write_groupportbit_preserve(self.device_index, groupportbit, value)
        print(f"Group Port Bit {groupportbit} set to {value} (preserved)")

    def set_line_preserve(self, line_number, value):
        """Set a digital output line to a specific value without affecting other lines."""
        if not (0 <= line_number < self.dio.max_lines):
            raise ValueError(f"Line number {line_number} exceeds max for model {self.dio_model}")
        self.dio.write_line_preserve(self.device_index, line_number, value)
        print(f"Line {line_number} set to {value} (preserved)")

    def reset_all_lines_low(self):
        """Reset all digital output lines to low."""
        self.dio.reset_all_lines_low(self.device_index)
        print("All lines reset to low")

    # Function to process the Switch Driver Command
    # Example command: "0;0B4,1;0B5,1;0B6,1;0B7,1;0B1,1;3A1,1"
    # Each command separated by semicolon ';' and paired with on (1) or off (0) state
    # '0' means reset all lines low
    # It's possible to only have a single command like "0B4,1"
    # Only '0' is acceptable as single part. Other commands must be 2-part like "0B4,1" or "0B4,0"
    def process_switch_driver_command(self, command):
        """Process the Switch Driver Command to set lines."""
        if not command:
            print("No command provided.")
            return
        
        # Split commands by ';' or also accept single command without ';'
        commands = command.split(';')
        if len(commands) == 1 and ',' in commands[0]:
            # Single command without ';'
            commands = [commands[0]]
        elif len(commands) == 1:
            # Single command with no ',' or ';'
            commands = [f"{commands[0]}"]
        elif len(commands) == 0:
            print("No valid commands found in the provided command string.")
            return
        print(f"Processing commands: {commands}")
        for cmd in commands:
            # If command is '0', set all pins to output and reset all lines to low
            if cmd == '0':
                self.dio.configure_output(self.device_index, {i: 0 for i in range(self.dio.max_lines)}, default_low=True)
                self.reset_all_lines_low()
                continue
            elif ',' not in cmd:
                print(f"Invalid command format: {cmd}. Expected format is 'line,value'.")
                continue
            else:
                # Split the command into line and value
                line, value = cmd.split(',')
                try:
                    groupportbit = line.strip()
                    value = int(value.strip())
                    self.set_groupportbit_preserve(groupportbit, value)
                except ValueError as e:
                    print(f"Error processing command '{cmd}': {e}")


# Main for testing

# Example usage from console or command line. Change to EXE if running as an executable.
# Start with: python src\shared\instr_drivers\instruments\test_head\testhead_control.py
# Example parameters:
# "C:\gitrepos\qsctestexecutive\Resources\LookupData\Amplifier_Testhead Switch Path Configuration.xlsx" "TestHead" "Initialize Testhead, Cells ON, Filter ON, Main ON"
# "C:\gitrepos\qsctestexecutive\Resources\LookupData\Amplifier_Testhead Switch Path Configuration.xlsx" "TestHead" "Initialize Testhead, Clear ALL"
# "C:\gitrepos\qsctestexecutive\Resources\LookupData\Amplifier_Testhead Switch Path Configuration.xlsx" "TestHead" "Configure Load Relays to 8ohms"
# "C:\gitrepos\qsctestexecutive\Resources\LookupData\Amplifier_Testhead Switch Path Configuration.xlsx" "TestHead" "CMRR Test Mode ON"

def main():
    """Main entry point for command-line usage"""
    # Accept 4+ arguments from command line: excel_file, sheet_name, dio_name, pathname_components...
    # Minimum 4 arguments: excel_file, sheet_name, dio_name, and at least one pathname component
    if len(sys.argv) < 5:
        print("Usage: python testhead_control.py <excel_file> <sheet_name> <dio_name> <path_component> [path_component2] [...]")
        print("Example: testhead_control.py \"file.xlsx\" \"Model_Common\" \"TestHead\" \"Reset\" \"Balanced Generator\" \"MIC\"")
        raise ValueError(f"Invalid number of arguments. Expected at least 4, got {len(sys.argv) - 1}")
    
    testhead_lookup_xlsx = sys.argv[1]
    sheet_name = sys.argv[2]
    dio_name = sys.argv[3]
    
    # Join all remaining arguments as pathname components with ", " separator
    pathname_components = sys.argv[4:]
    dio_pathname = ", ".join(pathname_components)
    
    print("Arguments received:")
    print(f"testhead_lookup_xlsx: {testhead_lookup_xlsx}")
    print(f"sheet_name: {sheet_name}")
    print(f"dio_name: {dio_name}")
    print(f"pathname_components: {pathname_components}")
    print(f"dio_pathname (joined): {dio_pathname}")
    # Create instance and run with the provided arguments
    testhead = Testhead_Control()
    testhead.run(testhead_lookup_xlsx=testhead_lookup_xlsx,
                 dio_name=dio_name,
                 dio_pathname=dio_pathname,
                 sheet_name=sheet_name)

    # ************************************
    # Example usage of Testhead_Control class and test code
    # ************************************
    # Just instantiate the class with parameters and it will do the rest
    '''
    testhead = Testhead_Control(testhead_lookup_xlsx=r"C:\\gitrepos\\qsctestexecutive\\Resources\\LookupData\\Amplifier_Testhead Switch Path Configuration.xlsx",
                                dio_name="TestHead",
                                #dio_pathname="Initialize Testhead, Cells ON, Filter ON, Main ON")
                                dio_pathname="Initialize Testhead, Clear ALL")
                                #dio_pathname="Configure Load Relays to 8ohms")
                                #dio_pathname="CMRR Test Mode ON")
    '''


if __name__ == "__main__" and not getattr(sys, 'frozen', False):
    # Only run main() if executed as a script, not when imported or frozen in exe
    main()

