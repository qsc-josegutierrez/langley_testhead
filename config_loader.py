"""
Configuration Loader for TestHead Control
Supports multiple configuration file formats: Excel (.xlsx) and JSON (.json)
"""
import os
import json
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class ConfigLoader:
    """Load and validate testhead configuration from Excel or JSON files"""
    
    def __init__(self, config_file_path):
        """
        Initialize config loader with a configuration file.
        
        Args:
            config_file_path (str): Path to Excel (.xlsx) or JSON (.json) config file
        """
        self.config_file_path = config_file_path
        self.file_format = self._detect_format()
        
        # Load configuration based on format
        if self.file_format == 'excel':
            self.dio_list_df = None
            self.dio_cmdlist_df = None
        elif self.file_format == 'json':
            self.config_data = None
    
    def _detect_format(self):
        """Detect configuration file format from extension"""
        _, ext = os.path.splitext(self.config_file_path)
        ext = ext.lower()
        
        if ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext == '.json':
            return 'json'
        else:
            raise ValueError(f"Unsupported config file format: {ext}. Supported: .xlsx, .xls, .json")
    
    def load_dio_list(self, sheet_name="DIO_List", header_row=0):
        """
        Load DIO device list configuration.
        
        For Excel: Read from specified sheet
        For JSON: Read from 'DIO_List' key
        
        Returns:
            DataFrame or dict: DIO list configuration
        """
        if self.file_format == 'excel':
            self.dio_list_df = self._read_excel_sheet(sheet_name, header_row)
            return self.dio_list_df
        elif self.file_format == 'json':
            with open(self.config_file_path, 'r') as f:
                data = json.load(f)
            self.config_data = data
            return data.get('DIO_List', [])
    
    def load_command_list(self, sheet_name="Model_Common", header_row=0):
        """
        Load command list configuration.
        
        For Excel: Read from specified sheet
        For JSON: Read from specified key
        
        Returns:
            DataFrame or dict: Command list configuration
        """
        if self.file_format == 'excel':
            self.dio_cmdlist_df = self._read_excel_sheet(sheet_name, header_row)
            return self.dio_cmdlist_df
        elif self.file_format == 'json':
            if self.config_data is None:
                with open(self.config_file_path, 'r') as f:
                    self.config_data = json.load(f)
            
            # Check if JSON has Model Sheets structure (all models in one list)
            if 'Model Sheets' in self.config_data and isinstance(self.config_data['Model Sheets'], list):
                # Filter items by Model_ field
                filtered_items = [
                    item for item in self.config_data['Model Sheets']
                    if item.get('Model_') == sheet_name
                ]
                return filtered_items
            else:
                # Original JSON format with separate keys for each model
                return self.config_data.get(sheet_name, [])
    
    def _read_excel_sheet(self, sheet_name, header_row=0):
        """Read Excel sheet to DataFrame"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for Excel support. Install with: pip install pandas openpyxl")
        
        if not os.path.exists(self.config_file_path):
            raise FileNotFoundError(f"Excel file not found at {self.config_file_path}")
        
        # Check if sheet exists
        xl = pd.ExcelFile(self.config_file_path)
        if sheet_name not in xl.sheet_names:
            raise ValueError(f"Sheet '{sheet_name}' not found in {self.config_file_path}")
        
        # Read Excel file to DataFrame (all data as string)
        df = pd.read_excel(self.config_file_path, sheet_name=sheet_name, 
                          dtype=str, header=header_row, keep_default_na=False)
        return df
    
    def get_device_info(self, dio_name):
        """
        Get MODEL and HEXADDRESS for a given DIO name.
        
        Args:
            dio_name (str): Name of the DIO device
            
        Returns:
            tuple: (model, hexaddress)
        """
        if self.file_format == 'excel':
            if self.dio_list_df is None:
                self.load_dio_list()
            
            if dio_name not in self.dio_list_df['NAME'].values:
                raise ValueError(f"DIO name '{dio_name}' not found in the DIO list.")
            
            model = self.dio_list_df.loc[self.dio_list_df['NAME'] == dio_name, 'MODEL'].values[0]
            address = self.dio_list_df.loc[self.dio_list_df['NAME'] == dio_name, 'HEXADDRESS'].values[0]
            return model, address
            
        elif self.file_format == 'json':
            if self.config_data is None:
                self.load_dio_list()
            
            dio_list = self.config_data.get('DIO_List', [])
            for device in dio_list:
                if device.get('NAME') == dio_name:
                    return device.get('MODEL'), device.get('HEXADDRESS')
            
            raise ValueError(f"DIO name '{dio_name}' not found in the DIO list.")
    
    def get_switch_command(self, pathname, sheet_name="Model_Common"):
        """
        Get SwitchDriverCommand for a given pathname.
        
        Args:
            pathname (str): Path name to lookup
            sheet_name (str): Sheet/key name for command list
            
        Returns:
            str: Switch driver command string
        """
        if self.file_format == 'excel':
            # Always reload to ensure we have the correct sheet
            self.dio_cmdlist_df = self._read_excel_sheet(sheet_name, header_row=0)
            
            # Check if PathName column exists
            if 'PathName' not in self.dio_cmdlist_df.columns:
                raise ValueError(f"'PathName' column not found in sheet '{sheet_name}'. Available columns: {list(self.dio_cmdlist_df.columns)}")
            
            if pathname not in self.dio_cmdlist_df['PathName'].values:
                raise ValueError(f"DIO pathname '{pathname}' not found in sheet '{sheet_name}'.")
            
            command = self.dio_cmdlist_df.loc[
                self.dio_cmdlist_df['PathName'] == pathname, 
                'SwitchDriverCommand'
            ].values[0]
            return command
            
        elif self.file_format == 'json':
            # Load the command list for the sheet if not already loaded
            cmd_list = self.load_command_list(sheet_name)
            
            # Search through the command list
            for cmd in cmd_list:
                if cmd.get('PathName') == pathname:
                    return cmd.get('SwitchDriverCommand')
            
            raise ValueError(f"DIO pathname '{pathname}' not found in the command list.")


def create_json_config_template(output_path="config/testhead_config_template.json"):
    """
    Create a template JSON configuration file for reference.
    
    Args:
        output_path (str): Path where template will be saved
    """
    template = {
        "DIO_List": [
            {
                "MODEL": "ACCESSIO_96",
                "NAME": "TestHead",
                "HEXADDRESS": "0x01"
            },
            {
                "MODEL": "ACCESSIO_48",
                "NAME": "TestHead2",
                "HEXADDRESS": "0x02"
            }
        ],
        "Model_Common": [
            {
                "PathName": "Initialize Testhead, Clear ALL",
                "SwitchDriverCommand": "0"
            },
            {
                "PathName": "Configure Load Relays to 8ohms",
                "SwitchDriverCommand": "0B4,1;0B5,1;0B6,1;0B7,1"
            }
        ],
        "Model_Specific": [
            {
                "PathName": "Custom Path 1",
                "SwitchDriverCommand": "0A1,1;0A2,1"
            }
        ]
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"JSON template created at: {output_path}")


if __name__ == "__main__":
    # Example usage
    create_json_config_template()
    print("JSON configuration template created successfully!")
