import network
import socket
import ujson as json
import os
import time


# Global variables
CONFIG_FILE = "wifi_config.json"


# ======== Wi-Fi 功能 ========
def start_ap_mode():
    """启动 AP 模式，创建热点"""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="ESP32_Config", authmode=network.AUTH_WPA_WPA2_PSK, password="12345678")
    print("AP started, connect to 'ESP32_Config' with password '12345678'")
    print("Access Web Server at: http://192.168.4.1")


def connect_to_wifi(ssid, password, callback):
    """连接到 Wi-Fi 网络"""
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    print(f"Connecting to Wi-Fi: {ssid}...")
    sta.connect(ssid, password)

    # 等待连接
    for i in range(20):  # 尝试 20 次，每次等待 500ms
        if sta.isconnected():
            print("Connected! Network config:", sta.ifconfig())
            callback(True)
            return True
        time.sleep(0.5)
    
    print("Failed to connect to Wi-Fi")
    callback(False)
    return False


def save_wifi_config(ssid, password):
    """保存 Wi-Fi 配置信息到文件"""
    with open(CONFIG_FILE, "w") as f:
        json.dump({"ssid": ssid, "password": password}, f)
    print("Wi-Fi configuration saved")


def load_wifi_config():
    """从文件加载 Wi-Fi 配置信息"""
    if CONFIG_FILE in os.listdir():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None


# ======== HTTP 服务器 ========
def start_web_server():
    """启动 HTTP 服务器"""
    addr = ('0.0.0.0', 80)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)
    server.listen(5)
    print("Web server started at http://192.168.4.1")
    
    while True:
        client, addr = server.accept()
        request = client.recv(1024).decode('utf-8')
        print("Request received:", request)

        if "GET / " in request:
            # 返回 Wi-Fi 配置页面
            response = """\
HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ESP32 WiFi 配置</title>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
            font-family: Arial, sans-serif;
        }
     .container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        label {
            margin-bottom: 5px;
        }
        input[type="text"], input[type="password"] {
            padding: 9px;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        button {
            padding: 10px 75px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
    </style>
    <script>
        function submitForm(event) {
            event.preventDefault();
            const ssid = document.querySelector('input[name="ssid"]').value;
            const password = document.querySelector('input[name="password"]').value;
            fetch('/wifi_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `ssid=${ssid}&password=${password}`
            })
          .then(response => response.text())
          .then(data => {
                    document.getElementById('status').textContent = data;
                })
          .catch(error => {
                    document.getElementById('status').textContent = 'Error occurred. Please try again.';
                });
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>ESP32 WiFi 配置</h1>
        <form id="wifiForm" onsubmit="submitForm(event)">
            <label>WiFi名称:</label>
            <input type="text" name="ssid">
            <label>密码:</label>
            <input type="password" name="password"><br>
            <button type="submit">连接</button>
        </form>
        <div id="status"></div>
    </div>
</body>
</html>
"""
            client.send(response.encode('utf-8'))
        
        elif "POST /wifi_config" in request:
            # 解析 POST 数据
            body = request.split("\r\n\r\n")[1]
            data = {key: value for key, value in (item.split("=") for item in body.split("&"))}
            ssid = data.get("ssid")
            password = data.get("password")

            # 保存配置并尝试连接 Wi-Fi
            save_wifi_config(ssid, password)
            def connection_callback(success):
                if success:
                    response = "HTTP/1.1 200 OK\r\n\r\nWi-Fi Connected!"
                else:
                    response = "HTTP/1.1 200 OK\r\n\r\nFailed to Connect Wi-Fi. Try Again."
                client.send(response.encode('utf-8'))
            connect_to_wifi(ssid, password, connection_callback)
        
        client.close()


# ======== 主程序 ========
def main():
    # 检查是否有保存的 Wi-Fi 配置
    config = load_wifi_config()
    if config:
        print("Loaded Wi-Fi config:", config)
        if connect_to_wifi(config["ssid"], config["password"], lambda x: None):
            print("Connected to saved Wi-Fi")
            return  # 已连接 Wi-Fi，不需要进入配网模式
    
    # 如果未连接 Wi-Fi，启动 AP 模式和 Web 配置
    start_ap_mode()
    start_web_server()


# 启动程序
if __name__ == "__main__":
    main()
