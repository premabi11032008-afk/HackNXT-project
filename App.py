import customtkinter as ct
import tkinter as tk
from tkinter import messagebox
from cryptography.fernet import Fernet
import os
import google.generativeai as genai
import threading
from Hospital_finder import HospitalApp
from Call_Doctors import DoctorListWindow
from Sos import EmergencyApp

DATA_FILE = "users.enc"
KEY_FILE = "key.key"
Heading="PFM- Prompt Free AI Medical Assistant"
cur_user= None

# Generate or load encryption key
if not os.path.exists(KEY_FILE):
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
else:
    key = open(KEY_FILE, "rb").read()

aes = Fernet(key)

# Load users
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        data = aes.decrypt(open(DATA_FILE, "rb").read()).decode()
        return eval(data)
    except:
        return {}

# Save users
def save_users(users: dict):
    encrypted = aes.encrypt(str(users).encode())
    open(DATA_FILE, "wb").write(encrypted)

users = load_users()
class App(ct.CTk):
    def __init__(self):
        super().__init__()

        self.title(Heading)
        self.geometry("1000x700")
        self.minsize(900, 600)

        self.current_page = None
        self.show_page(LoginPage)

    def show_page(self, PageClass):
        if self.current_page:
            self.current_page.destroy()
        self.current_page = PageClass(self)
        self.current_page.pack(fill="both", expand=True)

class LoginPage(ct.CTkFrame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root

        wrapper = ct.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.55, anchor="center")

        title = ct.CTkLabel(wrapper, text=Heading, font=ct.CTkFont(size=32, weight="bold"))
        title.pack(pady=(0, 20))

        self.user = ct.CTkEntry(wrapper, placeholder_text="Username", width=360)
        self.user.pack(pady=8)

        self.password = ct.CTkEntry(wrapper, placeholder_text="Password", show="*", width=360)
        self.password.pack(pady=8)

        btn_frame = ct.CTkFrame(wrapper, fg_color="transparent")
        btn_frame.pack(pady=12)

        ct.CTkButton(btn_frame, text="Login", width=160, command=self.login).grid(row=0, column=0, padx=10)
        ct.CTkButton(btn_frame, text="Create Account", width=160,
                     command=lambda: root.show_page(SignupPage)).grid(row=0, column=1)

        ct.CTkLabel(wrapper, text="By logging in you agree to our Terms.", font=ct.CTkFont(size=11)).pack(pady=10)

    def login(self):
        global cur_user
        user = self.user.get().strip()
        pw = self.password.get().strip()

        if users[user]["password"] == pw:
            cur_user= user
            self.root.show_page(ChatPage)
        else:
            messagebox.showerror("Error", "Incorrect login details")

class SignupPage(ct.CTkFrame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root

        wrapper = ct.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.55, anchor="center")

        ct.CTkLabel(wrapper, text="Create Account", font=ct.CTkFont(size=28, weight="bold")).pack(pady=(0, 20))

        self.name = ct.CTkEntry(wrapper, placeholder_text="Full Name", width=360)
        self.name.pack(pady=8)

        self.password = ct.CTkEntry(wrapper, placeholder_text="Password", show="*", width=360)
        self.password.pack(pady=8)

        self.confirm = ct.CTkEntry(wrapper, placeholder_text="Confirm Password", show="*", width=360)
        self.confirm.pack(pady=8)

        btn_frame = ct.CTkFrame(wrapper, fg_color="transparent")
        btn_frame.pack(pady=12)

        ct.CTkButton(btn_frame, text="Create Account", width=160, command=self.create).grid(row=0, column=0, padx=10)
        ct.CTkButton(btn_frame, text="Back to Login", width=160,
                     command=lambda: root.show_page(LoginPage)).grid(row=0, column=1)

    def create(self):
        name = self.name.get().strip()
        pw = self.password.get().strip()
        conf = self.confirm.get().strip()

        if not name  or not pw:
            messagebox.showwarning("Missing", "Fill all fields")
            return

        if pw != conf:
            messagebox.showerror("Error", "Passwords do not match")
            return

        users[name] = {"password": pw}
        print(users)
        save_users(users)

        messagebox.showinfo("Created", "Account Created Successfully")
        self.root.show_page(LoginPage)


class SlidingMenu(ct.CTkFrame):
    def __init__(self, root, width=250, **kwargs):
        super().__init__(root, fg_color="#1E1E1E", width=width, corner_radius=0, **kwargs)

        self.root = root
        self.menu_width = width
        self.is_open = False
        self.animating = False

        # Start hidden: positioned outside the left edge
        self.place(x=-self.menu_width, y=0, relheight=1)

        # Menu title
        ct.CTkLabel(self, text="Menu", font=ct.CTkFont(size=22, weight="bold")).pack(pady=20)

        ct.CTkButton(
    self, 
    text="🏥 Find Nearby Hospitals",
    command=self.open_hospital_finder
).pack(pady=8, padx=10)

        ct.CTkButton(self,
            text="📞 Contact Doctors",
            command=self.open_doctor_list
        ).pack(pady=8, padx=10)

        ct.CTkButton(self,
                     text="Emergency",
                     command=self.open_emergency).pack(pady=8, padx=10)
        
        ct.CTkButton(self, text="❌ Close Menu", command=self.toggle).pack(pady=20, padx=10)

    def open_doctor_list(self):
        try:
            win = DoctorListWindow()
            win.grab_set()  # make window modal
        except Exception as e:
            print("Error opening doctor list:", e)

    def open_emergency(self):
        try:
            _window = EmergencyApp()
            _window.mainloop()
        except Exception as e:
            print("Error opening hospital finder:", e)


    def open_hospital_finder(self):
        try:
            hospital_window = HospitalApp()
            hospital_window.mainloop()
        except Exception as e:
            print("Error opening hospital finder:", e)


    def toggle(self):
        if self.animating:
            return
        if self.is_open:
            self.slide_out(0)
        else:
            self.slide_in(0)

    # SLIDE IN (from -width → 0)
    def slide_in(self, step):
        if not self.winfo_exists():
            return

        self.animating = True

        x = -self.menu_width + step
        self.place(x=x, y=0)

        if step < self.menu_width:
            self.after(1, lambda: self.slide_in(step + 5))
        else:
            self.animating = False
            self.is_open = True

    # SLIDE OUT (from 0 → -width)
    def slide_out(self, step):
        if not self.winfo_exists():
            return

        self.animating = True

        x = 0 - step
        self.place(x=x, y=0)

        if step < self.menu_width:
            self.after(1, lambda: self.slide_out(step + 5))
        else:
            self.animating = False
            self.is_open = False


class ChatPage(ct.CTkFrame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.chat_history=[]

        ct.CTkLabel(self, text=Heading, font=ct.CTkFont(size=28, weight="bold")).pack(pady=12)

        # Scrollable frame to hold chat bubbles
        self.chat_area= ct.CTkScrollableFrame(self, width=900, height=520)
        self.chat_area.pack(pady=10)

        self.bottom = ct.CTkFrame(self)
        self.bottom.pack(pady=10)

        self.entry = ct.CTkEntry(self.bottom, placeholder_text="Type symptoms...", width=650)
        self.entry.pack(side="left", padx=10)

        ct.CTkButton(self.bottom, text="Send", command=self.analyze_symptoms).pack(side="left")
        # ENTER to send only when entry has focus
        self.entry.bind("<Return>", self.handle_enter)

        # SHIFT+ENTER for newline
        self.entry.bind("<Shift-Return>", self.handle_shift_enter)


        self.menu_btn = ct.CTkButton(self.bottom,
            text="⋮",
            width=50,
            command=self.open_menu,
            font=ct.CTkFont(size=20),
            fg_color="#303030",
            hover_color="#454545"
        )
        self.menu_btn.pack(side="left", padx=5)

        # --- SLIDING MENU INSTANCE ---
        self.side_menu = SlidingMenu(root)

    def handle_enter(self, event):
        widget = self.focus_get()
        if widget == self.entry:
            return self.analyze_symptoms()

    def handle_shift_enter(self, event):
        self.entry.insert("insert", "\n")
        return "break"   # prevents default behaviour

        
    def open_menu(self):
        self.side_menu.toggle()

    genai.configure(api_key="AIzaSyAm0XqCcCHTxWgUciVOq_TpYhAi3xrN0Yg")


    def destroy(self):
        if hasattr(self, "side_menu") and self.side_menu.winfo_exists():
            self.side_menu.destroy()
        super().destroy()


    def clean_markdown(self, text):
        import re
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # bold
        text = re.sub(r"\*(.*?)\*", r"\1", text)       # italic
        text = text.replace("_", "")                  # underscores
        text = text.replace("•", "• ")                # clean bullets
        text = text.replace("- ", "• ")               # bullets
        return text

    def beautify(self, text):
        text = self.clean_markdown(text)

        # Add emojis based on keywords
        replacements = {
            "Possible Conditions": "🩺 Possible Conditions",
            "Risk Score": "📊 Risk Score",
            "Urgency": "⏳ Urgency",
            "Recommended Actions": "📝 Recommended Actions",
            "Disclaimer": "⚠️ Disclaimer",
            "Symptoms": "🤒 Symptoms",
        }

        for key, emo in replacements.items():
            text = text.replace(key, emo)

        return text

    def add_bubble(self, text, side="left", color="#2E7D32"):
        bubble = ct.CTkFrame(
            self.chat_area,
            fg_color=color,
            corner_radius=20
        )
        bubble.pack(fill="x", pady=6, padx=20, anchor="e" if side == "right" else "w")

        label = ct.CTkLabel(
            bubble,
            text=text,
            font=ct.CTkFont(size=15),
            wraplength=700,
            justify="left"
        )
        label.pack(padx=15, pady=10)

        self.chat_area._parent_canvas.yview_moveto(1)  # auto scroll

    def analyze_symptoms(self,event=None):
        symptoms = self.entry.get().strip()
        if not symptoms:
            return

        self.entry.delete(0, "end")

        # user bubble
        self.add_bubble(f"🙂 You:\n{symptoms}", side="right", color="#1976D2")

        # Show typing bubble
        self.typing_bubble = ct.CTkFrame(self.chat_area, fg_color="#444")
        self.typing_bubble.pack(fill="x", pady=6, padx=20, anchor="w")

        ct.CTkLabel(
            self.typing_bubble,
            text="🤖 AI is analyzing...",
            font=ct.CTkFont(size=15)
        ).pack(padx=15, pady=8)

        self.chat_area._parent_canvas.yview_moveto(1)

        # Threading
        threading.Thread(target=self.run_api, args=(symptoms,), daemon=True).start()

    def run_api(self, symptoms):
        try:
            prompt = f"""
            Previous Chat History: {self.chat_history}
            You are a medical diagnostic assistant.

            patient Name if not provided abt the patient details in the symptoms: {cur_user}
            and return the risk score as one of the following levels: Low, Moderate, High. and the last
and if the risk is high or moderate, advise the user to seek immediate medical attention and give only 3 more critical steps to take immediately.
doesnot return anything else 
            if the symptoms are inadequate, ask for more information before analyzing just first time if the chat history contains it do not
            ask and produce the diagonised report
            keep the response concise and to the point.
            keep the tone empatheitic and keep the language simple for a layman to understand and keep the user realxed on the tone

            
            Analyze symptoms and return:

            1. Possible Conditions
            2. Reasoning
            3. Urgency
            4. Recommended Actions
            5. Recomanded feild for the cosulting doctor
            6. Disclaimer

            Symptoms: {symptoms}
            """

            model = genai.GenerativeModel("gemini-2.0-flash")
            self.chat_history.append(("User", symptoms))
            response = model.generate_content(prompt)
            text = response.text

        except Exception as e:
            text = f"❌ Error: {e}"

        self.after(0, lambda: self.display_response(text))

    def get_risk_color(self, text):
        text_low = text.lower()

        if "high" in text_low or "severe" in text_low or "critical" in text_low:
            return "#D32F2F"     # 🔴 Red (High Risk)

        if "moderate" in text_low or "medium" in text_low:
            return "#F9A825"     # 🟡 Yellow (Medium Risk)

        if "low" in text_low or "mild" in text_low:
            return "#2E7D32"     # 🟢 Green (Low Risk)

        return "#2E7D32"

    def display_response(self, text):

        self.typing_bubble.destroy()
        pretty = self.beautify(text)
        self.chat_history.append(("AI", pretty))

        if "disclaimer" in pretty.lower():
            self.chat_history=[]
        
        rsk_clour= self.get_risk_color(pretty)
        self.add_bubble(f"🤖 AI:\n{pretty}", side="left", color=rsk_clour)




if __name__ == "__main__":
    app = App()
    app.mainloop()
