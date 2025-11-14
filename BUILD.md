# Building Executables

This guide explains how to build standalone executables for the macro.

## Automatic Builds (GitHub Actions)

Executables are automatically built for all platforms when you:
- Create a git tag (e.g., `v1.0.0`)
- Push the tag: `git push origin v1.0.0`
- GitHub Actions will build and create a release with executables

## Manual Building

### Prerequisites

Install PyInstaller:
```bash
pip install pyinstaller
```

### Build Commands

**Windows:**
```bash
pyinstaller --onefile --windowed --name pt-macro --add-data "requirements.txt;." pt-macro.py
```

**macOS/Linux:**
```bash
pyinstaller --onefile --name pt-macro --add-data "requirements.txt:." pt-macro.py
```

The executable will be in the `dist/` folder.

### Using the spec file

You can also use the provided `pyinstaller.spec` file:
```bash
pyinstaller pyinstaller.spec
```

## Notes

- The executable is standalone and includes all dependencies
- First run may take a moment to extract files
- Windows may show a security warning (normal for unsigned executables)
- macOS/Linux may require execution permissions: `chmod +x pt-macro`

