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
        
        # Set application icon
        try:
            if getattr(sys, 'frozen', False):
                # Running as executable
                icon_path = os.path.join(os.path.dirname(sys.executable), "testhead_icon.ico")
            else:
                # Running as script
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testhead_icon.ico")
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            # Silently continue if icon cannot be loaded
            pass
        
        # Configure treeview style for grid lines
        style = ttk.Style()
        
        # Try to use a consistent theme across all Windows versions
        try:
            style.theme_use('clam')  # More consistent cross-platform theme
        except:
            style.theme_use('default')
        
        # Configure treeview to show grid-like appearance
        style.configure("Treeview",
                       background="#FFFFFF",
                       foreground="#000000",
                       rowheight=25,
                       fieldbackground="#FFFFFF",
                       borderwidth=1,
                       relief="solid")
        
        # Alternating row colors for grid effect
        style.map('Treeview', 
                 background=[('selected', '#0078D7')],
                 foreground=[('selected', '#FFFFFF')])
        
        # Configure treeview heading style with borders
        style.configure("Treeview.Heading",
                       background="#D0D0D0",
                       foreground="#000000",
                       relief="raised",
                       borderwidth=1)
        
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
        
        # Set up window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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
        main_frame.rowconfigure(0, weight=0)  # Configuration section - fixed height
        main_frame.rowconfigure(1, weight=1)  # Command List section - expandable
        main_frame.rowconfigure(2, weight=0)  # Status bar - fixed height
        
        # ===== TOP SECTION: Configuration Controls =====
        config_panel = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=5, pady=5)
        config_panel.columnconfigure(1, weight=1)
        config_panel.columnconfigure(3, weight=1)
        
        # Create a 4-column layout for Configuration section
        # Column 0: Label 1 | Column 1: Field 1 | Column 2: Label 2 | Column 3: Field 2
        
        # Row 0: Platform and Lookup Tables
        ttk.Label(config_panel, text="Platform:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(5,5))
        self.platform_var = tk.StringVar()
        self.platform_combo = ttk.Combobox(config_panel, textvariable=self.platform_var, width=35, state='readonly')
        self.platform_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0,10))
        self.platform_combo.bind('<<ComboboxSelected>>', self.on_platform_selected)
        
        ttk.Label(config_panel, text="Lookup Tables:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(5,5))
        self.lookup_table_var = tk.StringVar()
        self.lookup_table_combo = ttk.Combobox(config_panel, textvariable=self.lookup_table_var, width=35, state='readonly')
        self.lookup_table_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=(0,5))
        self.lookup_table_combo.bind('<<ComboboxSelected>>', self.on_lookup_table_selected)
        
        # Row 1: DIO Name and DIO Model
        ttk.Label(config_panel, text="DIO Name:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(5,5))
        self.dio_name_var = tk.StringVar()
        self.dio_name_combo = ttk.Combobox(config_panel, textvariable=self.dio_name_var, width=35, state='readonly')
        self.dio_name_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0,10))
        self.dio_name_combo.bind('<<ComboboxSelected>>', self.on_dio_name_selected)
        
        ttk.Label(config_panel, text="DIO Model:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(5,5))
        self.dio_model_var = tk.StringVar()
        dio_model_combo = ttk.Combobox(config_panel, textvariable=self.dio_model_var, width=35, state='readonly')
        dio_model_combo.grid(row=1, column=3, sticky=(tk.W, tk.E), pady=5, padx=(0,5))
        
        # Row 2: DIO Hex Address and Platform File Type
        ttk.Label(config_panel, text="DIO Hex Address:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=(5,5))
        self.dio_hex_var = tk.StringVar()
        dio_hex_entry = ttk.Entry(config_panel, textvariable=self.dio_hex_var, width=35, state='readonly')
        dio_hex_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0,10))
        
        ttk.Label(config_panel, text="Platform File Type:").grid(row=2, column=2, sticky=tk.W, pady=5, padx=(5,5))
        self.file_type_var = tk.StringVar(value="ALL")
        file_type_combo = ttk.Combobox(config_panel, textvariable=self.file_type_var, 
                                       values=["ALL", "JSON", "EXCEL"], width=35, state='readonly')
        file_type_combo.grid(row=2, column=3, sticky=(tk.W, tk.E), pady=5, padx=(0,5))
        file_type_combo.bind('<<ComboboxSelected>>', self.on_file_type_changed)
        
        # Row 3: DIO Command (spans all columns)
        ttk.Label(config_panel, text="DIO Command:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=(5,5))
        self.dio_command_var = tk.StringVar()
        dio_command_entry = ttk.Entry(config_panel, textvariable=self.dio_command_var)
        dio_command_entry.grid(row=3, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=(0,5))
        
        # Row 4: Lookup Table Filepath (spans all columns)
        ttk.Label(config_panel, text="Lookup Table Filepath:").grid(row=4, column=0, sticky=tk.W, pady=5, padx=(5,5))
        self.filepath_var = tk.StringVar()
        filepath_entry = ttk.Entry(config_panel, textvariable=self.filepath_var, state='readonly')
        filepath_entry.grid(row=4, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=(0,5))
        
        # Row 5: Settling Time and Buttons
        settling_button_frame = ttk.Frame(config_panel)
        settling_button_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(settling_button_frame, text="Settling Time (ms):").pack(side=tk.LEFT, padx=5)
        self.settling_time_var = tk.IntVar(value=10)
        settling_spinbox = ttk.Spinbox(settling_button_frame, from_=0, to=10000, textvariable=self.settling_time_var, width=10)
        settling_spinbox.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(settling_button_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        ttk.Button(settling_button_frame, text="To JSON", command=self.export_to_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(settling_button_frame, text="Execute Command", command=self.execute_manual_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(settling_button_frame, text="Reset All", command=self.reset_all_lines).pack(side=tk.LEFT, padx=5)
        
        # ===== BOTTOM SECTION: Command Table =====
        table_panel = ttk.LabelFrame(main_frame, text="Command List - Double click to execute command", padding="10")
        table_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        table_panel.columnconfigure(0, weight=1)
        table_panel.rowconfigure(0, weight=1)
        
        # Create Treeview with scrollbars
        tree_frame = ttk.Frame(table_panel)
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
        
        # Status bartable
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
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
                # JSON format - extract unique model names from Model Sheets
                with open(config_path, 'r') as f:
                    data = json.load(f)
                
                # Check if JSON has Model Sheets structure (all models in one list)
                if 'Model Sheets' in data and isinstance(data['Model Sheets'], list):
                    # Extract unique model names from Model_ field
                    model_names = set()
                    for item in data['Model Sheets']:
                        if 'Model_' in item and item['Model_']:
                            model_names.add(item['Model_'])
                    self.lookup_tables = sorted(list(model_names))
                else:
                    # Original JSON format with separate keys for each model
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
                    # Use tags to create alternating row colors
                    tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                    self.tree.insert('', tk.END, text=str(idx+1), values=values, tags=(tag,))
                
                # Configure row colors with explicit foreground
                self.tree.tag_configure('evenrow', background='#FFFFFF', foreground='#000000')
                self.tree.tag_configure('oddrow', background='#E8E8E8', foreground='#000000')
            
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
                    # Use tags to create alternating row colors
                    tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                    self.tree.insert('', tk.END, text=str(idx+1), values=values, tags=(tag,))
                
                # Configure row colors with explicit foreground
                self.tree.tag_configure('evenrow', background='#FFFFFF', foreground='#000000')
                self.tree.tag_configure('oddrow', background='#E8E8E8', foreground='#000000')
            
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
            testhead = Testhead_Control()
            
            # Run the control code
            testhead.run(testhead_lookup_xlsx=config_path,
                        dio_name=dio_name,
                        dio_pathname=pathname,
                        sheet_name=lookup_table)
            
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
            # Get current configuration
            dio_name = self.dio_name_var.get()
            
            if not dio_name:
                messagebox.showwarning("Warning", "Please select a DIO name first")
                return
            
            # Confirm reset action
            result = messagebox.askyesno("Confirm Reset", 
                                        f"Reset all relays to OFF for {dio_name}?\n\n"
                                        "This will set all DIO lines to LOW (0).")
            
            if not result:
                self.status_var.set("Reset cancelled")
                return
            
            self.status_var.set("Resetting all lines to LOW...")
            self.root.update()
            
            # Set DIO command to 0 and execute
            self.dio_command_var.set("0")
            pathname = "Reset All Lines"
            switch_command = "0"
            self.execute_command(pathname, switch_command)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset lines: {str(e)}")
            self.status_var.set("Reset failed")
    
    def on_closing(self):
        """Handle window close event properly"""
        try:
            # Clean up any resources if needed
            self.root.quit()
            self.root.destroy()
        except Exception:
            # Silently exit even if there's an error
            try:
                self.root.destroy()
            except:
                pass
    
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
    try:
        root = tk.Tk()
        app = TestHeadGUI(root)
        root.mainloop()
    except Exception as e:
        # Show error dialog if GUI fails to start
        try:
            import tkinter.messagebox as mb
            mb.showerror("Startup Error", f"Failed to start application:\n\n{str(e)}")
        except:
            # If messagebox fails, just print to console
            print(f"ERROR: Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
