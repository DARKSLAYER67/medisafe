import tkinter as tk
import urllib.request

def send_command(endpoint):
    ip = ip_entry.get().strip()
    url = f"http://{ip}{endpoint}"
    try:
        urllib.request.urlopen(url, timeout=2)
        status_label.config(text=f"Success! Sent: {endpoint}", fg="green")
    except Exception as e:
        status_label.config(text="Error: Could not reach ESP32", fg="red")

# Initialize Desktop App Window
root = tk.Tk()
root.title("10-LED Medicine Reminder & Audio Controller")
root.geometry("420x580")
root.config(bg="#f0f0f0")

tk.Label(root, text="ESP32 IP Address:", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=5)
ip_entry = tk.Entry(root, font=("Arial", 11), justify="center", width=18)
ip_entry.insert(0, "10.10.0.2")  # Replace with your ESP32's actual Serial Monitor IP
ip_entry.pack(pady=5)

# Frame for 10 LED & Audio controls
frame = tk.Frame(root, bg="#f0f0f0")
frame.pack(pady=10)

for i in range(1, 11):
    row_frame = tk.Frame(frame, bg="#f0f0f0")
    row_frame.pack(pady=2)
    
    tk.Label(row_frame, text=f"Med {i}:", width=6, bg="#f0f0f0", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
    
    btn_on = tk.Button(row_frame, text="ON", bg="#4CAF50", fg="white", width=8, 
                       command=lambda x=i: send_command(f"/led{x}/on"))
    btn_on.pack(side=tk.LEFT, padx=2)
    
    btn_off = tk.Button(row_frame, text="OFF", bg="#f44336", fg="white", width=8, 
                        command=lambda x=i: send_command(f"/led{x}/off"))
    btn_off.pack(side=tk.LEFT, padx=2)

# Master Controls (All ON / All OFF)
master_frame = tk.Frame(root, bg="#f0f0f0")
master_frame.pack(pady=10)
tk.Button(master_frame, text="All ON", bg="#2196F3", fg="white", width=12, command=lambda: send_command("/all/on")).pack(side=tk.LEFT, padx=5)
tk.Button(master_frame, text="All OFF", bg="#FF9800", fg="white", width=12, command=lambda: send_command("/all/off")).pack(side=tk.LEFT, padx=5)

status_label = tk.Label(root, text="Status: Ready", font=("Arial", 10), bg="#f0f0f0", fg="gray")
status_label.pack(pady=10)

root.mainloop()