# Exodia Contagion Macro for Warframe

A cross-platform Python macro automation tool for Warframe's Exodia Contagion combo. Works on macOS, Windows, and Linux.

**Made by Spacii-AN**

## Features

- **Exodia Contagion Sequence**: Automated execution of the complete combo sequence
- **Hold-to-Activate**: Macro only runs while the side mouse button is held down
- **Rapid Click Macro**: Quick 10-click burst function
- **Cross-Platform**: Supports macOS, Windows, and Linux
- **Window Detection**: Automatically stops when Warframe loses focus
- **Configurable**: Easy-to-modify keybinds and timing settings
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

1. Clone or download this repository:
   ```bash
   git clone <repository-url>
   cd PTmacro
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Configuration

### Warframe Settings
**IMPORTANT**: Before using the macro, ensure this setting is OFF in Warframe:
- `Melee with Fire Weapon Input` → **OFF**

### Keybinds
Edit the `KEYBINDS` dictionary in `5th_try.py` to customize controls:

```python
KEYBINDS = {
    'melee': 'e',                    # Melee attack key
    'jump': Key.space,               # Jump key
    'aim': Button.right,             # Aim button (right mouse)
    'fire': Button.left,             # Fire button (left mouse)
    'emote': '.',                    # Emote key
    'macro': Button.button8,         # Side mouse button (x1)
    'macro_alt': Button.button9,     # Alternative side button (x2)
    'rapid_click': 'j',              # Rapid click macro key
}
```

### FPS Settings
Adjust the `FPS` variable to match your Warframe FPS for optimal timing:
```python
FPS = 115  # Change to match your in-game FPS
```

## Usage

### Running the Script

**Option 1: Direct execution**
```bash
python 5th_try.py
```

**Option 2: Using the run script (Linux/macOS)**
```bash
./run.sh
```

**Option 3: Using virtual environment**
```bash
./venv/bin/python 5th_try.py
```

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
- Adjust the `FPS` variable to match your actual in-game FPS
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
├── 5th_try.py          # Main macro script
├── requirements.txt    # Python dependencies
├── run.sh             # Convenience run script (Linux/macOS)
├── venv/              # Virtual environment (if created)
└── README.md          # This file
```

## Technical Details

- **Precision Timing**: Uses high-precision sleep functions for consistent execution
- **Thread Safety**: Proper locking mechanisms for concurrent operations
- **Process Priority**: Attempts to set high priority for better performance
- **Window Detection**: Platform-specific methods to detect active Warframe window
- **Button State Tracking**: Real-time monitoring of button press/release states

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


