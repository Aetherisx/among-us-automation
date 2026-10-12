import tkinter as tk
from tkinter import ttk
import threading
import time
from collections import deque
import math
import ctypes
import mss
from PIL import Image, ImageTk
import pyperclip

# Windows ekran ölçeklendirme kaymalarını önlemek için DPI ayarı
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Among Us 18 Resmi Renk Veritabanı (İngilizce, Türkçe, Hex, Açık RGB, Gölge RGB)
AMONG_US_COLORS = [
    {"en": "Red",    "tr": "Kırmızı",   "hex": "#C51111", "rgb": (197, 17, 17),   "shadow": (122, 8, 56)},
    {"en": "Blue",   "tr": "Mavi",      "hex": "#132ED1", "rgb": (19, 46, 209),   "shadow": (9, 21, 142)},
    {"en": "Green",  "tr": "K.Yeşil",   "hex": "#117F2D", "rgb": (17, 127, 45),   "shadow": (10, 77, 46)},
    {"en": "Pink",   "tr": "Pembe",     "hex": "#ED54BA", "rgb": (237, 84, 186),  "shadow": (171, 43, 173)},
    {"en": "Orange", "tr": "Turuncu",   "hex": "#EF7D0D", "rgb": (239, 125, 13),  "shadow": (180, 62, 21)},
    {"en": "Yellow", "tr": "Sarı",      "hex": "#F5F557", "rgb": (245, 245, 87),  "shadow": (195, 136, 34)},
    {"en": "Black",  "tr": "Siyah",     "hex": "#3F474E", "rgb": (63, 71, 78),    "shadow": (30, 31, 38)},
    {"en": "White",  "tr": "Beyaz",     "hex": "#D6E0F0", "rgb": (214, 224, 240), "shadow": (131, 148, 191)},
    {"en": "Purple", "tr": "Mor",       "hex": "#6B2FBB", "rgb": (107, 47, 187),  "shadow": (59, 23, 124)},
    {"en": "Brown",  "tr": "Kahve",     "hex": "#71491E", "rgb": (113, 73, 30),   "shadow": (94, 38, 21)},
    {"en": "Cyan",   "tr": "Turkuaz",   "hex": "#38FEDC", "rgb": (56, 254, 220),  "shadow": (36, 168, 190)},
    {"en": "Lime",   "tr": "A.Yeşil",   "hex": "#50EF39", "rgb": (80, 239, 57),   "shadow": (21, 167, 66)},
    {"en": "Maroon", "tr": "Bordo",     "hex": "#5F1D2E", "rgb": (95, 29, 46),    "shadow": (65, 17, 26)},
    {"en": "Rose",   "tr": "Gül/A.Pem", "hex": "#ECC0D3", "rgb": (236, 192, 211), "shadow": (173, 117, 151)},
    {"en": "Banana", "tr": "Krem/Muz",  "hex": "#F0E7A8", "rgb": (240, 231, 168), "shadow": (194, 174, 114)},
    {"en": "Gray",   "tr": "Gri",       "hex": "#758593", "rgb": (117, 133, 147), "shadow": (70, 86, 100)},
    {"en": "Tan",    "tr": "Ten/Haki",  "hex": "#918877", "rgb": (145, 136, 119), "shadow": (81, 66, 62)},
    {"en": "Coral",  "tr": "Mercan",    "hex": "#D76464", "rgb": (215, 100, 100), "shadow": (155, 67, 94)}
]

# The Skeld Bölgelere Göre Odalar (Hızlı Bulmak İçin)
SKELD_ROOMS = {
    "Sol Бölge": ["Reactor", "Security", "Upper Engine", "Lower Engine", "MedBay", "Electrical"],
    "Orta Bölge": ["Cafeteria", "Admin", "Storage", "Hallway (Koridor)"],
    "Sağ Bölge": ["Weapons", "O2", "Navigation", "Shields", "Communications"]
}

class SkeldAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Skeld Kara Kutu & Çevirmen")
        self.root.geometry("460x780+10+10")
        self.root.configure(bg="#18191c")
        self.root.attributes("-topmost", True) # Her zaman üstte tut
        self.root.attributes("-alpha", 0.94)   # Hafif saydamlık

        # Seçili Durumlar
        self.selected_color = tk.StringVar(value="Red")
        self.selected_room = tk.StringVar(value="Electrical")

        # Zaman Makinesi Hafızası (Son 6 kare, her 1.3 saniyede 1 = ~8 saniye)
        self.frames = deque(maxlen=6)
        self.frozen_frames = []
        self.is_frozen = False
        self.current_frame_idx = 0
        self.display_pil_img = None

        self.build_ui()

        # Arka plan ekran yakalayıcıyı başlat
        self.running = True
        self.capture_thread = threading.Thread(target=self.screen_capture_loop, daemon=True)
        self.capture_thread.start()

    def build_ui(self):
        # --- 1. ZAMAN MAKİNESİ & PİKSEL DEDEKTİFİ ---
        tm_frame = tk.LabelFrame(self.root, text=" 🎥 Zaman Makinesi & Kostüm Renk Dedektifi ", 
                                 bg="#18191c", fg="#00ffcc", font=("Segoe UI", 9, "bold"))
        tm_frame.pack(fill="x", padx=8, pady=4)

        btn_bar = tk.Frame(tm_frame, bg="#18191c")
        btn_bar.pack(fill="x", padx=4, pady=2)

        self.freeze_btn = tk.Button(btn_bar, text="🚨 DONDUR (Son 8 Sn)", bg="#d92b2b", fg="white",
                                    font=("Segoe UI", 9, "bold"), command=self.toggle_freeze)
        self.freeze_btn.pack(side="left", padx=2, fill="x", expand=True)

        tk.Button(btn_bar, text="◀ Önceki", bg="#2f3136", fg="white", command=self.prev_frame).pack(side="left", padx=2)
        tk.Button(btn_bar, text="Sonraki ▶", bg="#2f3136", fg="white", command=self.next_frame).pack(side="left", padx=2)

        self.info_lbl = tk.Label(tm_frame, text="İpucu: Dondurup fotoğraftaki karakterin ÇANTASINA tıkla -> Rengi bulur!",
                                 bg="#18191c", fg="#b9bbbe", font=("Segoe UI", 8))
        self.info_lbl.pack()

        # Ekran görüntüsü tuvali (420x236 -> 16:9 oranında)
        self.canvas = tk.Canvas(tm_frame, width=420, height=236, bg="#0f1012", highlightthickness=1, highlightbackground="#444")
        self.canvas.pack(padx=4, pady=4)
        self.canvas.bind("<Button-1>", self.detect_pixel_color)

        # --- 2. SEÇİLİ DURUM GÖSTERGESİ ---
        status_frame = tk.Frame(self.root, bg="#202225", pady=4)
        status_frame.pack(fill="x", padx=8, pady=2)

        tk.Label(status_frame, text="Seçili Kişi:", bg="#202225", fg="#aaa", font=("Segoe UI", 9)).pack(side="left", padx=4)
        self.lbl_sel_color = tk.Label(status_frame, textvariable=self.selected_color, bg="#C51111", fg="white",
                                      font=("Segoe UI", 9, "bold"), width=10)
        self.lbl_sel_color.pack(side="left", padx=4)

        tk.Label(status_frame, text="Seçili Oda:", bg="#202225", fg="#aaa", font=("Segoe UI", 9)).pack(side="left", padx=4)
        self.lbl_sel_room = tk.Label(status_frame, textvariable=self.selected_room, bg="#3b4048", fg="#00ffcc",
                                     font=("Segoe UI", 9, "bold"), width=14)
        self.lbl_sel_room.pack(side="left", padx=4)

        # --- 3. 18 RENK SEÇİCİ ---
        color_frame = tk.LabelFrame(self.root, text=" 🎨 1. Renk Seç (Veya Yukarıdaki Fotoğraftan Üstüne Tıkla) ",
                                    bg="#18191c", fg="#ffffff", font=("Segoe UI", 9, "bold"))
        color_frame.pack(fill="x", padx=8, pady=3)

        for idx, c in enumerate(AMONG_US_COLORS):
            r, col = divmod(idx, 6)
            # Açık renklerde yazıyı siyah yap
            fg_col = "black" if c["en"] in ["Yellow", "White", "Cyan", "Lime", "Rose", "Banana"] else "white"
            btn = tk.Button(color_frame, text=f"{c['en']}\n({c['tr']})", bg=c["hex"], fg=fg_col,
                            font=("Segoe UI", 7, "bold"), width=10, height=2,
                            command=lambda c_obj=c: self.set_color(c_obj))
            btn.grid(row=r, column=col, padx=2, pady=2, sticky="nsew")

        # --- 4. THE SKELD ODA SEÇİCİ ---
        room_frame = tk.LabelFrame(self.root, text=" 🗺️ 2. The Skeld Oda Seç ",
                                   bg="#18191c", fg="#ffffff", font=("Segoe UI", 9, "bold"))
        room_frame.pack(fill="x", padx=8, pady=3)

        for col_idx, (region, rooms) in enumerate(SKELD_ROOMS.items()):
            reg_box = tk.Frame(room_frame, bg="#18191c")
            reg_box.grid(row=0, column=col_idx, padx=3, sticky="n")
            tk.Label(reg_box, text=region, bg="#18191c", fg="#00ffcc", font=("Segoe UI", 8, "bold")).pack()
            for rm in rooms:
                clean_rm = rm.split(" (")[0]
                tk.Button(reg_box, text=rm, bg="#2f3136", fg="white", font=("Segoe UI", 8), width=18,
                          command=lambda r_name=clean_rm: self.selected_room.set(r_name)).pack(pady=1)

        # --- 5. TIKLA & KONUŞ CÜMLE ÜRETİCİ ---
        chat_frame = tk.LabelFrame(self.root, text=" 💬 3. Tıkla -> Otomatik Kopyala (Oyunda Ctrl+V Yap) ",
                                   bg="#18191c", fg="#ffcc00", font=("Segoe UI", 9, "bold"))
        chat_frame.pack(fill="both", expand=True, padx=8, pady=3)

        actions = [
            ("💀 Ceset Burada", lambda c, r: f"Body is in {r}!"),
            ("🏃 Cesetten Kaçtı!", lambda c, r: f"I saw {c} running away from the body in {r}!"),
            ("🔪 Gözümün Önünde Kesti!", lambda c, r: f"{c} killed right in front of me in {r}! 100% {c}, vote {c}!"),
            ("🕳️️ Havalandırmaya (Vent) Girdi!", lambda c, r: f"I saw {c} vent in {r}! Vote {c}!"),
            ("🕵️ Şüpheli Davranıyor (Sus)", lambda c, r: f"{c} was acting very sus in {r}, faking tasks."),
            ("🛡️ Ben Bu Odadaydım (Alibi)", lambda c, r: f"I was in {r} doing my tasks the whole time."),
            ("🤝 Bu Kişi Beni Temizler (Clear)", lambda c, r: f"I was in {r} with {c}, {c} saw me and can clear me."),
            ("✅ Bu Kişi Masum (Görsel Görev)", lambda c, r: f"{c} is safe/clear, I saw {c} do a visual task in {r}."),
            ("❓ Neredeydiniz / Ceset Nerede?", lambda c, r: "Where is the body? Anyone saw anything?"),
            ("⏭️ Emin Değiliz, Skip Basalım", lambda c, r: "No strong info right now, let's skip vote.")
        ]

        for idx, (label_txt, template_fn) in enumerate(actions):
            r, col = divmod(idx, 2)
            btn = tk.Button(chat_frame, text=label_txt, bg="#3b4048", fg="white",
                            activebackground="#5865f2", activeforeground="white",
                            font=("Segoe UI", 8, "bold"), width=28, pady=3,
                            command=lambda fn=template_fn: self.generate_sentence(fn))
            btn.grid(row=r, column=col, padx=3, pady=2, sticky="nsew")

        self.copied_lbl = tk.Label(self.root, text="Hazır! Butona basınca cümle kopyalanır.",
                                   bg="#18191c", fg="#43b581", font=("Segoe UI", 9, "bold"))
        self.copied_lbl.pack(pady=2)

    def set_color(self, c_obj):
        self.selected_color.set(c_obj["en"])
        fg_col = "black" if c_obj["en"] in ["Yellow", "White", "Cyan", "Lime", "Rose", "Banana"] else "white"
        self.lbl_sel_color.config(bg=c_obj["hex"], fg=fg_col)

    def generate_sentence(self, template_fn):
        c = self.selected_color.get()
        r = self.selected_room.get()
        sentence = template_fn(c, r)
        pyperclip.copy(sentence)
        self.copied_lbl.config(text=f"📋 KOPYALANDI: \"{sentence}\"")

    def screen_capture_loop(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1] # Ana ekran
            while self.running:
                if not self.is_frozen:
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    # Hafızayı yormamak ve tuvale tam oturmak için 420x236 boyutuna küçült
                    img_resized = img.resize((420, 236), Image.Resampling.BILINEAR)
                    self.frames.append((time.strftime("%H:%M:%S"), img_resized))
                    self.root.after(0, self.update_canvas_live)
                time.sleep(1.3)

    def update_canvas_live(self):
        if not self.is_frozen and self.frames:
            ts, img = self.frames[-1]
            self.show_image_on_canvas(img, f"CANLI İZLENİYOR ({ts})")

    def toggle_freeze(self):
        if not self.is_frozen:
            self.is_frozen = True
            self.frozen_frames = list(self.frames)
            self.current_frame_idx = len(self.frozen_frames) - 1
            self.freeze_btn.config(text="▶️ CANLIYA DÖN", bg="#43b581")
            self.show_frozen_frame()
        else:
            self.is_frozen = False
            self.freeze_btn.config(text="🚨 DONDUR (Son 8 Sn)", bg="#d92b2b")

    def prev_frame(self):
        if not self.is_frozen:
            self.toggle_freeze()
        if self.frozen_frames and self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self.show_frozen_frame()

    def next_frame(self):
        if self.is_frozen and self.frozen_frames and self.current_frame_idx < len(self.frozen_frames) - 1:
            self.current_frame_idx += 1
            self.show_frozen_frame()

    def show_frozen_frame(self):
        if self.frozen_frames:
            ts, img = self.frozen_frames[self.current_frame_idx]
            sn_once = round((len(self.frozen_frames) - 1 - self.current_frame_idx) * 1.3, 1)
            self.show_image_on_canvas(img, f"DONDURULDU: {sn_once} sn önce ({ts})")

    def show_image_on_canvas(self, pil_img, title_text):
        self.display_pil_img = pil_img
        self.tk_img = ImageTk.PhotoImage(pil_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.canvas.create_rectangle(0, 0, 220, 20, fill="black", stipple="gray50")
        self.canvas.create_text(6, 10, anchor="w", text=title_text, fill="#00ffcc", font=("Segoe UI", 8, "bold"))

    def detect_pixel_color(self, event):
        if not self.display_pil_img:
            return
        x, y = event.x, event.y
        if 0 <= x < 420 and 0 <= y < 236:
            r, g, b = self.display_pil_img.getpixel((x, y))
            best_match = None
            min_dist = float("inf")

            # Hem ana rengi hem de gölge rengini kontrol et (kostüm altı gölgeler için)
            for c in AMONG_US_COLORS:
                for ref_rgb in [c["rgb"], c["shadow"]]:
                    dist = math.sqrt((r - ref_rgb[0])**2 + (g - ref_rgb[1])**2 + (b - ref_rgb[2])**2)
                    if dist < min_dist:
                        min_dist = dist
                        best_match = c

            if best_match:
                self.set_color(best_match)
                self.info_lbl.config(
                    text=f"🎯 Piksel Algılandı: {best_match['en']} ({best_match['tr']}) seçildi!",
                    fg="#ffcc00"
                )

if __name__ == "__main__":
    root = tk.Tk()
    app = SkeldAssistant(root)
    root.mainloop()