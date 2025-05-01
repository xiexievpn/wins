import tkinter as tk
from tkinter import messagebox, Menu
import subprocess, os, sys, ctypes
import requests
import json
import webbrowser

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)

def get_exe_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

exe_dir = get_exe_dir()
os.chdir(exe_dir)

proxy_state = 0

def toggle_autostart():
    global proxy_state
    try:
        result = subprocess.run(["cmd", "/c", "createplan.bat", str(proxy_state)], capture_output=True, text=True, check=True)
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
        subprocess.run(["cmd", "/c", "close.bat"], capture_output=True, text=True, check=True)
        subprocess.run(["cmd", "/c", "internet.bat"], capture_output=True, text=True, check=True)
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
        subprocess.run(["cmd", "/c", "close.bat"], capture_output=True, text=True, check=True)
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
                subprocess.run(["cmd", "/c", "close.bat"], capture_output=True, text=True, check=True)
                messagebox.showinfo("Information", "VPN is temporarily closed")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to close proxy on exit: {e.stderr}")
    window.destroy()

def save_uuid(uuid):
    with open("uuid.txt", "w") as file:
        file.write(uuid)

def load_uuid():
    if os.path.exists("uuid.txt"):
        with open("uuid.txt", "r") as file:
            return file.read().strip()
    return None

def check_login():
    entered_uuid = entry_uuid.get().strip()
    try:
        response = requests.post("https://vvv.xiexievpn.com/login", json={"code": entered_uuid})
        if response.status_code == 200:
            if chk_remember.get():
                save_uuid(entered_uuid)
            login_window.destroy()
            show_main_window(entered_uuid)
        elif response.status_code == 401:
            messagebox.showerror("Error", "invalid code")
        elif response.status_code == 403:
            messagebox.showerror("Error", "This code has expired")
        else:
            messagebox.showerror("Error", "Server Error")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Unable to connect to server: {e}")

import os

def fetch_config_data(uuid):
    try:
        print(f"传递的 UUID: {uuid}")

        # 请求服务器获取配置数据
        response = requests.post(
            "https://vvv.xiexievpn.com/getuserinfo",
            json={"code": uuid},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        # 打印响应的状态码和详细信息（调试用）
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Text: {response.text}")

        # -- 修改1：将响应内容保存到文件时，推荐也保存原JSON，便于排查 --
        try:
            response_data = response.json()  # 尝试解析 JSON
            # 将 JSON 数据用更友好的方式写入文件
            with open("server_response.txt", "w", encoding="utf-8") as f:
                f.write(f"Response Status Code: {response.status_code}\n")
                f.write(f"Response Headers: {response.headers}\n")
                f.write("Response JSON:\n")
                json.dump(response_data, f, indent=4, ensure_ascii=False)
        except json.JSONDecodeError:
            # 如果服务端确实返回的不是 JSON，或者出错
            print("服务器返回的数据无法解析为 JSON。")
            messagebox.showerror("Error", "服务器返回的数据无法解析为 JSON。")
            return

        # 如果响应状态码不是 200，就直接报错
        if response.status_code != 200:
            print(f"获取配置数据失败，状态码: {response.status_code}")
            messagebox.showerror("Error", f"获取配置数据失败，状态码: {response.status_code}")
            return

        # -- 修改2：从返回的 JSON 数据中获取 "v2rayurl" 字段 --
        if "v2rayurl" not in response_data:
            print("服务器返回的 JSON 中没有 v2rayurl 字段")
            messagebox.showerror("Error", "服务器返回的 JSON 中没有 v2rayurl 字段")
            return

        url_string = response_data["v2rayurl"].strip()
        if not url_string.startswith("vless://"):
            # 如果 v2rayurl 并不是 vless:// 开头，可以进行相应处理
            print("服务器返回的数据不符合预期格式（不是 vless:// 开头）")
            messagebox.showerror("Error", "服务器返回的数据不符合预期格式（不是 vless:// 开头）")
            return

        # -- 修改3：保持你原有的 VLESS URL 解析逻辑 --
        try:
            # 示例：vless://<UUID>@abcd.rocketchats.xyz:443?security=reality&sni=abcd.rocketchats.xyz#...
            # 下面演示了类似的拆分方法
            uuid = url_string.split("@")[0].split("://")[1]
            domain = url_string.split("@")[1].split(":")[0].split(".")[0]
            jsonport_string = url_string.split(":")[2].split("?")[0]
            jsonport = int(jsonport_string)
            sni = url_string.split("sni=")[1].split("#")[0].replace("www.", "")

            print(f"提取的 UUID: {uuid}")
            print(f"提取的 Domain: {domain}")
            print(f"提取的 Port: {jsonport}")
            print(f"提取的 SNI: {sni}")

            # 构建 config.json 的数据结构
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

            current_dir = os.getcwd()
            print(f"当前工作目录: {current_dir}")

            # 写出 config.json
            with open("config.json", "w", encoding="utf-8") as config_file:
                json.dump(config_data, config_file, indent=4)
            print("config.json 文件已成功创建")

        except Exception as e:
            print(f"提取配置信息时发生错误: {e}")
            messagebox.showerror("Error", f"提取配置信息时发生错误: {e}")

    except requests.exceptions.RequestException as e:
        print(f"无法连接到服务器: {e}")
        messagebox.showerror("Error", f"无法连接到服务器: {e}")

def show_main_window(uuid):
    global window, btn_general_proxy, btn_close_proxy, chk_autostart
    window = tk.Tk()
    window.title("xiexie vpn")
    window.geometry("300x250")
    window.iconbitmap("favicon.ico")

    window.protocol("WM_DELETE_WINDOW", on_closing)

    btn_general_proxy = tk.Button(window, text="open vpn", command=set_general_proxy)
    btn_close_proxy = tk.Button(window, text="close vpn", command=close_proxy)
    btn_general_proxy.pack(pady=10)
    btn_close_proxy.pack(pady=10)

    chk_autostart = tk.BooleanVar()
    chk_autostart.trace_add("write", on_chk_change)
    try:
        result = subprocess.run(["schtasks", "/Query", "/TN", "simplevpn"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        if "Enabled" in result.stdout:
            chk_autostart.set(True)
        else:
            chk_autostart.set(False)
    except subprocess.CalledProcessError:
        chk_autostart.set(False)

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

label_uuid = tk.Label(login_window, text="p:")
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
