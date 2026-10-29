from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, time as dt_time
import threading
import time
from bot import TSUAssistantBot

app = Flask(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
LOGS_PATH = os.path.join(os.path.dirname(__file__), 'logs.txt')
SCHEDULE_PATH = os.path.join(os.path.dirname(__file__), 'schedule.json')

active_bot = None
bot_thread = None
scheduler_thread = None
scheduler_running = False

def load_schedule():
    if os.path.exists(SCHEDULE_PATH):
        with open(SCHEDULE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_schedule(schedule):
    with open(SCHEDULE_PATH, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

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
        # greet_in_chat() вызывается автоматически в stay_in_lecture при появлении новых сообщений
        active_bot.stay_in_lecture(duration)
        log_message(f"✓ Сеанс завершен")
    except Exception as e:
        log_message(f"✗ Ошибка: {e}")
    finally:
        active_bot = None

def scheduler_worker():
    global scheduler_running, bot_thread, active_bot
    log_message("📅 Планировщик запущен")
    while scheduler_running:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            schedule = load_schedule()
            config = load_config()
            fio = config.get('user_fio', '')
            
            for lesson in schedule:
                if not lesson.get('enabled', True):
                    continue
                lesson_time = lesson.get('time', '')
                if lesson_time == current_time and active_bot is None:
                    event_id = lesson.get('event_id', '')
                    duration = lesson.get('duration', 90)
                    lesson_name = lesson.get('name', 'Без названия')
                    log_message(f"⏰ Автозапуск: {lesson_name} ({event_id})")
                    bot_thread = threading.Thread(target=run_bot, args=(event_id, fio, duration), daemon=True)
                    bot_thread.start()
                    time.sleep(61)
                    break
        except Exception as e:
            log_message(f"✗ Ошибка планировщика: {e}")
        time.sleep(30)
    log_message("📅 Планировщик остановлен")

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
            # Устанавливаем флаг остановки, чтобы бот корректно завершился
            active_bot.should_stop = True
            log_message("⚠ Сигнал остановки отправлен боту...")
            time.sleep(2)  # Даём время на корректный выход
            # Если бот всё ещё активен, принудительно закрываем
            if active_bot:
                active_bot.close()
            log_message("✓ Бот остановлен пользователем")
        except Exception as e:
            log_message(f"✗ Ошибка при остановке: {e}")
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

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    return jsonify(load_schedule())

@app.route('/api/schedule', methods=['POST'])
def add_schedule_item():
    data = request.json
    schedule = load_schedule()
    new_lesson = {
        "id": len(schedule) + 1,
        "name": data.get('name', 'Без названия'),
        "event_id": data.get('event_id', ''),
        "time": data.get('time', ''),
        "duration": int(data.get('duration', 90)),
        "enabled": True
    }
    schedule.append(new_lesson)
    save_schedule(schedule)
    log_message(f"✓ Добавлена пара: {new_lesson['name']} в {new_lesson['time']}")
    return jsonify({"status": "ok", "lesson": new_lesson})

@app.route('/api/schedule/<int:lesson_id>', methods=['DELETE'])
def delete_schedule_item(lesson_id):
    schedule = load_schedule()
    schedule = [l for l in schedule if l.get('id') != lesson_id]
    for i, lesson in enumerate(schedule):
        lesson['id'] = i + 1
    save_schedule(schedule)
    log_message(f"✓ Удалена пара ID {lesson_id}")
    return jsonify({"status": "ok"})

@app.route('/api/schedule/<int:lesson_id>/toggle', methods=['POST'])
def toggle_schedule_item(lesson_id):
    schedule = load_schedule()
    for lesson in schedule:
        if lesson.get('id') == lesson_id:
            lesson['enabled'] = not lesson.get('enabled', True)
            status = "включена" if lesson['enabled'] else "отключена"
            log_message(f"✓ Пара '{lesson['name']}' {status}")
            break
    save_schedule(schedule)
    return jsonify({"status": "ok"})

@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    global scheduler_thread, scheduler_running
    if scheduler_running:
        return jsonify({"status": "error", "message": "Планировщик уже запущен"}), 400
    scheduler_running = True
    scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
    scheduler_thread.start()
    return jsonify({"status": "ok", "message": "Планировщик запущен"})

@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    global scheduler_running
    scheduler_running = False
    return jsonify({"status": "ok", "message": "Планировщик остановлен"})

@app.route('/api/scheduler/status', methods=['GET'])
def scheduler_status():
    return jsonify({"running": scheduler_running})

if __name__ == '__main__':
    if not os.path.exists(LOGS_PATH):
        open(LOGS_PATH, 'w', encoding='utf-8').close()
    log_message("▶ Веб-интерфейс запущен на http://localhost:5000")
    app.run(debug=False, host='localhost', port=5000)
