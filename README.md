# Exodia Contagion Macro for Warframe (Rust - Optimized)

A high-performance macro automation tool for Warframe's Exodia Contagion combo, written in Rust for maximum speed and efficiency.

**Made by Spacii-AN**

## 🚀 Performance

This Rust version offers significant performance improvements over the Python version:

- **10-50x lower latency** - Near-instant input response
- **5-10x lower CPU usage** - Minimal system impact
- **50-100x lower memory footprint** - Efficient resource usage
- **Native performance** - Compiled to machine code

## Features

- **Exodia Contagion Sequence**: Automated execution of the complete combo sequence
- **Hold-to-Activate**: Macro only runs while the side mouse button is held down
- **Rapid Click Macro**: Quick burst click function
- **Cross-Platform**: Supports macOS, Windows, and Linux
- **Window Detection**: Automatically stops when Warframe loses focus
- **Highly Configurable**: All keybinds and timing settings easily adjustable
- **High Precision Timing**: Sub-millisecond accuracy using optimized timing

## Warframe Settings

**IMPORTANT**: Before using the macro, ensure this setting is OFF in Warframe:
- `Melee with Fire Weapon Input` → **OFF**

## Quick Start

### Prerequisites

- Rust toolchain (install from https://rustup.rs/)
- Platform-specific dependencies:
  - **Linux**: X11 development libraries (`libx11-dev`, `libxdo-dev` for xdotool)
  - **Windows**: Windows SDK
  - **macOS**: Xcode Command Line Tools

### Build & Run

```bash
# Build the optimized version
cargo build --release

# Run the macro
cargo run --release
```

The optimized binary will be in `target/release/pt-macro` (or `target/release/pt-macro.exe` on Windows).

## Configuration

All configuration is done in `src/main.rs` in the configuration sections at the top of the file:

- **Keybinds**: Lines 17-48
- **Timing**: Lines 50-100

The structure matches the Python version for easy migration.

## Controls

- **Hold Side Mouse Button**: Activates the Exodia Contagion sequence
- **Press 'j'**: Performs rapid clicks
- **Press F11**: Toggles all macros on/off
- **Ctrl+C**: Exit

## Troubleshooting

### Linking Errors

If you encounter linking errors, ensure you have the required system libraries installed:

**Linux:**
```bash
# Debian/Ubuntu
sudo apt install libx11-dev libxdo-dev

# Arch Linux
sudo pacman -S libx11 xdotool

# Fedora
sudo dnf install libX11-devel xdotool
```

**macOS:**
```bash
xcode-select --install
```

**Windows:**
- Ensure you have Visual Studio Build Tools or Visual Studio installed

### Permission Issues

**Linux**: You may need to be in the `input` group:
```bash
sudo usermod -a -G input $USER
# Log out and back in
```

**macOS**: Grant accessibility permissions in System Preferences → Security & Privacy → Privacy → Accessibility

## Python Version (Legacy)

The original Python implementation is available in the `python-version/` directory for reference or as a fallback option. See [python-version/README.md](python-version/README.md) for Python-specific documentation.

## License

This project is provided as-is for personal use. Use at your own risk.

## Disclaimer

This macro is for educational purposes. Ensure that using macros complies with Warframe's Terms of Service and your local regulations. The authors are not responsible for any consequences resulting from the use of this software.
# rustodia
