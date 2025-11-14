# Exodia Contagion Macro for Warframe

A cross-platform Python macro automation tool for Warframe's Exodia Contagion combo. Works on macOS, Windows, and Linux.

**Made by Spacii-AN**

## Features

- **Exodia Contagion Sequence**: Automated execution of the complete combo sequence
- **Hold-to-Activate**: Macro only runs while the side mouse button is held down
- **Rapid Click Macro**: Quick 10-click burst function
- **Cross-Platform**: Supports macOS, Windows, and Linux
- **Window Detection**: Automatically stops when Warframe loses focus
- **Highly Configurable**: All keybinds and timing settings organized in dedicated sections for easy fine-tuning
- **High Precision**: Optimized timing for consistent execution

## Requirements

### Python
- Python 3.6 or higher

### Dependencies
Install dependencies using pip:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pynput>=1.7.6 psutil>=5.9.0
```

### Platform-Specific Requirements

#### Windows
- `pywin32` (optional, but recommended to suppress beeping sounds):
  ```bash
  pip install pywin32
  ```

#### macOS
- Accessibility permissions must be granted to Terminal/Python
- Go to: System Preferences → Security & Privacy → Privacy → Accessibility

#### Linux
- Optional tools for better window detection:
  ```bash
  # Debian/Ubuntu
  sudo apt install xdotool wmctrl
  
  # Arch Linux
  sudo pacman -S xdotool wmctrl
  
  # Fedora
  sudo dnf install xdotool wmctrl
  ```
  *Note: The macro will still work without these tools using process detection*

## Installation

### Easy Installation (Recommended)

**For Windows:**
1. Download or clone this repository
2. Double-click `launch.bat`
3. The script will automatically install dependencies and start the macro

**For macOS:**
1. Download or clone this repository
2. Double-click `launch.command`
3. The script will automatically install dependencies and start the macro

**For Linux:**
1. Download or clone this repository
2. Right-click `launch.sh` → Properties → Permissions → Check "Execute"
3. Or run: `chmod +x launch.sh`
4. Double-click `launch.sh` or run: `./launch.sh`
5. The script will automatically install dependencies and start the macro

### Manual Installation

If you prefer to install manually:

1. Clone or download this repository:
   ```bash
   git clone https://github.com/Spacii-AN/ptexodia
   cd PTmacro
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Create a virtual environment for isolated dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
   *Note: The launcher scripts automatically handle virtual environments, so this step is optional.*

## Configuration

### Warframe Settings
**IMPORTANT**: Before using the macro, ensure this setting is OFF in Warframe:
- `Melee with Fire Weapon Input` → **OFF**

### Keybinds
Edit the `KEYBINDS` dictionary in `pt-macro.py` (lines 79-89) to customize controls:

```python
# Enable/disable alternative macro button (line 77)
ENABLE_MACRO_ALT = True  # Set to False to disable second side mouse button

KEYBINDS = {
    'melee': 'e',                    # Melee attack key
    'jump': Key.space,               # Jump key
    'aim': Button.right,             # Aim button (right mouse)
    'fire': Button.left,             # Fire button (left mouse)
    'emote': '.',                    # Emote key
    'macro': None,                   # Auto-detects: Button.x1 (Windows) or Button.button8 (Linux/macOS)
    'macro_alt': None,               # Auto-detects: Button.x2 (Windows) or Button.button9 (Linux/macOS)
    'rapid_click': 'j',              # Rapid click macro key
}
```

**Important Note on Side Mouse Buttons:**
- **Windows**: Uses `Button.x1` and `Button.x2` for side mouse buttons
- **Linux/macOS**: Uses `Button.button8` and `Button.button9` for side mouse buttons
- The macro **automatically detects** the correct button for your platform
- You can **manually override** by setting `'macro'` and `'macro_alt'` to any button/key you want (see examples below)

#### Disabling Alternative Macro Button
If you only want to use one side mouse button, set `ENABLE_MACRO_ALT = False` on line 77. This will disable the second side mouse button (x2/button9) from triggering the macro.

#### Changing the Macro Button

You can easily change the macro button by editing the `'macro'` value in `KEYBINDS`. Here are examples:

**Side Mouse Buttons (Platform-Specific):**
```python
# Windows
'macro': Button.x1,        # First side button (x1)
'macro': Button.x2,       # Second side button (x2)

# Linux/macOS
'macro': Button.button8,  # First side button (button8)
'macro': Button.button9,  # Second side button (button9)
```

**Other Mouse Buttons:**
```python
'macro': Button.middle,   # Middle mouse button (scroll wheel click)
'macro': Button.right,   # Right mouse button (not recommended - conflicts with aim)
```

**Keyboard Keys:**
```python
'macro': Key.f1,         # Function keys (F1-F12)
'macro': Key.f2,
'macro': Key.ctrl,       # Control key
'macro': Key.shift,      # Shift key
'macro': 'q',            # Letter keys (make sure they don't conflict with game controls)
'macro': 'z',
```

**Examples:**
```python
# Use middle mouse button instead of side button
'macro': Button.middle,

# Use F1 key instead
'macro': Key.f1,

# Use Q key instead
'macro': 'q',
```

> **Note**: If you set `'macro'` to `None`, it will auto-detect the correct side mouse button for your platform (Button.x1 on Windows, Button.button8 on Linux/macOS).

> **Note**: For a complete list of all available buttons and keys, see [BUTTON_REFERENCE.md](BUTTON_REFERENCE.md)

### Fine-Tuning the Macro

All timing values are now organized in a dedicated **TIMING CONFIGURATION** section (lines 70-109) for easy adjustment. Here's what each setting does:

#### Game FPS (Line 75)
```python
FPS = 115  # Set this to match your in-game FPS
```
- **What it does**: Base FPS value used for automatic timing calculations
- **When to adjust**: If your game runs at a different FPS than 115

#### Jump Timing (Lines 78-79)
```python
JUMP_DELAY_MS = 1100  # Milliseconds between jumps
DOUBLE_JUMP_DELAY = JUMP_DELAY_MS / FPS / 1000
```
- **What it does**: Controls delay between double jumps and emote presses
- **When to adjust**: If jumps feel too fast/slow, or emote timing is off
- **Lower value** = faster jumps, **Higher value** = slower jumps

#### Aim & Melee Timing (Lines 82-83)
```python
AIM_MELEE_DELAY = 0.025  # Delay between aim and melee (seconds)
MELEE_HOLD_TIME = 0.050  # How long to hold melee (seconds)
```
- **AIM_MELEE_DELAY**: Time between pressing aim and pressing melee
  - **Lower** = faster melee activation
  - **Higher** = more delay before melee
- **MELEE_HOLD_TIME**: Duration melee key is held down
  - **Lower** = shorter melee press
  - **Higher** = longer melee press

#### Emote Cancel Timing (Lines 85-97)
```python
USE_EMOTE_FORMULA = True  # Use formula or manual delay
EMOTE_PREPARATION_DELAY_MANUAL = 0.100  # Manual delay (if formula disabled)
```
- **Formula-based** (default): Automatically calculates optimal delay based on FPS
- **Manual mode**: Set `USE_EMOTE_FORMULA = False` and adjust `EMOTE_PREPARATION_DELAY_MANUAL`
- **When to adjust**: If emote cancel isn't working properly

#### Rapid Fire Timing (Lines 100-101)
```python
RAPID_FIRE_DURATION_MS = 230  # Total rapid fire duration (milliseconds)
RAPID_FIRE_CLICK_DELAY = 0.001  # Delay between shots (seconds)
```
- **RAPID_FIRE_DURATION_MS**: How long the rapid fire sequence lasts
  - **Lower** = shorter burst
  - **Higher** = longer burst
- **RAPID_FIRE_CLICK_DELAY**: Time between each shot
  - **Lower** = faster firing rate
  - **Higher** = slower firing rate

#### Sequence Loop Timing (Lines 104-105)
```python
SEQUENCE_END_DELAY = 0.050  # Delay at end of sequence (seconds)
LOOP_DELAY = 0.0005  # Delay between sequence loops (seconds)
```
- **SEQUENCE_END_DELAY**: Pause after completing one full sequence
- **LOOP_DELAY**: Delay before starting the next sequence
  - **Lower** = faster repetition
  - **Higher** = slower repetition

#### Rapid Click Macro (Lines 108-109)
```python
RAPID_CLICK_COUNT = 10  # Number of clicks
RAPID_CLICK_DELAY = 0.05  # Delay between clicks (seconds)
```
- **RAPID_CLICK_COUNT**: How many clicks to perform
- **RAPID_CLICK_DELAY**: Time between each click

### Quick Reference: Most Common Adjustments

| Issue | Line to Edit | What to Change |
|-------|-------------|----------------|
| Macro too fast/slow overall | 75 | Adjust `FPS` to match your game |
| Jumps feel off | 78 | Adjust `JUMP_DELAY_MS` (in milliseconds) |
| Melee not activating properly | 82 | Adjust `AIM_MELEE_DELAY` (lower = faster) |
| Melee held too long/short | 83 | Adjust `MELEE_HOLD_TIME` |
| Emote cancel not working | 88-89 | Set `USE_EMOTE_FORMULA = False` and adjust `EMOTE_PREPARATION_DELAY_MANUAL` |
| Rapid fire too short/long | 100 | Adjust `RAPID_FIRE_DURATION_MS` |
| Rapid fire too fast/slow | 101 | Adjust `RAPID_FIRE_CLICK_DELAY` |
| Sequences repeating too fast | 105 | Increase `LOOP_DELAY` |

## Usage

### Running the Script

**Option 1: Using the launcher (Easiest - Recommended)**
- **Windows**: Double-click `launch.bat`
- **macOS**: Double-click `launch.command`
- **Linux**: Double-click `launch.sh` or run `./launch.sh`

The launcher will automatically:
- Check for Python installation
- Create a virtual environment (if needed)
- Install/update all dependencies
- Start the macro

**Option 2: Direct execution**
```bash
python pt-macro.py
```

**Option 3: Using virtual environment (if you created one manually)**
```bash
./venv/bin/python pt-macro.py  # Linux/macOS
venv\Scripts\python pt-macro.py  # Windows
```
*Note: The launcher scripts automatically create and use a virtual environment, so this is only needed if you created one manually.*

### Controls

- **Hold Side Mouse Button (x1 or x2)**: Activates the Exodia Contagion sequence
  - The macro runs continuously while the button is held
  - Releases immediately when you let go of the button
  
- **Press 'j'**: Performs 10 rapid left mouse clicks

- **Press F11**: Toggles all macros on/off

### How It Works

The Exodia Contagion sequence executes:
1. Double jump
2. Aim + Melee attack
3. Emote cancel (timing based on FPS)
4. Rapid fire sequence

The macro automatically stops if:
- You release the side mouse button
- Warframe window loses focus
- You toggle macros off with F11

## Troubleshooting

### Macro doesn't start
- Ensure Warframe is the active/focused window
- Check that "Melee with Fire Weapon Input" is OFF in Warframe settings
- Verify you have the required permissions (macOS accessibility, Linux input device access)

### Macro runs but timing is off
- Adjust the `FPS` variable (line 75) to match your actual in-game FPS
- Fine-tune individual timing values in the **TIMING CONFIGURATION** section (lines 70-109)
- See the "Fine-Tuning the Macro" section above for detailed timing adjustments
- Check that your system can handle the precision timing

### Permission errors (Linux)
- You may need to be in the `input` group:
  ```bash
  sudo usermod -a -G input $USER
  ```
  (Log out and back in for changes to take effect)

### Beeping sounds (Windows)
- Install `pywin32` to use direct input and suppress beeping:
  ```bash
  pip install pywin32
  ```

### Window detection not working (Linux)
- Install `xdotool` or `wmctrl` for better window detection
- The macro will still work using process detection as a fallback

## Project Structure

```
PTmacro/
├── pt-macro.py         # Main macro script
├── requirements.txt    # Python dependencies
├── launch.bat          # Windows launcher (double-click to run)
├── launch.sh           # Linux launcher (double-click or ./launch.sh)
├── launch.command      # macOS launcher (double-click to run)
├── BUTTON_REFERENCE.md # Complete reference of all available buttons and keys
└── README.md          # This file
```

*Note: The launcher scripts automatically create a virtual environment (venv/) when needed, but it's not included in the repository.*

## Technical Details

- **Precision Timing**: Uses high-precision sleep functions for consistent execution
- **Thread Safety**: Proper locking mechanisms for concurrent operations
- **Process Priority**: Attempts to set high priority for better performance
- **Window Detection**: Platform-specific methods to detect active Warframe window
- **Button State Tracking**: Real-time monitoring of button press/release states
- **Cross-Platform Button Support**: Automatically detects and uses correct side mouse button names
  - Windows: Uses `Button.x1` and `Button.x2` for side mouse buttons
  - Linux/macOS: Uses `Button.button8` and `Button.button9` for side mouse buttons
  - Fully configurable - you can override with any button or key you prefer
- **Organized Configuration**: All keybinds and timing values are clearly organized in dedicated sections at the top of the file
- **Graceful Shutdown**: Proper signal handling for clean exit with Ctrl+C

## License

This project is provided as-is for personal use. Use at your own risk.

## Disclaimer

This macro is for educational purposes. Ensure that using macros complies with Warframe's Terms of Service and your local regulations. The authors are not responsible for any consequences resulting from the use of this software.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Credits

- **Author**: Spacii-AN
- **Platform Support**: macOS, Windows, Linux

# ptexodia


