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
        self.base_url = "https://e-class.tsu.ru/#login_by_id"
    
    def start_driver(self):
        """Инициализация веб-драйвера"""
        options = webdriver.FirefoxOptions()
        options.add_argument("--disable-logging")
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", False)
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
    
    def stay_in_lecture(self, duration_minutes: int = 5):
        """Остаёмся в аудитории указанное время"""
        try:
            print(f"Бот находится в аудитории {duration_minutes} минут...")
            end_time = time.time() + (duration_minutes * 60)
            while time.time() < end_time:
                remaining = int((end_time - time.time()) / 60)
                print(f"Осталось {remaining} минут", end='\r')
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nПолучен сигнал выхода")
    
    def exit_lecture(self):
        """Выход из аудитории"""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Поиск кнопки выхода
            exit_button = wait.until(
                EC.element_to_be_clickable((By.ID, "exit_button"))
            )
            exit_button.click()
            print("Выход из аудитории выполнен")
            
        except TimeoutException:
            print("Ошибка: кнопка выхода не найдена")
            raise
        except Exception as e:
            print(f"Ошибка при выходе: {e}")
            raise
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            print("Браузер закрыт")


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
