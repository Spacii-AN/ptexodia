#!/usr/bin/env python3
"""
Exodia Contagion Macro GUI for Warframe
Made by Spacii-AN

GUI version of the macro with visual configuration and system tray support.
Uses the core logic from pt-macro.py (keeps it completely untouched)
"""

import sys
import os
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import importlib.util
import platform

# Try to import system tray support
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# Import pt-macro.py as a module (keeps it untouched)
# Handle both script and executable paths
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    base_path = sys._MEIPASS
else:
    # Running as script
    base_path = os.path.dirname(os.path.abspath(__file__))

macro_path = os.path.join(base_path, "pt-macro.py")
if not os.path.exists(macro_path):
    # Try current directory
    macro_path = "pt-macro.py"

spec = importlib.util.spec_from_file_location("pt_macro", macro_path)
pt_macro = importlib.util.module_from_spec(spec)
sys.modules["pt_macro"] = pt_macro
spec.loader.exec_module(pt_macro)

# Now we can access all functions and variables from pt-macro.py
# We'll update the config variables dynamically


def find_ee_log():
    """Auto-detect EE.log file location on all platforms"""
    system = platform.system()
    possible_paths = []
    
    if system == 'Windows':
        # Windows common locations
        localappdata = os.environ.get('LOCALAPPDATA', '')
        appdata = os.environ.get('APPDATA', '')
        if localappdata:
            possible_paths.append(os.path.join(localappdata, 'Warframe', 'EE.log'))
        if appdata:
            possible_paths.append(os.path.join(appdata, 'Warframe', 'EE.log'))
        # Also check Program Files locations
        program_files = os.environ.get('ProgramFiles', '')
        if program_files:
            possible_paths.append(os.path.join(program_files, 'Warframe', 'EE.log'))
        program_files_x86 = os.environ.get('ProgramFiles(x86)', '')
        if program_files_x86:
            possible_paths.append(os.path.join(program_files_x86, 'Warframe', 'EE.log'))
    elif system == 'Darwin':  # macOS
        home = os.path.expanduser('~')
        possible_paths.append(os.path.join(home, 'Library', 'Application Support', 'Warframe', 'EE.log'))
        possible_paths.append(os.path.join(home, 'Library', 'Warframe', 'EE.log'))
    else:  # Linux
        home = os.path.expanduser('~')
        possible_paths.append(os.path.join(home, '.local', 'share', 'Warframe', 'EE.log'))
        possible_paths.append(os.path.join(home, 'Warframe', 'EE.log'))
        possible_paths.append(os.path.join(home, '.steam', 'steam', 'steamapps', 'common', 'Warframe', 'EE.log'))
        # Also check common Steam locations
        possible_paths.append(os.path.join(home, '.steam', 'steam', 'steamapps', 'compatdata', '230410', 'pfx', 'drive_c', 'users', 'steamuser', 'AppData', 'Local', 'Warframe', 'EE.log'))
    
    # Check each path and return the first one that exists
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            return path
    
    return None


class MacroConfig:
    """Configuration manager for the macro"""
    
    def __init__(self, config_file="macro_config.json"):
        self.config_file = config_file
        self.default_config = {
            "keybinds": {
                "melee": "e",
                "jump": "space",
                "aim": "right",
                "fire": "left",
                "emote": ".",
                "macro": "button8",
                "macro_alt": "button9",
                "rapid_click": "j"
            },
            "timing": {
                "fps": 115,
                "jump_delay_ms": 1100,
                "aim_melee_delay": 0.025,
                "melee_hold_time": 0.050,
                "use_emote_formula": True,
                "emote_preparation_delay_manual": 0.100,
                "rapid_fire_duration_ms": 230,
                "rapid_fire_click_delay": 0.001,
                "sequence_end_delay": 0.050,
                "loop_delay": 0.0005,
                "rapid_click_count": 10,
                "rapid_click_delay": 0.05
            },
            "settings": {
                "enable_macro_alt": True,
                "log_file": "",
                "enable_logging": False
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    merged = self.default_config.copy()
                    for key in merged:
                        if key in config:
                            merged[key].update(config[key])
                    return merged
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False


class MacroGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.config = MacroConfig()
        self.macro_module = pt_macro
        
        # Modern color scheme
        self.colors = {
            'bg': '#2b2b2b',  # Dark background
            'fg': '#ffffff',  # White text
            'accent': '#4a9eff',  # Blue accent
            'accent_hover': '#5fb3ff',
            'success': '#4caf50',  # Green
            'danger': '#f44336',  # Red
            'frame_bg': '#3c3c3c',  # Slightly lighter frame
            'entry_bg': '#404040',  # Entry background
            'text_bg': '#1e1e1e',  # Text widget background
            'border': '#555555'
        }
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("Exodia Contagion Macro - Warframe")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Set root background
        self.root.configure(bg=self.colors['bg'])
        
        # Prevent window resizing
        self.root.resizable(False, False)
        
        # Apply modern styling
        self.setup_styles()
        
        # System tray
        self.tray_icon = None
        self.tray_thread = None
        
        # Listeners
        self.kb_listener = None
        self.mouse_listener = None
        self.background_thread = None
        
        # Key capture state
        self.capturing_key = None
        self.capture_listener = None
        self.capture_mouse_listener = None
        
        # Initialize status_var before setup_gui
        self.status_var = tk.StringVar(value="Ready - Configure settings and click 'Start Macro'")
        
        # Setup GUI
        self.setup_gui()
        self.load_config_to_gui()
        
        # Auto-detect EE.log if not set
        if not self.log_file_var.get():
            log_path = find_ee_log()
            if log_path:
                self.log_file_var.set(log_path)
                self.log(f"Auto-detected EE.log: {log_path}")
        
        self.apply_config_to_macro()
        
        # Start background check
        self.macro_module.start_background_check()
    
    def setup_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        
        # Try to use a modern theme
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        
        # Configure button styles
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=10)
        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_hover']),
                            ('pressed', self.colors['accent'])])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=10)
        style.map('Success.TButton',
                 background=[('active', '#66bb6a'),
                            ('pressed', '#43a047')])
        
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=10)
        style.map('Danger.TButton',
                 background=[('active', '#ef5350'),
                            ('pressed', '#e53935')])
        
        # Configure notebook style
        style.configure('TNotebook',
                       background=self.colors['bg'],
                       borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=self.colors['frame_bg'],
                       foreground=self.colors['fg'],
                       padding=[20, 10],
                       borderwidth=0)
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['accent']),
                            ('active', self.colors['frame_bg'])],
                 foreground=[('selected', 'white'),
                            ('active', self.colors['fg'])])
        
        # Configure frame styles
        style.configure('Card.TLabelframe',
                       background=self.colors['bg'],
                       foreground=self.colors['fg'],
                       borderwidth=1,
                       relief='flat')
        style.configure('Card.TLabelframe.Label',
                       background=self.colors['bg'],
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 10, 'bold'))
        
        # Configure label styles
        style.configure('Heading.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 16, 'bold'))
        style.configure('Subheading.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['fg'],
                       font=('Segoe UI', 11))
    
    def setup_gui(self):
        """Setup the GUI interface"""
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors['accent'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame,
                               text="Exodia Contagion Macro",
                               font=('Segoe UI', 20, 'bold'),
                               bg=self.colors['accent'],
                               fg='white')
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(header_frame,
                                 text="Warframe Automation Tool",
                                 font=('Segoe UI', 10),
                                 bg=self.colors['accent'],
                                 fg='white')
        subtitle_label.pack()
        
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Controls
        controls_frame = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(controls_frame, text="  Controls  ")
        self.setup_controls_tab(controls_frame)
        
        # Tab 2: Keybinds
        keybinds_frame = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(keybinds_frame, text="  Keybinds  ")
        self.setup_keybinds_tab(keybinds_frame)
        
        # Tab 3: Timing
        timing_frame = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(timing_frame, text="  Timing  ")
        self.setup_timing_tab(timing_frame)
        
        # Tab 4: Settings
        settings_frame = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(settings_frame, text="  Settings  ")
        self.setup_settings_tab(settings_frame)
        
        # Status bar
        status_bar = tk.Label(self.root,
                             textvariable=self.status_var,
                             bg=self.colors['frame_bg'],
                             fg=self.colors['fg'],
                             font=('Segoe UI', 9),
                             anchor='w',
                             padx=10,
                             pady=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_controls_tab(self, parent):
        """Setup controls tab"""
        # Control buttons with modern styling
        btn_container = tk.Frame(parent, bg=self.colors['bg'])
        btn_container.pack(pady=30)
        
        btn_frame = tk.Frame(btn_container, bg=self.colors['bg'])
        btn_frame.pack()
        
        self.start_btn = ttk.Button(btn_frame, text="Start Macro", 
                                   command=self.start_macro, 
                                   style='Success.TButton',
                                   width=18)
        self.start_btn.pack(side=tk.LEFT, padx=8, pady=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop Macro", 
                                   command=self.stop_macro, 
                                   style='Danger.TButton',
                                   width=18,
                                   state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=8, pady=5)
        
        save_btn = ttk.Button(btn_frame, text="Save Config", 
                             command=self.save_config, 
                             style='Accent.TButton',
                             width=18)
        save_btn.pack(side=tk.LEFT, padx=8, pady=5)
        
        load_btn = ttk.Button(btn_frame, text="Load Config", 
                             command=self.load_config, 
                             style='Accent.TButton',
                             width=18)
        load_btn.pack(side=tk.LEFT, padx=8, pady=5)
        
        # Status display with modern card style
        status_frame = ttk.LabelFrame(parent, text="Status Log", 
                                     style='Card.TLabelframe',
                                     padding=15)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Text widget with modern styling
        text_container = tk.Frame(status_frame, bg=self.colors['text_bg'])
        text_container.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(text_container, 
                                   height=20, 
                                   wrap=tk.WORD, 
                                   font=("Consolas", 10),
                                   bg=self.colors['text_bg'],
                                   fg='#d4d4d4',
                                   insertbackground=self.colors['accent'],
                                   selectbackground=self.colors['accent'],
                                   selectforeground='white',
                                   borderwidth=0,
                                   relief='flat',
                                   padx=10,
                                   pady=10)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        self.log("=== Exodia Contagion Macro GUI ===")
        self.log("Configure your settings in the tabs above")
        self.log("Click 'Start Macro' to begin listening for button presses")
        self.log("")
    
    def setup_keybinds_tab(self, parent):
        """Setup keybinds configuration tab"""
        # Scrollable frame
        canvas = tk.Canvas(parent, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        frame = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Keybind entries with descriptions
        keybinds = [
            ("Melee", "melee", "Melee attack key"),
            ("Jump", "jump", "Jump key (usually Space)"),
            ("Aim", "aim", "Aim button (usually Right Mouse)"),
            ("Fire", "fire", "Fire button (usually Left Mouse)"),
            ("Emote", "emote", "Emote key"),
            ("Macro Button", "macro", "Side mouse button to trigger macro (button8/x1)"),
            ("Macro Alt Button", "macro_alt", "Alternative side button (button9/x2)"),
            ("Rapid Click", "rapid_click", "Key for rapid click macro")
        ]
        
        self.keybind_vars = {}
        self.set_button_widgets = {}
        for label, key, desc in keybinds:
            card = tk.Frame(frame, bg=self.colors['frame_bg'], relief='flat', bd=1)
            card.pack(fill=tk.X, pady=5, padx=5)
            
            row = tk.Frame(card, bg=self.colors['frame_bg'])
            row.pack(fill=tk.X, padx=15, pady=10)
            
            label_widget = tk.Label(row, text=f"{label}:", 
                                   bg=self.colors['frame_bg'],
                                   fg=self.colors['fg'],
                                   font=('Segoe UI', 10, 'bold'),
                                   width=18,
                                   anchor='w')
            label_widget.pack(side=tk.LEFT)
            
            var = tk.StringVar()
            entry = tk.Entry(row, textvariable=var, 
                           width=20,
                           bg=self.colors['entry_bg'],
                           fg=self.colors['fg'],
                           font=('Segoe UI', 10),
                           insertbackground=self.colors['accent'],
                           relief='flat',
                           bd=5)
            entry.pack(side=tk.LEFT, padx=10)
            self.keybind_vars[key] = var
            
            # Set Button
            set_btn = ttk.Button(row, text="Set Button", 
                               command=lambda k=key: self.start_capture_key(k),
                               style='Accent.TButton',
                               width=12)
            set_btn.pack(side=tk.LEFT, padx=5)
            self.set_button_widgets[key] = set_btn
            
            desc_label = tk.Label(row, text=desc, 
                                 bg=self.colors['frame_bg'],
                                 fg='#888888',
                                 font=('Segoe UI', 9))
            desc_label.pack(side=tk.LEFT, padx=5)
        
        # Enable macro alt checkbox
        checkbox_frame = tk.Frame(frame, bg=self.colors['bg'])
        checkbox_frame.pack(pady=15)
        
        self.enable_alt_var = tk.BooleanVar()
        checkbox = tk.Checkbutton(checkbox_frame, 
                                 text="Enable Alternative Macro Button",
                                 variable=self.enable_alt_var,
                                 bg=self.colors['bg'],
                                 fg=self.colors['fg'],
                                 selectcolor=self.colors['frame_bg'],
                                 activebackground=self.colors['bg'],
                                 activeforeground=self.colors['fg'],
                                 font=('Segoe UI', 10))
        checkbox.pack()
        
        # Button reference section
        ref_frame = ttk.LabelFrame(frame, text="Button Reference", 
                                   style='Card.TLabelframe',
                                   padding=15)
        ref_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ref_text = """Mouse Buttons:
• Button.left / 'left' - Left mouse button
• Button.right / 'right' - Right mouse button
• Button.middle / 'middle' - Middle mouse button
• Button.button8 / 'button8' - First side button (x1) - Recommended
• Button.button9 / 'button9' - Second side button (x2)

Keyboard Keys:
• Key.space / 'space' - Spacebar
• Key.enter / 'enter' - Enter
• Key.f1 to Key.f12 / 'f1' to 'f12' - Function keys
• Regular letters: 'a', 'b', 'c', etc.
• Regular numbers: '1', '2', '3', etc.
• Special chars: '.', ',', ';', etc.

Click 'Set Button' next to any keybind, then press the key/button you want to assign."""
        
        ref_label = tk.Label(ref_frame, 
                           text=ref_text,
                           bg=self.colors['bg'],
                           fg=self.colors['fg'],
                           font=('Consolas', 9),
                           justify=tk.LEFT,
                           anchor='nw')
        ref_label.pack(fill=tk.BOTH, expand=True, anchor=tk.W)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_timing_tab(self, parent):
        """Setup timing configuration tab"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        frame = scrollable_frame
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Timing variables
        self.timing_vars = {}
        
        # FPS
        self.create_timing_entry(frame, "FPS", "fps", 115, "Your in-game FPS")
        
        # Jump timing
        self.create_timing_entry(frame, "Jump Delay (ms)", "jump_delay_ms", 1100, "Milliseconds between jumps")
        
        # Aim & Melee
        self.create_timing_entry(frame, "Aim-Melee Delay (s)", "aim_melee_delay", 0.025, "Delay between aim and melee")
        self.create_timing_entry(frame, "Melee Hold Time (s)", "melee_hold_time", 0.050, "How long to hold melee")
        
        # Emote
        self.create_timing_entry(frame, "Emote Delay Manual (s)", "emote_preparation_delay_manual", 0.100, "Manual emote delay")
        
        checkbox_frame = tk.Frame(frame, bg=self.colors['bg'])
        checkbox_frame.pack(pady=10)
        self.use_emote_formula_var = tk.BooleanVar()
        checkbox = tk.Checkbutton(checkbox_frame, 
                                 text="Use Emote Formula (auto-calculated)",
                                 variable=self.use_emote_formula_var,
                                 bg=self.colors['bg'],
                                 fg=self.colors['fg'],
                                 selectcolor=self.colors['frame_bg'],
                                 activebackground=self.colors['bg'],
                                 activeforeground=self.colors['fg'],
                                 font=('Segoe UI', 10))
        checkbox.pack()
        
        # Rapid Fire
        self.create_timing_entry(frame, "Rapid Fire Duration (ms)", "rapid_fire_duration_ms", 230, "Total rapid fire duration")
        self.create_timing_entry(frame, "Rapid Fire Click Delay (s)", "rapid_fire_click_delay", 0.001, "Delay between shots")
        
        # Loop timing
        self.create_timing_entry(frame, "Sequence End Delay (s)", "sequence_end_delay", 0.050, "Delay at end of sequence")
        self.create_timing_entry(frame, "Loop Delay (s)", "loop_delay", 0.0005, "Delay between sequences")
        
        # Rapid Click
        self.create_timing_entry(frame, "Rapid Click Count", "rapid_click_count", 10, "Number of clicks")
        self.create_timing_entry(frame, "Rapid Click Delay (s)", "rapid_click_delay", 0.05, "Delay between clicks")
    
    def create_timing_entry(self, parent, label, key, default, tooltip=""):
        """Create a timing entry widget"""
        card = tk.Frame(parent, bg=self.colors['frame_bg'], relief='flat', bd=1)
        card.pack(fill=tk.X, pady=4, padx=5)
        
        row = tk.Frame(card, bg=self.colors['frame_bg'])
        row.pack(fill=tk.X, padx=15, pady=10)
        
        label_widget = tk.Label(row, text=f"{label}:", 
                               bg=self.colors['frame_bg'],
                               fg=self.colors['fg'],
                               font=('Segoe UI', 10, 'bold'),
                               width=28,
                               anchor='w')
        label_widget.pack(side=tk.LEFT)
        
        var = tk.StringVar(value=str(default))
        entry = tk.Entry(row, textvariable=var, 
                       width=18,
                       bg=self.colors['entry_bg'],
                       fg=self.colors['fg'],
                       font=('Segoe UI', 10),
                       insertbackground=self.colors['accent'],
                       relief='flat',
                       bd=5)
        entry.pack(side=tk.LEFT, padx=10)
        self.timing_vars[key] = var
        
        if tooltip:
            tooltip_label = tk.Label(row, text=tooltip, 
                                   bg=self.colors['frame_bg'],
                                   fg='#888888',
                                   font=('Segoe UI', 9))
            tooltip_label.pack(side=tk.LEFT, padx=5)
    
    def setup_settings_tab(self, parent):
        """Setup settings tab"""
        # Scrollable frame
        canvas = tk.Canvas(parent, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        frame = scrollable_frame
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # System tray
        tray_frame = ttk.LabelFrame(frame, text="System Tray", 
                                   style='Card.TLabelframe',
                                   padding=15)
        tray_frame.pack(fill=tk.X, pady=10)
        
        self.minimize_to_tray_var = tk.BooleanVar(value=True)
        checkbox = tk.Checkbutton(tray_frame, 
                                 text="Minimize to System Tray",
                                 variable=self.minimize_to_tray_var,
                                 bg=self.colors['bg'],
                                 fg=self.colors['fg'],
                                 selectcolor=self.colors['frame_bg'],
                                 activebackground=self.colors['bg'],
                                 activeforeground=self.colors['fg'],
                                 font=('Segoe UI', 10))
        checkbox.pack(anchor=tk.W)
        
        if not TRAY_AVAILABLE:
            warning_label = tk.Label(tray_frame, 
                                   text="⚠ System tray requires: pip install pystray pillow",
                                   bg=self.colors['bg'],
                                   fg='#ff9800',
                                   font=('Segoe UI', 9))
            warning_label.pack(anchor=tk.W, pady=(5, 0))
            self.minimize_to_tray_var.set(False)
        
        # Log file location
        log_frame = ttk.LabelFrame(frame, text="Log File", 
                                  style='Card.TLabelframe',
                                  padding=15)
        log_frame.pack(fill=tk.X, pady=10)
        
        log_row = tk.Frame(log_frame, bg=self.colors['bg'])
        log_row.pack(fill=tk.X)
        
        label = tk.Label(log_row, text="EE.log Location:", 
                        bg=self.colors['bg'],
                        fg=self.colors['fg'],
                        font=('Segoe UI', 10),
                        width=15,
                        anchor='w')
        label.pack(side=tk.LEFT, padx=5)
        
        self.log_file_var = tk.StringVar(value="")
        log_entry = tk.Entry(log_row, textvariable=self.log_file_var, 
                           width=40,
                           bg=self.colors['entry_bg'],
                           fg=self.colors['fg'],
                           font=('Segoe UI', 10),
                           insertbackground=self.colors['accent'],
                           relief='flat',
                           bd=5)
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        def auto_detect_log():
            """Auto-detect EE.log location"""
            log_path = find_ee_log()
            if log_path:
                self.log_file_var.set(log_path)
                self.log(f"Auto-detected EE.log: {log_path}")
                self.status_var.set(f"Auto-detected EE.log: {log_path}")
            else:
                self.log("Could not auto-detect EE.log. Please browse manually.")
                self.status_var.set("EE.log not found - please browse manually")
                messagebox.showinfo("Not Found", 
                                 "Could not automatically find EE.log.\n\n"
                                 "Common locations:\n"
                                 "Windows: %LOCALAPPDATA%\\Warframe\\EE.log\n"
                                 "macOS: ~/Library/Application Support/Warframe/EE.log\n"
                                 "Linux: ~/.local/share/Warframe/EE.log\n\n"
                                 "Please use Browse to select it manually.")
        
        def browse_log_file():
            filename = filedialog.askopenfilename(
                title="Select EE.log file",
                filetypes=[("Log files", "*.log"), ("All files", "*.*")]
            )
            if filename:
                self.log_file_var.set(filename)
                self.log(f"Selected EE.log: {filename}")
        
        auto_detect_btn = ttk.Button(log_row, text="Auto-detect", 
                                    command=auto_detect_log,
                                    style='Accent.TButton',
                                    width=12)
        auto_detect_btn.pack(side=tk.LEFT, padx=5)
        
        browse_btn = ttk.Button(log_row, text="Browse...", 
                               command=browse_log_file,
                               style='Accent.TButton',
                               width=12)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # Info
        info_frame = ttk.LabelFrame(frame, text="Information", 
                                   style='Card.TLabelframe',
                                   padding=15)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        info_text = """This GUI allows you to configure the macro without editing code.

1. Configure your keybinds and timing in the tabs
2. Click 'Save Config' to save your settings
3. Click 'Start Macro' to begin
4. Hold your side mouse button to activate the macro
5. Press F11 to toggle macros on/off

The macro will only run when Warframe is the active window."""
        
        info_label = tk.Label(info_frame, 
                             text=info_text,
                             bg=self.colors['bg'],
                             fg=self.colors['fg'],
                             font=('Segoe UI', 10),
                             justify=tk.LEFT,
                             anchor='nw')
        info_label.pack(fill=tk.BOTH, expand=True, anchor=tk.W)
    
    def log(self, message):
        """Add message to log"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_var.set(message)
    
    def load_config_to_gui(self):
        """Load configuration into GUI elements"""
        # Load keybinds
        for key, var in self.keybind_vars.items():
            value = self.config.config.get("keybinds", {}).get(key, "")
            var.set(str(value))
        
        # Load timing
        for key, var in self.timing_vars.items():
            value = self.config.config.get("timing", {}).get(key, "")
            var.set(str(value))
        
        # Load settings
        self.enable_alt_var.set(self.config.config.get("settings", {}).get("enable_macro_alt", True))
        self.use_emote_formula_var.set(self.config.config.get("timing", {}).get("use_emote_formula", True))
        
        # Load log file location
        if hasattr(self, 'log_file_var'):
            self.log_file_var.set(self.config.config.get("settings", {}).get("log_file", ""))
    
    def apply_config_to_macro(self):
        """Apply GUI configuration to pt-macro.py module"""
        # Convert keybind strings to proper objects
        from pynput.keyboard import Key
        from pynput.mouse import Button
        
        # Update keybinds in pt-macro module
        keybinds = {}
        for key, var in self.keybind_vars.items():
            value = var.get().strip().lower()
            if key == "jump":
                if value == "space":
                    keybinds[key] = Key.space
                else:
                    keybinds[key] = value  # Fallback to string
            elif key == "aim":
                if value == "right":
                    keybinds[key] = Button.right
                else:
                    keybinds[key] = value
            elif key == "fire":
                if value == "left":
                    keybinds[key] = Button.left
                else:
                    keybinds[key] = value
            elif key == "macro":
                if value in ["button8", "x1", "8"]:
                    keybinds[key] = Button.button8
                else:
                    keybinds[key] = value
            elif key == "macro_alt":
                if value in ["button9", "x2", "9"]:
                    keybinds[key] = Button.button9
                else:
                    keybinds[key] = value
            else:
                keybinds[key] = var.get()  # String keys like 'e', '.', 'j'
        
        # Update timing in pt-macro module
        fps = float(self.timing_vars["fps"].get())
        self.macro_module.FPS = fps
        self.macro_module.JUMP_DELAY_MS = float(self.timing_vars["jump_delay_ms"].get())
        self.macro_module.DOUBLE_JUMP_DELAY = self.macro_module.JUMP_DELAY_MS / fps / 1000
        self.macro_module.AIM_MELEE_DELAY = float(self.timing_vars["aim_melee_delay"].get())
        self.macro_module.MELEE_HOLD_TIME = float(self.timing_vars["melee_hold_time"].get())
        self.macro_module.USE_EMOTE_FORMULA = self.use_emote_formula_var.get()
        self.macro_module.EMOTE_PREPARATION_DELAY_MANUAL = float(self.timing_vars["emote_preparation_delay_manual"].get())
        self.macro_module.RAPID_FIRE_DURATION_MS = float(self.timing_vars["rapid_fire_duration_ms"].get())
        self.macro_module.RAPID_FIRE_CLICK_DELAY = float(self.timing_vars["rapid_fire_click_delay"].get())
        self.macro_module.SEQUENCE_END_DELAY = float(self.timing_vars["sequence_end_delay"].get())
        self.macro_module.LOOP_DELAY = float(self.timing_vars["loop_delay"].get())
        self.macro_module.RAPID_CLICK_COUNT = int(self.timing_vars["rapid_click_count"].get())
        self.macro_module.RAPID_CLICK_DELAY = float(self.timing_vars["rapid_click_delay"].get())
        
        # Update emote delay
        if self.macro_module.USE_EMOTE_FORMULA:
            import math
            _raw_emote_delay = (-26 * math.log(fps) + 245) / 1000
            self.macro_module.EMOTE_PREPARATION_DELAY = max(0, _raw_emote_delay)
        else:
            self.macro_module.EMOTE_PREPARATION_DELAY = self.macro_module.EMOTE_PREPARATION_DELAY_MANUAL
        
        # Update keybinds in pt-macro module
        for key, value in keybinds.items():
            self.macro_module.KEYBINDS[key] = value
        
        self.macro_module.ENABLE_MACRO_ALT = self.enable_alt_var.get()
        if not self.enable_alt_var.get():
            self.macro_module.KEYBINDS['macro_alt'] = None
        else:
            # Re-enable if it was disabled
            if self.macro_module.KEYBINDS.get('macro_alt') is None:
                self.macro_module.KEYBINDS['macro_alt'] = Button.button9
    
    def save_config(self):
        """Save configuration from GUI"""
        # Save keybinds
        for key, var in self.keybind_vars.items():
            self.config.config.setdefault("keybinds", {})[key] = var.get()
        
        # Save timing
        for key, var in self.timing_vars.items():
            try:
                value = float(var.get()) if '.' in var.get() else int(var.get())
                self.config.config.setdefault("timing", {})[key] = value
            except ValueError:
                self.log(f"Invalid value for {key}: {var.get()}")
        
        # Save settings
        self.config.config.setdefault("settings", {})["enable_macro_alt"] = self.enable_alt_var.get()
        self.config.config.setdefault("timing", {})["use_emote_formula"] = self.use_emote_formula_var.get()
        
        # Save log file location
        if hasattr(self, 'log_file_var'):
            self.config.config.setdefault("settings", {})["log_file"] = self.log_file_var.get()
        
        if self.config.save_config():
            self.log("Configuration saved successfully!")
        else:
            self.log("Error saving configuration")
    
    def load_config(self):
        """Load configuration from file"""
        self.config = MacroConfig()
        self.load_config_to_gui()
        self.apply_config_to_macro()
        self.log("Configuration loaded!")
    
    def start_macro(self):
        """Start the macro"""
        if self.macro_module.running:
            return
        
        self.apply_config_to_macro()  # Apply current GUI settings
        self.save_config()  # Save config before starting
        
        self.macro_module.running = True
        self.macro_module.macro_enabled = True
        
        # Start listeners using pynput directly
        from pynput import keyboard
        from pynput.mouse import Listener as MouseListener
        
        self.kb_listener = keyboard.Listener(
            on_press=self.macro_module.on_press,
            on_release=self.macro_module.on_release
        )
        self.mouse_listener = MouseListener(
            on_click=self.macro_module.on_click
        )
        
        self.kb_listener.start()
        self.mouse_listener.start()
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log("Macro started! Hold side mouse button to activate.")
        self.log("Press F11 to toggle macros on/off")
        self.status_var.set("Macro Running - Hold side mouse button to activate")
    
    def stop_macro(self):
        """Stop the macro"""
        self.macro_module.running = False
        self.macro_module.macro_enabled = False
        
        if self.kb_listener:
            self.kb_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Macro stopped!")
        self.status_var.set("Macro Stopped")
    
    def start_capture_key(self, keybind_name):
        """Start capturing a key/button press"""
        if self.capturing_key:
            self.stop_capture_key()
        
        self.capturing_key = keybind_name
        self.set_button_widgets[keybind_name].config(text="Press key/button...", state=tk.DISABLED)
        self.log(f"Capturing key for '{keybind_name}'... Press any key or mouse button")
        self.status_var.set(f"Capturing key for '{keybind_name}'... Press any key or button")
        
        from pynput import keyboard
        from pynput.mouse import Listener as MouseListener
        
        def on_key_press(key):
            if not self.capturing_key:
                return False
            
            try:
                # Handle special keys
                if hasattr(key, 'name'):
                    key_str = key.name
                    # Map common special keys
                    if key_str == 'space':
                        value = 'space'
                    elif key_str.startswith('f') and len(key_str) > 1:
                        value = key_str  # f1, f2, etc.
                    elif key_str in ['enter', 'tab', 'backspace', 'delete', 'esc', 'shift', 'ctrl', 'alt', 'cmd']:
                        value = key_str
                    else:
                        value = key_str
                else:
                    # Regular character key - remove quotes
                    key_repr = str(key)
                    if key_repr.startswith("'") and key_repr.endswith("'"):
                        value = key_repr[1:-1]  # Remove quotes
                    elif key_repr.startswith('Key.'):
                        value = key_repr.replace('Key.', '')
                    else:
                        value = key_repr.replace("'", "")
                
                self.set_keybind_value(keybind_name, value, 'keyboard')
                return False  # Stop listener
            except Exception as e:
                self.log(f"Error capturing key: {e}")
                return False
        
        def on_mouse_click(x, y, button, pressed):
            if not self.capturing_key or not pressed:
                return
            
            try:
                button_name = str(button).replace('Button.', '')
                self.set_keybind_value(keybind_name, button_name, 'mouse')
                return False  # Stop listener
            except Exception as e:
                self.log(f"Error capturing mouse button: {e}")
                return False
        
        self.capture_listener = keyboard.Listener(on_press=on_key_press)
        self.capture_mouse_listener = MouseListener(on_click=on_mouse_click)
        
        self.capture_listener.start()
        self.capture_mouse_listener.start()
    
    def stop_capture_key(self):
        """Stop capturing key/button"""
        if self.capturing_key:
            old_key = self.capturing_key
            self.capturing_key = None
            
            if self.capture_listener:
                self.capture_listener.stop()
                self.capture_listener = None
            if self.capture_mouse_listener:
                self.capture_mouse_listener.stop()
                self.capture_mouse_listener = None
            
            if old_key in self.set_button_widgets:
                self.set_button_widgets[old_key].config(text="Set Button", state=tk.NORMAL)
    
    def set_keybind_value(self, keybind_name, value, input_type):
        """Set the keybind value after capture"""
        # Convert to appropriate format
        if input_type == 'mouse':
            # Mouse buttons
            if value == 'left':
                display_value = 'left'
            elif value == 'right':
                display_value = 'right'
            elif value == 'middle':
                display_value = 'middle'
            elif value.startswith('button'):
                display_value = value
            else:
                display_value = value
        else:
            # Keyboard keys
            if value == 'space':
                display_value = 'space'
            elif value.startswith('f') and value[1:].isdigit():
                display_value = value  # f1, f2, etc.
            else:
                display_value = value
        
        # Update the entry
        if keybind_name in self.keybind_vars:
            self.keybind_vars[keybind_name].set(display_value)
            self.log(f"Set {keybind_name} to: {display_value}")
            self.status_var.set(f"Set {keybind_name} to: {display_value}")
        
        # Stop capturing
        self.stop_capture_key()
    
    def on_closing(self):
        """Handle window closing"""
        # Stop any active key capture
        self.stop_capture_key()
        
        if self.minimize_to_tray_var.get() and TRAY_AVAILABLE:
            self.root.withdraw()
            self.create_tray_icon()
        else:
            self.quit()
    
    def create_tray_icon(self):
        """Create system tray icon"""
        if not TRAY_AVAILABLE:
            return
        
        # Create simple icon
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        
        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Start Macro", self.start_macro),
            pystray.MenuItem("Stop Macro", self.stop_macro),
            pystray.MenuItem("Quit", self.quit)
        )
        
        self.tray_icon = pystray.Icon("Macro", image, "Exodia Contagion Macro", menu)
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()
    
    def show_window(self):
        """Show the main window"""
        self.root.deiconify()
        self.root.lift()
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
    
    def quit(self):
        """Quit the application"""
        self.stop_macro()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MacroGUI()
    app.run()
