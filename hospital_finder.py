"""
CustomTkinter app — List hospitals near Coimbatore using OSM (Overpass)
Features:
- Search bar (filter by name/address)
- Filter: All / Open now / Closed / Unknown
- Scrollable list with name, address, opening_hours, status
- Open in Google Maps button
"""

import customtkinter as ctk
import requests
import webbrowser
import datetime
import re
import pytz
from math import radians, cos, sin, asin, sqrt

COIMBATORE_COORD = (11.100824, 77.026695) 
SEARCH_RADIUS_METERS = 7000       
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSM_TIMEOUT = 180               

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def haversine(lat1, lon1, lat2, lon2):
    # returns distance in km
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def overpass_query(lat, lon, radius):
    # Query for hospitals and clinics (nodes/ways/relations)
    query = f"""
    [out:json][timeout:{OSM_TIMEOUT}];
    (
      node["amenity"~"hospital|clinic"](around:{radius},{lat},{lon});
      way["amenity"~"hospital|clinic"](around:{radius},{lat},{lon});
      relation["amenity"~"hospital|clinic"](around:{radius},{lat},{lon});
      node["healthcare"="hospital"](around:{radius},{lat},{lon});
      way["healthcare"="hospital"](around:{radius},{lat},{lon});
      relation["healthcare"="hospital"](around:{radius},{lat},{lon});
    );
    out center tags;
    """
    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=OSM_TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def normalize_address(tags):
    parts = []
    for k in ("addr:full", "addr:street", "addr:housenumber", "addr:city", "addr:postcode", "addr:state"):
        v = tags.get(k)
        if v and v not in parts:
            parts.append(v)
    # fallback to "street" or "place" tag
    if not parts:
        for k in ("street", "place", "name", "operator"):
            v = tags.get(k)
            if v:
                parts.append(v)
                break
    return ", ".join(parts) if parts else "Address not available"

WEEKDAY_MAP = {
    "Mo": 0, "Tu": 1, "We": 2, "Th": 3, "Fr": 4, "Sa": 5, "Su": 6
}

def parse_time_hhmm(s):
    # "HH:MM" -> (hour, minute)
    try:
        h, m = s.split(":")
        return int(h), int(m)
    except Exception:
        return None

def time_in_range(start, end, now):
    # start,end are (h,m); handles overnight ranges (e.g., 22:00-06:00)
    s_minutes = start[0]*60 + start[1]
    e_minutes = end[0]*60 + end[1]
    n_minutes = now.hour*60 + now.minute
    if s_minutes <= e_minutes:
        return s_minutes <= n_minutes < e_minutes
    else:
        # overnight
        return n_minutes >= s_minutes or n_minutes < e_minutes

def check_open_now(opening_hours_str, tz):
    if not opening_hours_str:
        return None
    s = opening_hours_str.strip()
    s = s.replace("−", "-")  # different hyphen chars
    s = s.replace("–", "-")
    s = s.replace(" ", " ")
    s = s.strip()
    lower = s.lower()
    if "24/7" in lower or "24h" in lower or "open 24" in lower:
        return True

    # split on ';' for multiple rules; evaluate in order and return first match
    rules = [r.strip() for r in opening_hours_str.split(";") if r.strip()]
    now = datetime.datetime.now(tz)
    today_wd = now.weekday()  # 0=Monday .. 6=Sunday

    for rule in rules:
        # e.g. "Mo-Fr 09:00-18:00" or "09:00-21:00" or "Mo-Su 10:00-22:00"
        m_day_time = re.match(r"(?:(?P<days>[A-Za-z0-9,\- ]+)\s+)?(?P<times>\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})", rule)
        if not m_day_time:
            # try single time range alone
            m_time = re.match(r"(?P<times>\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})", rule)
            if m_time:
                times = m_time.group("times")
                start_s, end_s = [t.strip() for t in times.split("-")]
                start = parse_time_hhmm(start_s)
                end = parse_time_hhmm(end_s)
                if start and end and time_in_range(start, end, now):
                    return True
                else:
                    # this rule says closed for now (but other rules could match)
                    continue
            else:
                # cannot parse rule -> skip
                continue

        days_part = m_day_time.group("days")
        times = m_day_time.group("times")
        start_s, end_s = [t.strip() for t in times.split("-")]
        start = parse_time_hhmm(start_s)
        end = parse_time_hhmm(end_s)
        if not (start and end):
            continue

        if days_part:
            days_part = days_part.strip()
            # support comma separated or hyphen range: Mo,Tu or Mo-Fr
            matched = False
            # expand each comma-separated segment
            for seg in days_part.split(","):
                seg = seg.strip()
                if "-" in seg:
                    a,b = [x.strip() for x in seg.split("-")]
                    if a in WEEKDAY_MAP and b in WEEKDAY_MAP:
                        a_idx = WEEKDAY_MAP[a]
                        b_idx = WEEKDAY_MAP[b]
                        if a_idx <= b_idx:
                            if a_idx <= today_wd <= b_idx:
                                matched = True
                                break
                        else:
                            # wrap around (e.g., Fr-Mo)
                            if today_wd >= a_idx or today_wd <= b_idx:
                                matched = True
                                break
                else:
                    if seg in WEEKDAY_MAP:
                        if WEEKDAY_MAP[seg] == today_wd:
                            matched = True
                            break
            if not matched:
                # rule doesn't apply for today
                continue

        # rule applies for today -> check time range
        if time_in_range(start, end, now):
            return True
        else:
            return False

    return None  # no rule matched or unknown


def fetch_hospitals(lat=COIMBATORE_COORD[0], lon=COIMBATORE_COORD[1], radius=SEARCH_RADIUS_METERS):
    j = overpass_query(lat, lon, radius)
    elements = j.get("elements", [])
    items = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("operator") or "Unnamed Hospital/Clinic"
        # get coordinates: nodes have lat/lon, ways/relations have center
        if el.get("type") == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        else:
            center = el.get("center") or el.get("bounds")
            if isinstance(center, dict):
                lat = center.get("lat") or center.get("minlat")
                lon = center.get("lon") or center.get("minlon")
            else:
                lat = COIMBATORE_COORD[0]
                lon = COIMBATORE_COORD[1]
        address = normalize_address(tags)
        oh = tags.get("opening_hours")
        items.append({
            "name": name,
            "address": address,
            "lat": lat,
            "lon": lon,
            "tags": tags,
            "opening_hours": oh
        })
    # deduplicate by (name, lat, lon)
    uniq = {}
    for it in items:
        key = (it["name"], round(float(it.get("lat") or 0), 5), round(float(it.get("lon") or 0), 5))
        if key not in uniq:
            uniq[key] = it
    return list(uniq.values())

class HospitalApp(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("Hospitals near Coimbatore (OSM)")
        self.geometry("800x650")
        self.minsize(700, 500)

        # Top frame
        top = ctk.CTkFrame(self)
        top.pack(fill="x", pady=20, padx=20)

        lbl = ctk.CTkLabel(top, text="Hospitals & Clinics — Coimbatore", font=ctk.CTkFont(size=22, weight="bold"))
        lbl.grid(row=0, column=0, sticky="w", padx=(10,0))

        btn_refresh = ctk.CTkButton(top, text="Refresh", command=self.refresh)
        btn_refresh.grid(row=0, column=2, padx=10)

        # Search and filter
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(top, placeholder_text="Search name or address...", textvariable=self.search_var, width=380)
        search_entry.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(12,6))
        search_entry.bind("<KeyRelease>", lambda e: self.apply_filters())

        self.filter_var = ctk.StringVar(value="All")
        rb_frame = ctk.CTkFrame(top)
        rb_frame.grid(row=1, column=2, padx=10, pady=(12,6))
        ctk.CTkLabel(rb_frame, text="Filter:").pack(side="left", padx=(6,4))
        for opt in ["All", "Open now", "Closed", "Unknown"]:
            ctk.CTkRadioButton(rb_frame, text=opt, variable=self.filter_var, value=opt, command=self.apply_filters).pack(side="left", padx=4)

        # Results count label
        self.count_lbl = ctk.CTkLabel(self, text="Loading...", anchor="w")
        self.count_lbl.pack(fill="x", padx=24, pady=(6,0))

        # Scrollable results frame
        self.results_frame = ctk.CTkScrollableFrame(self, width=760, height=420)
        self.results_frame.pack(padx=20, pady=12, fill="both", expand=True)

        # Data storage
        self.all_items = []
        self.displayed_items = []

        # initial load
        self.refresh()

    def clear_results(self):
        for child in self.results_frame.winfo_children():
            child.destroy()

    def refresh(self):
        self.count_lbl.configure(text="Fetching hospitals from OpenStreetMap...")
        self.clear_results()
        try:
            items = fetch_hospitals()
            # compute distance and open status
            tz = pytz.timezone("Asia/Kolkata")
            for it in items:
                lat = float(it.get("lat") or COIMBATORE_COORD[0])
                lon = float(it.get("lon") or COIMBATORE_COORD[1])
                it["distance_km"] = haversine(COIMBATORE_COORD[0], COIMBATORE_COORD[1], lat, lon)
                it["open_now"] = check_open_now(it.get("opening_hours"), tz)
            # sort by distance
            items.sort(key=lambda x: x.get("distance_km", 9999))
            self.all_items = items
            self.count_lbl.configure(text=f"Found {len(items)} results within {SEARCH_RADIUS_METERS/1000:.1f} km")
            self.apply_filters()
        except Exception as e:
            self.count_lbl.configure(text="Failed to fetch data: " + str(e))

    def apply_filters(self):
        q = self.search_var.get().lower().strip()
        filt = self.filter_var.get()
        results = []
        for it in self.all_items:
            name = (it.get("name") or "").lower()
            addr = (it.get("address") or "").lower()
            if q and (q not in name and q not in addr):
                continue
            status = it.get("open_now")
            if filt == "Open now" and status is not True:
                continue
            if filt == "Closed" and status is not False:
                continue
            if filt == "Unknown" and status is not None:
                continue
            results.append(it)
        self.displayed_items = results
        self.render_results()

    def render_results(self):
        self.clear_results()
        if not self.displayed_items:
            lbl = ctk.CTkLabel(self.results_frame, text="No hospitals match your search/filter.", justify="center")
            lbl.pack(pady=20)
            return

        for it in self.displayed_items:
            frame = ctk.CTkFrame(self.results_frame)
            frame.pack(fill="x", padx=12, pady=8)

            title = it.get("name", "Unnamed")
            dist = it.get("distance_km")
            dist_s = f"{dist:.1f} km" if dist is not None else ""
            header = ctk.CTkLabel(frame, text=f"{title}    ({dist_s})", font=ctk.CTkFont(size=16, weight="bold"))
            header.pack(anchor="w", padx=10, pady=(8,2))

            addr = it.get("address", "")
            addr_lbl = ctk.CTkLabel(frame, text=addr, font=ctk.CTkFont(size=12))
            addr_lbl.pack(anchor="w", padx=10)

            oh = it.get("opening_hours") or "Not provided"
            oh_lbl = ctk.CTkLabel(frame, text=f"Opening hours: {oh}", font=ctk.CTkFont(size=11))
            oh_lbl.pack(anchor="w", padx=10, pady=(2,4))

            status = it.get("open_now")
            if status is True:
                status_text = "Open now"
            elif status is False:
                status_text = "Closed now"
            else:
                status_text = "Open/Closed: Unknown"
            status_lbl = ctk.CTkLabel(frame, text=status_text, font=ctk.CTkFont(size=12, weight="bold"))
            status_lbl.pack(anchor="w", padx=10, pady=(0,8))

            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=(0,8))
            lat = it.get("lat")
            lon = it.get("lon")
            def open_maps(lat=lat, lon=lon):
                if lat is None or lon is None:
                    return
                url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                webbrowser.open(url)

            ctk.CTkButton(btn_frame, text="Open in Google Maps", command=open_maps).pack(side="right")

            # Optionally a details button to show tags (small popup)
            def show_tags(tags=it.get("tags")):
                popup = ctk.CTkToplevel(self)
                popup.title("Tags / Details")
                popup.geometry("420x300")
                txt = ctk.CTkTextbox(popup, wrap="word")
                txt.pack(fill="both", expand=True, padx=10, pady=10)
                pretty = "\n".join([f"{k}: {v}" for k,v in (tags or {}).items()])
                txt.insert("0.0", pretty or "No tags")
                txt.configure(state="disabled")
            ctk.CTkButton(btn_frame, text="Details", command=show_tags).pack(side="right", padx=(0,8))

if __name__ == "__main__":
    app = HospitalApp()
    app.mainloop()
