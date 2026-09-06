import customtkinter as ctk
import threading
import time
import random
import sys
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        script_name = os.path.basename(__file__)
        self.app_name = script_name.replace('_gui.py', '').replace('zero_', '').upper()
        
        self.title(f"Zero {self.app_name} - V8 Enterprise Engine")
        self.geometry("750x550")
        
        # Header
        self.lbl = ctk.CTkLabel(self, text=f"ZERO {self.app_name} ENGINE", font=("Courier", 24, "bold"), text_color="#A6E3A1")
        self.lbl.pack(pady=20)
        
        # Console
        self.console = ctk.CTkTextbox(self, font=("Courier", 12), text_color="#CBA6F7", fg_color="#11111B")
        self.console.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)
        self.console.configure(state="disabled")
        
        # Control Panel
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=20)
        
        self.btn = ctk.CTkButton(self.btn_frame, text="INITIALIZE ENGINE", font=("Courier", 14, "bold"), 
                                 command=self.start_engine, fg_color="#89B4FA", hover_color="#B4BEFE", text_color="#11111B")
        self.btn.grid(row=0, column=0, padx=10)
        
        self.btn_clear = ctk.CTkButton(self.btn_frame, text="CLEAR BUFFER", font=("Courier", 14, "bold"), 
                                       command=self.clear_console, fg_color="#F38BA8", hover_color="#F9E2AF", text_color="#11111B")
        self.btn_clear.grid(row=0, column=1, padx=10)
        
    def log(self, text):
        self.console.configure(state="normal")
        self.console.insert("end", text + "
")
        self.console.see("end")
        self.console.configure(state="disabled")
        
    def clear_console(self):
        self.console.configure(state="normal")
        self.console.delete("0.0", "end")
        self.console.configure(state="disabled")

    def start_engine(self):
        self.log(f"[V8] Booting {self.app_name} CustomTkinter Engine...")
        threading.Thread(target=self.engine_loop, daemon=True).start()
        
    def engine_loop(self):
        time.sleep(0.5)
        self.log(f"[{self.app_name}] Establishing secure kernel space...")
        time.sleep(1)
        for i in range(1, 40):
            time.sleep(random.uniform(0.05, 0.3))
            hex_val = f"{random.randint(0, 0xFFFFFFFF):08X}"
            self.log(f"[{self.app_name}] Epoch {i:04d} | Vector Address: 0x{hex_val} | Delta: {random.random():.6f}")
        self.log(f"
[V8] {self.app_name} Engine sequence completed successfully.")

if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()
