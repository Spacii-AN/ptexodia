#!/usr/bin/env python3
"""
Exodia Contagion Macro for Warframe (macOS version + windows version)
Made by Spacii-AN

IMPORTANT:
- Ensure "Melee with Fire Weapon Input" setting is OFF in Warframe
- This script requires accessibility permissions on macOS
- Required dependencies: 
  - pip install pynput
  - For Windows: pip install pywin32 (to suppress beeping)
"""

import time
import math
import threading
import os
import sys
import subprocess
import signal
import psutil
from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button, Listener as MouseListener

# Import Windows-specific libraries if on Windows
if sys.platform == "win32":
    try:
        import win32api
        import win32con
        WINDOWS_DIRECT_INPUT = True
    except ImportError:
        print("WARNING: win32api not found. Install with: pip install pywin32")
        print("Using fallback mouse control which may cause beeping sounds.")
        WINDOWS_DIRECT_INPUT = False
else:
    WINDOWS_DIRECT_INPUT = False


def get_side_mouse_button(button_number=1):
    """
    Get the side mouse button in a cross-platform way.
    Windows uses Button.x1/x2, Linux/macOS use Button.button8/button9.
    button_number: 1 for first side button (x1/button8), 2 for second side button (x2/button9)
    """
    try:
        if button_number == 1:
            # Try x1 first (Windows)
            if hasattr(Button, 'x1'):
                return Button.x1
            # Fallback to button8 (Linux/macOS)
            elif hasattr(Button, 'button8'):
                return Button.button8
            else:
                # Last resort: try to get it anyway
                return getattr(Button, 'x1', getattr(Button, 'button8', None))
        else:  # button_number == 2
            # Try x2 first (Windows)
            if hasattr(Button, 'x2'):
                return Button.x2
            # Fallback to button9 (Linux/macOS)
            elif hasattr(Button, 'button9'):
                return Button.button9
            else:
                # Last resort: try to get it anyway
                return getattr(Button, 'x2', getattr(Button, 'button9', None))
    except (AttributeError, TypeError):
        # If all else fails, return None and let the user configure manually
        return None


# ============================================================================
# KEYBIND CONFIGURATION
# ============================================================================
# Edit the values below to customize your keybinds
# ============================================================================

# Enable/disable alternative macro button (second side mouse button)
ENABLE_MACRO_ALT = True  # Set to False to disable the second side mouse button

# Keybind Settings
# You can manually set 'macro' and 'macro_alt' to any button/key you want
# Examples:
#   'macro': Button.x1,        # Windows: first side button
#   'macro': Button.button8,   # Linux/macOS: first side button
#   'macro': Button.middle,    # Middle mouse button
#   'macro': Key.f1,           # F1 key
#   'macro': 'q',              # Q key
# If set to None, will auto-detect based on platform
KEYBINDS = {
    'melee': 'e',                    # Melee attack key
    'jump': Key.space,               # Jump key
    'aim': Button.right,             # Aim button (right mouse)
    'fire': Button.left,             # Fire button (left mouse)
    'emote': '.',                    # Emote key
    'macro': None,                   # Macro trigger: Auto-detects Button.x1 (Windows) or Button.button8 (Linux/macOS)
    'macro_alt': None,               # Alternative macro trigger: Auto-detects Button.x2 (Windows) or Button.button9 (Linux/macOS)
    'rapid_click': 'j',              # Rapid click macro key
}

# Auto-detect side mouse buttons if not manually set
# Windows uses Button.x1/x2, Linux/macOS use Button.button8/button9
if KEYBINDS['macro'] is None:
    try:
        KEYBINDS['macro'] = get_side_mouse_button(1)
        if KEYBINDS['macro'] is None:
            # Fallback: try direct access
            if hasattr(Button, 'x1'):
                KEYBINDS['macro'] = Button.x1  # Windows
            elif hasattr(Button, 'button8'):
                KEYBINDS['macro'] = Button.button8  # Linux/macOS
    except (AttributeError, TypeError):
        # If button8/x1 doesn't exist, try the other
        if hasattr(Button, 'x1'):
            KEYBINDS['macro'] = Button.x1
        elif hasattr(Button, 'button8'):
            KEYBINDS['macro'] = Button.button8

if ENABLE_MACRO_ALT and KEYBINDS['macro_alt'] is None:
    try:
        KEYBINDS['macro_alt'] = get_side_mouse_button(2)
        if KEYBINDS['macro_alt'] is None:
            # Fallback: try direct access
            if hasattr(Button, 'x2'):
                KEYBINDS['macro_alt'] = Button.x2  # Windows
            elif hasattr(Button, 'button9'):
                KEYBINDS['macro_alt'] = Button.button9  # Linux/macOS
    except (AttributeError, TypeError):
        # If button9/x2 doesn't exist, try the other
        if hasattr(Button, 'x2'):
            KEYBINDS['macro_alt'] = Button.x2
        elif hasattr(Button, 'button9'):
            KEYBINDS['macro_alt'] = Button.button9

# ============================================================================
# TIMING CONFIGURATION
# ============================================================================
# Adjust these values to fine-tune the macro timing
# ============================================================================

# --- Game FPS ---
FPS = 115  # Set this to match your in-game FPS for optimal timing

# --- Jump Timing ---
JUMP_DELAY_MS = 1100  # Milliseconds: Delay between jumps (and emote presses)
DOUBLE_JUMP_DELAY = JUMP_DELAY_MS / FPS / 1000  # Calculated: Converted to seconds

# --- Aim & Melee Timing ---
AIM_MELEE_DELAY = 0.025  # Seconds: Delay between pressing aim and pressing melee (lower = faster)
MELEE_HOLD_TIME = 0.050  # Seconds: How long to hold melee key

# --- Emote Cancel Timing ---
# Formula-based: -26 * ln(fps) + 245 (automatically calculated)
# You can override this by setting USE_EMOTE_FORMULA = False and adjusting EMOTE_PREPARATION_DELAY_MANUAL
USE_EMOTE_FORMULA = True  # Set to False to use manual delay instead of formula
EMOTE_PREPARATION_DELAY_MANUAL = 0.100  # Seconds: Manual emote delay (used if USE_EMOTE_FORMULA = False)

if USE_EMOTE_FORMULA:
    _raw_emote_delay = (-26 * math.log(FPS) + 245) / 1000
    EMOTE_PREPARATION_DELAY = max(0, _raw_emote_delay)
    if _raw_emote_delay < 0:
        print(f"WARNING: FPS {FPS} is too high for optimal emote cancel timing. Using minimum delay.")
else:
    EMOTE_PREPARATION_DELAY = EMOTE_PREPARATION_DELAY_MANUAL

# --- Rapid Fire Timing ---
RAPID_FIRE_DURATION_MS = 230  # Milliseconds: Total duration of rapid fire sequence
RAPID_FIRE_CLICK_DELAY = 0.001  # Seconds: Delay between each rapid fire click (lower = faster)

# --- Sequence Loop Timing ---
SEQUENCE_END_DELAY = 0.050  # Seconds: Delay at end of sequence before next loop
LOOP_DELAY = 0.0005  # Seconds: Delay between sequence loops (lower = faster repetition)

# --- Rapid Click Macro Timing ---
RAPID_CLICK_COUNT = 10  # Number: Number of clicks for rapid click macro
RAPID_CLICK_DELAY = 0.05  # Seconds: Delay between rapid clicks

# ============================================================================
# END OF USER CONFIGURATION
# ============================================================================
# Everything below this line is code logic - do not modify unless you know
# what you're doing. All user-configurable settings are above this line.
# ============================================================================

# Global state
running = False
macro_enabled = True
warframe_active = False
rapid_clicking = False
rapid_clicking_lock = threading.Lock()  # Add lock for thread safety

# Controllers
kb = keyboard.Controller()
mouse = mouse.Controller()


def set_high_priority():
    """Set process to high priority to match AHK's ProcessSetPriority("A")."""
    try:
        if sys.platform == "darwin":
            os.nice(10)
        elif sys.platform == "win32":
            import psutil
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS)
    except Exception as e:
        print(f"Failed to set process priority: {e}")


def is_warframe_active():
    """Check if Warframe is the active window."""
    try:
        if sys.platform == "darwin":
            cmd = "lsappinfo info -only name $(lsappinfo front) | awk -F'\"' '{print $4}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return "Warframe" in result.stdout
        elif sys.platform == "win32":
            import win32gui, win32process
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            import psutil
            try:
                proc = psutil.Process(pid)
                return proc.name().lower() == "warframe.x64.exe"
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                return False
        return True
    except Exception:
        return True


def background_app_check():
    """Monitor the active application in a background thread."""
    global running, warframe_active
    
    while True:
        current_state = is_warframe_active()
        
        if not current_state and running:
            running = False
            print("Warframe window lost focus - macro stopped")
        
        warframe_active = current_state
        time.sleep(1)


def start_background_check():
    """Start background monitoring of Warframe window state."""
    check_thread = threading.Thread(target=background_app_check)
    check_thread.daemon = True
    check_thread.start()


def precise_sleep(seconds):
    """High-precision sleep function matching AHK's lSleep function."""
    if seconds <= 0:
        return
        
    seconds_ms = seconds * 1000
    start_time = time.time()
    
    # For longer sleeps, use regular sleep with overhead compensation
    if seconds_ms > 40:
        compensation_time = seconds - 0.020
        if compensation_time > 0:
            time.sleep(compensation_time)
    
    # Busy-wait for the remaining time
    end_time = start_time + seconds
    while time.time() < end_time:
        pass


def press_key(key):
    """Press and release a keyboard key."""
    if not running:
        return
    
    # Convert string keys to KeyCode objects
    if isinstance(key, str):
        key = KeyCode.from_char(key)
    
    kb.press(key)
    kb.release(key)


def click_mouse(button):
    """Press and release a mouse button."""
    with rapid_clicking_lock:
        if not running and not rapid_clicking:
            return
    mouse.press(button)
    mouse.release(button)


def execute_contagion_sequence():
    """Execute one complete Exodia Contagion sequence."""
    if not running:
        return
        
    # Double jump
    print("Executing double jump...")
    press_key(KEYBINDS['jump'])
    precise_sleep(DOUBLE_JUMP_DELAY)
    
    press_key(KEYBINDS['jump'])
    precise_sleep(DOUBLE_JUMP_DELAY)
    
    # Aim and melee
    print("Pressing aim...")
    mouse.press(KEYBINDS['aim'])
    precise_sleep(AIM_MELEE_DELAY)
    
    print("Pressing melee...")
    press_key(KEYBINDS['melee'])
    precise_sleep(MELEE_HOLD_TIME)
    
    print("Releasing aim...")
    mouse.release(KEYBINDS['aim'])
    
    # Emote cancel
    precise_sleep(EMOTE_PREPARATION_DELAY)
    
    press_key(KEYBINDS['emote'])
    precise_sleep(DOUBLE_JUMP_DELAY)
    
    press_key(KEYBINDS['emote'])
    precise_sleep(DOUBLE_JUMP_DELAY)
    
    # Rapid fire
    start_time = time.time()
    
    if not running:
        return
    
    while True:
        click_mouse(KEYBINDS['fire'])
        precise_sleep(RAPID_FIRE_CLICK_DELAY)
        
        if not running:
            break
            
        current_time = time.time()
        elapsed_ms = (current_time - start_time) * 1000
        
        if elapsed_ms > RAPID_FIRE_DURATION_MS:
            break
    
    # End-of-sequence delay
    if running:
        precise_sleep(SEQUENCE_END_DELAY)


def contagion_loop():
    """Main loop that executes contagion sequences while key is held."""
    global running
    
    try:
        while running:
            execute_contagion_sequence()
            precise_sleep(LOOP_DELAY)
    finally:
        kb.release(KEYBINDS['melee'])
        kb.release(KEYBINDS['emote'])
        mouse.release(KEYBINDS['aim'])
        mouse.release(KEYBINDS['fire'])


def execute_rapid_click():
    """Execute 10 rapid left mouse clicks."""
    global rapid_clicking
    
    with rapid_clicking_lock:
        rapid_clicking = True
    
    # Use Windows-specific direct input to avoid beeping sounds
    if sys.platform == "win32" and WINDOWS_DIRECT_INPUT:
        for i in range(RAPID_CLICK_COUNT):
            if not macro_enabled:
                break
                
            # Use Windows API directly to avoid beeping
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.01)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            precise_sleep(RAPID_CLICK_DELAY)
    else:
        # Use pynput for other platforms
        for i in range(RAPID_CLICK_COUNT):
            if not macro_enabled:
                break
                
            mouse.press(KEYBINDS['fire'])
            time.sleep(0.01)
            mouse.release(KEYBINDS['fire'])
            precise_sleep(RAPID_CLICK_DELAY)
    
    with rapid_clicking_lock:
        rapid_clicking = False


def rapid_click_thread():
    """Thread function for the rapid click macro."""
    global rapid_clicking
    
    try:
        execute_rapid_click()
    finally:
        # Ensure mouse button is released and state is reset
        mouse.release(KEYBINDS['fire'])
        with rapid_clicking_lock:
            rapid_clicking = False


def on_press(key):
    """Handle keyboard press events."""
    global running, macro_enabled, warframe_active
    
    try:
        warframe_active = is_warframe_active()
        if not warframe_active:
            return
            
        # Check for rapid click macro key (keyboard only)
        rapid_click_key_matches = (
            (isinstance(KEYBINDS['rapid_click'], str) and key == KeyCode.from_char(KEYBINDS['rapid_click']))
        )
        
        if rapid_click_key_matches and macro_enabled:
            # Start rapid click thread
            click_thread = threading.Thread(target=rapid_click_thread)
            click_thread.daemon = True
            click_thread.start()
        elif key == Key.f11:
            macro_enabled = not macro_enabled
            print(f"Macro {'enabled' if macro_enabled else 'disabled'}")
    except AttributeError:
        pass


def on_release(key):
    """Handle keyboard release events."""
    global running, warframe_active
    
    try:
        warframe_active = is_warframe_active()
        if not warframe_active:
            if running:
                running = False
            return
    except AttributeError:
        pass


def on_click(x, y, button, pressed):
    """Handle mouse click events."""
    global running, macro_enabled, warframe_active
    
    try:
        warframe_active = is_warframe_active()
        if not warframe_active:
            return
            
        # Check for contagion macro key (mouse button)
        # Check for contagion macro key (side mouse buttons)
        macro_button = KEYBINDS.get('macro')
        macro_alt_button = KEYBINDS.get('macro_alt')
        if button == macro_button or (ENABLE_MACRO_ALT and macro_alt_button and button == macro_alt_button):
            if pressed and not running and macro_enabled:
                running = True
                thread = threading.Thread(target=contagion_loop)
                thread.daemon = True
                thread.start()
            elif not pressed and running:
                running = False
    except AttributeError:
        pass


def cleanup_and_exit(signum=None, frame=None):
    """Clean up resources and exit gracefully."""
    global running
    running = False
    print("\n\nShutting down macro...")
    print("Goodbye!")
    sys.exit(0)


def main():
    """Main program entry point."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup_and_exit)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, cleanup_and_exit)
    
    try:
        set_high_priority()
        
        # Platform-specific messages
        platform_name = {
            "darwin": "macOS",
            "win32": "Windows",
            "linux": "Linux"
        }.get(sys.platform, sys.platform)
        
        print(f"=== Exodia Contagion Macro for Warframe ({platform_name}) ===")
        print("\nKEY SETTINGS:")
        print(f"  - Hold side mouse button (x1 or x2) to activate the contagion sequence")
        print(f"  - Press '{KEYBINDS['rapid_click']}' to perform {RAPID_CLICK_COUNT} rapid clicks")
        print("  - Press F11 to toggle all macros on/off")
        print(f"\nDEBUG INFO:")
        print(f"  - Melee key: '{KEYBINDS['melee']}'")
        print(f"  - Jump key: {KEYBINDS['jump']}")
        print(f"  - Aim button: {KEYBINDS['aim']}")
        print(f"  - Fire button: {KEYBINDS['fire']}")
        print(f"  - Emote key: '{KEYBINDS['emote']}'")
        print("\nPress Ctrl+C to exit\n")
        
        start_background_check()
        print("Starting macro listener...")
        with keyboard.Listener(on_press=on_press, on_release=on_release) as kb_listener, \
             MouseListener(on_click=on_click) as mouse_listener:
            kb_listener.join()
            mouse_listener.join()
    except KeyboardInterrupt:
        cleanup_and_exit()
    except Exception as e:
        print(f"\nError: {e}")
        cleanup_and_exit()


if __name__ == "__main__":
    main() 