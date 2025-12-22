================================================================================
                    TESTHEAD CONTROL - DEPLOYMENT GUIDE
================================================================================

OVERVIEW
--------
This application controls ACCESIO Digital I/O (DIO) boards for testhead 
switching operations. It reads configuration from Excel or JSON files and
sends commands to the hardware via the AIOUSB.dll driver.

================================================================================
                         SYSTEM REQUIREMENTS
================================================================================

Hardware:
  - ACCESIO DIO board (Model 16, 48, or 96 line)
  - Board must be programmed with unique EEPROM ID
  - USB connection to PC

Software:
  - Windows 7 or later (32-bit or 64-bit)
  - AIOUSB.dll driver (see installation below)
  - Configuration files (Excel .xlsx or JSON)

================================================================================
                            INSTALLATION
================================================================================

OPTION 1: Using Pre-Built Executable (Recommended)
---------------------------------------------------
1. Copy the entire testhead_control folder to your PC:
   - testhead_control.exe
   - config/ folder (with .xlsx files)
   - (optional) drivers/ folder with AIOUSB.dll

2. Install AIOUSB.dll driver:
   a. Copy AIOUSB.dll to C:\Windows\System32\
      OR
   b. Place AIOUSB.dll in the drivers\ subfolder next to the .exe

3. Verify configuration files are in config/ folder

4. Done! Run testhead_control.exe from command line


OPTION 2: Running from Python Source
-------------------------------------
1. Install Python 3.8 or later from python.org

2. Install dependencies:
   > pip install -r requirements.txt

3. Install AIOUSB.dll (same as above)

4. Run the script:
   > python testhead_control.py [arguments]

================================================================================
                              USAGE
================================================================================

Command Line Syntax:
--------------------
testhead_control.exe <config_file> <sheet_name> <dio_name> <path_component1> [path_component2] [...]

Parameters:
  config_file      : Excel (.xlsx) or JSON config file name or full path
                     If just filename, searches in config/ folder
  sheet_name       : Sheet/section name (e.g., "Model_Common")
  dio_name         : DIO device name from DIO_List (e.g., "TestHead")
  path_components  : One or more pathname parts, will be joined with ", "

Examples:
---------
1. Using default config file (in config/ folder):
   > testhead_control.exe "Amplifier_Testhead Switch Path Configuration.xlsx" "Model_Common" "TestHead" "Initialize Testhead" "Clear ALL"

2. Using full path to config file:
   > testhead_control.exe "C:\Configs\MyTesthead.xlsx" "Model_Common" "TestHead" "Configure Load Relays to 8ohms"

3. Using JSON config:
   > testhead_control.exe "testhead_config.json" "Model_Common" "TestHead" "CMRR Test Mode ON"

4. Multiple pathname components:
   > testhead_control.exe "config.xlsx" "Model_Common" "TestHead" "Reset" "Balanced Generator" "MIC"
   (This joins to: "Reset, Balanced Generator, MIC")

================================================================================
                        CONFIGURATION FILES
================================================================================

EXCEL FORMAT (.xlsx)
--------------------
Required Sheets:

1. DIO_List Sheet:
   Columns: MODEL, NAME, HEXADDRESS
   Example:
     MODEL         | NAME      | HEXADDRESS
     ACCESSIO_96   | TestHead  | 0x01
     ACCESSIO_48   | TestHead2 | 0x02

2. Command Sheet (e.g., Model_Common):
   Columns: PathName, SwitchDriverCommand
   Example:
     PathName                              | SwitchDriverCommand
     Initialize Testhead, Clear ALL        | 0
     Configure Load Relays to 8ohms        | 0B4,1;0B5,1;0B6,1;0B7,1
     CMRR Test Mode ON                     | 0A1,1;0A2,1

JSON FORMAT (.json)
-------------------
Structure:
{
  "DIO_List": [
    {
      "MODEL": "ACCESSIO_96",
      "NAME": "TestHead",
      "HEXADDRESS": "0x01"
    }
  ],
  "Model_Common": [
    {
      "PathName": "Initialize Testhead, Clear ALL",
      "SwitchDriverCommand": "0"
    }
  ]
}

See config/testhead_config_template.json for full example.

================================================================================
                          SWITCH COMMANDS
================================================================================

Command Format:
---------------
Commands are semicolon-separated: "cmd1;cmd2;cmd3"

Command Types:
  0              : Reset all lines to LOW (initialize)
  GroupPortBit,Value : Set specific line
    - Group: 0-3 (connector number)
    - Port: A, B, C
    - Bit: 0-7
    - Value: 0 (LOW) or 1 (HIGH)

Examples:
  "0"                           : Reset all lines
  "0B4,1"                       : Set line 0B4 to HIGH
  "0B4,1;0B5,1;0B6,1;0B7,1"    : Set multiple lines HIGH
  "0;0A1,1;0A2,1"               : Reset, then set 0A1 and 0A2 HIGH

================================================================================
                          ADDING NEW CONFIGS
================================================================================

To Add New Testhead Configuration:
-----------------------------------
1. Create new Excel file or add to existing:
   - Add DIO_List entry with unique NAME and HEXADDRESS
   - Create new sheet or use existing (e.g., "Model_XYZ")
   - Add PathName and SwitchDriverCommand entries

2. Place file in config/ folder

3. Run with new config:
   > testhead_control.exe "MyNewConfig.xlsx" "Model_XYZ" "NewTestHead" "Command Name"

To Add JSON Config:
-------------------
1. Use config_loader.py to generate template:
   > python config_loader.py

2. Edit testhead_config_template.json with your data

3. Place in config/ folder and use as shown above

================================================================================
                         TROUBLESHOOTING
================================================================================

Error: "AIOUSB.dll not found"
  Solution: Copy AIOUSB.dll to C:\Windows\System32\ or drivers\ folder

Error: "Device with board ID XX not found"
  Solution: 
  - Check USB connection
  - Verify EEPROM ID matches HEXADDRESS in config
  - Try different USB port
  - Check Windows Device Manager for ACCESIO device

Error: "Excel file not found"
  Solution:
  - Use full path to Excel file
  - Verify file is in config/ folder
  - Check filename spelling and extension

Error: "Column 'XXX' not found"
  Solution:
  - Verify Excel sheet has correct column names (case-sensitive)
  - Check for extra spaces in column headers
  - Ensure using correct sheet name

Error: "DIO pathname 'XXX' not found"
  Solution:
  - Check exact pathname spelling in Excel/JSON
  - Pathname components are joined with ", " (comma-space)
  - Case-sensitive matching

================================================================================
                          BUILDING FROM SOURCE
================================================================================

To Create Executable:
---------------------
1. Install Python and dependencies:
   > pip install -r requirements.txt

2. Run build script:
   > build_exe.bat

3. Executable will be in dist\ folder

4. Deploy entire dist\ folder to target PC

================================================================================
                          SUPPORT & CONTACT
================================================================================

For issues or questions:
  - Check this README first
  - Review configuration file format
  - Verify hardware connections
  - Check Windows Event Viewer for driver issues

Version: 1.0
Date: December 19, 2025
