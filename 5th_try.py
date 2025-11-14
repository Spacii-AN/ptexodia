#!/usr/bin/env python3
"""
Exodia Contagion Macro for Warframe (macOS, Windows, and Linux version)
Made by Spacii-AN

IMPORTANT:
- Ensure "Melee with Fire Weapon Input" setting is OFF in Warframe
- This script requires accessibility permissions on macOS
- On Linux, may require xdotool or wmctrl for window detection (optional)
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


# Configuration
KEYBINDS = {
    'melee': 'e',
    'jump': Key.space,
    'aim': Button.right,
    'fire': Button.left,
    'emote': '.',
    'macro': Button.button8,  # Side mouse button (x1) - first side button
    'macro_alt': Button.button9,  # Alternative side mouse button (x2) - second side button
    'rapid_click': 'j',  # New keybind for rapid click macro
}

FPS = 115

# Timing calculations (milliseconds converted to seconds for Python)
DOUBLE_JUMP_DELAY = 1100 / FPS / 1000
AIM_MELEE_DELAY = 0.025  # Faster delay for quicker melee

# Emote cancel timing based on FPS formula: -26 * ln(fps) + 245
_raw_emote_delay = (-26 * math.log(FPS) + 245) / 1000
EMOTE_PREPARATION_DELAY = max(0, _raw_emote_delay)
if _raw_emote_delay < 0:
    print(f"WARNING: FPS {FPS} is too high for optimal emote cancel timing. Using minimum delay.")

# Add rapid click configuration
RAPID_CLICK_COUNT = 10
RAPID_CLICK_DELAY = 0.05

# Global state
running = False
button_held = False  # Track if macro button is currently held
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
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS)
        elif sys.platform == "linux":
            # Linux: use nice to increase priority (negative values = higher priority)
            # Note: May require root or proper permissions
            try:
                os.nice(-10)
            except PermissionError:
                # If we can't set high priority, try at least normal priority
                try:
                    os.nice(0)
                except Exception:
                    pass
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
            
            try:
                proc = psutil.Process(pid)
                return proc.name().lower() == "warframe.x64.exe"
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                return False
        elif sys.platform == "linux":
            # Try xdotool first (most common on X11)
            try:
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True,
                    text=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    window_name = result.stdout.strip().lower()
                    return "warframe" in window_name
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
            
            # Try wmctrl as fallback
            try:
                result = subprocess.run(
                    ["wmctrl", "-l"],
                    capture_output=True,
                    text=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    # Find active window (marked with *)
                    for line in result.stdout.split('\n'):
                        if '*' in line and 'warframe' in line.lower():
                            return True
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
            
            # Fallback: check if Warframe process is running
            # This is less accurate but works without window manager tools
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        proc_name = proc.info['name'].lower()
                        if 'warframe' in proc_name or 'warframe.x64' in proc_name:
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            except Exception:
                pass
            
            # If we can't determine, assume Warframe is active (safer for macro)
            return True
        return True
    except Exception:
        return True


def background_app_check():
    """Monitor the active application in a background thread."""
    global running, button_held, warframe_active
    
    while True:
        current_state = is_warframe_active()
        
        if not current_state and running:
            running = False
            button_held = False
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
    if not running or not button_held:
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
    if not running or not button_held:
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
    precise_sleep(0.050)  # Faster melee hold time
    
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
    
    if not running or not button_held:
        return
    
    while True:
        if not running or not button_held:
            break
        click_mouse(KEYBINDS['fire'])
        precise_sleep(0.001)
        
        if not running or not button_held:
            break
            
        current_time = time.time()
        elapsed_ms = (current_time - start_time) * 1000
        
        if elapsed_ms > 230:
            break
    
    # End-of-sequence delay
    if running and button_held:
        precise_sleep(0.050)


def contagion_loop():
    """Main loop that executes contagion sequences while key is held."""
    global running, button_held
    
    try:
        while running and button_held:
            execute_contagion_sequence()
            # Check button state more frequently
            if not button_held:
                break
            precise_sleep(0.0005)
    finally:
        running = False
        button_held = False
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
    global running, button_held, macro_enabled, warframe_active
    
    try:
        warframe_active = is_warframe_active()
        if not warframe_active:
            return
            
        # Check for contagion macro key (side mouse buttons)
        if button == KEYBINDS['macro'] or button == KEYBINDS['macro_alt']:
            if pressed and not running and macro_enabled:
                button_held = True
                running = True
                thread = threading.Thread(target=contagion_loop)
                thread.daemon = True
                thread.start()
            elif not pressed:
                # Immediately stop when button is released
                button_held = False
                running = False
    except AttributeError:
        pass


def main():
    """Main program entry point."""
    set_high_priority()
    
    # Platform-specific messages
    platform_name = {
        "darwin": "macOS",
        "win32": "Windows",
        "linux": "Linux"
    }.get(sys.platform, sys.platform)
    
    print(f"=== Exodia Contagion Macro for Warframe ({platform_name}) ===")
    
    if sys.platform == "linux":
        print("\nNOTE: For better window detection on Linux, consider installing:")
        print("  - xdotool: sudo apt install xdotool (or equivalent)")
        print("  - wmctrl: sudo apt install wmctrl (or equivalent)")
        print("  (The macro will still work without these, using process detection)")
    
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
    
    start_background_check()
    print("Starting macro listener...")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as kb_listener, \
         MouseListener(on_click=on_click) as mouse_listener:
        kb_listener.join()
        mouse_listener.join()


if __name__ == "__main__":
    main() 