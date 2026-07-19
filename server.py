import machine
import network
import socket
import json
import asyncio
from machine import Pin, ADC, PWM, I2C

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='WiFi-name')
ap.config(authmode=3, password='WiFi-password')

pin_numbers = [0, 2, 4, 5]
pins = [machine.Pin(i, machine.Pin.IN) for i in pin_numbers]

pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)

LED_R = Pin(32, Pin.OUT)
LED_G = Pin(15, Pin.OUT)
LED_B = Pin(14, Pin.OUT)

pwm_r = PWM(LED_R, freq=5000)
pwm_g = PWM(LED_G, freq=5000)
pwm_b = PWM(LED_B, freq=5000)

button = Pin(33, Pin.IN, Pin.PULL_UP)

i2c = I2C(0, scl=Pin(22), sda=Pin(23), freq=400000)

MCP_ADDR = 0x18
TEMP_REG_MCP = 0x05

current_duty = 0
current_temp = None
led_mode = "pot"  # "pot" or "temp"

def read_mcp9808():
    try:
        i2c.writeto(MCP_ADDR, bytes([TEMP_REG_MCP]))
        data = i2c.readfrom(MCP_ADDR, 2)
        upper = data[0] & 0x1F
        lower = data[1]
        if upper & 0x10:
            upper = upper & 0x0F
            temp = 256.0 - (upper * 16.0 + lower / 16.0)
        else:
            temp = (upper * 16.0) + (lower / 16.0)
        return round(temp, 3)
    except Exception as e:
        print(f"[ERROR] Temperature read failed: {e}")
        return None

def set_rgb(duty):
    global current_duty
    current_duty = duty
    pwm_r.duty(duty)
    pwm_g.duty(duty)
    pwm_b.duty(duty)

async def sensor_task():
    global current_temp, led_mode
    print("[INFO] Sensor monitoring task started")
    
    while True:
        current_temp = read_mcp9808()
        
        if led_mode == "pot":
            pot_value = pot.read()          # 0-4095
            duty = pot_value >> 2           # 0-1023
            set_rgb(duty)
        elif led_mode == "temp" and current_temp is not None:
            duty = int(max(0, min(1023, (current_temp - 25) * (1023 / 10))))
            set_rgb(duty)
        
        await asyncio.sleep(0.1)

async def button_task():
    global led_mode
    print("[INFO] Button control task started")
    
    while True:
        if button.value() == 0:          # Button pressed
            led_mode = "temp" if led_mode == "pot" else "pot"
            print(f"[INFO] Mode switched to: {led_mode}")
            
            while button.value() == 0:
                await asyncio.sleep(0.05)
            await asyncio.sleep(0.2)
        
        await asyncio.sleep(0.01)

html_template = """<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Sensor Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
        th {{ background-color: #f0f0f0; }}
        a {{ margin-right: 10px; padding: 8px 12px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
        a:hover {{ background-color: #0056b3; }}
    </style>
</head>
<body>
    <h1>ESP32 Sensor Dashboard</h1>
    <p><strong>Mode:</strong> {mode} | <strong>RGB Duty:</strong> {duty} | <strong>Temperature:</strong> {temp} °C</p>
    
    <h2>Digital Pins</h2>
    <table>
        <tr><th>Pin</th><th>Value</th></tr>
        {pin_rows}
    </table>
    
    <h2>Controls</h2>
    <a href="/led?mode=pot">Set Pot Mode</a>
    <a href="/led?mode=temp">Set Temp Mode</a>
    <a href="/sensors">View JSON Data</a>
</body>
</html>
"""

async def handle_client(reader, writer):
    global led_mode
    try:
        request_line = await reader.readline()

        while True:
            line = await reader.readline()
            if not line or line == b'\r\n':
                break
        
        if not request_line:
            writer.close()
            await writer.wait_closed()
            return
        
        req = request_line.decode('utf-8', errors='ignore')
        print(f"[INFO] Request: {req.strip()}")
        
        response_body = ""
        content_type = "text/html"
        status = "200 OK"
        
        if 'GET / ' in req or 'GET /index' in req:
            pin_rows = ''.join([
                f'<tr><td>Pin {pin_numbers[i]}</td><td>{pins[i].value()}</td></tr>'
                for i in range(len(pins))
            ])
            
            response_body = html_template.format(
                mode=led_mode,
                duty=current_duty,
                temp=current_temp if current_temp is not None else "N/A",
                pin_rows=pin_rows
            )
            content_type = "text/html"
        
        elif 'GET /sensors' in req:
            data = {
                "potentiometer": pot.read(),
                "temperature": current_temp,
                "rgb_duty": current_duty,
                "mode": led_mode,
                "button": button.value()
            }
            response_body = json.dumps(data)
            content_type = "application/json"
        
        elif 'GET /pins' in req:
            data = {
                "pins": [
                    {"pin": pin_numbers[i], "value": pins[i].value()}
                    for i in range(len(pins))
                ]
            }
            response_body = json.dumps(data)
            content_type = "application/json"
        
        elif 'GET /led?mode=pot' in req:
            led_mode = "pot"
            data = {"status": "ok", "mode": "pot"}
            response_body = json.dumps(data)
            content_type = "application/json"
        
        elif 'GET /led?mode=temp' in req:
            led_mode = "temp"
            data = {"status": "ok", "mode": "temp"}
            response_body = json.dumps(data)
            content_type = "application/json"
        
        else:
            status = "404 Not Found"
            response_body = "Endpoint not found."
            content_type = "text/plain"
        
        response_header = f"HTTP/1.1 {status}\r\nContent-Type: {content_type}\r\nContent-Length: {len(response_body)}\r\nConnection: close\r\n\r\n"
        response = response_header + response_body
        
        writer.write(response.encode())
        await writer.drain()
        
    except Exception as e:
        print(f"[ERROR] Client handling error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def server_task():
    try:
        server = await asyncio.start_server(handle_client, '0.0.0.0', 80)
        print("[INFO] Web server listening on 0.0.0.0:80")
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"[ERROR] Server error: {e}")


async def main():
    print("[INFO] Starting ESP32 application...")
    await asyncio.gather(sensor_task(), button_task(), server_task())

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("[INFO] Application stopped.")
