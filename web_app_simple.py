from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import threading
from bot import TSUAssistantBot

app = Flask(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
LOGS_PATH = os.path.join(os.path.dirname(__file__), 'logs.txt')

active_bot = None
bot_thread = None

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"user_fio": "Ваше Полное ФИО", "default_duration_minutes": 90, "schedule": []}

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(LOGS_PATH, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    print(log_entry, end='')

def run_bot(event_id, fio, duration):
    global active_bot
    try:
        log_message(f"▶ Запуск бота для мероприятия {event_id}...")
        active_bot = TSUAssistantBot()
        active_bot.start_driver()
        active_bot.login(event_id, fio)
        log_message(f"✓ Успешный вход в мероприятие")
        active_bot.stay_in_lecture(duration)
        log_message(f"✓ Сеанс завершен")
    except Exception as e:
        log_message(f"✗ Ошибка: {e}")
    finally:
        if active_bot:
            active_bot.close()
        active_bot = None

@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    save_config(data)
    log_message(f"✓ Конфиг обновлен: {data['user_fio']}")
    return jsonify({"status": "ok"})

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    global bot_thread, active_bot
    if active_bot is not None:
        return jsonify({"status": "error", "message": "Бот уже запущен"}), 400
    data = request.json
    event_id = data.get('event_id')
    fio = data.get('fio')
    duration = int(data.get('duration', 90))
    if not event_id or not fio:
        return jsonify({"status": "error", "message": "Отсутствуют ID мероприятия или ФИО"}), 400
    bot_thread = threading.Thread(target=run_bot, args=(event_id, fio, duration), daemon=True)
    bot_thread.start()
    return jsonify({"status": "ok", "message": "Бот запущен"})

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    global active_bot
    if active_bot:
        try:
            active_bot.close()
            log_message("✓ Бот остановлен пользователем")
        except:
            pass
        active_bot = None
        return jsonify({"status": "ok", "message": "Бот остановлен"})
    return jsonify({"status": "error", "message": "Бот не запущен"}), 400

@app.route('/api/bot/status', methods=['GET'])
def bot_status():
    global active_bot
    return jsonify({
        "running": active_bot is not None,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    if os.path.exists(LOGS_PATH):
        with open(LOGS_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    open(LOGS_PATH, 'w', encoding='utf-8').close()
    log_message("✓ Логи очищены")
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    if not os.path.exists(LOGS_PATH):
        open(LOGS_PATH, 'w', encoding='utf-8').close()
    log_message("▶ Веб-интерфейс запущен на http://localhost:5000")
    app.run(debug=False, host='localhost', port=5000)
