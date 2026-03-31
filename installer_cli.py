import urllib.request
import urllib.error
import ssl
import os
import sys
import time

VERSION = "1.0"
GAME_URL = "https://github.com/NeuronActivation31/my-singing-monsters/releases/download/v1.1/My.Singing.Monsters.exe"
INSTALL_DIR = os.path.join(os.path.expanduser("~"), "Desktop")

def show_banner():
    print("\n" + "="*50)
    print("    MY SINGING MONSTERS - ICE AGE")
    print("         Installer v" + VERSION)
    print("="*50 + "\n")

def download_file(url, dest):
    # Create SSL context that works on all systems
    ctx = ssl.create_default_context()
    
    # Follow redirects manually
    while True:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        resp = urllib.request.urlopen(req, context=ctx, timeout=60)
        
        # Check if we got redirected
        if resp.status == 302 or resp.status == 301:
            url = resp.headers.get("Location")
            print(f"  Following redirect...", flush=True)
            continue
        break
    
    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    
    with open(dest, "wb") as f:
        while True:
            chunk = resp.read(8192)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            
            if total > 0:
                pct = (downloaded / total) * 100
                bars = int(pct // 2)
                bar = "█" * bars + "░" * (50 - bars)
                print(f"\r  [{bar}] {pct:.1f}%  ({downloaded//1024} KB)", end="", flush=True)
    print()

def main():
    show_banner()
    
    # Check if already installed
    dest = os.path.join(INSTALL_DIR, "My Singing Monsters Ice Age.exe")
    if os.path.exists(dest):
        print("  There is already MSMIA on your PC/Sandbox!\n")
        print("  Press Enter to exit...")
        input()
        return
    
    print(f"  Install location: {INSTALL_DIR}\n")
    
    # Ask for confirmation
    try:
        choice = input("  Press Enter to install (or 'q' to quit): ").strip().lower()
        if choice == 'q':
            print("\n  Cancelled.")
            return
    except KeyboardInterrupt:
        print("\n\n  Cancelled.")
        return
    
    print("\n  Downloading game...")
    
    try:
        download_file(GAME_URL, dest)
        
        print("\n  ✓ Installation complete!")
        print(f"  ✓ Game installed to: {dest}\n")
        print("  Press Enter to exit...")
        input()
        
    except Exception as e:
        print(f"\n  ✗ Error: {e}\n")
        print("  Press Enter to exit...")
        input()
        sys.exit(1)

if __name__ == "__main__":
    main()
