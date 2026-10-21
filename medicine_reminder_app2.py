from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
import datetime

class MedicineReminderApp(App):
    def build(self):
        # Root layout for portrait/clean mobile & desktop display
        root = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        # Title Header
        root.add_widget(Label(
            text="Smart Medicine Reminder", 
            font_size=22, 
            bold=True, 
            size_hint_y=None, 
            height=40,
            color=(0.1, 0.4, 0.8, 1)
        ))
        
        # ESP32 IP Address Section
        ip_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        ip_layout.add_widget(Label(text="ESP32 IP:", bold=True, size_hint_x=None, height=40, width=70))
        self.ip_input = TextInput(
            text="192.168.1.50", 
            multiline=False, 
            halign='center',
            font_size=15
        )
        ip_layout.add_widget(self.ip_input)
        root.add_widget(ip_layout)
        
        # Status Bar
        self.status_label = Label(
            text="Status: Ready", 
            font_size=13, 
            color=(0.4, 0.4, 0.4, 1), 
            size_hint_y=None, 
            height=25
        )
        root.add_widget(self.status_label)

        # Scrollable container for schedules and manual controls
        scroll = ScrollView(size_hint=(1, 1))
        content_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=12)
        content_layout.bind(minimum_height=content_layout.setter('height'))

        # --- SCHEDULES SECTION (12-Hour Format) ---
        content_layout.add_widget(Label(
            text="-- Schedules (e.g., 08:00 AM) --", 
            font_size=15, 
            bold=True, 
            size_hint_y=None, 
            height=30
        ))
        
        self.time_inputs = []
        default_times = ["08:00 AM", "12:00 PM", "04:00 PM", "08:00 PM", "10:00 PM", "12:00 AM"]
        
        for i in range(1, 7):
            sched_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
            sched_row.add_widget(Label(text=f"Med {i} Time:", bold=True, size_hint_x=None, width=85))
            
            t_input = TextInput(
                text=default_times[i-1], 
                multiline=False, 
                halign='center',
                font_size=14
            )
            self.time_inputs.append(t_input)
            sched_row.add_widget(t_input)
            content_layout.add_widget(sched_row)

        # --- MANUAL CONTROLS SECTION ---
        content_layout.add_widget(Label(
            text="-- Manual Controls --", 
            font_size=15, 
            bold=True, 
            size_hint_y=None, 
            height=35
        ))
        
        for i in range(1, 7):
            row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=40)
            row.add_widget(Label(text=f"Med {i}:", bold=True, size_hint_x=None, width=50))
            
            btn_on = Button(text="ON", background_color=(0.2, 0.7, 0.3, 1))
            btn_on.bind(on_press=lambda instance, x=i: self.send_command(f"/led{x}/on", f"Med {i} Turned ON"))
            row.add_widget(btn_on)
            
            btn_off = Button(text="OFF", background_color=(0.8, 0.2, 0.2, 1))
            btn_off.bind(on_press=lambda instance, x=i: self.send_command(f"/led{x}/off", f"Med {i} Turned OFF"))
            row.add_widget(btn_off)
            
            content_layout.add_widget(row)
            
        # Master Controls
        master_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=10)
        btn_all_on = Button(text="All ON", background_color=(0.1, 0.5, 0.9, 1))
        btn_all_on.bind(on_press=lambda x: self.send_command("/all/on", "All Medicines ON"))
        master_layout.add_widget(btn_all_on)
        
        btn_all_off = Button(text="All OFF", background_color=(0.9, 0.6, 0.1, 1))
        btn_all_off.bind(on_press=lambda x: self.send_command("/all/off", "All Medicines OFF"))
        master_layout.add_widget(btn_all_off)
        
        content_layout.add_widget(master_layout)
        scroll.add_widget(content_layout)
        root.add_widget(scroll)

        # Check schedules every 30 seconds
        Clock.schedule_interval(self.check_schedules, 30)

        return root

    def send_command(self, endpoint, success_message="Success"):
        ip = self.ip_input.text.strip()
        url = f"http://{ip}{endpoint}"
        
        def success_cb(req, result):
            self.status_label.text = f"Status: {success_message}"
            
        def error_cb(req, err):
            self.status_label.text = "Error: Could not reach ESP32"

        UrlRequest(url, on_success=success_cb, on_failure=error_cb, on_error=error_cb, timeout=3)

    def check_schedules(self, dt):
        now = datetime.datetime.now().strftime("%I:%M %p")
        
        for i, t_input in enumerate(self.time_inputs):
            scheduled_time = t_input.text.strip().upper()
            if now == scheduled_time:
                med_num = i + 1
                self.status_label.text = f"Schedule Triggered: Med {med_num}!"
                self.send_command(f"/led{med_num}/on", f"Scheduled Med {med_num} Triggered")

if __name__ == '__main__':
    MedicineReminderApp().run()