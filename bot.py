from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.firefox import GeckoDriverManager
import time
import json
import os
from datetime import datetime


class TSUAssistantBot:
    def __init__(self):
        self.driver = None
        self.greeted = False  # Флаг отправки приветствия
        self.farewelled = False  # Флаг отправки прощания
        self.last_greet_text = None  # Текст для приветствий
        self.last_farewell_text = None  # Текст для прощаний
        self.last_greet_index = -1  # Индекс для приветствий
        self.last_farewell_index = -1  # Индекс для прощаний
        self.should_stop = False  # Флаг для остановки цикла        self.send_button_cache = None  # Кэш кнопки отправки        self.base_url = "https://e-class.tsu.ru/#login_by_id"
    
    def start_driver(self):
        """Инициализация веб-драйвера с расширением Mind for Firefox"""
        options = webdriver.FirefoxOptions()
        options.add_argument("--disable-logging")
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", False)
        
        # Читаем путь к профилю из config.json
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        firefox_profile_path = None
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    firefox_profile_path = config.get('firefox_profile_path')
            except:
                pass
        
        # Если путь к профилю указан, используем его
        if firefox_profile_path and os.path.exists(firefox_profile_path):
            options.add_argument('-profile')
            options.add_argument(firefox_profile_path)
            print(f"✓ Используется профиль Firefox с расширением Mind")
        else:
            print("⚠ Профиль Firefox не указан в config.json")
            print("   Расширение 'Mind for Firefox' может быть недоступно")
        
        try:
            driver_path = GeckoDriverManager().install()
            service = Service(driver_path)
            self.driver = webdriver.Firefox(service=service, options=options)
        except Exception as e:
            print(f"Ошибка с webdriver-manager: {e}")
            print("Пробую запустить Firefox напрямую...")
            self.driver = webdriver.Firefox(options=options)
        
        # Увеличиваем timeout
        self.driver.set_page_load_timeout(60)
        self.driver.set_script_timeout(60)
    
    def login(self, identifier: str, fio: str):
        """
        Вход в систему с использованием идентификатора и ФИО
        
        Args:
            identifier: Идентификатор студента
            fio: Фамилия Имя Отчество
        """
        try:
            self.driver.get(self.base_url)
            print(f"Переход на страницу входа: {self.base_url}")
        except TimeoutException:
            print("⚠ Timeout при загрузке страницы, но продолжаю...")
            # Останавливаем загрузку страницы если она зависла
            try:
                self.driver.execute_script("window.stop();")
            except:
                pass
        
        try:
            
            # Закрываем модальное окно с разрешениями
            print("▶ Закрываю модальное окно разрешений...")
            time.sleep(1.5)
            
            # Пробуем нажать кнопку "Блокировать"
            try:
                block_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Блокировать')]")
                if block_buttons and block_buttons[0].is_displayed():
                    block_buttons[0].click()
                    print("✓ Нажата кнопка 'Блокировать' (уведомления запрещены)")
            except Exception as e:
                print(f"⚠ Не удалось нажать 'Блокировать': {e}")
            
            # Закрываем кросс-ик в левом верхнем углу модального окна
            try:
                close_buttons = self.driver.find_elements(By.XPATH, "//button[@aria-label='Закрыть' or contains(text(), '×')]")
                for btn in close_buttons:
                    if btn.is_displayed():
                        btn.click()
                        print("✓ Закрыто модальное окно")
                        break
            except:
                pass
            
            print("▶ Ожидание появления полей ввода...")
            wait = WebDriverWait(self.driver, 30)
            
            # Активно ждём появления хотя бы 1 текстового поля для ID мероприятия
            try:
                wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "input")) >= 1)
                print("✓ Поля появились на странице")
            except TimeoutException:
                print("⚠ Timeout при ожидании полей, пробую продолжить...")
            
            # Логируем, что найдено на странице
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"Найдено элементов input: {len(all_inputs)}")
            
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            print(f"Найдено текстовых полей: {len(text_inputs)}")
            
            print(f"\nДетали найденных полей:")
            for i, inp in enumerate(text_inputs[:10]):
                try:
                    placeholder = inp.get_attribute("placeholder")
                    name = inp.get_attribute("name")
                    id_attr = inp.get_attribute("id")
                    visible = inp.is_displayed()
                    print(f"  Поле {i}: id={id_attr}, name={name}, placeholder={placeholder}, visible={visible}")
                except:
                    pass
            
            # Согласно скриншоту, нужно ввести ID мероприятия в единственное поле
            if len(text_inputs) >= 1:
                try:
                    print("\n▶ Заполняю поле ID мероприятия...")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", text_inputs[0])
                    text_inputs[0].click()
                    text_inputs[0].clear()
                    # Используем identifier как ID мероприятия
                    text_inputs[0].send_keys(identifier)
                    print(f"✓ Введён ID мероприятия: {identifier}")
                except Exception as e:
                    print(f"✗ Ошибка при заполнении поля: {e}")
                
                time.sleep(1)
                
                # Ищем и нажимаем кнопку "Продолжить"
                print("▶ Ищу кнопку 'Продолжить'...")
                
                # Ищем кнопку "Продолжить" в div.mind-button-text
                button = None
                
                # Способ 1: найти div с текстом "Продолжить"
                try:
                    button = self.driver.find_element(By.XPATH, "//div[contains(@class, 'mind-button-text') and contains(text(), 'Продолжить')]")
                    print("✓ Найдена кнопка в div.mind-button-text")
                except:
                    pass
                
                # Способ 2: найти td с текстом "Продолжить"
                if not button:
                    try:
                        button = self.driver.find_element(By.XPATH, "//td[contains(text(), 'Продолжить')]")
                        print("✓ Найдена кнопка в td")
                    except:
                        pass
                
                # Способ 3: поискать любую кнопку с текстом "Продолжить"
                if not button:
                    try:
                        button = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Продолжить')]")
                        print("✓ Найдена кнопка по тексту")
                    except:
                        pass
                
                if button:
                    try:
                        print(f"▶ Нажимаю кнопку 'Продолжить'...")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        button.click()
                        print("✓ Кнопка нажата")
                        time.sleep(2)
                        
                        # Теперь ждём появления поля для ввода ФИО
                        print("\n▶ Ожидание поля ввода ФИО...")
                        time.sleep(1.5)
                        
                        # Ищем поле для ФИО - оно находится внутри структуры с imarker="guestName"
                        fio_field = None
                        try:
                            # Самый специфичный селектор
                            fio_field = self.driver.find_element(By.CSS_SELECTOR, 
                                "div[imarker='guestName'] input.mind-textbox-content")
                            print("✓ Найдено поле ввода ФИО (по imarker='guestName')")
                        except:
                            try:
                                # Альтернативный селектор
                                fio_field = self.driver.find_element(By.CSS_SELECTOR, 
                                    "input.mind-textbox-content[maxlength='100']")
                                print("✓ Найдено поле ввода ФИО (по maxlength)")
                            except:
                                try:
                                    fio_field = self.driver.find_element(By.CSS_SELECTOR, "input.mind-textbox-content")
                                    print("✓ Найдено поле ввода ФИО (по классу)")
                                except:
                                    print("✗ Поле ФИО не найдено")
                        
                        if fio_field:
                            # Вводим ФИО
                            print(f"▶ Ввожу ФИО: {fio}...")
                            
                            # Прокручиваем в представление
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", fio_field)
                            time.sleep(0.5)
                            
                            # Работаем полностью через JavaScript (единственный надежный способ)
                            self.driver.execute_script("""
                                var input = arguments[0];
                                var value = arguments[1];
                                
                                // Убеждаемся что элемент видим и доступен
                                input.style.display = 'block';
                                input.style.visibility = 'visible';
                                input.style.opacity = '1';
                                input.disabled = false;
                                input.readOnly = false;
                                
                                // Устанавливаем фокус
                                input.focus();
                                input.click();
                                
                                // Полностью очищаем предыдущее значение
                                input.value = '';
                                
                                // Вставляем новое значение
                                input.value = value;
                                
                                // Генерируем события input для каждого символа
                                var inputEvent = new InputEvent('input', {
                                    bubbles: true,
                                    cancelable: true,
                                    data: value
                                });
                                input.dispatchEvent(inputEvent);
                                
                                // Триггерим события изменения
                                input.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
                                input.dispatchEvent(new Event('blur', { bubbles: true }));
                            """, fio_field, fio)
                            
                            print("✓ ФИО введено через JavaScript")
                            time.sleep(1)
                            
                            # Проверяем значение
                            current_value = fio_field.get_attribute('value')
                            print(f"  Проверка: в поле '{current_value}'")
                            
                            time.sleep(2)
                            
                            # Ищем кнопку "Войти в мероприятие"
                            print("▶ Ищу кнопку 'Войти в мероприятие'...")
                            enter_button = None
                            
                            try:
                                enter_button = self.driver.find_element(By.XPATH, 
                                    "//div[contains(@class, 'mind-button-text') and contains(text(), 'Войти в мероприятие')]")
                                print("✓ Найдена кнопка 'Войти в мероприятие'")
                            except:
                                try:
                                    enter_button = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Войти в мероприятие')]")
                                    print("✓ Найдена кнопка (альтернативный поиск)")
                                except:
                                    print("✗ Кнопка 'Войти в мероприятие' не найдена")
                            
                            if enter_button:
                                print("▶ Нажимаю кнопку 'Войти в мероприятие'...")
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", enter_button)
                                time.sleep(0.5)
                                try:
                                    enter_button.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", enter_button)
                                print("✓ Кнопка нажата")
                                time.sleep(5)
                                print("✓✓✓ Успешный вход в мероприятие! ✓✓✓")
                            else:
                                print("Нажмите кнопку 'Войти в мероприятие' вручную...")
                                input("Нажмите Enter после входа...")
                        else:
                            print("Введите ФИО вручную и нажмите 'Войти в мероприятие'...")
                            input("Нажмите Enter после входа...")
                        
                    except Exception as e:
                        print(f"✗ Ошибка при нажатии кнопки: {e}")
                        print("Попробую через JavaScript...")
                        try:
                            self.driver.execute_script("arguments[0].click();", button)
                            print("✓ Кнопка нажата через JavaScript")
                            time.sleep(5)
                        except:
                            print("Нажмите кнопку вручную и нажмите Enter...")
                            input("Нажмите Enter после входа...")
                else:
                    print("✗ Кнопка 'Продолжить' не найдена")
                    # Пробуем нажать Enter в поле
                    try:
                        print("▶ Пробую нажать Enter в поле ввода...")
                        text_inputs[0].send_keys(Keys.RETURN)
                        print("✓ Нажат Enter в поле ввода")
                        time.sleep(5)
                    except:
                        print("Нажмите кнопку вручную и нажмите Enter...")
                        input("Нажмите Enter после входа...")
            else:
                print(f"\n✗ Не найдено ни одного поля ввода")
                print("Введите данные вручную и нажмите Enter...")
                input("Нажмите Enter после ручного входа на сайт...")
            
        except Exception as e:
            print(f"\n✗ Критическая ошибка при входе: {e}")
            import traceback
            traceback.print_exc()
            print("\nБраузер остаётся открытым для ручного входа")
            input("Нажмите Enter после ручного входа на сайт...")
    
    def join_lecture(self, lecture_id: str):
        """
        Вход в аудиторию лекции
        
        Args:
            lecture_id: Идентификатор аудитории/лекции
        """
        try:
            lecture_url = f"https://e-class.tsu.ru/#lecture/{lecture_id}"
            self.driver.get(lecture_url)
            print(f"Переход в аудиторию: {lecture_url}")
            
            wait = WebDriverWait(self.driver, 15)
            time.sleep(2)
            
            # Пытаемся дождаться загрузки аудитории
            selectors = [
                (By.CLASS_NAME, "lecture-room"),
                (By.CSS_SELECTOR, "[class*='lecture']"),
                (By.XPATH, "//*[contains(@class, 'room')]")
            ]
            
            loaded = False
            for selector in selectors:
                try:
                    wait.until(EC.presence_of_element_located(selector))
                    print(f"Аудитория загружена по селектору: {selector}")
                    loaded = True
                    break
                except TimeoutException:
                    continue
            
            if loaded:
                print(f"Вход в аудиторию {lecture_id} выполнен")
            else:
                print(f"Предполагаемый вход в аудиторию {lecture_id} (элемент не найден, но страница загружена)")
            
        except Exception as e:
            print(f"Ошибка при входе в аудиторию: {e}")
            raise
    
    def send_chat_message(self, message: str):
        """Отправка сообщения в чат"""
        try:
            print(f"\n▶ Отправляю сообщение в чат: '{message}'")
            
            # Находим iframe чата
            chat_iframe = self.driver.find_element(
                By.CSS_SELECTOR, "iframe.emptyText.external-chat-emptyText[imarker='enterMessageArea']"
            )
            
            # Используем JavaScript для установки текста в iframe
            js_script = """
            var iframe = arguments[0];
            var message = arguments[1];
            var doc = iframe.contentDocument || iframe.contentWindow.document;
            var body = doc.body;
            body.innerHTML = message;
            body.textContent = message;
            
            // Триггерим события для активации кнопки отправки
            var inputEvent = new Event('input', { bubbles: true });
            body.dispatchEvent(inputEvent);
            
            var changeEvent = new Event('change', { bubbles: true });
            body.dispatchEvent(changeEvent);
            
            var keyupEvent = new Event('keyup', { bubbles: true });
            body.dispatchEvent(keyupEvent);
            """
            
            self.driver.execute_script(js_script, chat_iframe, message)
            print("✓ Текст установлен в поле чата")
            
            time.sleep(0.5)
            
            # Используем кэшированную кнопку или ищем новую
            send_button = self.send_button_cache
            
            # Проверяем валидность кэша
            if send_button:
                try:
                    send_button.is_displayed()
                except:
                    send_button = None
                    self.send_button_cache = None
            
            # Если кэш недействителен, ищем кнопку заново
            if not send_button:
                try:
                    send_button = self.driver.find_element(By.CSS_SELECTOR, "div[imarker='sendMessageButton']")
                    self.send_button_cache = send_button
                except:
                    try:
                        all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div.gray-decorated-button")
                        for btn in all_buttons:
                            try:
                                if btn.get_attribute("title") == "Отправить":
                                    send_button = btn
                                    self.send_button_cache = btn
                                    break
                            except:
                                pass
                    except:
                        pass
            
            if send_button:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", send_button)
                time.sleep(0.3)
                try:
                    send_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", send_button)
                print(f"✓ Сообщение '{message}' отправлено!")
                return True
            else:
                print("✗ Кнопка отправки не найдена")
                return False
                
        except Exception as e:
            print(f"⚠ Ошибка при отправке сообщения: {e}")
            return False
    
    def greet_in_chat(self):
        """Отправка приветствия в чат если видны новые сообщения"""
        try:
            if self.greeted:
                return
            
            try:
                messages = self.driver.find_elements(By.CSS_SELECTOR, "span.external-chatMessage[imarker='messageContent']")
                
                if not messages:
                    print(f"    ⚠ Чат пуст")
                    return
                
                current_index = len(messages) - 1
                current_last = messages[-1].text.strip()
                
                print(f"    Индекс: {current_index} (было: {self.last_greet_index}), текст: '{current_last[:50]}'")
                
                # Проверяем: изменился индекс ИЛИ текст
                if current_index > self.last_greet_index or current_last != self.last_greet_text:
                    print(f"    ✓ Новое сообщение обнаружено!")
                    self.last_greet_index = current_index
                    self.last_greet_text = current_last
                    
                    print("    ▶ Отправляю приветствие...")
                    if self.send_chat_message("Здравствуйте"):
                        self.greeted = True
                else:
                    print(f"    ⚠ Новых сообщений нет")
                    
            except Exception as e:
                print(f"    ⚠ Ошибка при проверке чата: {e}")
                
        except Exception as e:
            print(f"    ⚠ Ошибка при отправке приветствия: {e}")
    
    def check_farewell_messages(self):
        """Проверка наличия прощальных сообщений (аналогично приветствию)"""
        try:
            farewell_words = [
                'до свидания', 'досвидания', 'пока', 'до встречи',
                'доброго вечера', 'спокойной ночи', 'всем пока',
                'до завтра', 'удачи', 'bye', 'goodbye'
            ]
            
            messages = self.driver.find_elements(By.CSS_SELECTOR, "span.external-chatMessage[imarker='messageContent']")
            
            if not messages:
                return False
            
            current_index = len(messages) - 1
            current_last = messages[-1].text.strip().lower()
            
            print(f"    Индекс: {current_index} (было: {self.last_farewell_index}), текст: '{current_last[:50]}'")
            
            # Проверяем: изменился индекс ИЛИ текст (так же как в приветствии)
            if current_index > self.last_farewell_index or current_last != self.last_farewell_text:
                print(f"    ✓ Проверяю на прощальные слова...")
                
                # Проверяем, есть ли прощальные слова в сообщении
                for word in farewell_words:
                    if word in current_last:
                        print(f"    ✓ Обнаружено прощальное слово: '{word}'")
                        self.last_farewell_index = current_index
                        self.last_farewell_text = current_last
                        return True
                
                # Обновляем индекс и текст даже если не нашли прощание
                self.last_farewell_index = current_index
                self.last_farewell_text = current_last
                print(f"    ⚠ Прощальных слов не найдено")
            else:
                print(f"    ⚠ Новых сообщений нет")
            
            return False
            
        except Exception as e:
            print(f"⚠ Ошибка при проверке прощальных сообщений: {e}")
            return False
    
    def farewell_in_chat(self):
        """Отправка прощания в чат при обнаружении прощальных сообщений"""
        try:
            # Если ещё не поздоровались, пропускаем
            if not self.greeted:
                return False
            
            # Если уже прощались, пропускаем
            if self.farewelled:
                return False
            
            print("\n▶ Проверяю прощальные сообщения в чате...")
            
            # Проверяем наличие прощальных сообщений
            if self.check_farewell_messages():
                print("▶ Отправляю прощание...")
                if self.send_chat_message("До свидания"):
                    self.farewelled = True
                    return True
            else:
                print("⚠ Прощальных сообщений не найдено")
                return False
                
        except Exception as e:
            print(f"⚠ Ошибка при отправке прощания: {e}")
            return False
    
    def stay_in_lecture(self, duration_minutes: int = 5):
        """Остаёмся в аудитории и отслеживаем прощания"""
        try:
            print(f"Бот находится в аудитории {duration_minutes} минут...")
            
            # Инициализируем запоминание последнего сообщения
            print("▶ Запоминаю текущее состояние чата...")
            time.sleep(2)
            messages = self.driver.find_elements(By.CSS_SELECTOR, "span.external-chatMessage[imarker='messageContent']")
            if messages:
                self.last_greet_index = len(messages) - 1
                self.last_farewell_index = len(messages) - 1
                self.last_greet_text = messages[-1].text.strip()
                self.last_farewell_text = messages[-1].text.strip().lower()
                print(f"✓ В чате {len(messages)} сообщений, последнее: '{self.last_greet_text[:50]}...'")
            else:
                self.last_greet_index = -1
                self.last_farewell_index = -1
                self.last_greet_text = None
                self.last_farewell_text = None
                print("✓ Чат пуст, жду первого сообщения")
            
            end_time = time.time() + (duration_minutes * 60)
            check_interval = 10  # Проверяем и приветствия, и прощания каждые 10 секунд
            last_check = 0
            
            while time.time() < end_time:
                # Проверяем флаг остановки
                if self.should_stop:
                    print("\n⚠ Получен сигнал остановки, выхожу из аудитории...")
                    self.exit_lecture()
                    time.sleep(1)
                    self.close()
                    break
                
                remaining = int((end_time - time.time()) / 60)
                print(f"Осталось {remaining} минут", end='\r')
                
                current_time = time.time()
                
                # Проверяем оба события каждые 10 секунд
                if current_time - last_check >= check_interval:
                    print("\n▶ Проверка чата...")
                    
                    # Проверяем приветствия
                    if not self.greeted:
                        print("  → Проверяю новые сообщения для приветствия...")
                        self.greet_in_chat()
                    else:
                        print("  → Приветствие уже отправлено, пропускаю")
                    
                    # Проверяем прощания
                    print("  → Проверяю прощальные сообщения...")
                    if self.farewell_in_chat():
                        print("\n✓ Прощание отправлено")
                        time.sleep(1)
                        
                        # Выход из аудитории
                        self.exit_lecture()
                        
                        time.sleep(2)
                        # Закрываем браузер
                        self.close()
                        break
                    
                    last_check = current_time
                
                time.sleep(10)
            
            # Если цикл завершился по истечению времени (не по break)
            print("\n⏱ Время истекло, выхожу из аудитории...")
            self.exit_lecture()
            time.sleep(1)
            self.close()
            
        except KeyboardInterrupt:
            print("\nПолучен сигнал выхода")
    
    def exit_lecture(self):
        """Выход из аудитории"""
        try:
            print("\n▶ Ищу кнопку выхода...")
            
            # Ищем кнопку выхода - она содержит текст "Выйти"
            exit_button = None
            
            try:
                # Вариант 1: по тексту "Выйти"
                exit_button = self.driver.find_element(By.XPATH, 
                    "//*[contains(text(), 'Выйти')]")
                print("✓ Найдена кнопка выхода")
            except:
                pass
            
            if not exit_button:
                try:
                    # Вариант 2: по классу GBDGNBYOVE содержащему текст "Выйти"
                    exit_button = self.driver.find_element(By.XPATH, 
                        "//div[contains(@class, 'GBDGNBYOVE')]/ancestor::div[contains(@class, 'gray-decorated-button')]")
                    print("✓ Найдена кнопка выхода (вариант 2)")
                except:
                    pass
            
            if exit_button:
                print("▶ Нажимаю кнопку выхода...")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", exit_button)
                time.sleep(0.5)
                try:
                    exit_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", exit_button)
                print("✓ Выход из аудитории выполнен")
                time.sleep(2)
                return True
            else:
                print("✗ Кнопка выхода не найдена")
                return False
                
        except Exception as e:
            print(f"⚠ Ошибка при выходе из аудитории: {e}")
            return False
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            print("✓ Браузер закрыт")


def main():
    """Главная функция"""
    bot = TSUAssistantBot()
    
    try:
        # Инициализация драйвера
        bot.start_driver()
        
        # Загружаем конфиг
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        fio = "Гость"
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                fio = config.get('user_fio', 'Гость')
                
                if fio != "Ваше Полное ФИО":
                    print(f"✓ Загружено ФИО из config.json: {fio}")
                else:
                    print("⚠ Отредактируйте config.json и введите своё ФИО")
                    fio = input("Введите ваше ФИО: ").strip()
        
        # ID мероприятия вводим каждый раз (для тестирования разных)
        event_id = input("\nВведите ID мероприятия/лекции: ").strip()
        
        if not event_id:
            print("Ошибка: ID мероприятия не может быть пусто")
            return
        
        # Вход в систему с ID мероприятия и ФИО
        bot.login(event_id, fio)
        
        print("\nВход в мероприятие выполнен!")
        time.sleep(2)
        
        # greet_in_chat() вызывается автоматически в stay_in_lecture при появлении новых сообщений
        
        # Получение времени пребывания
        default_duration = 90
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_duration = config.get('default_duration_minutes', 90)
        
        duration_input = input(f"Сколько минут оставаться в мероприятии? (по умолчанию {default_duration}): ").strip()
        duration_minutes = int(duration_input) if duration_input else default_duration
        
        # Остаёмся в мероприятии
        bot.stay_in_lecture(duration_minutes)
        
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        bot.close()


if __name__ == "__main__":
    main()
