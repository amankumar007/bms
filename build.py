#!/usr/bin/env python3
"""
Build script for BMS Monitor App V2
Creates executables for Windows, Linux, and macOS using PyInstaller

Usage:
    python build.py --platform windows    # Build for Windows (.exe)
    python build.py --platform linux      # Build for Linux (binary)
    python build.py --platform mac        # Build for macOS (.app)
    python build.py --platform all        # Build for current platform
    
Options:
    --onefile       Create single executable file (default)
    --onedir        Create directory with executable and dependencies
    --console       Show console window (for debugging)
    --clean         Clean build artifacts before building
    --name NAME     Custom name for the executable (default: BMSMonitorApp)
"""

import argparse
import os
import sys
import shutil
import subprocess
import platform


APP_NAME = "BMSMonitorApp"
APP_VERSION = "2.0.0"
MAIN_SCRIPT = "main.py"
ICON_WINDOWS = "assets/icon.ico"  # Optional: Add your icon
ICON_MAC = "assets/icon.icns"     # Optional: Add your icon
ICON_LINUX = "assets/icon.png"    # Optional: Add your icon


def get_current_platform():
    """Detect the current platform"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "mac"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


def check_pyinstaller():
    """Check if PyInstaller is installed, install if not"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print("⚠ PyInstaller not found. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                         check=True)
            print("✓ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install PyInstaller")
            return False


def clean_build():
    """Clean previous build artifacts"""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = [f"{APP_NAME}.spec"]
    
    print("\n🧹 Cleaning build artifacts...")
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed: {dir_name}/")
    
    for file_name in files_to_clean:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"  Removed: {file_name}")
    
    # Clean __pycache__ in subdirectories
    for root, dirs, files in os.walk("src"):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                path = os.path.join(root, dir_name)
                shutil.rmtree(path)
                print(f"  Removed: {path}/")
    
    print("✓ Clean complete\n")


def build_app(target_platform, onefile=True, console=False, app_name=None):
    """Build the application for the specified platform"""
    
    current_platform = get_current_platform()
    
    # Cross-compilation warning
    if target_platform != current_platform and target_platform != "all":
        print(f"\n⚠ WARNING: Cross-compilation is not supported by PyInstaller!")
        print(f"  You are on '{current_platform}' but trying to build for '{target_platform}'")
        print(f"  The build will be created for your current platform: '{current_platform}'")
        print(f"  To build for {target_platform}, run this script on a {target_platform} machine.\n")
        target_platform = current_platform
    
    if target_platform == "all":
        target_platform = current_platform
    
    name = app_name or APP_NAME
    
    print(f"\n🔨 Building {name} v{APP_VERSION} for {target_platform.upper()}...")
    print(f"  Mode: {'Single File' if onefile else 'Directory'}")
    print(f"  Console: {'Enabled' if console else 'Disabled (GUI only)'}")
    print()
    
    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", name,
        "--noconfirm",
    ]
    
    # One file or one directory
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    # Console or windowed
    if not console:
        cmd.append("--windowed")
    
    # Platform-specific settings
    if target_platform == "windows":
        if os.path.exists(ICON_WINDOWS):
            cmd.extend(["--icon", ICON_WINDOWS])
        # Windows-specific options
        cmd.extend([
            "--version-file", "version_info.txt" if os.path.exists("version_info.txt") else "",
        ])
        # Remove empty version file arg if not exists
        if "--version-file" in cmd and "" in cmd:
            idx = cmd.index("--version-file")
            cmd.pop(idx)
            cmd.pop(idx)
            
    elif target_platform == "mac":
        if os.path.exists(ICON_MAC):
            cmd.extend(["--icon", ICON_MAC])
        # macOS-specific options
        cmd.extend([
            "--osx-bundle-identifier", "com.bmsmonitor.app",
        ])
        
    elif target_platform == "linux":
        if os.path.exists(ICON_LINUX):
            cmd.extend(["--icon", ICON_LINUX])
    
    # Hidden imports for PyQt6 and other dependencies
    hidden_imports = [
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtWebEngineCore",
        "serial",
        "serial.tools",
        "serial.tools.list_ports",
        "pandas",
        "numpy",
        "plotly",
        "plotly.graph_objects",
        "plotly.io",
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Collect all from packages that need data files
    cmd.extend(["--collect-all", "plotly"])
    
    # Add paths
    cmd.extend(["--paths", "src"])
    
    # Add the main script
    cmd.append(MAIN_SCRIPT)
    
    print("📦 Running PyInstaller...")
    print(f"  Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✓ Build successful!")
        
        # Show output location
        if onefile:
            if target_platform == "windows":
                output = f"dist/{name}.exe"
            elif target_platform == "mac":
                output = f"dist/{name}.app"
            else:
                output = f"dist/{name}"
        else:
            output = f"dist/{name}/"
        
        print(f"\n📁 Output location: {output}")
        
        if os.path.exists("dist"):
            print("\n📂 Contents of dist/:")
            for item in os.listdir("dist"):
                item_path = os.path.join("dist", item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    size_mb = size / (1024 * 1024)
                    print(f"  📄 {item} ({size_mb:.1f} MB)")
                else:
                    print(f"  📁 {item}/")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed with error code: {e.returncode}")
        return False


def create_version_info():
    """Create Windows version info file"""
    version_parts = APP_VERSION.split(".")
    while len(version_parts) < 4:
        version_parts.append("0")
    
    version_tuple = ", ".join(version_parts[:4])
    
    version_info = f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_tuple}),
    prodvers=({version_tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'BMS Monitor'),
         StringStruct(u'FileDescription', u'BMS Monitoring Application'),
         StringStruct(u'FileVersion', u'{APP_VERSION}'),
         StringStruct(u'InternalName', u'{APP_NAME}'),
         StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
         StringStruct(u'ProductName', u'{APP_NAME}'),
         StringStruct(u'ProductVersion', u'{APP_VERSION}')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open("version_info.txt", "w") as f:
        f.write(version_info)
    print("✓ Created version_info.txt for Windows")


def main():
    parser = argparse.ArgumentParser(
        description="Build BMS Monitor App for different platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py --platform windows          # Build Windows .exe
  python build.py --platform linux            # Build Linux binary
  python build.py --platform mac              # Build macOS .app
  python build.py --platform windows --onedir # Build with directory structure
  python build.py --clean --platform linux    # Clean and build for Linux
        """
    )
    
    parser.add_argument(
        "--platform", "-p",
        choices=["windows", "linux", "mac", "all"],
        default="all",
        help="Target platform (default: current platform)"
    )
    
    parser.add_argument(
        "--onefile",
        action="store_true",
        default=True,
        help="Create single executable file (default)"
    )
    
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Create directory with executable and dependencies"
    )
    
    parser.add_argument(
        "--console",
        action="store_true",
        help="Show console window (for debugging)"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building"
    )
    
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help=f"Custom name for executable (default: {APP_NAME})"
    )
    
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Only clean build artifacts, don't build"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"  BMS Monitor App Build Script")
    print(f"  Version: {APP_VERSION}")
    print(f"  Current Platform: {get_current_platform().upper()}")
    print("=" * 60)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"\n📂 Working directory: {script_dir}")
    
    # Clean if requested
    if args.clean or args.clean_only:
        clean_build()
        if args.clean_only:
            print("✓ Clean only mode - exiting")
            return 0
    
    # Check PyInstaller
    if not check_pyinstaller():
        return 1
    
    # Create version info for Windows
    if args.platform in ["windows", "all"] and get_current_platform() == "windows":
        create_version_info()
    
    # Build
    onefile = not args.onedir
    success = build_app(
        target_platform=args.platform,
        onefile=onefile,
        console=args.console,
        app_name=args.name
    )
    
    if success:
        print("\n" + "=" * 60)
        print("  ✅ BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("  ❌ BUILD FAILED!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

