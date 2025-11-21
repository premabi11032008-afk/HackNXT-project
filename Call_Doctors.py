# Call_Doctors.py
import customtkinter as ct
from tkinter import messagebox
import math
import random
import threading
import time

# Ensure default appearance mode is readable
# Users can toggle between "Light" and "Dark" from the doctor window
ct.set_appearance_mode("Dark")
ct.set_default_color_theme("blue")

def _rating_to_stars(rating, max_stars=5):
    """Return a simple text star representation (★ and ☆)"""
    full = int(math.floor(rating))
    half = 1 if (rating - full) >= 0.5 else 0
    empty = max_stars - full - half
    return "★" * full + ("½" if half else "") + "☆" * empty

class DoctorListWindow(ct.CTkToplevel):
    def __init__(self):
        super().__init__()

        self.title("Contact Doctors")
        self.geometry("700x640")
        self.resizable(False, False)

        # Example doctor data with rating (0-5) and fee (0 = free)
        self.doctors = [
            {"id": 1, "name": "Dr. Arjun Kumar", "special": "Cardiologist", "fee": 1200, "phone": "+911234567890", "rating": 4.6},
            {"id": 2, "name": "Dr. Meera Sen", "special": "Dermatologist", "fee": 0, "phone": "+919876543210", "rating": 4.1},
            {"id": 3, "name": "Dr. Rajesh Patel", "special": "Neurologist", "fee": 1500, "phone": "+919001112233", "rating": 4.8},
            {"id": 4, "name": "Dr. Sneha Varma", "special": "General Physician", "fee": 0, "phone": "+918765432100", "rating": 3.9},
            {"id": 5, "name": "Dr. Kavin Rao", "special": "Orthopedic", "fee": 900, "phone": "+919112223344", "rating": 4.3},
            {"id": 6, "name": "Dr. Aditi Shah", "special": "ENT", "fee": 700, "phone": "+919223344556", "rating": 4.0},
            {"id": 7, "name": "Dr. Manoj Iyer", "special": "Pediatrician", "fee": 0, "phone": "+919334455667", "rating": 4.4},
            {"id": 8, "name": "Dr. Priya Menon", "special": "Gynecologist", "fee": 1300, "phone": "+919445566778", "rating": 4.7},
            {"id": 9, "name": "Dr. Harish Nair", "special": "General Physician", "fee": 0, "phone": "+919556677889", "rating": 3.8},
            {"id": 10, "name": "Dr. Suresh Babu", "special": "Cardiologist", "fee": 1400, "phone": "+919667788990", "rating": 4.5}
        ]

        # Top controls: Search + Payment filter + Sorting + Theme toggle
        controls = ct.CTkFrame(self)
        controls.pack(fill="x", padx=12, pady=(10, 6))

        # Search
        self.search_entry = ct.CTkEntry(controls, placeholder_text="Search by name or specialty...")
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0,8))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())

        # Payment filter: All / Free / Paid
        self.payment_filter = ct.CTkOptionMenu(controls, values=["All", "Free", "Paid"], command=lambda _: self.refresh_list())
        self.payment_filter.grid(row=0, column=1, padx=(0,8))

        # Sort options
        self.sort_var = ct.CTkOptionMenu(controls,
                                         values=["Default", "Rating (High→Low)", "Price (Low→High)", "Specialization (A→Z)"],
                                         command=lambda _: self.refresh_list())
        self.sort_var.grid(row=0, column=2, padx=(0,8))

        # Dark/Light toggle
        self.theme_button = ct.CTkButton(controls, text="Toggle Theme", width=110, command=self.toggle_theme)
        self.theme_button.grid(row=0, column=3)

        controls.grid_columnconfigure(0, weight=1)

        # Scrollable area for doctors
        self.list_frame = ct.CTkScrollableFrame(self, width=660, height=520)
        self.list_frame.pack(padx=12, pady=(0,12), fill="both", expand=False)

        # Initially populated list
        self.refresh_list(animate=True)

    def toggle_theme(self):
        current = ct.get_appearance_mode()
        ct.set_appearance_mode("Light" if current == "Dark" else "Dark")

    def refresh_list(self, animate=False):
        # clear old list
        for w in self.list_frame.winfo_children():
            w.destroy()

        q = self.search_entry.get().lower().strip()
        pay_filter = self.payment_filter.get() if hasattr(self.payment_filter, "get") else "All"
        sort_choice = self.sort_var.get() if hasattr(self.sort_var, "get") else "Default"

        # Filter
        filtered = []
        for d in self.doctors:
            name_ok = q in d["name"].lower() or q in d["special"].lower() or q == ""
            if not name_ok:
                continue
            if pay_filter == "Free" and d["fee"] != 0:
                continue
            if pay_filter == "Paid" and d["fee"] == 0:
                continue
            filtered.append(d)

        # Sorting
        if sort_choice == "Rating (High→Low)":
            filtered.sort(key=lambda x: x.get("rating", 0), reverse=True)
        elif sort_choice == "Price (Low→High)":
            filtered.sort(key=lambda x: x.get("fee", 0))
        elif sort_choice == "Specialization (A→Z)":
            filtered.sort(key=lambda x: x.get("special", "").lower())
        # Default = keep original order

        # Create cards
        # We'll add a subtle highlight animation: flash from a brighter color to normal
        for i, doc in enumerate(filtered):
            card = ct.CTkFrame(self.list_frame, fg_color="#262626", corner_radius=12)
            card.pack(fill="x", padx=10, pady=(8, 6))

            toprow = ct.CTkFrame(card, fg_color="transparent")
            toprow.pack(fill="x", pady=(8,2), padx=10)

            name_lbl = ct.CTkLabel(toprow, text=f"{doc['name']}", font=ct.CTkFont(size=15, weight="bold"))
            name_lbl.pack(side="left", anchor="w")

            rating_text = f"{doc['rating']:.1f} ({_rating_to_stars(doc['rating'])})"
            ct.CTkLabel(toprow, text=rating_text).pack(side="right", anchor="e")

            mid = ct.CTkFrame(card, fg_color="transparent")
            mid.pack(fill="x", padx=10, pady=2)

            ct.CTkLabel(mid, text=f"Specialty: {doc['special']}").pack(side="left", anchor="w")
            fee_text = "Free" if doc["fee"] == 0 else f"₹{doc['fee']}"
            ct.CTkLabel(mid, text=f" | Fee: {fee_text}").pack(side="left", anchor="w", padx=(8,0))

            # Bottom row buttons
            brow = ct.CTkFrame(card, fg_color="transparent")
            brow.pack(fill="x", padx=10, pady=(6,10))

            ct.CTkButton(brow,
                         text="📞 Call",
                         width=110,
                         command=lambda d=doc: self.call_doctor(d)).pack(side="right", padx=(8,0))

            ct.CTkButton(brow,
                         text="📋 Details",
                         width=110,
                         command=lambda d=doc: self.show_details(d)).pack(side="right", padx=(8,0))

            # Subtle animation: flash highlight then return to normal
            def animate_card(widget, iterations=6, base=0):
                # alternate between slightly lighter and normal
                if base >= iterations:
                    # ensure final normal color
                    try:
                        widget.configure(fg_color="#262626")
                    except:
                        pass
                    return
                if base % 2 == 0:
                    try:
                        widget.configure(fg_color="#2f2f2f")
                    except:
                        pass
                else:
                    try:
                        widget.configure(fg_color="#262626")
                    except:
                        pass
                widget.after(80, lambda: animate_card(widget, iterations, base + 1))

            # schedule animation slightly staggered
            self.after(60 * i, lambda w=card: animate_card(w))

    def show_details(self, doc):
        # Small detail popup; can be extended to a full page
        info = f"Name: {doc['name']}\nSpecialty: {doc['special']}\nFee: {'Free' if doc['fee']==0 else '₹'+str(doc['fee'])}\nRating: {doc['rating']}\nPhone: {doc.get('phone','N/A')}"
        messagebox.showinfo("Doctor details", info)

    def call_doctor(self, doc):
        """
        Desktop: show simulated call popup and phone number.
        If you're on a platform that supports 'tel:' URI (like mobile), you can try to open it.
        For Android real-call integration see the Kivy example (separate snippet).
        """

        phone = doc.get("phone")
        if not phone:
            messagebox.showerror("No phone", "No phone number available for this doctor.")
            return

        # Show simulated call dialog
        res = messagebox.askquestion("Call Doctor", f"Do you want to call {doc['name']} at {phone}?")
        if res == "yes":
            # On many desktop environments you can't place real calls; show info
            # On Android or mobile, a tel: URL could be used; attempt but handle failure
            try:
                import webbrowser
                webbrowser.open(f"tel:{phone}")
                # for many desktops this will either do nothing or be handled by an associated app
            except Exception as e:
                messagebox.showinfo("Calling (simulated)", f"Simulated calling {doc['name']} at {phone}\n\nError trying tel: scheme: {e}")
