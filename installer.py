import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import os
import sys
import threading

VERSION = "1.0"
GAME_URL = "https://github.com/NeuronActivation31/my-singing-monsters/releases/latest/download/MySingingMonsters.exe"
INSTALL_DIR = os.path.join(os.path.expanduser("~"), "Desktop")

class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("My Singing Monsters - Ice Age Installer")
        self.geometry("450x300")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        
        # Icon attempt
        try:
            self.iconbitmap(default='')
        except:
            pass
        
        # Title
        tk.Label(self, text="My Singing Monsters", font=("Arial", 20, "bold"), 
                 fg="#8ec8ff", bg="#1a1a2e").pack(pady=(30, 0))
        tk.Label(self, text="~ Ice Age ~", font=("Arial", 14), 
                 fg="#5090d0", bg="#1a1a2e").pack()
        
        # Status
        self.status_label = tk.Label(self, text="Click Install to begin", 
                                     font=("Arial", 11), fg="white", bg="#1a1a2e")
        self.status_label.pack(pady=30)
        
        # Progress bar
        self.progress = ttk.Progressbar(self, length=350, mode='determinate')
        self.progress.pack(pady=10)
        
        # Progress text
        self.progress_label = tk.Label(self, text="", font=("Arial", 9), 
                                       fg="#aaa", bg="#1a1a2e")
        self.progress_label.pack()
        
        # Buttons frame
        btn_frame = tk.Frame(self, bg="#1a1a2e")
        btn_frame.pack(pady=20)
        
        self.install_btn = tk.Button(btn_frame, text="Install", command=self.install,
                                     font=("Arial", 12, "bold"), bg="#2d5a8a", fg="white",
                                     activebackground="#3d7aba", width=15, cursor="hand2")
        self.install_btn.pack(side=tk.LEFT, padx=10)
        
        self.cancel_btn = tk.Button(btn_frame, text="Cancel", command=self.quit,
                                    font=("Arial", 12), bg="#555", fg="white",
                                    activebackground="#777", width=10, cursor="hand2")
        self.cancel_btn.pack(side=tk.LEFT, padx=10)
        
    def install(self):
        self.install_btn.config(state='disabled')
        self.status_label.config(text="Downloading game...")
        threading.Thread(target=self.download_game, daemon=True).start()
    
    def download_game(self):
        try:
            req = urllib.request.Request(GAME_URL, headers={"User-Agent": "MSM-Installer/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                dest = os.path.join(INSTALL_DIR, "My Singing Monsters Ice Age.exe")
                
                with open(dest, "wb") as f:
                    while True:
                        chunk = resp.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = (downloaded / total) * 100
                            self.progress['value'] = pct
                            self.progress_label.config(text=f"{downloaded//1024} KB / {total//1024} KB")
            
            self.progress['value'] = 100
            self.status_label.config(text="Installation complete!")
            self.progress_label.config(text=f"Installed to: {dest}")
            self.install_btn.config(text="Done", state='normal', command=self.quit)
            messagebox.showinfo("Success", "My Singing Monsters - Ice Age has been installed to your Desktop!")
            
        except Exception as e:
            self.status_label.config(text="Download failed!")
            self.progress_label.config(text=str(e))
            self.install_btn.config(state='normal')

if __name__ == "__main__":
    app = Installer()
    app.mainloop()
