# TestHead Control System - Complete Guide

## 📋 Table of Contents
1. [What Is This System?](#what-is-this-system)
2. [System Architecture](#system-architecture)
3. [Configuration Files](#configuration-files)
4. [How Commands Work](#how-commands-work)
5. [Usage from Audio Precision](#usage-from-audio-precision)
6. [Usage from LabVIEW](#usage-from-labview)
7. [Command Reference](#command-reference)
8. [Troubleshooting](#troubleshooting)
9. [Change Log](#change-log)

---

## What Is This System?

### Business Purpose
This system controls **ACCESIO USB DIO (Digital Input/Output) hardware** that operates **relays in a TestHead fixture**. The TestHead is used to route audio signals through different paths for testing QSC products.

### Real-World Example
Think of it like a **railroad switchyard**:
- The TestHead has multiple audio paths (like railroad tracks)
- Relays act as switches to route signals
- You tell the system which path you want (e.g., "Generator 1", "Analyzer 2")
- The system flips the correct relays to create that path

### Key Hardware
- **ACCESIO USB DIO Boards**: Models iO-96, iO-48, iO-16
- **Relays**: Connected to DIO pins, control audio signal routing
- **TestHead Fixture**: Physical box with connectors and relays

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR APPLICATION                         │
│        (Audio Precision / LabVIEW / Command Line)          │
└──────────────────────┬──────────────────────────────────────┘
                       │ Calls Python script/executable
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              testhead_control.py (THIS CODE)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Reads Config File (Excel or JSON)               │  │
│  │  2. Looks up command: "Generator 1" → "0B2,1;0B3,1" │  │
│  │  3. Finds hardware: "TestHead" → Board ID 0x01      │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │ Sends hardware commands
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              AIOUSB.dll (ACCESIO Driver)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ USB Communication
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           ACCESIO USB DIO Board (Physical Hardware)         │
│               Controls Relays in TestHead                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration Files

### Structure (Excel or JSON)

Your config files have **2 main sections**:

#### 1. **DIO_List** - Hardware Inventory
Defines which physical DIO boards you have:

| NAME      | MODEL        | HEXADDRESS |
|-----------|--------------|------------|
| TestHead  | ACCESSIO_48  | 0x01       |
| TestHead2 | ACCESSIO_96  | 0x02       |

- **NAME**: Friendly name you'll use in commands
- **MODEL**: Board type (iO-96, iO-48, iO-16)
- **HEXADDRESS**: Unique ID programmed into board's EEPROM

#### 2. **Model Sheets** - Command Lookup Tables
Maps friendly command names to actual relay operations:

| PATHNAME         | SwitchDriverCommand    |
|------------------|------------------------|
| Reset            | 0                      |
| Generator 1      | 0B2,1;0B3,1            |
| Analyzer 2       | 0C6,1                  |
| Balanced Analyzer| 0A2,0                  |

- **PATHNAME**: Human-readable command name
- **SwitchDriverCommand**: Actual relay control codes

### Command Syntax Explained
```
0B2,1;0B3,1;0B4,0
│││ │ │││ │ │││ │
│││ │ │││ │ │││ └─ Value: 0=OFF, 1=ON
│││ │ │││ │ ││└─── Bit number
│││ │ │││ │ │└──── Port letter (A, B, C, etc.)
│││ │ │││ │ └───── Group/Port identifier
│││ │ │││ └─────── Separator (comma)
│││ │ ││└────────── Separator (semicolon) for multiple commands
│││ │ ││
│││ │ │└─────────── Second relay command
│││ │ └──────────── First relay command
│││ └────────────── Special: "0" = Reset ALL relays to OFF
```

**Examples:**
- `0` - Reset all relays to OFF
- `0B2,1` - Turn ON relay at Port B, Bit 2
- `0A0,0` - Turn OFF relay at Port A, Bit 0  
- `0B2,1;0B3,1;0B4,1` - Turn ON 3 relays (creates a signal path)

---

## How Commands Work

### Flow Diagram

```
1. YOU CALL THE SCRIPT
   ↓
   python testhead_control.py "config.xlsx" "Model_T002" "TestHead" "Generator 1"
   
2. SCRIPT LOADS CONFIG FILE
   ↓
   Reads: "Langley_Testhead Switch Path Configuration.xlsx"
   
3. HARDWARE LOOKUP
   ↓
   Finds: NAME="TestHead" → MODEL=ACCESSIO_48, HEXADDRESS=0x01
   
4. COMMAND LOOKUP  
   ↓
   Finds: "Generator 1" in sheet "Model_T002" → "0B2,1;0B3,1"
   
5. HARDWARE INIT
   ↓
   Connects to ACCESIO board via USB (Board ID: 0x01)
   
6. RELAY CONTROL
   ↓
   Executes: Turn ON Port B Bit 2, Turn ON Port B Bit 3
   
7. SUCCESS
   ↓
   Returns: command_success = True
```

### Two Execution Modes

#### Mode 1: **Config Lookup** (Normal Use)
```python
testhead = Testhead_Control()
testhead.run(
    config_file_name="Langley_Testhead Switch Path Configuration.xlsx",
    dio_name="TestHead",
    command_name="Generator 1",  # Looks this up in config
    sheet_name="Model_T002"
)
```
✅ **Use Case**: Audio Precision test sequences, LabVIEW automation
✅ **Benefit**: Friendly names, easy to change routing without code changes

#### Mode 2: **Direct Command** (Manual Control)
```python
testhead = Testhead_Control()
testhead.run_direct_command(
    config_file_name="config.xlsx",
    dio_name="TestHead",
    switch_command="0B2,1;0B3,1"  # Raw relay command
)
```
✅ **Use Case**: Debugging, manual testing, reset operations
✅ **Benefit**: No config file lookup needed

---

## Usage from Audio Precision

### Method 1: Python Script Call

Audio Precision can execute external programs using **Sequence Steps**.

#### Audio Precision Sequence Setup:
```
1. Add "External Program" step
2. Program Path: 
   C:\Python314\python.exe
   
3. Arguments:
   "C:\TestHeadControl\testhead_control.py" 
   "C:\TestHeadControl\config\Langley_Testhead Switch Path Configuration.xlsx" 
   "Model_T002" 
   "TestHead" 
   "Generator 1"
   
4. Wait for completion: YES
5. Check return code: 0 = success
```

#### Example Sequence:
```
Step 1: Reset TestHead
  Command: python testhead_control.py "config.xlsx" "Model_Common" "TestHead" "Reset"

Step 2: Connect Generator 1
  Command: python testhead_control.py "config.xlsx" "Model_T002" "TestHead" "Generator 1"

Step 3: Run Audio Test
  [Audio Precision test here]

Step 4: Connect Analyzer 2
  Command: python testhead_control.py "config.xlsx" "Model_T002" "TestHead" "Analyzer 2"

Step 5: Measure Response
  [Audio Precision measurement]
```

### Method 2: Python API Integration

For direct Python API access within Audio Precision (if supported):

```python
import sys
sys.path.append("C:\\TestHeadControl")
from testhead_control import Testhead_Control

# Initialize and configure
testhead = Testhead_Control()
testhead.run(
    config_file_name="config.xlsx",
    dio_name="TestHead", 
    command_name="Generator 1",
    sheet_name="Model_T002"
)
```

**Advantages:**
- Fastest execution
- Direct integration
- No external process overhead

**Disadvantages:**
- Requires Python environment in Audio Precision
- More complex setup

### Method 3: Compiled CLI Executable (Recommended)

Use the **testhead_control.exe** for full automation:

```
Audio Precision External Program:
  Program: C:\TestHeadControl\testhead_control.exe
  Arguments: "config.xlsx" "Model_T002" "TestHead" "Generator 1"
```

**Advantages:**
- No Python installation needed on test PC
- Faster execution
- Single file deployment
- Relays persist after program exits
- Full automation support

**Disadvantages:**
- Need to rebuild executable when code changes

### Method 4: Python COM/ActiveX (Advanced)

If Audio Precision supports Python scripting:

```python
import sys
sys.path.append(r"C:\TestHeadControl")
from testhead_control import Testhead_Control

# In your Audio Precision script
testhead = Testhead_Control()
testhead.run(
    config_file_name=r"C:\TestHeadControl\config\Langley_Testhead.xlsx",
    dio_name="TestHead",
    command_name="Generator 1",
    sheet_name="Model_T002"
)

if testhead.command_success:
    print("TestHead configured successfully")
else:
    print("ERROR: TestHead configuration failed")
```

---

## Usage from LabVIEW

### Method 1: System Exec VI (Recommended)

LabVIEW can call external executables using **System Exec.vi**:

```
┌─────────────────────────────────────────┐
│  LabVIEW Block Diagram                  │
├─────────────────────────────────────────┤
│                                         │
│  [System Exec.vi]                       │
│    ├─ command line: String Input       │
│    ├─ wait: TRUE (Boolean)             │
│    ├─ standard output: String Output   │
│    └─ return code: Numeric Output      │
│                                         │
└─────────────────────────────────────────┘
```

#### LabVIEW VI Setup:

**1. Create Command String:**
```
Command Line = 
"C:\Python314\python.exe " + 
"C:\TestHeadControl\testhead_control.py " +
Chr(34) + Config_File + Chr(34) + " " +  # Chr(34) = quote character
Chr(34) + Sheet_Name + Chr(34) + " " +
Chr(34) + DIO_Name + Chr(34) + " " +
Chr(34) + Command_Name + Chr(34)
```

**Example result:**
```
C:\Python314\python.exe "C:\TestHeadControl\testhead_control.py" "config.xlsx" "Model_T002" "TestHead" "Generator 1"
```

**2. Execute and Check:**
```
System Exec.vi → Return Code
│
├─ 0 = Success
└─ Non-zero = Error

Parse Standard Output for debug info
```

### Method 2: Python Node (LabVIEW 2018+)

If you have LabVIEW Python integration:

```
[Python Node]
  Code:
    import sys
    sys.path.append(r"C:\TestHeadControl")
    from testhead_control import Testhead_Control
    
    testhead = Testhead_Control()
    testhead.run(
        config_file_name=config_file,
        dio_name=dio_name,
        command_name=command_name,
        sheet_name=sheet_name
    )
    
    return testhead.command_success
```

### Method 3: LabVIEW + Executable

**Simplest for deployment:**

```
[System Exec.vi]
  command line: 
    "C:\TestHeadControl\testhead_control.exe " +
    Config + " " + Sheet + " " + DIO + " " + Command
  
  wait: TRUE
  return code → [Case Structure]
    ├─ 0: Continue test
    └─ else: Show error, stop test
```

### LabVIEW Example Test Sequence

```
┌──────────────────────────────────────────────────────┐
│ TestHead LabVIEW Sequence                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. [System Exec] Reset TestHead                    │
│     ↓                                                │
│  2. [Delay 100ms] Wait for relays                   │
│     ↓                                                │
│  3. [System Exec] Connect Generator 1               │
│     ↓                                                │
│  4. [Audio Output VI] Start signal generation       │
│     ↓                                                │
│  5. [Delay 500ms] Signal settling time              │
│     ↓                                                │
│  6. [System Exec] Connect Analyzer 2                │
│     ↓                                                │
│  7. [Audio Input VI] Measure response               │
│     ↓                                                │
│  8. [System Exec] Reset TestHead (cleanup)          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## Command Reference

### GUI Application

```bash
testhead_gui.exe
```

**Features:**
- Visual configuration file selection
- Browse and execute commands
- Real-time command execution
- Export to JSON format
- Automatically resets all relays when GUI closes (safety feature)

### Command-Line Syntax

```bash
python testhead_control.py <config_file> <sheet_name> <dio_name> <command_name>

# Or compiled executable:
testhead_control.exe <config_file> <sheet_name> <dio_name> <command_name>
```

### Required Parameters

| Parameter      | Description                          | Example                                      |
|----------------|--------------------------------------|----------------------------------------------|
| config_file    | Path to Excel or JSON config file    | "Langley_Testhead Configuration.xlsx"       |
| sheet_name     | Lookup table name in config file     | "Model_T002" or "Model_Common"              |
| dio_name       | Hardware device name from DIO_List   | "TestHead"                                   |
| command_name   | Command to execute from lookup table | "Generator 1" or "Reset"                     |

### Multiple Commands (Sequential Execution)

```bash
# Use | separator for multiple commands
python testhead_control.py "config.xlsx" "Model_T002" "TestHead" "Reset|Generator 1|Analyzer 2"

# This executes:
#   1. Reset
#   2. Generator 1  
#   3. Analyzer 2
# Stops on first failure
```

### Python API Usage

```python
from testhead_control import Testhead_Control

# Create instance (does NOT execute anything)
testhead = Testhead_Control()

# Execute command with config lookup
testhead.run(
    config_file_name="Langley_Testhead.xlsx",
    dio_name="TestHead",
    command_name="Generator 1",
    sheet_name="Model_T002"
)

# Check success
if testhead.command_success:
    print("Command executed successfully")
else:
    print("Command failed")

# Execute direct command (no config lookup)
testhead.run_direct_command(
    config_file_name="Langley_Testhead.xlsx",
    dio_name="TestHead",
    switch_command="0B2,1;0B3,1"
)
```

### Return Codes

| Code | Meaning           | Action                                    |
|------|-------------------|-------------------------------------------|
| 0    | Success           | Command executed, relays switched         |
| 1    | Error             | Check error message, verify config/hardware|

---

## Troubleshooting

### Common Errors

#### "Device with board ID 0xXX not found"
**Cause**: Hardware not connected or wrong board ID
**Solution**:
1. Check USB connection
2. Verify board ID in EEPROM matches config file HEXADDRESS
3. Try: `python -c "from accesio import accesio_dio; dio = accesio_dio.AccesDIO('ACCESSIO_48'); print(dio.list_devices())"`

#### "PathName 'Generator 1' not found"
**Cause**: Command name doesn't exist in config file
**Solution**:
1. Open config file
2. Check sheet name is correct
3. Verify exact spelling (case-sensitive)
4. Look at PATHNAME column for available commands

#### "AIOUSB.dll not found"
**Cause**: ACCESIO driver not installed
**Solution**:
1. Install AIOUSB driver from ACCESIO
2. Copy AIOUSB.dll to C:\Windows\System32
3. Or place in same folder as executable

#### "Config file not found"
**Cause**: Wrong path or file missing
**Solution**:
1. Use absolute path: `C:\TestHeadControl\config\file.xlsx`
2. Or place config in `config/` subfolder next to executable

### Debugging Tips

**1. Test from command line first:**
```bash
python testhead_control.py "config.xlsx" "Model_Common" "TestHead" "Reset"
```

**2. Check hardware connection:**
```python
from accesio import accesio_dio
dio = accesio_dio.AccesDIO('ACCESSIO_48')
devices = dio.list_devices()
print(f"Found {len(devices)} devices")
```

**3. Verify config file:**
```python
from config_loader import ConfigLoader
loader = ConfigLoader("config.xlsx")
dio_list = loader.load_dio_list()
print(dio_list)
```

**4. Test single relay:**
```bash
python testhead_control.py "config.xlsx" "TestHead" "0B2,1"
```

---

## Quick Start Examples

### Audio Precision - Simple Test

```
1. Reset TestHead:
   python testhead_control.py "config.xlsx" "Model_Common" "TestHead" "Reset"

2. Configure Generator 1:
   python testhead_control.py "config.xlsx" "Model_T002" "TestHead" "Generator 1"

3. [Run your Audio Precision test]

4. Cleanup:
   python testhead_control.py "config.xlsx" "Model_Common" "TestHead" "Reset"
```

### LabVIEW - VI Example

```
String: Config_Path = "C:\TestHeadControl\config\Langley_Testhead.xlsx"
String: Sheet = "Model_T002"
String: Device = "TestHead"
String: Command = "Generator 1"

[Build Command String]
  Command_Line = "python testhead_control.py" + 
                 " " + Config_Path + 
                 " " + Sheet + 
                 " " + Device + 
                 " " + Command

[System Exec.vi]
  Input: Command_Line
  Output: Return_Code, Standard_Output
  
[Case Structure on Return_Code]
  Case 0: Continue
  Default: Display Error
```

---

## Support & Maintenance

### Adding New Commands

1. Open config file (Excel or JSON)
2. Add row to appropriate Model sheet:
   - PATHNAME: Friendly name
   - SwitchDriverCommand: Relay codes
3. Save file
4. Test: `python testhead_control.py "config.xlsx" "Sheet" "Device" "New Command"`

### Config File Locations

The system searches in this order:
1. Absolute path (if provided)
2. Next to executable
3. `config/` subfolder next to executable
4. `config/` subfolder in current directory

### Log Output

All operations print to console:
- Config file loaded
- Hardware found
- Commands executed
- Success/failure status

Redirect to log file:
```bash
python testhead_control.py args... > testhead.log 2>&1
```

---

**Need Help?** 
- Check error messages carefully
- Test commands from command line first
- Verify config file with GUI application
- Check hardware connections and board IDs

---

## Change Log

### Version 2.0 - December 30, 2025

#### Major Refactoring
- **Class Structure Redesign**: Separated `__init__()` from execution logic
  - `__init__()` now only initializes state (no parameters needed)
  - New `run()` method handles all execution logic with mandatory parameters
  - Rationale: Enables object reuse and multiple command execution with same instance

#### Parameter Changes
- **Renamed Parameters** (for clarity):
  - `testhead_lookup_xlsx` → `config_file_name` (now supports both .xlsx and .json)
  - `dio_pathname` → `command_name` (more accurately describes the lookup value)
- **Mandatory Parameters**: All parameters now required (no defaults)
  - `config_file_name`: Path to configuration file
  - `dio_name`: DIO device identifier from DIO_List
  - `command_name`: Command to execute from Model sheets
  - `sheet_name`: Which Model sheet to search
  - Rationale: Explicit > Implicit; prevents accidental use of wrong config/device

#### New Features
- **Dual Configuration Format Support**: 
  - Existing Excel (.xlsx) format
  - New JSON format with identical structure
  - Unified `ConfigLoader` class handles both automatically
  
- **Direct Command Execution**:
  - New `run_direct_command()` method bypasses configuration lookup
  - Accepts raw relay commands (e.g., "0B2,1;0B3,1") 
  - Powers GUI "Execute Command" and "Reset All" buttons
  - Rationale: Enables manual testing and troubleshooting without config file entries

- **Multiple Command Execution**:
  - CLI now supports pipe-separated commands: `"Reset|Generator 1|Analyzer 2"`
  - Executes commands sequentially on same hardware instance
  - Rationale: Reduces overhead for complex test sequences

#### Bug Fixes
- **Case-Insensitive Column Matching**:
  - Fixed "PathName column not found" errors
  - `ConfigLoader` now matches column names case-insensitively
  - Handles variations: "PathName", "PATHNAME", "pathname", etc.
  - Rationale: Excel files from different sources had inconsistent column naming

- **GUI Button Execution Errors**:
  - Fixed "Execute Command" button attempting config lookup for manual commands
  - Fixed "Reset All" button attempting config lookup for reset command
  - Solution: Added `run_direct_command()` for these operations
  - Rationale: Manual commands shouldn't require config file entries

#### Integration Enhancements
- **PyInstaller Executable Compilation**:
  - Created `testhead_gui.spec` for reproducible builds
  - Automatic bundling of `config/` directory with executables
  - Hidden imports properly configured for pandas/openpyxl
  - Build command: `pyinstaller testhead_gui.spec --clean`

- **Audio Precision Integration Documentation**:
  - Three integration methods documented: CLI, GUI with flag, Python API
  - Workflow examples for automated test sequences
  - Relay state management patterns
  - Error handling recommendations

- **LabVIEW Integration Documentation**:
  - System Exec VI patterns for CLI execution
  - Python Node integration for direct API access
  - Executable invocation with proper path handling
  - Return code interpretation

#### Validation & Input Handling
- **Robust Error Checking**:
  - ValueError exceptions for missing parameters
  - Config file existence validation
  - Device name validation against DIO_List
  - Command name validation against Model sheets
  - Clear error messages for troubleshooting

#### Documentation
- **Comprehensive User Guide**: Created `TESTHEAD_CONTROL_GUIDE.md`
  - System architecture explanation with visual diagrams
  - Business purpose and real-world examples
  - Configuration file structure documentation
  - Complete command reference
  - Audio Precision integration patterns
  - LabVIEW integration patterns
  - Troubleshooting guide
  - Quick start examples

### Technical Debt Addressed
- Removed implicit parameter defaults (explicit > implicit)
- Eliminated parameter name ambiguity
- Centralized configuration loading logic
- Unified Excel/JSON handling
- Separated concerns: initialization vs. execution
- Added comprehensive input validation

### Breaking Changes
⚠️ **Version 1.x code will not work with Version 2.0**
- All function signatures changed
- Parameters now mandatory
- Different parameter names
- Must update calling code in:
  - Audio Precision sequences
  - LabVIEW VIs
  - Custom scripts

### Migration Guide
**Old (v1.x):**
```python
testhead = Testhead_Control()
testhead.run()  # Used defaults
```

**New (v2.0):**
```python
testhead = Testhead_Control()
testhead.run(
    config_file_name="config.xlsx",
    dio_name="TestHead",
    command_name="Generator 1",
    sheet_name="Model_T002"
)
```

### Deployment Notes
- Recompile executables after code changes
- Validate Audio Precision integration
- Update AP test sequences with new parameter names
- Update LabVIEW VIs with new command structure
