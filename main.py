import tkinter as tk
from tkinter import messagebox, Menu
import subprocess, os, sys, ctypes
import requests
import json
import webbrowser
import platform

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)

def get_persistent_path(filename):
    if platform.system() == "Windows":
        appdata = os.getenv('APPDATA')
        your_app_folder = os.path.join(appdata, "XieXieVPN")
        os.makedirs(your_app_folder, exist_ok=True)
        return os.path.join(your_app_folder, filename)
    else:
        home = os.path.expanduser("~")
        your_app_folder = os.path.join(home, ".XieXieVPN")
        os.makedirs(your_app_folder, exist_ok=True)
        return os.path.join(your_app_folder, filename)

AUTOSTART_FILE = get_persistent_path("autostart_state.txt")

def save_autostart_state(state: bool):
    with open(AUTOSTART_FILE, "w", encoding="utf-8") as f:
        f.write("1" if state else "0")

def load_autostart_state() -> bool:
    if os.path.exists(AUTOSTART_FILE):
        with open(AUTOSTART_FILE, "r", encoding="utf-8") as f:
            return f.read().strip() == "1"
    return False

def get_exe_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

exe_dir = get_exe_dir()

proxy_state = 0

def toggle_autostart():
    global proxy_state
    try:
        save_autostart_state(chk_autostart.get())
        exe_path = sys.executable
        arg1 = "1"
        tr_value = f"\"{exe_path}\" {arg1}"
        cmd = [
                "schtasks",
                "/Create",
                "/SC", "ONLOGON",
                "/TN", "simplevpn",
                "/TR", tr_value,
                "/RL", "HIGHEST",
                "/F",
        ]
        try:
             result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
               print(e.stderr)
        if chk_autostart.get():
            subprocess.run(['schtasks', '/Change', '/TN', 'simplevpn', '/ENABLE'], capture_output=True, text=True, check=True)
        else:
            subprocess.run(['schtasks', '/Change', '/TN', 'simplevpn', '/DISABLE'], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to modify autostart task: {e.stderr}\nReturn code: {e.returncode}")

def on_chk_change(*args):
    toggle_autostart()

def set_general_proxy():
    global proxy_state
    try:
        subprocess.run(["cmd", "/c", resource_path("close.bat")], capture_output=True, text=True, check=True)
        subprocess.run(["cmd", "/c", resource_path("internet.bat")], capture_output=True, text=True, check=True)
        messagebox.showinfo("Information", "VPN setup successfully")
        btn_general_proxy.config(state="disabled")
        btn_close_proxy.config(state="normal")
        proxy_state = 1
        toggle_autostart()
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to set general proxy: {e.stderr}")

def close_proxy():
    global proxy_state
    try:
        subprocess.run(["cmd", "/c", resource_path("close.bat")], capture_output=True, text=True, check=True)
        messagebox.showinfo("Information", "VPN is closed")
        btn_close_proxy.config(state="disabled")
        btn_general_proxy.config(state="normal")
        proxy_state = 0
        toggle_autostart()
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to close proxy: {e.stderr}")

def on_closing():
    close_state = btn_close_proxy["state"]
    general_state = btn_general_proxy["state"]
    if close_state == "normal":
        if general_state == "disabled":
            try:
                subprocess.run(["cmd", "/c", resource_path("close.bat")], capture_output=True, text=True, check=True)
                messagebox.showinfo("Information", "VPN is temporarily closed")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to close proxy on exit: {e.stderr}")
    window.destroy()

def save_uuid(uuid):
    with open(get_persistent_path("uuid.txt"), "w", encoding="utf-8") as f:
        f.write(uuid)

def load_uuid():
    path_ = get_persistent_path("uuid.txt")
    if os.path.exists(path_):
        with open(path_, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def remove_uuid_file():
    path_ = get_persistent_path("uuid.txt")
    if os.path.exists(path_):
        os.remove(path_)

def check_login():
    entered_uuid = entry_uuid.get().strip()
    try:
        response = requests.post("https://vvv.xiexievpn.com/login", json={"code": entered_uuid})
        if response.status_code == 200:
            if chk_remember.get():
                save_uuid(entered_uuid)
            login_window.destroy()
            show_main_window(entered_uuid)
        else:
            remove_uuid_file()
            if response.status_code == 401:
                messagebox.showerror("Error", "invalid code")
            elif response.status_code == 403:
                messagebox.showerror("Error", "This code has expired")
            else:
                messagebox.showerror("Error", "Server Error")
    except requests.exceptions.RequestException as e:
        remove_uuid_file()
        messagebox.showerror("Error", f"Unable to connect to server: {e}")

def on_remember_changed(*args):
    if not chk_remember.get():
        remove_uuid_file()

def do_adduser(uuid):
    try:
        requests.post(
            "https://vvv.xiexievpn.com/adduser",
            json={"code": uuid},
            timeout=2
        )
    except requests.exceptions.RequestException as e:
        print(f"{e}")

def poll_getuserinfo(uuid):
    try:
        response = requests.post(
            "https://vvv.xiexievpn.com/getuserinfo",
            json={"code": uuid},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        response_data = response.json()
        v2rayurl = response_data.get("v2rayurl", "")
        zone = response_data.get("zone", "")

        if v2rayurl:
            parse_and_write_config(v2rayurl)
            return
        else:
            window.after(3000, lambda: poll_getuserinfo(uuid))

    except requests.exceptions.RequestException as e:
        window.after(3000, lambda: poll_getuserinfo(uuid))

def parse_and_write_config(url_string):
    try:
        # 以 vless:// 开头
        if not url_string.startswith("vless://"):
            messagebox.showerror("Error", "not valid data）")
            return

        uuid = url_string.split("@")[0].split("://")[1]
        domain = url_string.split("@")[1].split(":")[0].split(".")[0]
        jsonport_string = url_string.split(":")[2].split("?")[0]
        jsonport = int(jsonport_string)
        sni = url_string.split("sni=")[1].split("#")[0].replace("www.", "")

        config_data = {
            "log": {
                "loglevel": "error"
            },
                "dns": {
        "servers": [
            {
                "tag": "bootstrap", 
                "address": "223.5.5.5", 
                "domains": [ ], 
                "expectIPs": [
                    "geoip:cn"
                ], 
                "detour": "direct"
            }, 
            {
                "tag": "remote-doh", 
                "address": "https://dns.google/dns-query ", 
                "detour": "proxy"
            }, 
            "localhost"
        ], 
        "queryStrategy": "UseIPv4"
    },
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    {
                "type": "field", 
                "inboundTag": [
                    "dns-in"
                ], 
                "outboundTag": "proxy"
            }, 
                    {
                        "type": "field",
                        "domain": ["geosite:category-ads-all"],
                        "outboundTag": "block"
                    },
                    {
                        "type": "field",
                        "protocol": ["bittorrent"],
                        "outboundTag": "direct"
                    },
                    {
                        "type": "field",
                        "domain": ["geosite:geolocation-!cn"],
                        "outboundTag": "proxy"
                    },
                    {
                        "type": "field",
                        "ip": ["geoip:cn", "geoip:private"],
                        "outboundTag": "proxy"
                    }
                ]
            },
            "inbounds": [
                {
            "tag": "dns-in", 
            "listen": "127.0.0.1", 
            "port": 53, 
            "protocol": "dokodemo-door", 
            "settings": {
                "address": "8.8.8.8", 
                "port": 53, 
                "network": "tcp,udp"
            }
        },
                {
                    "listen": "127.0.0.1",
                    "port": 10808,
                    "protocol": "socks"
                },
                {
                    "listen": "127.0.0.1",
                    "port": 1080,
                    "protocol": "http"
                }
            ],
            "outbounds": [
                {
                    "protocol": "vless",
                    "settings": {
                        "vnext": [
                            {
                                "address": f"{domain}.rocketchats.xyz",
                                "port": 443,
                                "users": [
                                    {
                                        "id": uuid,
                                        "encryption": "none",
                                        "flow": "xtls-rprx-vision"
                                    }
                                ]
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "reality",
                        "realitySettings": {
                            "show": False,
                            "fingerprint": "chrome",
                            "serverName": f"{domain}.rocketchats.xyz",
                            "publicKey": "mUzqKeHBc-s1m03iD8Dh1JoL2B9JwG5mMbimEoJ523o",
                            "shortId": "",
                            "spiderX": ""
                        }
                    },
                    "tag": "proxy"
                },
                {
                    "protocol": "freedom",
                    "tag": "direct"
                },
                {
                    "protocol": "blackhole",
                    "tag": "block"
                }
            ]
        }

        with open(resource_path("config.json"), "w", encoding="utf-8") as config_file:
            json.dump(config_data, config_file, indent=4)

    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Error", f"{e}")

def fetch_config_data(uuid):
    try:
        print(f"{uuid}")

        # 请求服务器获取配置数据
        response = requests.post(
            "https://vvv.xiexievpn.com/getuserinfo",
            json={"code": uuid},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Text: {response.text}")

        try:
            response_data = response.json() 
            with open("server_response.txt", "w", encoding="utf-8") as f:
                f.write(f"Response Status Code: {response.status_code}\n")
                f.write(f"Response Headers: {response.headers}\n")
                f.write("Response JSON:\n")
                json.dump(response_data, f, indent=4, ensure_ascii=False)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Not JSON。")
            return
            
        if response.status_code != 200:
            print(f"{response.status_code}")
            messagebox.showerror("Error", f"{response.status_code}")
            return

        if "v2rayurl" not in response_data:
            messagebox.showerror("Error", "No valid data")
            return

        url_string = response_data["v2rayurl"].strip()
        if not url_string.startswith("vless://"):
            messagebox.showerror("Error", "No valid data")
            return

        try:
            uuid = url_string.split("@")[0].split("://")[1]
            domain = url_string.split("@")[1].split(":")[0].split(".")[0]
            jsonport_string = url_string.split(":")[2].split("?")[0]
            jsonport = int(jsonport_string)
            sni = url_string.split("sni=")[1].split("#")[0].replace("www.", "")
            
            config_data = {
                "log": {
                    "loglevel": "error"
                },
                "routing": {
                    "domainStrategy": "IPIfNonMatch",
                    "rules": [
                        {
                            "type": "field",
                            "domain": ["geosite:category-ads-all"],
                            "outboundTag": "block"
                        },
                        {
                            "type": "field",
                            "protocol": ["bittorrent"],
                            "outboundTag": "direct"
                        },
                        {
                            "type": "field",
                            "domain": ["geosite:geolocation-!cn"],
                            "outboundTag": "proxy"
                        },
                        {
                            "type": "field",
                            "ip": ["geoip:cn", "geoip:private"],
                            "outboundTag": "proxy"
                        }
                    ]
                },
                "inbounds": [
                    {
                        "listen": "127.0.0.1",
                        "port": 10808,
                        "protocol": "socks"
                    },
                    {
                        "listen": "127.0.0.1",
                        "port": 1080,
                        "protocol": "http"
                    }
                ],
                "outbounds": [
                    {
                        "protocol": "vless",
                        "settings": {
                            "vnext": [
                                {
                                    "address": f"{domain}.rocketchats.xyz",
                                    "port": 443,
                                    "users": [
                                        {
                                            "id": uuid,
                                            "encryption": "none",
                                            "flow": "xtls-rprx-vision"
                                        }
                                    ]
                                }
                            ]
                        },
                        "streamSettings": {
                            "network": "tcp",
                            "security": "reality",
                            "realitySettings": {
                                "show": False,
                                "fingerprint": "chrome",
                                "serverName": f"{domain}.rocketchats.xyz",
                                "publicKey": "mUzqKeHBc-s1m03iD8Dh1JoL2B9JwG5mMbimEoJ523o",
                                "shortId": "",
                                "spiderX": ""
                            }
                        },
                        "tag": "proxy"
                    },
                    {
                        "protocol": "freedom",
                        "tag": "direct"
                    },
                    {
                        "protocol": "blackhole",
                        "tag": "block"
                    }
                ]
            }

            with open(resource_path("config.json"), "w", encoding="utf-8") as config_file:
                json.dump(config_data, config_file, indent=4)

        except Exception as e:
            print(f"{e}")
            messagebox.showerror("Error", f"{e}")

    except requests.exceptions.RequestException as e:
        print(f"{e}")
        messagebox.showerror("Error", f"无法连接到服务器: {e}")

def fetch_config_data(uuid):
    try:
        response = requests.post(
            "https://vvv.xiexievpn.com/getuserinfo",
            json={"code": uuid},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        response_data = response.json()
        v2rayurl = response_data.get("v2rayurl", "")
        zone = response_data.get("zone", "")

        if not v2rayurl and not zone:
            do_adduser(uuid)
            window.after(10, lambda: poll_getuserinfo(uuid))

        elif not v2rayurl:
            window.after(10, lambda: poll_getuserinfo(uuid))

        else:
            parse_and_write_config(v2rayurl)

    except requests.exceptions.RequestException as e:
        print(f"{e}")
        messagebox.showerror("Error", f"{e}")

def show_main_window(uuid):
    global window, btn_general_proxy, btn_close_proxy, chk_autostart
    window = tk.Tk()
    window.title("xiexie vpn")
    window.geometry("300x250")
    window.iconbitmap(resource_path("favicon.ico"))

    window.protocol("WM_DELETE_WINDOW", on_closing)

    btn_general_proxy = tk.Button(window, text="open vpn", command=set_general_proxy)
    btn_close_proxy = tk.Button(window, text="close vpn", command=close_proxy)
    btn_general_proxy.pack(pady=10)
    btn_close_proxy.pack(pady=10)

    chk_autostart = tk.BooleanVar()
    chk_autostart.set(load_autostart_state())
    chk_autostart.trace_add("write", on_chk_change)

    chk_autostart_button = tk.Checkbutton(window, text="autostart", variable=chk_autostart, command=toggle_autostart)
    chk_autostart_button.pack(pady=10)

    lbl_switch_region = tk.Label(window, text="switch region", fg="blue", cursor="hand2")
    lbl_switch_region.pack(pady=5)
    lbl_switch_region.bind("<Button-1>", lambda event: (
        messagebox.showinfo("switch region", "This application needs to be restarted after switching regions"),
        webbrowser.open(f"https://xiexievpn.com/app.html?code={uuid}")
    ))

    fetch_config_data(uuid)

    if len(sys.argv) > 1:
        try:
            start_state = int(sys.argv[1])
            if start_state == 1:
                set_general_proxy()
        except ValueError:
            pass

    window.deiconify()
    window.attributes('-topmost', True)
    window.attributes('-topmost', False)     

    window.mainloop()

# Login window
login_window = tk.Tk()
login_window.title("login")
login_window.geometry("300x200")
login_window.iconbitmap("favicon.ico")

label_uuid = tk.Label(login_window, text="your access code:")
label_uuid.pack(pady=10)

entry_uuid = tk.Entry(login_window)
entry_uuid.pack(pady=5)
entry_uuid.bind("<Control-Key-a>", lambda event: entry_uuid.select_range(0, tk.END))
entry_uuid.bind("<Control-Key-c>", lambda event: login_window.clipboard_append(entry_uuid.selection_get()))
entry_uuid.bind("<Control-Key-v>", lambda event: entry_uuid.insert(tk.INSERT, login_window.clipboard_get()))

menu = Menu(entry_uuid, tearoff=0)
menu.add_command(label="copy", command=lambda: login_window.clipboard_append(entry_uuid.selection_get()))
menu.add_command(label="paste", command=lambda: entry_uuid.insert(tk.INSERT, login_window.clipboard_get()))
menu.add_command(label="select all", command=lambda: entry_uuid.select_range(0, tk.END))

def show_context_menu(event):
    menu.post(event.x_root, event.y_root)

entry_uuid.bind("<Button-3>", show_context_menu)

chk_remember = tk.BooleanVar()
chk_remember_button = tk.Checkbutton(login_window, text="automatically login next time", variable=chk_remember)
chk_remember_button.pack(pady=5)

btn_login = tk.Button(login_window, text="login", command=check_login)
btn_login.pack(pady=10)

saved_uuid = load_uuid()
if saved_uuid:
    entry_uuid.insert(0, saved_uuid)
    check_login()

login_window.mainloop()

