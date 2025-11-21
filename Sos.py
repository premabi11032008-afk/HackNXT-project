import customtkinter as ctk
import threading
import time
from playsound import playsound
import random

# -----------------------
# Simulated GPS Function
# -----------------------
def fake_gps(callback):
    """Simulate changing GPS coordinates every 2 seconds."""
    while True:
        lat = round(random.uniform(10.000, 11.000), 5)
        lon = round(random.uniform(76.900, 77.200), 5)
        callback(lat, lon)
        time.sleep(2)

# -----------------------
# Main UI Class
# -----------------------
class EmergencyApp(ctk.CTkToplevel):

    def __init__(self):
        super().__init__()
        self.title("Emergency Alert System")
        self.geometry("400x500")
        ctk.set_appearance_mode("dark")

        # Alarm flag
        self.alarm_active = False

        # ---------- STATUS LABEL ----------
        self.status_label = ctk.CTkLabel(self, 
                                         text="Status: Ready",
                                         font=("Arial", 24))
        self.status_label.pack(pady=20)

        # ---------- LOCATION LABEL ----------
        self.location_label = ctk.CTkLabel(self, 
                                           text="Location: Unknown",
                                           font=("Arial", 20))
        self.location_label.pack(pady=20)

        # ---------- EMERGENCY BUTTON ----------
        self.btn_emergency = ctk.CTkButton(self,
                                           text="EMERGENCY",
                                           fg_color="red",
                                           hover_color="#aa0000",
                                           font=("Arial", 32),
                                           command=self.start_emergency)
        self.btn_emergency.pack(pady=30, ipadx=10, ipady=10)

        # ---------- STOP BUTTON ----------
        self.btn_stop = ctk.CTkButton(self,
                                      text="STOP",
                                      fg_color="gray20",
                                      hover_color="gray30",
                                      font=("Arial", 26),
                                      command=self.stop_emergency)
        self.btn_stop.pack(pady=10, ipadx=10, ipady=10)

    # ---------------------------------
    # Start emergency
    # ---------------------------------
    def start_emergency(self):
        if self.alarm_active:
            return
        
        self.alarm_active = True
        self.status_label.configure(text="Status: ALARM ON")
        self.btn_emergency.configure(state="disabled")

        # Play alarm sound in thread
        threading.Thread(target=self.play_alarm, daemon=True).start()

        # Fake GPS in background
        threading.Thread(target=fake_gps, args=(self.update_location,), daemon=True).start()

    # ---------------------------------
    # Stop everything
    # ---------------------------------
    def stop_emergency(self):
        self.alarm_active = False
        self.status_label.configure(text="Status: Stopped")
        self.btn_emergency.configure(state="normal")

    # ---------------------------------
    # Alarm sound loop
    # ---------------------------------
    def play_alarm(self):
        while self.alarm_active:
            try:
                playsound("alarm.mp3")
            except:
                pass

    # ---------------------------------
    # Update location
    # ---------------------------------
    def update_location(self, lat, lon):
        if self.alarm_active:
            self.location_label.configure(text=f"Location: {lat}, {lon}")

# -------------------------------------
# Run the App
# -------------------------------------
if __name__ == "__main__":
    app = EmergencyApp()
    app.mainloop()
