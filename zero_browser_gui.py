import customtkinter as ctk
import threading
import time
import math
import socket
import urllib.request
import json
import sqlite3
import random

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Zero Browser - Web Explorer")
        self.geometry("800x600")
        self.configure(fg_color="#1a1a24")
        
        # Header
        self.header = ctk.CTkLabel(self, text="Zero Browser - Web Explorer", font=("Helvetica", 24, "bold"), text_color="#00C7FF")
        self.header.pack(pady=20)
        
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)
        
        self.setup_ui()
        
    
    def setup_ui(self):
        bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        bar.pack(fill=ctk.X, pady=5)
        
        self.url = ctk.StringVar(value="http://example.com")
        self.url_entry = ctk.CTkEntry(bar, textvariable=self.url, font=("Courier", 14))
        self.url_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        
        ctk.CTkButton(bar, text="Go", command=self.fetch).pack(side=ctk.RIGHT, padx=5)
        
        self.render = ctk.CTkTextbox(self.main_frame, font=("Courier", 12))
        self.render.pack(fill=ctk.BOTH, expand=True, pady=10)
        
    def fetch(self):
        self.render.delete("0.0", "end")
        self.render.insert("0.0", "Fetching...")
        def do_fetch():
            try:
                url = self.url.get()
                if not url.startswith("http"): url = "http://" + url
                req = urllib.request.urlopen(url)
                html = req.read().decode('utf-8')
                self.render.delete("0.0", "end")
                self.render.insert("0.0", html)
            except Exception as e:
                self.render.delete("0.0", "end")
                self.render.insert("0.0", f"Error: {e}")
        threading.Thread(target=do_fetch).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
