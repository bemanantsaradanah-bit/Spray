from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import os
from datetime import datetime
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25
)

# Stocker les dernières données
last_data = {
    "temperature": "--",
    "humidity": "--",
    "time": "En attente..."
}

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>🌡️ ESP32 DHT Monitor - Temps Réel</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 28px;
        }
        .status {
            text-align: center;
            margin-bottom: 20px;
            font-weight: bold;
            font-size: 18px;
        }
        .online { color: #28a745; }
        .offline { color: #dc3545; }
        .sensor-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin: 15px 0;
            text-align: center;
            transition: transform 0.3s;
        }
        .sensor-card:hover {
            transform: translateY(-5px);
        }
        .sensor-value {
            font-size: 48px;
            font-weight: bold;
            margin: 15px 0;
        }
        .sensor-label {
            font-size: 16px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .icon {
            font-size: 40px;
            margin-bottom: 10px;
        }
        .update-time {
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-size: 14px;
        }
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌡️ Moniteur DHT</h1>
        
        <div class="status" id="status">
            <span id="statusText" class="offline">🔴 En attente de connexion...</span>
        </div>
        
        <div class="sensor-card">
            <div class="icon">🌡️</div>
            <div class="sensor-label">Température</div>
            <div class="sensor-value" id="temperature">--°C</div>
        </div>
        
        <div class="sensor-card">
            <div class="icon">💧</div>
            <div class="sensor-label">Humidité</div>
            <div class="sensor-value" id="humidity">--%</div>
        </div>
        
        <div class="update-time">
            📡 Dernière mise à jour : <span id="updateTime">En attente...</span>
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', function() {
            document.getElementById('statusText').className = 'online';
            document.getElementById('statusText').innerHTML = '🟢 Connecté en temps réel';
        });
        
        socket.on('disconnect', function() {
            document.getElementById('statusText').className = 'offline';
            document.getElementById('statusText').innerHTML = '🔴 Déconnecté';
        });
        
        socket.on('update_sensor', function(data) {
            // Mettre à jour température
            document.getElementById('temperature').textContent = data.temperature + '°C';
            // Animation
            document.getElementById('temperature').classList.add('pulse');
            setTimeout(() => {
                document.getElementById('temperature').classList.remove('pulse');
            }, 1000);
            
            // Mettre à jour humidité
            document.getElementById('humidity').textContent = data.humidity + '%';
            document.getElementById('humidity').classList.add('pulse');
            setTimeout(() => {
                document.getElementById('humidity').classList.remove('pulse');
            }, 1000);
            
            // Mettre à jour le temps
            document.getElementById('updateTime').textContent = data.time;
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_PAGE

@socketio.on('connect')
def connect():
    print("✅ Client connecté!", flush=True)
    sys.stdout.flush()
    emit('update_sensor', last_data)

@socketio.on('sensor_data')
def handle_sensor_data(data):
    global last_data
    last_data = {
        "temperature": data.get('temperature', 0),
        "humidity": data.get('humidity', 0),
        "device": data.get('device', 'ESP32'),
        "time": datetime.now().strftime("%H:%M:%S")
    }
    
    print(f"📩 ESP32: 🌡️ {last_data['temperature']}°C | 💧 {last_data['humidity']}%", flush=True)
    sys.stdout.flush()
    
    # Broadcast à tous les clients connectés
    socketio.emit('update_sensor', last_data, broadcast=True)

@socketio.on('disconnect')
def disconnect():
    print("❌ Client déconnecté!", flush=True)
    sys.stdout.flush()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Serveur DHT démarré sur port {port}", flush=True)
    socketio.run(app, host='0.0.0.0', port=port, debug=False)