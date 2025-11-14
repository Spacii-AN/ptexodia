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
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("Exodia Contagion Macro - Warframe")
        self.root.geometry("900x750")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # System tray
        self.tray_icon = None
        self.tray_thread = None
        
        # Listeners
        self.kb_listener = None
        self.mouse_listener = None
        self.background_thread = None
        
        # Setup GUI
        self.setup_gui()
        self.load_config_to_gui()
        self.apply_config_to_macro()
        
        # Start background check
        self.macro_module.start_background_check()
    
    def setup_gui(self):
        """Setup the GUI interface"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Controls
        controls_frame = ttk.Frame(notebook)
        notebook.add(controls_frame, text="Controls")
        self.setup_controls_tab(controls_frame)
        
        # Tab 2: Keybinds
        keybinds_frame = ttk.Frame(notebook)
        notebook.add(keybinds_frame, text="Keybinds")
        self.setup_keybinds_tab(keybinds_frame)
        
        # Tab 3: Timing
        timing_frame = ttk.Frame(notebook)
        notebook.add(timing_frame, text="Timing")
        self.setup_timing_tab(timing_frame)
        
        # Tab 4: Settings
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        self.setup_settings_tab(settings_frame)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Configure settings and click 'Start Macro'")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_controls_tab(self, parent):
        """Setup controls tab"""
        # Control buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=20)
        
        self.start_btn = ttk.Button(btn_frame, text="Start Macro", command=self.start_macro, width=20)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop Macro", command=self.stop_macro, width=20, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Save Config", command=self.save_config, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Load Config", command=self.load_config, width=20).pack(side=tk.LEFT, padx=5)
        
        # Status display
        status_frame = ttk.LabelFrame(parent, text="Status Log", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.status_text = tk.Text(status_frame, height=20, wrap=tk.WORD, font=("Consolas", 9))
        self.status_text.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        self.log("=== Exodia Contagion Macro GUI ===")
        self.log("Configure your settings in the tabs above")
        self.log("Click 'Start Macro' to begin listening for button presses")
        self.log("")
    
    def setup_keybinds_tab(self, parent):
        """Setup keybinds configuration tab"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
        for label, key, desc in keybinds:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=f"{label}:", width=20).pack(side=tk.LEFT)
            var = tk.StringVar()
            entry = ttk.Entry(row, textvariable=var, width=20)
            entry.pack(side=tk.LEFT, padx=5)
            self.keybind_vars[key] = var
            ttk.Label(row, text=desc, foreground="gray", font=("TkDefaultFont", 8)).pack(side=tk.LEFT, padx=5)
        
        # Enable macro alt checkbox
        self.enable_alt_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Enable Alternative Macro Button", variable=self.enable_alt_var).pack(pady=10)
        
        ttk.Label(frame, text="Note: For button names, see BUTTON_REFERENCE.md", foreground="blue", font=("TkDefaultFont", 8)).pack(pady=5)
    
    def setup_timing_tab(self, parent):
        """Setup timing configuration tab"""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        frame = scrollable_frame
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
        self.use_emote_formula_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Use Emote Formula (auto-calculated)", variable=self.use_emote_formula_var).pack(pady=5)
        
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
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=f"{label}:", width=30).pack(side=tk.LEFT)
        var = tk.StringVar(value=str(default))
        entry = ttk.Entry(row, textvariable=var, width=15)
        entry.pack(side=tk.LEFT, padx=5)
        if tooltip:
            ttk.Label(row, text=tooltip, foreground="gray", font=("TkDefaultFont", 8)).pack(side=tk.LEFT)
        self.timing_vars[key] = var
    
    def setup_settings_tab(self, parent):
        """Setup settings tab"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # System tray
        tray_frame = ttk.LabelFrame(frame, text="System Tray", padding=10)
        tray_frame.pack(fill=tk.X, pady=5)
        
        self.minimize_to_tray_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tray_frame, text="Minimize to System Tray", variable=self.minimize_to_tray_var).pack(anchor=tk.W)
        
        if not TRAY_AVAILABLE:
            ttk.Label(tray_frame, text="System tray requires: pip install pystray pillow", foreground="red").pack(anchor=tk.W)
            self.minimize_to_tray_var.set(False)
        
        # Info
        info_frame = ttk.LabelFrame(frame, text="Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        info_text = """
This GUI allows you to configure the macro without editing code.

1. Configure your keybinds and timing in the tabs
2. Click 'Save Config' to save your settings
3. Click 'Start Macro' to begin
4. Hold your side mouse button to activate the macro
5. Press F11 to toggle macros on/off

The macro will only run when Warframe is the active window.
        """
        ttk.Label(info_frame, text=info_text.strip(), justify=tk.LEFT).pack(anchor=tk.W)
    
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
        
        if self.config.save_config():
            self.log("Configuration saved successfully!")
            messagebox.showinfo("Success", "Configuration saved!")
        else:
            self.log("Error saving configuration")
            messagebox.showerror("Error", "Failed to save configuration")
    
    def load_config(self):
        """Load configuration from file"""
        self.config = MacroConfig()
        self.load_config_to_gui()
        self.apply_config_to_macro()
        self.log("Configuration loaded!")
        messagebox.showinfo("Success", "Configuration loaded!")
    
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
    
    def on_closing(self):
        """Handle window closing"""
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
