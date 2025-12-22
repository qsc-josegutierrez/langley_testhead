"""
TestHead Control GUI Application - Simplified Launcher
Provides visual interface for managing and executing testhead configurations
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json
from pathlib import Path

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class TestHeadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TestHead Control - Set Parameters")
        self.root.geometry("1400x800")
        
        # State variables
        self.config_loader = None
        self.current_platform = None
        self.current_lookup_table = None
        self.config_files = []
        self.lookup_tables = []
        
        # Get app directory for finding config files
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.config_dir = os.path.join(self.app_dir, "config")
        
        # Create GUI
        self.create_widgets()
        
        # Load available config files
        self.load_config_files()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(2, weight=1)
        
        # ===== LEFT PANEL: Configuration Controls =====
        left_panel = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        row = 0
        
        # Platform selection
        ttk.Label(left_panel, text="Platform:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.platform_var = tk.StringVar()
        self.platform_combo = ttk.Combobox(left_panel, textvariable=self.platform_var, width=40, state='readonly')
        self.platform_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.platform_combo.bind('<<ComboboxSelected>>', self.on_platform_selected)
        row += 1
        
        # Lookup Tables selection
        ttk.Label(left_panel, text="Lookup Tables:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.lookup_table_var = tk.StringVar()
        self.lookup_table_combo = ttk.Combobox(left_panel, textvariable=self.lookup_table_var, width=40, state='readonly')
        self.lookup_table_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.lookup_table_combo.bind('<<ComboboxSelected>>', self.on_lookup_table_selected)
        row += 1
        
        # Lookup Table Filepath
        ttk.Label(left_panel, text="Lookup Table Filepath:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.filepath_var = tk.StringVar()
        filepath_entry = ttk.Entry(left_panel, textvariable=self.filepath_var, width=40, state='readonly')
        filepath_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # Separator
        ttk.Separator(left_panel, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # DIO Name
        ttk.Label(left_panel, text="DIO Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.dio_name_var = tk.StringVar()
        self.dio_name_combo = ttk.Combobox(left_panel, textvariable=self.dio_name_var, width=40, state='readonly')
        self.dio_name_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.dio_name_combo.bind('<<ComboboxSelected>>', self.on_dio_name_selected)
        row += 1
        
        # DIO Model
        ttk.Label(left_panel, text="DIO Model:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.dio_model_var = tk.StringVar()
        dio_model_combo = ttk.Combobox(left_panel, textvariable=self.dio_model_var, width=40, state='readonly')
        dio_model_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # DIO Hex Address
        ttk.Label(left_panel, text="DIO Hex Address:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.dio_hex_var = tk.StringVar()
        dio_hex_entry = ttk.Entry(left_panel, textvariable=self.dio_hex_var, width=40, state='readonly')
        dio_hex_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # Separator
        ttk.Separator(left_panel, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # DIO Command
        ttk.Label(left_panel, text="DIO Command:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.dio_command_var = tk.StringVar()
        dio_command_entry = ttk.Entry(left_panel, textvariable=self.dio_command_var, width=40)
        dio_command_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # Platform File Type
        ttk.Label(left_panel, text="Platform File Type:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.file_type_var = tk.StringVar(value="ALL")
        file_type_combo = ttk.Combobox(left_panel, textvariable=self.file_type_var, 
                                       values=["ALL", "JSON", "EXCEL"], width=40, state='readonly')
        file_type_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        file_type_combo.bind('<<ComboboxSelected>>', self.on_file_type_changed)
        row += 1
        
        # Settling Time
        settling_frame = ttk.Frame(left_panel)
        settling_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(settling_frame, text="Settling Time between Commands (ms):").pack(side=tk.LEFT, padx=5)
        self.settling_time_var = tk.IntVar(value=10)
        settling_spinbox = ttk.Spinbox(settling_frame, from_=0, to=10000, textvariable=self.settling_time_var, width=10)
        settling_spinbox.pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Separator
        ttk.Separator(left_panel, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(left_panel)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="To JSON", command=self.export_to_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Execute Command", command=self.execute_manual_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset All", command=self.reset_all_lines).pack(side=tk.LEFT, padx=5)
        
        # ===== RIGHT PANEL: Command Table =====
        right_panel = ttk.LabelFrame(main_frame, text="Command List - Double click to execute command", padding="10")
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        # Create Treeview with scrollbars
        tree_frame = ttk.Frame(right_panel)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Treeview
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=vsb.set, xscrollcommand=hsb.set, 
                                 selectmode='browse', height=20)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Bind double-click and selection events
        self.tree.bind('<Double-Button-1>', self.on_tree_double_click)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_selection_changed)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(fill=tk.X, padx=5)
    
    def load_config_files(self):
        """Load all config files from config directory"""
        try:
            if not os.path.exists(self.config_dir):
                messagebox.showerror("Error", f"Config directory not found: {self.config_dir}")
                return
            
            # Find all .json and .xlsx files
            files = []
            for file in os.listdir(self.config_dir):
                if file.endswith(('.json', '.xlsx', '.xls')):
                    files.append(file)
            
            self.config_files = sorted(files)
            self.apply_file_type_filter()
            
            self.status_var.set(f"Loaded {len(self.config_files)} configuration file(s)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config files: {str(e)}")
            self.status_var.set("Error loading config files")
    
    def apply_file_type_filter(self):
        """Filter config files based on Platform File Type selection"""
        file_type = self.file_type_var.get()
        
        if file_type == "ALL":
            filtered_files = self.config_files
        elif file_type == "JSON":
            filtered_files = [f for f in self.config_files if f.endswith('.json')]
        elif file_type == "EXCEL":
            filtered_files = [f for f in self.config_files if f.endswith(('.xlsx', '.xls'))]
        else:
            filtered_files = self.config_files
        
        self.platform_combo['values'] = filtered_files
        
        if filtered_files and self.platform_var.get() not in filtered_files:
            self.platform_combo.current(0)
            self.on_platform_selected(None)
        elif not filtered_files:
            self.platform_var.set('')
            self.lookup_table_combo['values'] = []
            self.dio_name_combo['values'] = []
    
    def on_file_type_changed(self, event):
        """Handle file type filter change"""
        self.apply_file_type_filter()
        self.status_var.set(f"Filtered by: {self.file_type_var.get()}")
    
    def on_platform_selected(self, event):
        """Handle platform selection change"""
        try:
            platform_file = self.platform_var.get()
            if not platform_file:
                return
            
            config_path = os.path.join(self.config_dir, platform_file)
            self.filepath_var.set(config_path)
            
            # Load configuration using config_loader
            from config_loader import ConfigLoader
            self.config_loader = ConfigLoader(config_path)
            
            # Determine file type and update display
            if platform_file.endswith('.json'):
                self.file_type_var.set("JSON")
            else:
                self.file_type_var.set("EXCEL")
            
            # Load lookup tables (sheets or JSON keys)
            # Filter out system sheets: Rev History, DIO_List, Reference
            system_sheets = ['Rev History', 'DIO_List']
            
            if self.config_loader.file_format == 'excel':
                import pandas as pd
                xl = pd.ExcelFile(config_path)
                # Get all sheets except system sheets and those starting with "Reference"
                self.lookup_tables = [
                    sheet for sheet in xl.sheet_names 
                    if sheet not in system_sheets and not sheet.startswith('Reference')
                ]
            else:
                # JSON format
                with open(config_path, 'r') as f:
                    data = json.load(f)
                self.lookup_tables = [
                    key for key in data.keys() 
                    if key not in system_sheets and not key.startswith('Reference')
                ]
            
            self.lookup_table_combo['values'] = self.lookup_tables
            if self.lookup_tables:
                self.lookup_table_combo.current(0)
                self.on_lookup_table_selected(None)
            
            # Load DIO names
            self.load_dio_names()
            
            self.status_var.set(f"Loaded platform: {platform_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load platform: {str(e)}")
            self.status_var.set("Error loading platform")
    
    def on_lookup_table_selected(self, event):
        """Handle lookup table selection change"""
        try:
            lookup_table = self.lookup_table_var.get()
            if not lookup_table or not self.config_loader:
                return
            
            self.current_lookup_table = lookup_table
            
            # Load command list for this lookup table
            self.load_command_table(lookup_table)
            
            self.status_var.set(f"Loaded lookup table: {lookup_table}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load lookup table: {str(e)}")
            self.status_var.set("Error loading lookup table")
    
    def load_dio_names(self):
        """Load available DIO device names"""
        try:
            if not self.config_loader:
                return
            
            dio_list = self.config_loader.load_dio_list()
            
            if self.config_loader.file_format == 'excel':
                dio_names = dio_list['NAME'].tolist()
            else:
                dio_names = [device['NAME'] for device in dio_list]
            
            self.dio_name_combo['values'] = dio_names
            if dio_names:
                self.dio_name_combo.current(0)
                self.on_dio_name_selected(None)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load DIO names: {str(e)}")
    
    def on_dio_name_selected(self, event):
        """Handle DIO name selection change"""
        try:
            dio_name = self.dio_name_var.get()
            if not dio_name or not self.config_loader:
                return
            
            # Get device info
            model, hex_address = self.config_loader.get_device_info(dio_name)
            
            # Map model names to display names
            model_map = {
                "ACCESSIO_96": "Acces iO-96",
                "ACCESSIO_48": "Acces iO-48",
                "ACCESSIO_16": "Acces iO-16"
            }
            display_model = model_map.get(model.upper(), model)
            
            self.dio_model_var.set(display_model)
            self.dio_hex_var.set(hex_address)
            
            self.status_var.set(f"Selected DIO: {dio_name} ({display_model})")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load DIO info: {str(e)}")
    
    def load_command_table(self, sheet_name):
        """Load command table for selected lookup table"""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Load command list
            cmd_list = self.config_loader.load_command_list(sheet_name)
            
            if self.config_loader.file_format == 'excel':
                # Get all columns
                columns = list(cmd_list.columns)
                
                # Setup columns
                self.tree['columns'] = columns
                self.tree['show'] = 'tree headings'
                
                # Configure columns
                self.tree.column('#0', width=50, anchor=tk.W)
                self.tree.heading('#0', text='#')
                
                for col in columns:
                    self.tree.column(col, width=150, anchor=tk.W)
                    self.tree.heading(col, text=col)
                
                # Add data
                for idx, row in cmd_list.iterrows():
                    values = [str(row[col]) for col in columns]
                    self.tree.insert('', tk.END, text=str(idx+1), values=values)
            
            else:
                # JSON format
                if not cmd_list:
                    return
                
                # Get all keys from first item
                columns = list(cmd_list[0].keys())
                
                # Setup columns
                self.tree['columns'] = columns
                self.tree['show'] = 'tree headings'
                
                # Configure columns
                self.tree.column('#0', width=50, anchor=tk.W)
                self.tree.heading('#0', text='#')
                
                for col in columns:
                    self.tree.column(col, width=150, anchor=tk.W)
                    self.tree.heading(col, text=col)
                
                # Add data
                for idx, item in enumerate(cmd_list):
                    values = [str(item.get(col, '')) for col in columns]
                    self.tree.insert('', tk.END, text=str(idx+1), values=values)
            
            self.status_var.set(f"Loaded {len(cmd_list)} command(s)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load command table: {str(e)}")
            self.status_var.set("Error loading command table")
    
    def on_tree_selection_changed(self, event):
        """Handle tree selection change - populate DIO Command field"""
        try:
            selection = self.tree.selection()
            if not selection:
                return
            
            item = selection[0]
            values = self.tree.item(item, 'values')
            
            if not values:
                return
            
            # Find SwitchDriverCommand column
            columns = self.tree['columns']
            cmd_idx = None
            for idx, col in enumerate(columns):
                if 'switchdrivercommand' in col.lower():
                    cmd_idx = idx
                    break
            
            if cmd_idx is not None and cmd_idx < len(values):
                command = values[cmd_idx]
                self.dio_command_var.set(command)
                
        except Exception as e:
            # Silently ignore selection errors
            pass
    
    def on_tree_double_click(self, event):
        """Handle double-click on tree item to execute command"""
        try:
            selection = self.tree.selection()
            if not selection:
                return
            
            item = selection[0]
            values = self.tree.item(item, 'values')
            
            # Find PathName and SwitchDriverCommand columns (case-insensitive)
            columns = self.tree['columns']
            pathname_idx = None
            cmd_idx = None
            
            for idx, col in enumerate(columns):
                col_lower = col.lower()
                if 'pathname' in col_lower:
                    pathname_idx = idx
                if 'switchdrivercommand' in col_lower:
                    cmd_idx = idx
            
            if pathname_idx is None:
                messagebox.showwarning("Warning", "PathName column not found in table")
                return
            
            if cmd_idx is None:
                messagebox.showwarning("Warning", "SwitchDriverCommand column not found in table")
                return
            
            pathname = values[pathname_idx]
            switch_command = values[cmd_idx]
            
            # Execute command
            self.execute_command(pathname, switch_command)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute command: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def execute_command(self, pathname, switch_command):
        """Execute a switch command on the hardware"""
        try:
            self.status_var.set(f"Executing: {pathname}...")
            self.root.update()
            
            # Get current configuration
            platform_file = self.platform_var.get()
            dio_name = self.dio_name_var.get()
            lookup_table = self.current_lookup_table or "Model_Common"
            
            if not all([platform_file, dio_name, lookup_table]):
                messagebox.showwarning("Warning", "Please select platform, DIO name, and lookup table")
                return
            
            config_path = os.path.join(self.config_dir, platform_file)
            
            # Import and execute command
            from testhead_control import Testhead_Control
            testhead = Testhead_Control(
                testhead_lookup_xlsx=config_path,
                dio_name=dio_name,
                dio_pathname=pathname,
                sheet_name=lookup_table
            )
            
            if testhead.command_success:
                self.status_var.set(f"✓ Executed: {pathname}")
                messagebox.showinfo("Success", f"Command executed successfully:\n{pathname}\n\nCommand: {switch_command}")
            else:
                self.status_var.set(f"✗ Failed: {pathname}")
                messagebox.showerror("Error", "Command execution failed")
            
        except Exception as e:
            messagebox.showerror("Error", f"Execution error: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def execute_manual_command(self):
        """Execute manually entered DIO command"""
        try:
            command = self.dio_command_var.get()
            if not command:
                messagebox.showwarning("Warning", "Please enter a DIO command")
                return
            
            # Create a temporary pathname for manual command
            pathname = f"Manual Command: {command}"
            self.execute_command(pathname, command)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute manual command: {str(e)}")
    
    def reset_all_lines(self):
        """Reset all DIO lines to low"""
        try:
            self.dio_command_var.set("0")
            self.execute_manual_command()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset lines: {str(e)}")
    
    def export_to_json(self):
        """Export current configuration to JSON file"""
        try:
            if not self.config_loader:
                messagebox.showwarning("Warning", "No configuration loaded")
                return
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=self.config_dir,
                title="Export to JSON"
            )
            
            if not filename:
                return
            
            # If source is Excel, convert to JSON format
            if self.config_loader.file_format == 'excel':
                # Load all data
                dio_list_df = self.config_loader.load_dio_list()
                
                json_data = {
                    "DIO_List": dio_list_df.to_dict('records')
                }
                
                # Load all lookup tables
                for table_name in self.lookup_tables:
                    cmd_df = self.config_loader.load_command_list(table_name)
                    json_data[table_name] = cmd_df.to_dict('records')
                
                # Save to JSON
                with open(filename, 'w') as f:
                    json.dump(json_data, f, indent=2)
                
                messagebox.showinfo("Success", f"Configuration exported to:\n{filename}")
                self.status_var.set(f"Exported to: {os.path.basename(filename)}")
            
            else:
                # Already JSON, just copy
                import shutil
                shutil.copy2(self.config_loader.config_file_path, filename)
                messagebox.showinfo("Success", f"Configuration copied to:\n{filename}")
                self.status_var.set(f"Copied to: {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
            self.status_var.set("Export failed")


def main():
    """Main entry point for GUI application"""
    root = tk.Tk()
    app = TestHeadGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
