# Build Instructions for BMS Monitor App V2

This guide explains how to build standalone executables for Windows, Linux, and macOS.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Building Locally](#building-locally)
  - [Windows Build](#windows-build)
  - [Linux Build](#linux-build)
  - [macOS Build](#macos-build)
- [Build Options](#build-options)
- [GitHub Actions (Automated Cross-Platform Builds)](#github-actions-automated-cross-platform-builds)
- [Troubleshooting](#troubleshooting)
- [Output Files](#output-files)

---

## Quick Start

```bash
# Install dependencies
pip install pyinstaller

# Build for current platform
python build.py --platform all

# Output will be in dist/ folder
```

---

## Prerequisites

### All Platforms

1. **Python 3.8+** installed
2. **Project dependencies** installed:
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or using uv
   uv sync
   ```

3. **PyInstaller** installed:
   ```bash
   pip install pyinstaller>=6.0.0
   ```

### Platform-Specific Requirements

| Platform | Additional Requirements |
|----------|------------------------|
| Windows  | None (just Python) |
| Linux    | `sudo apt install python3-dev` (Debian/Ubuntu) |
| macOS    | Xcode Command Line Tools: `xcode-select --install` |

---

## Building Locally

> ⚠️ **Important:** PyInstaller cannot cross-compile. You must build on the target platform.
> - To create Windows `.exe` → Build on Windows
> - To create Linux binary → Build on Linux
> - To create macOS `.app` → Build on macOS

### Windows Build

```powershell
# Open PowerShell or Command Prompt

# Navigate to project directory
cd path\to\BMSMonitorAppV2

# Activate virtual environment (if using)
.\.venv\Scripts\activate

# Install PyInstaller
pip install pyinstaller

# Build
python build.py --platform windows

# Output: dist\BMSMonitorApp.exe
```

### Linux Build

```bash
# Navigate to project directory
cd /path/to/BMSMonitorAppV2

# Activate virtual environment (if using)
source .venv/bin/activate

# Install PyInstaller
pip install pyinstaller

# Build
python build.py --platform linux

# Output: dist/BMSMonitorApp

# Make executable (if needed)
chmod +x dist/BMSMonitorApp
```

### macOS Build

```bash
# Navigate to project directory
cd /path/to/BMSMonitorAppV2

# Activate virtual environment (if using)
source .venv/bin/activate

# Install PyInstaller
pip install pyinstaller

# Build
python build.py --platform mac

# Output: dist/BMSMonitorApp.app
```

---

## Build Options

| Option | Description | Example |
|--------|-------------|---------|
| `--platform` | Target platform: `windows`, `linux`, `mac`, `all` | `--platform linux` |
| `--onefile` | Single executable (default) | `--onefile` |
| `--onedir` | Directory with dependencies | `--onedir` |
| `--console` | Show console window (debugging) | `--console` |
| `--clean` | Clean before building | `--clean` |
| `--name` | Custom executable name | `--name MyApp` |
| `--clean-only` | Only clean, don't build | `--clean-only` |

### Examples

```bash
# Build with custom name
python build.py --platform windows --name "BMS_Monitor_V2"

# Clean build with console (for debugging)
python build.py --clean --platform linux --console

# Build as directory (faster startup, easier to debug)
python build.py --platform windows --onedir

# Just clean build artifacts
python build.py --clean-only
```

---

## GitHub Actions (Automated Cross-Platform Builds)

For automated builds on all platforms, add this workflow file to your repository:

### Setup

1. Create `.github/workflows/build.yml` in your repository
2. Push to GitHub
3. Go to **Actions** tab → **Run workflow** or push a tag

### Workflow File

Create `.github/workflows/build.yml`:

```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'  # Trigger on version tags like v1.0.0
  workflow_dispatch:  # Manual trigger

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: windows-latest
            platform: windows
            artifact: BMSMonitorApp.exe
          - os: ubuntu-latest
            platform: linux
            artifact: BMSMonitorApp
          - os: macos-latest
            platform: mac
            artifact: BMSMonitorApp.app

    runs-on: ${{ matrix.os }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pyinstaller
          pip install PyQt6 PyQt6-WebEngine pyserial pandas numpy plotly

      - name: Build executable
        run: python build.py --platform ${{ matrix.platform }}

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: BMSMonitorApp-${{ matrix.platform }}
          path: dist/${{ matrix.artifact }}

  release:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            BMSMonitorApp-windows/BMSMonitorApp.exe
            BMSMonitorApp-linux/BMSMonitorApp
            BMSMonitorApp-macos/BMSMonitorApp.app
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Using GitHub Actions

1. **Manual Build:**
   - Go to your repo → **Actions** → **Build Executables**
   - Click **Run workflow**

2. **Automatic Release:**
   ```bash
   git tag v2.0.0
   git push origin v2.0.0
   ```
   This creates a release with all platform builds attached.

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError" during build

Add hidden imports in `build.py`:
```python
hidden_imports = [
    "your_missing_module",
]
```

#### 2. PyQt6 WebEngine issues on Linux

```bash
# Install system dependencies
sudo apt install libxcb-xinerama0 libxkbcommon-x11-0
```

#### 3. Large file size

Use `--onedir` instead of `--onefile`:
```bash
python build.py --platform linux --onedir
```

#### 4. App doesn't start (no error)

Build with console to see errors:
```bash
python build.py --platform windows --console
```

#### 5. Missing DLLs on Windows

Ensure Visual C++ Redistributable is installed on target machine.

### Build Logs

Check `build/` folder for detailed PyInstaller logs if build fails.

---

## Output Files

After successful build:

```
dist/
├── BMSMonitorApp.exe      # Windows executable
├── BMSMonitorApp          # Linux binary
└── BMSMonitorApp.app/     # macOS application bundle
```

### File Sizes (Approximate)

| Platform | Size |
|----------|------|
| Windows | ~80-120 MB |
| Linux | ~100-150 MB |
| macOS | ~100-150 MB |

---

## Adding App Icons

Place icons in `assets/` folder:

| File | Platform | Format |
|------|----------|--------|
| `icon.ico` | Windows | ICO, 256x256 |
| `icon.icns` | macOS | ICNS |
| `icon.png` | Linux | PNG, 256x256 |

---

## Distribution Checklist

Before distributing:

- [ ] Test on clean machine without Python installed
- [ ] Verify all features work
- [ ] Check file size is reasonable
- [ ] Include any required runtime (VC++ Redist for Windows)
- [ ] Sign executable (recommended for production)
  - Windows: Use `signtool`
  - macOS: Use `codesign`

---

## Need Help?

- PyInstaller docs: https://pyinstaller.org/
- PyQt6 deployment: https://doc.qt.io/qt-6/deployment.html
- Report issues: [Create an issue in the repository]

