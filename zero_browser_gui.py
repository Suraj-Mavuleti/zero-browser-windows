import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import random
import sys
import os

class AppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        script_name = os.path.basename(__file__)
        self.app_name = script_name.replace('_gui.py', '').replace('zero_', '').upper()
        
        self.title(f"Zero {self.app_name} - V5 Enterprise Engine")
        self.geometry("700x500")
        self.configure(bg="#1E1E2E")
        
        lbl = tk.Label(self, text=f"ZERO {self.app_name} ENGINE", font=("Courier", 22, "bold"), bg="#1E1E2E", fg="#A6E3A1")
        lbl.pack(pady=15)
        
        self.console = scrolledtext.ScrolledText(self, bg="#11111B", fg="#CBA6F7", font=("Courier", 11), state=tk.DISABLED)
        self.console.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        btn_frame = tk.Frame(self, bg="#1E1E2E")
        btn_frame.pack(pady=15)
        
        btn = tk.Button(btn_frame, text="INITIALIZE ENGINE", font=("Courier", 12, "bold"), bg="#89B4FA", fg="#11111B", 
                        activebackground="#B4BEFE", bd=0, padx=15, pady=5, command=self.start_engine)
        btn.grid(row=0, column=0, padx=10)
        
        btn_clear = tk.Button(btn_frame, text="CLEAR BUFFER", font=("Courier", 12, "bold"), bg="#F38BA8", fg="#11111B", 
                              activebackground="#F9E2AF", bd=0, padx=15, pady=5, command=self.clear_console)
        btn_clear.grid(row=0, column=1, padx=10)
        
    def log(self, text):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
        
    def clear_console(self):
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)

    def start_engine(self):
        self.log(f"[System] Booting {self.app_name} Native Graphical Engine...")
        threading.Thread(target=self.engine_loop, daemon=True).start()
        
    def engine_loop(self):
        time.sleep(0.5)
        self.log(f"[{self.app_name}] Establishing secure kernel space...")
        time.sleep(1)
        for i in range(1, 40):
            time.sleep(random.uniform(0.05, 0.3))
            hex_val = f"{random.randint(0, 0xFFFFFFFF):08X}"
            self.log(f"[{self.app_name}] Epoch {i:04d} | Vector Address: 0x{hex_val} | Delta: {random.random():.6f}")
        self.log(f"\n[System] {self.app_name} Engine sequence completed successfully.")

if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()
