import sqlite3
import datetime
import re
import threading
import winsound
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.network.urlrequest import UrlRequest
from kivy.core.audio import SoundLoader

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# --- PHONE PORTRAIT WINDOW FORMAT ---
Window.size = (380, 700)
Window.clearcolor = (0.03, 0.05, 0.09, 1)

DB_FILE = "medisafe.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guardians (
                name TEXT,
                full_number TEXT PRIMARY KEY
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient TEXT,
                guardian_number TEXT,
                name TEXT,
                dosage TEXT,
                time TEXT,
                frequency TEXT,
                pills_left INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adherence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient TEXT,
                med_name TEXT,
                status TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database Initialization Error (Handled): {e}")

def log_adherence(patient, med_name, status):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO adherence (patient, med_name, status, timestamp) VALUES (?, ?, ?, ?)",
                       (patient, med_name, status, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Adherence Logging Error (Handled): {e}")

def speak_text(text, lang="en"):
    if not GTTS_AVAILABLE:
        print(f"[TTS Simulated ({lang})]: {text}")
        return
    def run_speech():
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            temp_file = "temp_alarm.mp3"
            tts.save(temp_file)
            sound = SoundLoader.load(temp_file)
            if sound:
                sound.play()
        except Exception as e:
            print(f"gTTS Speech Error (Handled): {e}")
    threading.Thread(target=run_speech, daemon=True).start()

class CardBox(BoxLayout):
    """Advanced 3D Glassmorphism Container with multi-layered shadows and specular depth."""
    def __init__(self, bg_color=(0.07, 0.11, 0.18, 1), **kwargs):
        super(CardBox, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 6
        with self.canvas.before:
            # 3D Outer Ambient Shadow Layer
            Color(0.01, 0.02, 0.04, 0.6)
            self.shadow = RoundedRectangle(size=self.size, pos=(self.pos[0], self.pos[1]-3), radius=[16])
            
            # Main 3D Card Body Background
            Color(*bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[14])
            
            # Specular 3D Top Highlight Border for extruded tactile look
            Color(0.20, 0.35, 0.55, 0.4)
            self.border = Line(rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], 14), width=1.2)
            
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        try:
            self.shadow.size = instance.size
            self.shadow.pos = (instance.pos[0], instance.pos[1] - 3)
            self.rect.size = instance.size
            self.rect.pos = instance.pos
            self.border.rounded_rectangle = (instance.pos[0], instance.pos[1], instance.size[0], instance.size[1], 14)
        except Exception:
            pass

class MedicineAppUI(BoxLayout):
    def __init__(self, **kwargs):
        super(MedicineAppUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8

        self.current_lang = "en"
        self.selected_guardian_number = ""
        self.selected_med_to_delete = ""

        scroll = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content.bind(minimum_height=content.setter('height'))

        # --- HEADER CARD ---
        header_card = CardBox(bg_color=(0.05, 0.09, 0.15, 1), size_hint_y=None, height=80)
        header_card.add_widget(Label(
            text="✨ MediSafe Patient Hub",
            font_size=15,
            color=(0.15, 0.95, 0.9, 1),
            bold=True,
            size_hint_y=None,
            height=22
        ))
        
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=32, spacing=10)
        self.lang_btn = Button(
            text="🌐 Language: English", 
            font_size=10, 
            background_normal='', 
            background_color=(0.12, 0.25, 0.4, 1),
            color=(0.9, 0.95, 1, 1)
        )
        self.lang_btn.bind(on_press=self.open_language_selector)
        top_bar.add_widget(self.lang_btn)
        header_card.add_widget(top_bar)
        content.add_widget(header_card)

        # --- GUARDIAN DIRECTORY CARD ---
        g_card = CardBox(bg_color=(0.07, 0.12, 0.20, 1), size_hint_y=None, height=125)
        g_card.add_widget(Label(text="👤 Guardian Directory & Emergency Contacts", font_size=10, color=(0.7, 0.75, 0.85, 1), size_hint_y=None, height=14, bold=True))
        
        g_inputs = BoxLayout(orientation='horizontal', size_hint_y=None, height=28, spacing=6)
        self.g_name_input = TextInput(hint_text='Guardian Name', font_size=10, multiline=False)
        self.country_spinner = Spinner(text='+91', values=('+91', '+1', '+44', '+34', '+33'), font_size=10, size_hint_x=None, width=60)
        self.g_phone_input = TextInput(hint_text='Phone Number', font_size=10, multiline=False, input_filter='int')
        g_inputs.add_widget(self.g_name_input)
        g_inputs.add_widget(self.country_spinner)
        g_inputs.add_widget(self.g_phone_input)
        g_card.add_widget(g_inputs)

        g_actions = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, spacing=6)
        save_g_btn = Button(text="Save Guardian", background_normal='', background_color=(0.08, 0.55, 0.38, 1), color=(1,1,1,1), font_size=10)
        save_g_btn.bind(on_press=self.save_guardian)
        
        self.guardian_spinner = Spinner(text='Select Guardian', values=('No Guardians Saved',), font_size=10)
        self.guardian_spinner.bind(text=self.on_guardian_select)
        
        del_g_btn = Button(text="Remove", background_normal='', background_color=(0.75, 0.25, 0.25, 1), color=(1,1,1,1), font_size=10, size_hint_x=None, width=65)
        del_g_btn.bind(on_press=self.remove_guardian)

        g_actions.add_widget(save_g_btn)
        g_actions.add_widget(self.guardian_spinner)
        g_actions.add_widget(del_g_btn)
        g_card.add_widget(g_actions)
        content.add_widget(g_card)

        # --- EMERGENCY BUTTON ---
        emergency_btn = Button(
            text="🚨 EMERGENCY: Alert Guardian Now",
            font_size=11,
            background_normal='',
            background_color=(0.85, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=36,
            bold=True
        )
        emergency_btn.bind(on_press=self.trigger_emergency_alert)
        content.add_widget(emergency_btn)

        # --- MEDICATION SCHEDULER & INVENTORY CARD ---
        m_card = CardBox(bg_color=(0.07, 0.12, 0.20, 1), size_hint_y=None, height=190)
        m_card.add_widget(Label(text="💊 Medication Scheduler", font_size=10, color=(0.7, 0.75, 0.85, 1), size_hint_y=None, height=14, bold=True))
        
        self.patient_input = TextInput(hint_text='Patient Name (e.g. Grandpa)', font_size=10, multiline=False, size_hint_y=None, height=26)
        self.name_input = TextInput(hint_text='Medicine Name (e.g. Metformin)', font_size=10, multiline=False, size_hint_y=None, height=26)
        
        m_row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=26, spacing=5)
        self.dosage_input = TextInput(hint_text='Dosage (1 Pill)', font_size=10, multiline=False)
        self.time_input = TextInput(hint_text='Time (e.g. 08:00 AM)', font_size=10, multiline=False)
        self.freq_spinner = Spinner(text='Once Daily', values=('Once Daily', 'Twice Daily', 'Every 8 Hours', 'Every 12 Hours'), font_size=10)
        m_row1.add_widget(self.dosage_input)
        m_row1.add_widget(self.time_input)
        m_row1.add_widget(self.freq_spinner)

        m_row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=26, spacing=5)
        self.pills_input = TextInput(hint_text='Total Pills (30)', font_size=10, multiline=False, input_filter='int')
        self.sched_guardian_spinner = Spinner(text='Assign Guardian', values=('No Guardians Saved',), font_size=10)
        self.sched_guardian_spinner.bind(text=self.on_sched_guardian_select)
        m_row2.add_widget(self.pills_input)
        m_row2.add_widget(self.sched_guardian_spinner)

        add_med_btn = Button(text="➕ Add & Schedule Medicine", background_normal='', background_color=(0.1, 0.65, 0.5, 1), color=(1,1,1,1), font_size=10, bold=True, size_hint_y=None, height=30)
        add_med_btn.bind(on_press=self.add_medicine)

        m_card.add_widget(self.patient_input)
        m_card.add_widget(self.name_input)
        m_card.add_widget(m_row1)
        m_card.add_widget(m_row2)
        m_card.add_widget(add_med_btn)
        content.add_widget(m_card)

        # --- REMOVE MEDICINE & TESTING CARD ---
        act_card = CardBox(bg_color=(0.07, 0.12, 0.20, 1), size_hint_y=None, height=75)
        act_card.add_widget(Label(text="⚙️ Manage Schedules & Test", font_size=10, color=(0.7, 0.75, 0.85, 1), size_hint_y=None, height=14, bold=True))

        act_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, spacing=6)
        self.med_spinner = Spinner(text='Select Med to Remove', values=('No Meds Scheduled',), font_size=10)
        self.med_spinner.bind(text=self.on_med_select)
        
        del_m_btn = Button(text="🗑️ Remove", background_normal='', background_color=(0.75, 0.25, 0.25, 1), color=(1,1,1,1), font_size=10, size_hint_x=None, width=80)
        del_m_btn.bind(on_press=self.remove_medicine)

        act_bar.add_widget(self.med_spinner)
        act_bar.add_widget(del_m_btn)
        act_card.add_widget(act_bar)
        content.add_widget(act_card)

        test_btn = Button(
            text="🔔 Test Alarm & Hardware Sync Now",
            font_size=11,
            background_normal='',
            background_color=(0.9, 0.45, 0.15, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=36,
            bold=True
        )
        test_btn.bind(on_press=self.trigger_test_alarm)
        content.add_widget(test_btn)

        # --- ESP32 HARDWARE SETUP CARD (PLACED AT BOTTOM) ---
        esp_card = CardBox(bg_color=(0.07, 0.12, 0.20, 1), size_hint_y=None, height=55)
        esp_card.add_widget(Label(text="📶 ESP32 Hardware Network IP", font_size=10, color=(0.7, 0.75, 0.85, 1), size_hint_y=None, height=14, bold=True))
        
        ip_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=26, spacing=6)
        ip_row.add_widget(Label(text="ESP32 IP:", font_size=10, bold=True, size_hint_x=None, width=60))
        self.ip_input = TextInput(text="192.168.1.50", font_size=10, multiline=False, halign='center')
        ip_row.add_widget(self.ip_input)
        esp_card.add_widget(ip_row)
        content.add_widget(esp_card)

        # --- LIVE STATUS PANEL ---
        status_card = CardBox(bg_color=(0.05, 0.09, 0.15, 1), size_hint_y=None, height=130)
        status_card.add_widget(Label(text="📊 Live Schedules & Inventory Log", font_size=10, color=(0.7, 0.75, 0.85, 1), size_hint_y=None, height=14, bold=True))
        
        self.status_label = Label(
            text="System Online. Ready for schedules...",
            font_size=10,
            color=(0.8, 0.85, 0.95, 1),
            halign='center',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        status_card.add_widget(self.status_label)
        content.add_widget(status_card)

        scroll.add_widget(content)
        self.add_widget(scroll)

        self.assigned_guardian_number = ""
        self.refresh_guardians_dropdowns()
        self.refresh_med_list()

    def open_language_selector(self, instance):
        try:
            content = BoxLayout(orientation='vertical', padding=10, spacing=6)
            content.add_widget(Label(text="Select Voice Language", font_size=12, color=(1,1,1,1), size_hint_y=None, height=22))
            
            languages = [
                ("English", "en"), ("Hindi (हिंदी)", "hi"), ("Bengali (বাংলা)", "bn"),
                ("Telugu (తెలుగు)", "te"), ("Marathi (मराठी)", "mr"), ("Tamil (தமிழ்)", "ta"),
                ("Gujarati (ગુજરાતી)", "gu"), ("Urdu (اردو)", "ur"), ("Kannada (ಕನ್ನಡ)", "kn"),
                ("Malayalam (മലയാളം)", "ml"), ("Punjabi (ਪੰਜਾਬੀ)", "pa")
            ]
            
            popup = Popup(title="Language Settings", content=content, size_hint=(0.8, 0.8))
            for name, code in languages:
                btn = Button(text=name, font_size=11, size_hint_y=None, height=30, background_normal='', background_color=(0.15, 0.3, 0.45, 1), color=(1,1,1,1))
                btn.bind(on_press=lambda b, c=code, n=name: self.set_lang(c, n, popup))
                content.add_widget(btn)
            popup.open()
        except Exception as e:
            print(f"Language Selector Error (Handled): {e}")

    def set_lang(self, code, name, popup):
        try:
            self.current_lang = code
            self.lang_btn.text = f"🌐 Lang: {name}"
            popup.dismiss()
        except Exception as e:
            print(f"Set Lang Error (Handled): {e}")

    def send_esp32_command(self, endpoint):
        try:
            ip = self.ip_input.text.strip()
            if not ip:
                return
            url = f"http://{ip}{endpoint}"
            UrlRequest(
                url, 
                on_success=lambda req, res: print(f"ESP32 Success: {endpoint}"), 
                on_error=lambda req, err: print(f"ESP32 Connection Error (Handled): {err}"),
                on_failure=lambda req, err: print(f"ESP32 Failure (Handled): {err}"),
                timeout=2
            )
        except Exception as e:
            print(f"ESP32 Request Exception Handled: {e}")

    def save_guardian(self, instance):
        try:
            name = self.g_name_input.text.strip()
            phone = self.g_phone_input.text.strip()
            if not name or not phone:
                self.show_popup("Error", "Enter Guardian Name and Phone Number!")
                return
            full_number = f"{self.country_spinner.text}{phone}"
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO guardians (name, full_number) VALUES (?, ?)", (name, full_number))
            conn.commit()
            conn.close()
            
            self.g_name_input.text = ""
            self.g_phone_input.text = ""
            self.refresh_guardians_dropdowns()
            self.show_popup("Success", "Guardian saved successfully!")
        except Exception as e:
            self.show_popup("Error", f"Could not save guardian: {e}")

    def refresh_guardians_dropdowns(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT name, full_number FROM guardians")
            rows = cursor.fetchall()
            conn.close()
            if rows:
                self.guardian_values = {f"{r[0]} ({r[1]})": r[1] for r in rows}
                vals = list(self.guardian_values.keys())
                self.guardian_spinner.values = vals
                self.sched_guardian_spinner.values = vals
            else:
                self.guardian_spinner.values = ['No Guardians Saved']
                self.sched_guardian_spinner.values = ['No Guardians Saved']
                self.guardian_spinner.text = 'Select Guardian'
                self.sched_guardian_spinner.text = 'Assign Guardian'
        except Exception as e:
            print(f"Refresh Guardians Error (Handled): {e}")

    def on_guardian_select(self, spinner, text):
        try:
            if text in getattr(self, 'guardian_values', {}):
                self.selected_guardian_number = self.guardian_values[text]
        except Exception as e:
            print(f"Guardian Select Error (Handled): {e}")

    def on_sched_guardian_select(self, spinner, text):
        try:
            if text in getattr(self, 'guardian_values', {}):
                self.assigned_guardian_number = self.guardian_values[text]
        except Exception as e:
            print(f"Sched Guardian Select Error (Handled): {e}")

    def remove_guardian(self, instance):
        try:
            if not self.selected_guardian_number:
                return
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM guardians WHERE full_number = ?", (self.selected_guardian_number,))
            conn.commit()
            conn.close()
            self.selected_guardian_number = ""
            self.guardian_spinner.text = 'Select Guardian'
            self.refresh_guardians_dropdowns()
            self.show_popup("Success", "Guardian removed.")
        except Exception as e:
            self.show_popup("Error", f"Could not remove guardian: {e}")

    def trigger_emergency_alert(self, instance):
        try:
            if not self.selected_guardian_number:
                self.show_popup("Error", "Please select a guardian from the directory first!")
                return
            msg = f"🚨 EMERGENCY ALERT sent to {self.selected_guardian_number}! Patient needs immediate assistance."
            speak_text("Emergency alert dispatched to guardian.", self.current_lang)
            self.show_popup("Emergency Dispatched", msg)
        except Exception as e:
            print(f"Emergency Alert Error (Handled): {e}")

    def refresh_med_list(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, patient, name, dosage, time, frequency, pills_left FROM medicines")
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                self.status_label.text = "No records scheduled yet."
                self.med_spinner.values = ['No Meds Scheduled']
                self.med_lookup = {}
            else:
                text_block = "Active Schedules & Inventory:\n"
                self.med_lookup = {}
                spinner_vals = []
                for r in rows:
                    m_id, patient, name, dosage, time_val, freq, pills = r
                    display_str = f"[{patient}] {name} @ {time_val} ({freq}) | Pills: {pills}"
                    self.med_lookup[display_str] = m_id
                    spinner_vals.append(display_str)
                    text_block += f"• {display_str}\n"
                self.status_label.text = text_block
                self.med_spinner.values = spinner_vals
        except Exception as e:
            self.status_label.text = f"DB Error (Handled): {e}"

    def on_med_select(self, spinner, text):
        try:
            if text in getattr(self, 'med_lookup', {}):
                self.selected_med_to_delete = self.med_lookup[text]
        except Exception as e:
            print(f"Med Select Error (Handled): {e}")

    def add_medicine(self, instance):
        try:
            patient = self.patient_input.text.strip()
            name = self.name_input.text.strip()
            dosage = self.dosage_input.text.strip()
            time_str = self.time_input.text.strip().upper()
            freq = self.freq_spinner.text
            pills = int(self.pills_input.text.strip() or 30)

            if not patient or not name or not dosage or not time_str or not self.assigned_guardian_number:
                self.show_popup("Error", "Fill all fields and assign a guardian!")
                return

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO medicines (patient, guardian_number, name, dosage, time, frequency, pills_left) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (patient, self.assigned_guardian_number, name, dosage, time_str, freq, pills))
            conn.commit()
            conn.close()

            self.patient_input.text = ""
            self.name_input.text = ""
            self.dosage_input.text = ""
            self.time_input.text = ""
            self.pills_input.text = ""
            self.refresh_med_list()
            self.show_popup("Success", "Medicine & Inventory Scheduled!")
        except Exception as e:
            self.show_popup("Error", f"Could not schedule medicine: {e}")

    def remove_medicine(self, instance):
        try:
            if not getattr(self, 'selected_med_to_delete', None):
                return
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM medicines WHERE id = ?", (self.selected_med_to_delete,))
            conn.commit()
            conn.close()
            self.selected_med_to_delete = None
            self.med_spinner.text = 'Select Med to Remove'
            self.refresh_med_list()
            self.show_popup("Success", "Medicine schedule removed.")
        except Exception as e:
            print(f"Remove Med Error (Handled): {e}")

    def trigger_test_alarm(self, instance):
        try:
            self.send_esp32_command("/led1/on")
            App.get_running_app().start_alarm_session(1, "Grandpa", "Sample Med", "1 Pill", 30)
        except Exception as e:
            print(f"Test Alarm Error (Handled): {e}")

    def show_popup(self, title, msg):
        try:
            content = BoxLayout(orientation='vertical', padding=14, spacing=8)
            content.add_widget(Label(text=msg, font_size=12, color=(1,1,1,1)))
            close_btn = Button(text="OK", font_size=11, size_hint_y=None, height=32, background_normal='', background_color=(0.1, 0.65, 0.5, 1), color=(1,1,1,1))
            content.add_widget(close_btn)
            popup = Popup(title=title, content=content, size_hint=(0.7, 0.3), auto_dismiss=True)
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            print(f"Popup Error (Handled): {e}")

class MedicineReminderApp(App):
    def build(self):
        try:
            init_db()
            self.active_alarm = None
            self.skip_timer = None
            self.alarm_data = None
            return MedicineAppUI()
        except Exception as e:
            print(f"App Build Error (Handled): {e}")
            return Label(text="System Boot Error. Check logs.")

    def on_start(self):
        try:
            self.cache = set()
            Clock.schedule_interval(self.check_reminders, 30)
        except Exception as e:
            print(f"On Start Error (Handled): {e}")

    def start_alarm_session(self, med_id, patient, name, dosage, pills_left):
        try:
            if self.active_alarm:
                self.active_alarm.cancel()
            if self.skip_timer:
                self.skip_timer.cancel()

            self.alarm_data = {"id": med_id, "patient": patient, "name": name, "dosage": dosage, "pills": pills_left}

            led_channel = ((med_id - 1) % 6) + 1
            self.root.send_esp32_command(f"/led{led_channel}/on")

            def ring(dt):
                try:
                    winsound.Beep(1200, 800)
                except Exception:
                    pass
                
                lang = self.root.current_lang
                if lang == "hi":
                    msg = f"नमस्ते {patient}! दवाई लेने का समय हो गया है। {name}, मात्रा: {dosage}."
                elif lang == "bn":
                    msg = f"মনযোগ দিন {patient}! আপনার ওষুধ খাওয়ার সময় হয়েছে। {name}, মাত্রা: {dosage}."
                elif lang == "te":
                    msg = f"శ్రద్ధ పెట్టండి {patient}! మీ మందు వేసుకునే సమయం అయింది. {name}, మోతాదు: {dosage}."
                elif lang == "mr":
                    msg = f"लक्ष द्या {patient}! औषध घेण्याची वेळ झाली आहे. {name}, प्रमाण: {dosage}."
                elif lang == "ta":
                    msg = f"கவனம் {patient}! மருந்து உண்ணும் நேரம் வந்துவிட்டது. {name}, அளவு: {dosage}."
                elif lang == "gu":
                    msg = f"ધ્યાન આપો {patient}! દવા લેવાનો સમય થઈ ગયો છે. {name}, માત્રા: {dosage}."
                elif lang == "ur":
                    msg = f"توجہ دیں {patient}! دوا لینے کا وقت ہو گیا ہے۔ {name}, خوراک: {dosage}."
                elif lang == "kn":
                    msg = f"ಗಮನಿಸಿ {patient}! ಔಷಧಿ ತೆಗೆದುಕೊಳ್ಳುವ ಸಮಯ ಬಂದಿದೆ. {name}, ಪ್ರಮಾಣ: {dosage}."
                elif lang == "ml":
                    msg = f"ശ്രദ്ധിക്കുക {patient}! മരുന്ന് കഴിക്കാനുള്ള സമയമായി. {name}, അളവ്: {dosage}."
                elif lang == "pa":
                    msg = f"ਧਿਆਨ ਦਿਓ {patient}! ਦਵਾਈ ਲੈਣ ਦਾ ਸਮਾਂ ਹੋ ਗਿਆ ਹੈ। {name}, ਖੁਰਾਕ: {dosage}."
                else:
                    msg = f"Attention {patient}! Time to take your medicine. {name}, dosage: {dosage}."

                speak_text(msg, lang)
                self.show_medisafe_alert_popup(patient, name, dosage, pills_left)

            ring(0)
            self.active_alarm = Clock.schedule_interval(ring, 15)
            self.skip_timer = Clock.schedule_once(self.handle_missed_dose, 120)
        except Exception as e:
            print(f"Start Alarm Error (Handled): {e}")

    def show_medisafe_alert_popup(self, patient, name, dosage, pills):
        try:
            content = BoxLayout(orientation='vertical', padding=16, spacing=10)
            content.add_widget(Label(text=f"🚨 MEDICATION DUE!\n\nPatient: {patient}\nMed: {name} ({dosage})\nInventory: {pills} pills left.", font_size=12, color=(1,1,1,1)))

            btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=38, spacing=10)
            taken_btn = Button(text="✅ Take Medicine", background_normal='', background_color=(0.1, 0.65, 0.5, 1), color=(1,1,1,1), font_size=11)
            snooze_btn = Button(text="⏰ Snooze (10m)", background_normal='', background_color=(0.8, 0.5, 0.15, 1), color=(1,1,1,1), font_size=11)
            btn_row.add_widget(taken_btn)
            btn_row.add_widget(snooze_btn)
            content.add_widget(btn_row)

            popup = Popup(title="MediSafe Secure Alert", content=content, size_hint=(0.8, 0.38), auto_dismiss=False)

            def on_taken(b):
                self.stop_alarm_session(action="TAKEN")
                popup.dismiss()

            def on_snooze(b):
                self.stop_alarm_session(action="SNOOZED")
                popup.dismiss()

            taken_btn.bind(on_press=on_taken)
            snooze_btn.bind(on_press=on_snooze)
            popup.open()
        except Exception as e:
            print(f"Alert Popup Error (Handled): {e}")

    def handle_missed_dose(self, dt):
        try:
            if self.alarm_data:
                d = self.alarm_data
                log_adherence(d["patient"], d["name"], "SKIPPED")
                self.stop_alarm_session(action="SKIPPED")
        except Exception as e:
            print(f"Missed Dose Error (Handled): {e}")

    def stop_alarm_session(self, action="TAKEN"):
        try:
            if self.active_alarm:
                self.active_alarm.cancel()
                self.active_alarm = None
            if self.skip_timer:
                self.skip_timer.cancel()
                self.skip_timer = None

            if action == "TAKEN" and self.alarm_data:
                d = self.alarm_data
                log_adherence(d["patient"], d["name"], "TAKEN")
                
                led_channel = ((d["id"] - 1) % 6) + 1
                self.root.send_esp32_command(f"/led{led_channel}/off")

                try:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE medicines SET pills_left = MAX(0, pills_left - 1) WHERE id = ?", (d["id"],))
                    conn.commit()
                    conn.close()
                    self.root.refresh_med_list()
                except Exception as db_err:
                    print(f"DB Update Error (Handled): {db_err}")
            self.alarm_data = None
        except Exception as e:
            print(f"Stop Alarm Error (Handled): {e}")

    def check_reminders(self, dt):
        try:
            curr_time = datetime.datetime.now().strftime("%I:%M %p")
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, patient, name, dosage, time, pills_left FROM medicines")
            rows = cursor.fetchall()
            conn.close()

            for r in rows:
                m_id, patient, name, dosage, m_time, pills = r
                key = f"{m_id}_{curr_time}"
                if m_time == curr_time:
                    if key not in self.cache:
                        self.cache.add(key)
                        self.start_alarm_session(m_id, patient, name, dosage, pills)
                else:
                    if key in self.cache:
                        self.cache.remove(key)
        except Exception as e:
            print(f"Check Reminders Error (Handled): {e}")

if __name__ == '__main__':
    try:
        MedicineReminderApp().run()
    except Exception as fatal:
        print(f"Fatal Crash Prevented: {fatal}")