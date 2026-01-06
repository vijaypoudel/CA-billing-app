import os
import subprocess
import sys
import shutil
import argparse

def build_app(onefile=False):
    print(f"Building CA Billing App ({'Single File' if onefile else 'Folder'} mode)...")
    
    # 1. Install PyInstaller if missing
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Define Command
    # --noconfirm: overwrite existing
    # --windowed: no console window
    # --name: output name
    
    mode_flag = "--onefile" if onefile else "--onedir"
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        mode_flag,
        "--windowed",
        "--name=CABillingApp",
        "--clean",
        "ca_billing_app/main.py"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("\nBuild Complete!")
        
        output_base = os.path.join(os.getcwd(), 'dist')
        if onefile:
            ext = ".exe" if os.name == 'nt' else ".app" if sys.platform == 'darwin' else ""
            print(f"Executable is located in: {os.path.join(output_base, 'CABillingApp' + ext)}")
            print("You can share this single file directly with anyone on the SAME operating system.")
        else:
            print(f"Folder is located in: {os.path.join(output_base, 'CABillingApp')}")
            print("You MUST zip this entire folder before sharing.")
            
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build CA Billing App")
    parser.add_argument("--onefile", action="store_true", help="Build as a single executable file")
    args = parser.parse_args()
    
    build_app(onefile=args.onefile)
