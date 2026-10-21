import tkinter as tk
import urllib.request

def send_command(endpoint):
    ip = ip_entry.get().strip()
    url = f"http://{ip}{endpoint}"
    try:
        response = urllib.request.urlopen(url, timeout=2)
        data = response.read().decode('utf-8')
        status_label.config(text=f"Success: {data}", fg="green")
    except Exception as e:
        status_label.config(text="Error: Could not reach ESP32", fg="red")

def get_rtc_time():
    ip = ip_entry.get().strip()
    url = f"http://{ip}/time"
    try:
        response = urllib.request.urlopen(url, timeout=2)
        time_str = response.read().decode('utf-8')
        time_display_label.config(text=f"Live RTC Time: {time_str}", fg="#0D47A1")
        status_label.config(text="Fetched RTC time successfully", fg="green")
    except Exception as e:
        time_display_label.config(text="Live RTC Time: Connection Error", fg="red")
        status_label.config(text="Error: Could not reach ESP32", fg="red")

root = tk.Tk()
root.title("6-Channel Medicine Reminder Controller")
root.geometry("450x560")
root.config(bg="#f0f0f0")

# ESP32 IP Address Input
tk.Label(root, text="ESP32 IP Address:", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=5)
ip_entry = tk.Entry(root, font=("Arial", 11), justify="center", width=20)
ip_entry.insert(0, "10.10.0.2")  # Default to your Wokwi or local network IP
ip_entry.pack(pady=5)

# RTC Live Time Display Box
time_frame = tk.Frame(root, bg="#e0e0e0", bd=1, relief=tk.SOLID)
time_frame.pack(pady=8, fill=tk.X, padx=20)
time_display_label = tk.Label(time_frame, text="Live RTC Time: --", font=("Arial", 10, "bold"), bg="#e0e0e0", fg="#333")
time_display_label.pack(pady=5)
tk.Button(time_frame, text="Refresh RTC Time", bg="#607D8B", fg="white", font=("Arial", 9, "bold"), command=get_rtc_time).pack(pady=4)

# 6-LED Control Frame
frame = tk.Frame(root, bg="#f0f0f0")
frame.pack(pady=5)

for i in range(1, 7):
    row_frame = tk.Frame(frame, bg="#f0f0f0")
    row_frame.pack(pady=3)
    
    tk.Label(row_frame, text=f"Med {i}:", width=6, bg="#f0f0f0", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
    
    btn_on = tk.Button(row_frame, text="ON", bg="#4CAF50", fg="white", width=8, 
                       command=lambda x=i: send_command(f"/led{x}/on"))
    btn_on.pack(side=tk.LEFT, padx=3)
    
    btn_off = tk.Button(row_frame, text="OFF", bg="#f44336", fg="white", width=8, 
                        command=lambda x=i: send_command(f"/led{x}/off"))
    btn_off.pack(side=tk.LEFT, padx=3)

# Master Controls
master_frame = tk.Frame(root, bg="#f0f0f0")
master_frame.pack(pady=8)
tk.Button(master_frame, text="All ON", bg="#2196F3", fg="white", width=11, command=lambda: send_command("/all/on")).pack(side=tk.LEFT, padx=5)
tk.Button(master_frame, text="All OFF", bg="#FF9800", fg="white", width=11, command=lambda: send_command("/all/off")).pack(side=tk.LEFT, padx=5)

# Status Bar
status_label = tk.Label(root, text="Status: Ready", font=("Arial", 10), bg="#f0f0f0", fg="gray")
status_label.pack(pady=8)

root.mainloop()