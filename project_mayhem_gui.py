"""
Project Mayhem - Desktop GUI для бота входа на лекции ТГУ
Использует PyQt6 для интерфейса
"""

import sys
import json
import threading
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QSpinBox, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QCheckBox, QTimeEdit,
                             QMessageBox, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QAction
from bot import TSUAssistantBot
import schedule

class LogSignal(QObject):
    """Сигнал для безопасной передачи логов в GUI"""
    message = pyqtSignal(str)

class ProjectMayhemGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.active_bot = None
        self.bot_thread = None
        self.scheduler_running = False
        self.scheduler_thread = None
        self.log_signal = LogSignal()
        self.log_signal.message.connect(self.append_log)
        
        self.load_config()
        self.load_schedule()
        self.init_ui()
        self.create_tray_icon()
        
        # Обработчик сигнала от трея
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except:
            self.config = {
                "default_duration_minutes": 90,
                "user_fio": "",
                "firefox_profile_path": ""
            }
    
    def save_config(self):
        """Сохранение конфигурации"""
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def load_schedule(self):
        """Загрузка расписания"""
        try:
            with open('schedule.json', 'r', encoding='utf-8') as f:
                self.schedule_data = json.load(f)
        except:
            self.schedule_data = []
    
    def save_schedule(self):
        """Сохранение расписания"""
        with open('schedule.json', 'w', encoding='utf-8') as f:
            json.dump(self.schedule_data, f, ensure_ascii=False, indent=2)
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Project Mayhem - Бот для входа на лекции ТГУ")
        self.setGeometry(100, 100, 900, 700)
        
        # Устанавливаем иконку
        if os.path.exists("icon.png"):
            self.setWindowIcon(QIcon("icon.png"))
        
        # Темная тема
        self.set_dark_theme()
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Заголовок
        title = QLabel("Project Mayhem")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #38BDF8; padding: 10px;")
        main_layout.addWidget(title)
        
        # Секция запуска
        main_layout.addWidget(self.create_bot_section())
        
        # Секция настроек
        main_layout.addWidget(self.create_settings_section())
        
        # Секция расписания
        main_layout.addWidget(self.create_schedule_section())
        
        # Секция логов
        main_layout.addWidget(self.create_logs_section())
        
    def set_dark_theme(self):
        """Установка темной темы"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(26, 26, 26))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(17, 17, 17))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(34, 34, 34))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(34, 34, 34))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(136, 136, 136))
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 1px solid #333;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                color: #ffffff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QSpinBox, QTimeEdit {
                color: #ffffff;
                background: #111;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
            }
            QTextEdit {
                color: #ffffff;
                background: #111;
                border: 1px solid #333;
                border-radius: 4px;
            }
            QListWidget {
                color: #ffffff;
                background: #111;
                border: 1px solid #333;
            }
            QListWidget::item {
                color: #ffffff;
            }
        """)
        
    def create_bot_section(self):
        """Секция управления ботом"""
        group = QGroupBox("Запуск")
        layout = QVBoxLayout()
        
        # Статус
        self.bot_status_label = QLabel("● Бот остановлен")
        self.bot_status_label.setStyleSheet("padding: 10px; background: #111; border-radius: 4px; border-left: 3px solid #666;")
        layout.addWidget(self.bot_status_label)
        
        # ID мероприятия
        id_layout = QVBoxLayout()
        id_layout.addWidget(QLabel("ID мероприятия:"))
        self.event_id_input = QLineEdit()
        self.event_id_input.setPlaceholderText("Введите ID")
        id_layout.addWidget(self.event_id_input)
        layout.addLayout(id_layout)
        
        # Длительность
        duration_layout = QVBoxLayout()
        duration_layout.addWidget(QLabel("Длительность (минуты):"))
        self.duration_input = QSpinBox()
        self.duration_input.setMinimum(1)
        self.duration_input.setMaximum(300)
        self.duration_input.setValue(self.config.get('default_duration_minutes', 90))
        duration_layout.addWidget(self.duration_input)
        layout.addLayout(duration_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("Запустить")
        self.start_btn.setStyleSheet("background: #38BDF8; color: #000; padding: 10px; font-weight: bold;")
        self.start_btn.clicked.connect(self.start_bot)
        
        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.setStyleSheet("background: #EF4444; color: #fff; padding: 10px; font-weight: bold;")
        self.stop_btn.clicked.connect(self.stop_bot)
        self.stop_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        layout.addLayout(buttons_layout)
        
        group.setLayout(layout)
        return group
    
    def create_settings_section(self):
        """Секция настроек"""
        group = QGroupBox("Настройки")
        layout = QVBoxLayout()
        
        # ФИО
        layout.addWidget(QLabel("ФИО:"))
        self.fio_input = QLineEdit()
        self.fio_input.setText(self.config.get('user_fio', ''))
        layout.addWidget(self.fio_input)
        
        # Кнопка сохранения
        save_btn = QPushButton("Сохранить")
        save_btn.setStyleSheet("background: #38BDF8; color: #000; padding: 10px; font-weight: bold;")
        save_btn.clicked.connect(self.save_fio)
        layout.addWidget(save_btn)
        
        group.setLayout(layout)
        return group
    
    def create_schedule_section(self):
        """Секция расписания"""
        group = QGroupBox("Расписание")
        layout = QVBoxLayout()
        
        # Статус планировщика
        self.scheduler_status_label = QLabel("● Планировщик выключен")
        self.scheduler_status_label.setStyleSheet("padding: 10px; background: #111; border-radius: 4px; border-left: 3px solid #666;")
        layout.addWidget(self.scheduler_status_label)
        
        # Форма добавления пары
        add_layout = QHBoxLayout()
        self.lesson_name_input = QLineEdit()
        self.lesson_name_input.setPlaceholderText("Название пары")
        self.lesson_event_id_input = QLineEdit()
        self.lesson_event_id_input.setPlaceholderText("ID")
        self.lesson_time_input = QTimeEdit()
        self.lesson_time_input.setDisplayFormat("HH:mm")
        self.lesson_duration_input = QSpinBox()
        self.lesson_duration_input.setMinimum(1)
        self.lesson_duration_input.setMaximum(300)
        self.lesson_duration_input.setValue(90)
        
        add_layout.addWidget(self.lesson_name_input, 2)
        add_layout.addWidget(self.lesson_event_id_input, 1)
        add_layout.addWidget(self.lesson_time_input, 1)
        add_layout.addWidget(self.lesson_duration_input, 1)
        layout.addLayout(add_layout)
        
        # Кнопка добавления
        add_btn = QPushButton("Добавить пару")
        add_btn.setStyleSheet("background: #38BDF8; color: #000; padding: 10px; font-weight: bold;")
        add_btn.clicked.connect(self.add_lesson)
        layout.addWidget(add_btn)
        
        # Таблица расписания
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(6)
        self.schedule_table.setHorizontalHeaderLabels(["Название", "ID", "Время", "Длительность", "Вкл", "Действия"])
        self.schedule_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.refresh_schedule_table()
        layout.addWidget(self.schedule_table)
        
        # Кнопки планировщика
        scheduler_buttons = QHBoxLayout()
        self.scheduler_start_btn = QPushButton("Включить планировщик")
        self.scheduler_start_btn.setStyleSheet("background: #38BDF8; color: #000; padding: 10px; font-weight: bold;")
        self.scheduler_start_btn.clicked.connect(self.start_scheduler)
        
        self.scheduler_stop_btn = QPushButton("Выключить планировщик")
        self.scheduler_stop_btn.setStyleSheet("background: #EF4444; color: #fff; padding: 10px; font-weight: bold;")
        self.scheduler_stop_btn.clicked.connect(self.stop_scheduler)
        self.scheduler_stop_btn.setEnabled(False)
        
        scheduler_buttons.addWidget(self.scheduler_start_btn)
        scheduler_buttons.addWidget(self.scheduler_stop_btn)
        layout.addLayout(scheduler_buttons)
        
        group.setLayout(layout)
        return group
    
    def create_logs_section(self):
        """Секция логов"""
        group = QGroupBox("Логи")
        layout = QVBoxLayout()
        
        # Кнопка очистки
        clear_btn = QPushButton("Очистить")
        clear_btn.setStyleSheet("background: #475569; color: #fff; padding: 5px;")
        clear_btn.clicked.connect(self.clear_logs)
        layout.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Текстовое поле логов
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("background: #111; color: #aaa; font-family: monospace; font-size: 12px;")
        self.logs_text.setMaximumHeight(200)
        layout.addWidget(self.logs_text)
        
        group.setLayout(layout)
        return group
    
    def log_message(self, message):
        """Добавление сообщения в лог"""
        self.log_signal.message.emit(message)
    
    def append_log(self, message):
        """Добавление сообщения в текстовое поле (thread-safe)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs_text.append(f"[{timestamp}] {message}")
        self.logs_text.verticalScrollBar().setValue(self.logs_text.verticalScrollBar().maximum())
    
    def clear_logs(self):
        """Очистка логов"""
        self.logs_text.clear()
    
    def save_fio(self):
        """Сохранение ФИО"""
        self.config['user_fio'] = self.fio_input.text()
        self.save_config()
        self.log_message("✓ ФИО сохранено")
        QMessageBox.information(self, "Успех", "ФИО успешно сохранено")
    
    def start_bot(self):
        """Запуск бота"""
        event_id = self.event_id_input.text().strip()
        if not event_id:
            QMessageBox.warning(self, "Ошибка", "Введите ID мероприятия")
            return
        
        fio = self.config.get('user_fio', '')
        if not fio:
            QMessageBox.warning(self, "Ошибка", "Сохраните ФИО в настройках")
            return
        
        duration = self.duration_input.value()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.bot_status_label.setText("● Бот запущен")
        self.bot_status_label.setStyleSheet("padding: 10px; background: #111; border-radius: 4px; border-left: 3px solid #22D3EE; color: #22D3EE;")
        
        self.bot_thread = threading.Thread(target=self.run_bot, args=(event_id, fio, duration))
        self.bot_thread.start()
    
    def run_bot(self, event_id, fio, duration):
        """Запуск бота в отдельном потоке"""
        try:
            self.log_message(f"▶ Запуск бота для мероприятия {event_id}...")
            self.active_bot = TSUAssistantBot()
            self.active_bot.start_driver()
            self.active_bot.login(event_id, fio)
            self.log_message(f"✓ Успешный вход в мероприятие")
            self.active_bot.stay_in_lecture(duration)
            self.log_message(f"✓ Сеанс завершен")
        except Exception as e:
            self.log_message(f"✗ Ошибка: {e}")
        finally:
            self.active_bot = None
            self.log_signal.message.emit("reset_bot_ui")
    
    def stop_bot(self):
        """Остановка бота"""
        if self.active_bot:
            try:
                self.active_bot.should_stop = True
                self.log_message("⚠ Сигнал остановки отправлен боту...")
                QTimer.singleShot(2000, self.force_stop_bot)
            except Exception as e:
                self.log_message(f"✗ Ошибка при остановке: {e}")
    
    def force_stop_bot(self):
        """Принудительная остановка бота"""
        if self.active_bot:
            try:
                self.active_bot.close()
                self.log_message("✓ Бот остановлен пользователем")
            except:
                pass
            self.active_bot = None
        self.reset_bot_ui()
    
    def reset_bot_ui(self):
        """Сброс интерфейса бота"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.bot_status_label.setText("● Бот остановлен")
        self.bot_status_label.setStyleSheet("padding: 10px; background: #111; border-radius: 4px; border-left: 3px solid #666;")
    
    def add_lesson(self):
        """Добавление пары в расписание"""
        name = self.lesson_name_input.text().strip()
        event_id = self.lesson_event_id_input.text().strip()
        time = self.lesson_time_input.time().toString("HH:mm")
        duration = self.lesson_duration_input.value()
        
        if not name or not event_id:
            QMessageBox.warning(self, "Ошибка", "Заполните название и ID")
            return
        
        lesson = {
            "id": len(self.schedule_data) + 1,
            "name": name,
            "event_id": event_id,
            "time": time,
            "duration": duration,
            "enabled": True
        }
        
        self.schedule_data.append(lesson)
        self.save_schedule()
        self.refresh_schedule_table()
        
        self.lesson_name_input.clear()
        self.lesson_event_id_input.clear()
        self.log_message(f"✓ Пара '{name}' добавлена")
    
    def refresh_schedule_table(self):
        """Обновление таблицы расписания"""
        self.schedule_table.setRowCount(len(self.schedule_data))
        
        for i, lesson in enumerate(self.schedule_data):
            self.schedule_table.setItem(i, 0, QTableWidgetItem(lesson['name']))
            self.schedule_table.setItem(i, 1, QTableWidgetItem(lesson['event_id']))
            self.schedule_table.setItem(i, 2, QTableWidgetItem(lesson['time']))
            self.schedule_table.setItem(i, 3, QTableWidgetItem(str(lesson['duration'])))
            
            # Чекбокс
            checkbox = QCheckBox()
            checkbox.setChecked(lesson.get('enabled', True))
            checkbox.stateChanged.connect(lambda state, idx=i: self.toggle_lesson(idx, state))
            self.schedule_table.setCellWidget(i, 4, checkbox)
            
            # Кнопка удаления
            delete_btn = QPushButton("Удалить")
            delete_btn.setStyleSheet("background: #EF4444; color: #fff;")
            delete_btn.clicked.connect(lambda _, idx=i: self.delete_lesson(idx))
            self.schedule_table.setCellWidget(i, 5, delete_btn)
    
    def toggle_lesson(self, index, state):
        """Включение/выключение пары"""
        self.schedule_data[index]['enabled'] = (state == Qt.CheckState.Checked.value)
        self.save_schedule()
    
    def delete_lesson(self, index):
        """Удаление пары"""
        reply = QMessageBox.question(self, "Подтверждение", 
                                     f"Удалить пару '{self.schedule_data[index]['name']}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            name = self.schedule_data[index]['name']
            del self.schedule_data[index]
            self.save_schedule()
            self.refresh_schedule_table()
            self.log_message(f"✓ Пара '{name}' удалена")
    
    def start_scheduler(self):
        """Запуск планировщика"""
        if not self.schedule_data:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одну пару в расписание")
            return
        
        self.scheduler_running = True
        self.scheduler_start_btn.setEnabled(False)
        self.scheduler_stop_btn.setEnabled(True)
        self.scheduler_status_label.setText("● Планировщик включен")
        self.scheduler_status_label.setStyleSheet("padding: 10px; background: #111; border-radius: 4px; border-left: 3px solid #22D3EE; color: #22D3EE;")
        
        self.scheduler_thread = threading.Thread(target=self.run_scheduler)
        self.scheduler_thread.start()
        self.log_message("✓ Планировщик запущен")
    
    def run_scheduler(self):
        """Работа планировщика в отдельном потоке"""
        schedule.clear()
        
        for lesson in self.schedule_data:
            if lesson.get('enabled', True):
                schedule.every().day.at(lesson['time']).do(
                    self.scheduled_bot_run, 
                    lesson['event_id'], 
                    lesson['duration'],
                    lesson['name']
                )
        
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(30)
    
    def scheduled_bot_run(self, event_id, duration, name):
        """Запуск бота по расписанию"""
        self.log_message(f"⏰ Запуск по расписанию: {name}")
        fio = self.config.get('user_fio', '')
        threading.Thread(target=self.run_bot, args=(event_id, fio, duration)).start()
    
    def stop_scheduler(self):
        """Остановка планировщика"""
        self.scheduler_running = False
        self.scheduler_start_btn.setEnabled(True)
        self.scheduler_stop_btn.setEnabled(False)
        self.scheduler_status_label.setText("● Планировщик выключен")
        self.scheduler_status_label.setStyleSheet("padding: 10px; background: #111; border-radius: 4px; border-left: 3px solid #666;")
        schedule.clear()
        self.log_message("✓ Планировщик остановлен")
    
    def create_tray_icon(self):
        """Создание иконки в системном трее"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Устанавливаем иконку для трея
        if os.path.exists("icon.png"):
            self.tray_icon.setIcon(QIcon("icon.png"))
        
        self.tray_icon.setToolTip("Project Mayhem")
        
        # Создаём меню трея
        tray_menu = QMenu()
        show_action = QAction("Показать окно", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.quit_application)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """Обработка клика по иконке трея"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def changeEvent(self, event):
        """Обработка сворачивания окна"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized():
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    "Project Mayhem",
                    "Приложение свёрнуто в трей. Двойной клик для восстановления.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
    
    def quit_application(self):
        """Полное закрытие приложения"""
        if self.active_bot:
            self.active_bot.should_stop = True
        self.scheduler_running = False
        QApplication.quit()
    
    def closeEvent(self, event):
        """Обработка закрытия окна - сворачивание в трей"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Project Mayhem",
            "Приложение свёрнуто в трей. Двойной клик для восстановления.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ProjectMayhemGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
