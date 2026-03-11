import os
import sys
import subprocess
import json
import getpass
import shutil

SETTINGS_FILE = "settings.json"
REQUIREMENTS_FILE = "requirements.txt"

def print_header(text):
    print(f"\n{'='*50}\n{text}\n{'='*50}")

def check_imagemagick():
    """Wand requires ImageMagick to be installed at the OS level."""
    print_header("Step 1: Checking System Dependencies")
    
    # Check if the 'magick' or 'convert' command exists on the system
    has_magick = shutil.which("magick") or shutil.which("convert")
    
    if has_magick:
        print("[OK] ImageMagick is installed.")
    else:
        print("[WARNING] ImageMagick does not appear to be installed on this system.")
        print("The 'Wand' image processing library requires ImageMagick to run.")
        print("Please install it before running the app:")
        print(" - Windows: Download from https://imagemagick.org")
        print(" - Linux: sudo apt install libmagickwand-dev (or equivalent)")
        print(" - macOS: brew install imagemagick")
        
        input("\nPress Enter to acknowledge and continue anyway...")

def install_requirements():
    """Installs the python packages from requirements.txt."""
    print_header("Step 2: Installing Python Dependencies")
    
    if not os.path.exists(REQUIREMENTS_FILE):
        print(f"[ERROR] {REQUIREMENTS_FILE} not found. Skipping pip install.")
        return

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])
        print("\n[OK] All Python dependencies installed successfully.")
    except subprocess.CalledProcessError:
        print("\n[ERROR] Failed to install requirements. Please check your pip setup.")
        sys.exit(1)

def configure_internet_archive():
    """Helps the user generate their IA credentials and saves them."""
    print_header("Step 3: Internet Archive Configuration")
    
    print("To upload files to the Internet Archive, you need your API Keys.")
    print("You can find these by logging into archive.org and visiting:")
    print("https://archive.org/account/s3.php\n")
    
    configure = input("Do you want to configure your IA credentials now? (y/n): ").strip().lower()
    
    ia_access_key = ""
    ia_secret_key = ""
    
    if configure == 'y':
        ia_access_key = input("Enter your IA Access Key: ").strip()
        ia_secret_key = getpass.getpass("Enter your IA Secret Key (input will be hidden): ").strip()
        
        try:
            from internetarchive import configure as ia_config
            ia_config(ia_access_key, ia_secret_key)
            print("[OK] Internet Archive CLI credentials saved to system.")
        except ImportError:
            print("[WARNING] 'internetarchive' python library not found. Keys will only be saved to local settings.")
            
    return ia_access_key, ia_secret_key

def generate_settings(access_key, secret_key):
    """Creates the initial settings.json file for the PyQt app."""
    print_header("Step 4: Generating Application Settings")
    
    current_settings = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            try:
                current_settings = json.load(f)
            except json.JSONDecodeError:
                pass

    current_settings["ia_access_key"] = access_key or current_settings.get("ia_access_key", "")
    current_settings["ia_secret_key"] = secret_key or current_settings.get("ia_secret_key", "")
    current_settings["output_directory"] = current_settings.get("output_directory", os.path.expanduser("~/ArchiveExports"))
    current_settings["default_dpi"] = current_settings.get("default_dpi", 300)
    current_settings["auto_deskew"] = current_settings.get("auto_deskew", True)

    with open(SETTINGS_FILE, "w") as f:
        json.dump(current_settings, f, indent=4)
        
    print(f"[OK] Settings saved to {SETTINGS_FILE}")

def main():
    print("\nStarting School Archive Digitization Pipeline Setup...")
    
    check_imagemagick()
    install_requirements()
    access, secret = configure_internet_archive()
    generate_settings(access, secret)
    
    print_header("Setup Complete!")
    print("You can now run the application using:")
    print(f"    {sys.executable} main.py\n")

if __name__ == "__main__":
    main()