import schedule
import time
from datetime import datetime
import threading
import json
import os

class Scheduler:
    """Планировщик для автоматического запуска бота по расписанию"""
    
    def __init__(self, config_path, callback, log_func=None):
        self.config_path = config_path
        self.callback = callback
        self.log_func = log_func or print
        self.running = False
        self.thread = None
    
    def load_schedule(self):
        """Загружает расписание из конфига"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('schedule', [])
        except:
            return []
    
    def setup_jobs(self):
        """Настраивает задачи по расписанию"""
        schedule.clear()
        
        schedule_items = self.load_schedule()
        
        days_map = {
            'понедельник': 'monday',
            'вторник': 'tuesday',
            'среда': 'wednesday',
            'четверг': 'thursday',
            'пятница': 'friday',
            'суббота': 'saturday',
            'воскресенье': 'sunday'
        }
        
        for item in schedule_items:
            day_ru = item.get('day', '').lower()
            time_str = item.get('time', '')
            lecture_id = item.get('lecture_id', '')
            duration = item.get('duration_minutes', 90)
            
            if day_ru in days_map and time_str:
                day_en = days_map[day_ru]
                
                # Используем getattr для динамического вызова метода
                job = getattr(schedule.every(), day_en).at(time_str).do(
                    self.callback,
                    lecture_id=lecture_id,
                    duration=duration,
                    day=day_ru,
                    time=time_str
                )
                
                self.log_func(f"✓ Задача запланирована: {day_ru} в {time_str} (ID: {lecture_id})")
    
    def get_next_lecture(self):
        """Возвращает информацию о следующей лекции"""
        schedule_items = self.load_schedule()
        
        days_map = {
            'понедельник': 0,
            'вторник': 1,
            'среда': 2,
            'четверг': 3,
            'пятница': 4,
            'суббота': 5,
            'воскресенье': 6
        }
        
        now = datetime.now()
        current_day = now.weekday()
        current_time = now.strftime('%H:%M')
        
        next_lecture = None
        min_diff = float('inf')
        
        for item in schedule_items:
            day_ru = item.get('day', '').lower()
            time_str = item.get('time', '')
            
            if day_ru in days_map:
                day_num = days_map[day_ru]
                
                # Вычисляем разницу во времени
                if day_num > current_day or (day_num == current_day and time_str > current_time):
                    # Эта неделя
                    diff = (day_num - current_day) * 24 * 60
                    time_parts = time_str.split(':')
                    if len(time_parts) == 2:
                        diff += int(time_parts[0]) * 60 + int(time_parts[1]) - (now.hour * 60 + now.minute)
                else:
                    # Следующая неделя
                    diff = (7 - current_day + day_num) * 24 * 60
                    time_parts = time_str.split(':')
                    if len(time_parts) == 2:
                        diff += int(time_parts[0]) * 60 + int(time_parts[1]) - (now.hour * 60 + now.minute)
                
                if diff > 0 and diff < min_diff:
                    min_diff = diff
                    next_lecture = {
                        'day': day_ru,
                        'time': time_str,
                        'lecture_id': item.get('lecture_id', ''),
                        'duration': item.get('duration_minutes', 90),
                        'minutes_until': int(diff)
                    }
        
        return next_lecture
    
    def run_scheduler(self):
        """Запускает планировщик в отдельном потоке"""
        self.setup_jobs()
        
        print("▶ Планировщик начал работу")
        
        while self.running:
            schedule.run_pending()
            time.sleep(30)  # Проверяем каждые 30 секунд
        
        print("✓ Планировщик остановлен")
    
    def start(self):
        """Запускает планировщик"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Останавливает планировщик"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
