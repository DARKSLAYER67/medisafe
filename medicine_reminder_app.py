from datetime import datetime
import sqlite3
import re
import winsound

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle

from database import init_db, DB_FILE, log_adherence
from audio_tts import speak_text
from alerts import trigger_dual_guardian_alerts

# Sleek iPhone-style Dark Glass background
Window.clearcolor = (0.04, 0.06, 0.11, 1)

class CardBox(BoxLayout):
    """A custom container that creates an isolated, rounded glass card for each function."""
    def __init__(self, bg_color=(0.08, 0.12, 0.19, 1), **kwargs):
        super(CardBox, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 12
        self.spacing = 8
        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[14])
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos

class MedicineAppUI(BoxLayout):
    def __init__(self, **kwargs):
        super(MedicineAppUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 14
        self.spacing = 10

        self.current_lang = "en_us"
        self.selected_guardian_number = ""
        self.selected_med_to_delete = ""

        # --- HEADER CARD ---
        header_card = CardBox(bg_color=(0.06, 0.10, 0.16, 1), size_hint_y=None, height=75)
        title = Label(
            text="✨ MediSafe LiquidOS : Isolated Hub",
            font_size=18,
            color=(0.15, 0.9, 0.85, 1),
            bold=True
        )
        header_card.add_widget(title)

        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=32, spacing=10)
        self.lang_btn = Button(
            text="🌐 Language: English", 
            font_size=11, 
            background_normal='', 
            background_color=(0.15, 0.28, 0.42, 1),
            color=(0.9, 0.95, 1, 1)
        )
        self.lang_btn.bind(on_press=self.open_language_selector)
        top_bar.add_widget(self.lang_btn)
        header_card.add_widget(top_bar)
        self.add_widget(header_card)

        # --- CARD 1: GUARDIAN MANAGEMENT FUNCTION ---
        g_card = CardBox(bg_color=(0.08, 0.13, 0.20, 1), size_hint_y=None, height=115)
        g_card.add_widget(Label(text="👤 Guardian Directory & Emergency Contacts", font_size=12, color=(0.7, 0.75, 0.85, 1), size_hint_y=None, height=18, bold=True))
        
        g_inputs = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, spacing=6)
        self.g_name_input = TextInput(hint_text='Guardian Name', font_size=11, multiline=False)
        self.country_spinner = Spinner(text='+91', values=('+91', '+1', '+44', '+34', '+33'), font_size=11, size_hint_x=None, width=65)
        self.g_phone_input = TextInput(hint_text='Phone Number', font_size=11, multiline=False, input_filter='int')
        g_inputs.add_widget(self.g_name_input)
        g_inputs.add_widget(self.country_spinner)
        g_inputs.add_widget(self.g_phone_input)
        g_card.add_widget(g_inputs)

        g_actions = BoxLayout(orientation='horizontal', size_hint_y=None, height=32, spacing=6)
        save_g_btn = Button(text="Save Guardian", background_normal='', background_color=(0.08, 0.55, 0.38, 1), color=(1,1,1,1), font_size=11)
        save_g_btn.bind(on_press=self.save_guardian)
        
        self.guardian_spinner = Spinner(text='Select Guardian', values=('No Guardians Saved',), font_size=11)
        self.guardian_spinner.bind(text=self.on_guardian_select)
        
        del_g_btn = Button(text="Remove", background_normal='', background_color=(0.75, 0.25, 0.25, 1), color=(1,1,1,1), font_size=11, size_hint_x=None, width=70)
        del_g_btn.bind(on_press=self.remove_guardian)

        g_actions.add_widget(save_g_btn)
        g_actions.add_widget(self.guardian_spinner)
        g_actions.add_widget(del_g_btn)
        g_card.add_widget(g_actions)
        self.add_widget(g_card)

        # --- CARD 2: MEDICINE SCHEDULER & INVENTORY FUNCTION ---
        m_card = CardBox(bg_color=(0.08, 0.13, 0.20, 1), size_hint_y=None, height=170)
        m_card.add_widget(Label(text="💊 Medication Scheduler & Inventory Stock", font_size=12, color=(0.7, 0.75, 0.85, 1), size_hint_y=None, height=18, bold=True))
        
        self.patient_input = TextInput(hint_text='Patient Name (e.g. Grandpa)', font_size=11, multiline=False, size_hint_y=None, height=28)
        self.name_input = TextInput(hint_text='Medicine Name (e.g. Metformin)', font_size=11, multiline=False, size_hint_y=None, height=28)
        
        m_row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=28, spacing=5)
        self.dosage_input = TextInput(hint_text='Dosage (1 Pill)', font_size=11, multiline=False)
        self.time_input = TextInput(hint_text='Time 24h (14:30)', font_size=11, multiline=False)
        self.freq_spinner = Spinner(text='Once Daily', values=('Once Daily', 'Twice Daily', 'Every 8 Hours', 'Every 12 Hours', 'As Needed'), font_size=11)
        m_row1.add_widget(self.dosage_input)
        m_row1.add_widget(self.time_input)
        m_row1.add_widget(self.freq_spinner)

        m_row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=28, spacing=5)
        self.pills_input = TextInput(hint_text='Total Pills (30)', font_size=11, multiline=False, input_filter='int')
        self.rx_input = TextInput(hint_text='Prescription File/Link (Optional)', font_size=11, multiline=False)
        m_row2.add_widget(self.pills_input)
        m_row2.add_widget(self.rx_input)

        m_card.add_widget(self.patient_input)
        m_card.add_widget(self.name_input)
        m_card.add_widget(m_row1)
        m_card.add_widget(m_row2)
        self.add_widget(m_card)

        # --- CARD 3: ACTION & TESTING CONTROLS ---
        act_card = CardBox(bg_color=(0.08, 0.13, 0.20, 1), size_hint_y=None, height=85)
        act_card.add_widget(Label(text="⚙️ Actions & Hardware / Alarm Testing", font_size=12, color=(0.7, 0.75, 0.85, 1), size_hint_y=None, height=18, bold=True))

        act_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=34, spacing=6)
        add_btn = Button(text="➕ Add Med", background_normal='', background_color=(0.1, 0.65, 0.5, 1), color=(1,1,1,1), font_size=11, bold=True)
        add_btn.bind(on_press=self.add_medicine)
        
        self.med_spinner = Spinner(text='Select Med to Remove', values=('No Meds Scheduled',), font_size=11)
        self.med_spinner.bind(text=self.on_med_select)
        
        del_m_btn = Button(text="🗑️ Remove", background_normal='', background_color=(0.75, 0.25, 0.25, 1), color=(1,1,1,1), font_size=11)
        del_m_btn.bind(on_press=self.remove_medicine)

        act_bar.add_widget(add_btn)
        act_bar.add_widget(self.med_spinner)
        act_bar.add_widget(del_m_btn)
        act_card.add_widget(act_bar)
        self.add_widget(act_card)

        test_btn = Button(
            text="🔔 Test Glass Alarm & Dual Alerts Now",
            font_size=12,
            background_normal='',
            background_color=(0.9, 0.45, 0.15, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=36,
            bold=True
        )
        test_btn.bind(on_press=self.trigger_test_alarm)
        self.add_widget(test_btn)

        # --- CARD 4: LIVE DASHBOARD / STATUS PANEL ---
        status_card = CardBox(bg_color=(0.06, 0.10, 0.16, 1))
        status_card.add_widget(Label(text="📊 Live Schedule & Adherence Logs", font_size=12, color=(0.7, 0.75, 0.85, 1), size_hint_y=None, height=18, bold=True))
        
        self.status_label = Label(
            text="System Online. Isolated glass cards active...",
            font_size=11,
            color=(0.8, 0.85, 0.95, 1),
            halign='center',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        status_card.add_widget(self.status_label)
        self.add_widget(status_card)

        self.refresh_guardians_dropdown()
        self.refresh_med_list()

    def open_language_selector(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=6)
        content.add_widget(Label(text="Select Indian Language", font_size=13, color=(1,1,1,1), size_hint_y=None, height=25))
        
        languages = [
            ("English", "en_us"), ("Hindi (हिंदी)", "hi"), ("Bengali (বাংলা)", "bn"),
            ("Telugu (తెలుగు)", "te"), ("Marathi (मराठी)", "mr"), ("Tamil (தமிழ்)", "ta"),
            ("Gujarati (ગુજરાતી)", "gu"), ("Urdu (اردو)", "ur"), ("Kannada (ಕನ್ನಡ)", "kn"),
            ("Malayalam (മലയാളം)", "ml"), ("Punjabi (ਪੰਜਾਬੀ)", "pa")
        ]
        
        popup = Popup(title="Language Settings", content=content, size_hint=(0.7, 0.85))
        for name, code in languages:
            btn = Button(text=name, font_size=12, size_hint_y=None, height=32, background_normal='', background_color=(0.15, 0.3, 0.45, 1), color=(1,1,1,1))
            btn.bind(on_press=lambda b, c=code, n=name: self.set_lang(c, n, popup))
            content.add_widget(btn)
        popup.open()

    def set_lang(self, code, name, popup):
        self.current_lang = code
        self.lang_btn.text = f"🌐 Language: {name}"
        popup.dismiss()

    def save_guardian(self, instance):
        name = self.g_name_input.text.strip()
        phone = self.g_phone_input.text.strip()
        if not name or not phone:
            self.show_popup("Error", "Enter Guardian Name and Phone Number!")
            return
        full_number = f"{self.country_spinner.text}{phone}"
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO guardians (name, full_number) VALUES (?, ?)", (name, full_number))
            conn.commit()
            conn.close()
            self.g_name_input.text = ""
            self.g_phone_input.text = ""
            self.refresh_guardians_dropdown()
            self.show_popup("Success", "Guardian saved permanently!")
        except Exception as e:
            self.show_popup("Error", str(e))

    def refresh_guardians_dropdown(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT name, full_number FROM guardians")
            rows = cursor.fetchall()
            conn.close()
            if rows:
                self.guardian_values = {f"{r[0]} ({r[1]})": r[1] for r in rows}
                self.guardian_spinner.values = list(self.guardian_values.keys())
            else:
                self.guardian_spinner.values = ['No Guardians Saved']
                self.guardian_spinner.text = 'Select Guardian'
        except Exception as e:
            print(e)

    def on_guardian_select(self, spinner, text):
        if text in getattr(self, 'guardian_values', {}):
            self.selected_guardian_number = self.guardian_values[text]

    def remove_guardian(self, instance):
        if not self.selected_guardian_number:
            return
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM guardians WHERE full_number = ?", (self.selected_guardian_number,))
        conn.commit()
        conn.close()
        self.selected_guardian_number = ""
        self.guardian_spinner.text = 'Select Guardian'
        self.refresh_guardians_dropdown()

    def refresh_med_list(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, patient, name, dosage, time, frequency, pills_left, prescription_path FROM medicines")
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                self.status_label.text = "No records scheduled yet."
                self.med_spinner.values = ['No Meds Scheduled']
                self.med_lookup = {}
            else:
                text_block = "💎 Isolated Card Schedules & Inventory:\n"
                self.med_lookup = {}
                spinner_vals = []
                for r in rows:
                    m_id, patient, name, dosage, time_val, freq, pills, rx = r
                    display_str = f"[{patient}] {name} @ {time_val} ({freq}) | Pills: {pills}"
                    self.med_lookup[display_str] = m_id
                    spinner_vals.append(display_str)
                    text_block += f"• {display_str}\n"
                self.status_label.text = text_block
                self.med_spinner.values = spinner_vals
        except Exception as e:
            self.status_label.text = f"DB Error: {e}"

    def on_med_select(self, spinner, text):
        if text in getattr(self, 'med_lookup', {}):
            self.selected_med_to_delete = self.med_lookup[text]

    def add_medicine(self, instance):
        patient = self.patient_input.text.strip()
        name = self.name_input.text.strip()
        dosage = self.dosage_input.text.strip()
        time_str = self.time_input.text.strip()
        freq = self.freq_spinner.text
        pills = int(self.pills_input.text.strip() or 30)
        rx = self.rx_input.text.strip() or "None"

        if not patient or not self.selected_guardian_number or not name or not dosage or not time_str:
            self.show_popup("Error", "Fill all required fields and select a guardian!")
            return

        try:
            normalized_time = datetime.strptime(time_str, "%H:%M").strftime("%H:%M")
        except ValueError:
            self.show_popup("Error", "Time format must be HH:MM (24h)")
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO medicines (patient, guardian_number, name, dosage, time, frequency, prescription_path, pills_left) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (patient, self.selected_guardian_number, name, dosage, normalized_time, freq, rx, pills))
        conn.commit()
        conn.close()

        self.patient_input.text = ""
        self.name_input.text = ""
        self.dosage_input.text = ""
        self.time_input.text = ""
        self.pills_input.text = ""
        self.rx_input.text = ""
        self.refresh_med_list()
        self.show_popup("Success", "Medicine & Inventory Saved!")

    def remove_medicine(self, instance):
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

    def trigger_test_alarm(self, instance):
        p_name = self.patient_input.text.strip() or "Grandpa"
        g_phone = self.selected_guardian_number or "+910000000000"
        App.get_running_app().start_alarm_session(1, p_name, g_phone, "Sample Med", "2 Pills", 10)

    def show_popup(self, title, msg):
        content = BoxLayout(orientation='vertical', padding=14, spacing=8)
        content.add_widget(Label(text=msg, font_size=14, color=(1,1,1,1)))
        close_btn = Button(text="OK", font_size=13, size_hint_y=None, height=38, background_normal='', background_color=(0.1, 0.65, 0.5, 1), color=(1,1,1,1))
        content.add_widget(close_btn)
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.3), auto_dismiss=True)
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

class MedicineReminderApp(App):
    def build(self):
        init_db()
        self.active_alarm = None
        self.skip_timer = None
        self.alarm_data = None
        return MedicineAppUI()

    def on_start(self):
        self.cache = set()
        Clock.schedule_interval(self.check_reminders, 10)

    def start_alarm_session(self, med_id, patient, guardian, name, dosage, pills_left):
        if self.active_alarm:
            self.active_alarm.cancel()
        if self.skip_timer:
            self.skip_timer.cancel()

        self.alarm_data = {"id": med_id, "patient": patient, "guardian": guardian, "name": name, "dosage": dosage, "pills": pills_left}

        def ring(dt):
            try:
                winsound.Beep(1200, 800)
            except:
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

    def show_medisafe_alert_popup(self, patient, name, dosage, pills):
        content = BoxLayout(orientation='vertical', padding=16, spacing=10)
        stock_warning = f"\n⚠️ Low Stock! Only {pills} pills left." if pills <= 5 else f"\nInventory: {pills} pills left."
        content.add_widget(Label(text=f"🚨 MEDICATION DUE!\n\nPatient: {patient}\nMed: {name} ({dosage}){stock_warning}", font_size=14, color=(1,1,1,1)))

        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=10)
        taken_btn = Button(text="✅ Take Medicine", background_normal='', background_color=(0.1, 0.65, 0.5, 1), color=(1,1,1,1), font_size=13)
        snooze_btn = Button(text="⏰ Snooze (10m)", background_normal='', background_color=(0.8, 0.5, 0.15, 1), color=(1,1,1,1), font_size=13)
        btn_row.add_widget(taken_btn)
        btn_row.add_widget(snooze_btn)
        content.add_widget(btn_row)

        popup = Popup(title="MediSafe Card Alert", content=content, size_hint=(0.75, 0.38), auto_dismiss=False)

        def on_taken(b):
            self.stop_alarm_session(action="TAKEN")
            popup.dismiss()

        def on_snooze(b):
            self.stop_alarm_session(action="SNOOZED")
            popup.dismiss()
            Clock.schedule_once(lambda dt: self.trigger_snooze_restart(), 600)

        taken_btn.bind(on_press=on_taken)
        snooze_btn.bind(on_press=on_snooze)
        popup.open()

    def trigger_snooze_restart(self):
        if self.alarm_data:
            d = self.alarm_data
            self.start_alarm_session(d["id"], d["patient"], d["guardian"], d["name"], d["dosage"], d["pills"])

    def handle_missed_dose(self, dt):
        if self.alarm_data:
            d = self.alarm_data
            log_adherence(d["patient"], d["name"], "SKIPPED")
            alert_msg = f"⚠️ MEDISAFE ALERT: {d['patient']} missed their scheduled dose of {d['name']} ({d['dosage']}). Please check on them immediately!"
            trigger_dual_guardian_alerts(d["guardian"], alert_msg)
            self.stop_alarm_session(action="SKIPPED")

    def stop_alarm_session(self, action="TAKEN"):
        if self.active_alarm:
            self.active_alarm.cancel()
            self.active_alarm = None
        if self.skip_timer:
            self.skip_timer.cancel()
            self.skip_timer = None

        if action == "TAKEN" and self.alarm_data:
            d = self.alarm_data
            log_adherence(d["patient"], d["name"], "TAKEN")
            
            dose_str = d["dosage"]
            match = re.search(r'\d+', dose_str)
            pills_to_subtract = int(match.group()) if match else 1

            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("UPDATE medicines SET pills_left = MAX(0, pills_left - ?) WHERE id = ?", (pills_to_subtract, d["id"]))
                conn.commit()
                conn.close()
                self.root.refresh_med_list()
            except Exception as e:
                print(e)
        self.alarm_data = None

    def check_reminders(self, dt):
        curr_time = datetime.now().strftime("%H:%M")
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, patient, guardian_number, name, dosage, time, frequency, pills_left FROM medicines")
            rows = cursor.fetchall()
            conn.close()

            for r in rows:
                m_id, patient, guardian, name, dosage, m_time, freq, pills = r
                key = f"{m_id}_{curr_time}"
                if m_time == curr_time:
                    if key not in self.cache:
                        self.cache.add(key)
                        self.start_alarm_session(m_id, patient, guardian, name, dosage, pills)
                else:
                    if key in self.cache:
                        self.cache.remove(key)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    MedicineReminderApp().run()