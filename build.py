import os
import subprocess
import sys
import shutil
import argparse

def build_app(onefile=False, debug=False):
    print(f"Building CA Billing App ({'Single File' if onefile else 'Folder'} mode, {'DEBUG' if debug else 'Standard'})...")
    
    # 1. Install PyInstaller if missing
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Define Command
    mode_flag = "--onefile" if onefile else "--onedir"
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        mode_flag,
        "--name=CABillingApp",
        "--clean",
        "--paths=ca_billing_app",
        "--collect-all=PySide6",
        "--hidden-import=services",
        "--hidden-import=services.reporting_service",
        "--hidden-import=exports",
        "--hidden-import=exports.excel_exporter",
        "ca_billing_app/main.py"
    ]
    
    # Add windowed flag ONLY if not in debug mode
    if not debug:
        cmd.append("--windowed")
    
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("\nBuild Complete!")
        
        output_base = os.path.join(os.getcwd(), 'dist')
        if onefile:
            ext = ".exe" if os.name == 'nt' else ".app" if sys.platform == 'darwin' else ""
            print(f"Executable is located in: {os.path.join(output_base, 'CABillingApp' + ext)}")
        else:
            print(f"Folder is located in: {os.path.join(output_base, 'CABillingApp')}")
            
        if debug:
            print("\nDEBUG NOTE: Running the created file from a terminal (cmd/powershell) will now show any errors.")
        else:
            print("You can share this file with anyone on the SAME operating system.")
            
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build CA Billing App")
    parser.add_argument("--onefile", action="store_true", help="Build as a single executable file")
    parser.add_argument("--debug", action="store_true", help="Build with console visible for debugging")
    args = parser.parse_args()
    
    build_app(onefile=args.onefile, debug=args.debug)
