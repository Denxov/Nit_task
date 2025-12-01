import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import threading
import time
from server_discovery import ClientDiscovery


class OperatorClient:
    def __init__(self, host=None, port=12345):
        # Если host не указан, будем использовать auto-discovery
        self.host = host
        self.port = port
        self.socket = None
        self.username = None
        self.connected = False
        self.receive_thread = None
        self.lock = threading.Lock()
        self.current_tasks = [[], []]  # Задачи для двух конвейеров

    def auto_discover_server(self):
        """Автоматическое обнаружение сервера в сети"""
        print("🔍 Поиск сервера в сети...")
        discovery = ClientDiscovery()
        server_info = discovery.discover_first_server()

        if server_info:
            self.host = server_info.get('response_addr')
            self.port = server_info.get('port', self.port)
            print(f"✓ Найден сервер: {self.host}:{self.port}")
            return True
        else:
            print("✗ Сервер не найден в сети")
            return False

    def connect(self):
        try:
            # Если хост не указан, пытаемся найти сервер автоматически
            if not self.host:
                if not self.auto_discover_server():
                    return False

            print(f"Подключение к {self.host}:{self.port}...")

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(2)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(0.5)
            self.connected = True

            print("✓ Успешное подключение к серверу")

            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            return True

        except socket.timeout:
            print("✗ Таймаут подключения к серверу")
            return False
        except ConnectionRefusedError:
            print("✗ Сервер отказал в подключении")
            return False
        except Exception as e:
            print(f"✗ Ошибка подключения: {e}")
            return False

    def login(self, username, password):
        if not self.connected:
            if not self.connect():
                return {'status': 'error', 'message': 'Не удалось подключиться к серверу'}

        message = {
            'type': 'login',
            'username': username,
            'password': password
        }

        result = self.send_and_receive(message)
        if result.get('status') == 'success':
            self.username = username
            # После успешного входа запрашиваем текущие задачи
            self.request_tasks()
        return result

    def request_tasks(self):
        """Запрос текущих задач с сервера"""
        try:
            if not self.connected or not self.username:
                print("Нет подключения или пользователь не авторизован")
                return

            message = {
                'type': 'get_operator_tasks',
                'operator': self.username
            }

            result = self.send_and_receive(message)
            if result.get('status') == 'success' and result.get('type') == 'operator_tasks_response':
                tasks = result.get('tasks', [[], []])
                self.current_tasks = tasks
                print(
                    f"Получены задачи с сервера: конвейер 1 - {len(tasks[0])} задач, конвейер 2 - {len(tasks[1])} задач")

                # Уведомляем GUI о новых задачах
                if hasattr(self, 'on_tasks_updated'):
                    self.on_tasks_updated()
            else:
                print(f"Ошибка получения задач: {result.get('message', 'Unknown error')}")

        except Exception as e:
            print(f"Ошибка запроса задач: {e}")

    def send_and_receive(self, message):
        try:
            with self.lock:
                if not self.connected or not self.socket:
                    return {'status': 'error', 'message': 'Нет подключения к серверу'}

                # Отправляем сообщение
                message_str = json.dumps(message) + '\n'
                self.socket.send(message_str.encode('utf-8'))
                print(f"Отправлено: {message['type']}")

                # Получаем ответ с увеличенным таймаутом
                self.socket.settimeout(6.0)
                response_data = self.socket.recv(4096)  # Увеличиваем буфер
                self.socket.settimeout(0.5)

                if response_data:
                    response_str = response_data.decode('utf-8').strip()
                    # Берем первую строку (первое сообщение)
                    if '\n' in response_str:
                        response_str = response_str.split('\n')[0]

                    response = json.loads(response_str)
                    return response
                else:
                    return {'status': 'error', 'message': 'Пустой ответ от сервера'}

        except socket.timeout:
            if hasattr(self, 'socket') and self.socket:
                self.socket.settimeout(0.5)
            return {'status': 'error', 'message': 'Таймаут ожидания ответа'}
        except json.JSONDecodeError as e:
            if hasattr(self, 'socket') and self.socket:
                self.socket.settimeout(0.5)
            print(f"JSON decode error. Data: {response_data}")
            return {'status': 'error', 'message': 'Неверный формат ответа'}
        except ConnectionResetError:
            self.connected = False
            if hasattr(self, 'socket') and self.socket:
                self.socket.settimeout(0.5)
            return {'status': 'error', 'message': 'Соединение сброшено сервером'}
        except BrokenPipeError:
            self.connected = False
            if hasattr(self, 'socket') and self.socket:
                self.socket.settimeout(0.5)
            return {'status': 'error', 'message': 'Соединение с сервером разорвано'}
        except Exception as e:
            if hasattr(self, 'socket') and self.socket:
                self.socket.settimeout(0.5)
            print(f"Ошибка обмена данными: {e}")
            return {'status': 'error', 'message': str(e)}

    def receive_messages(self):
        buffer = ""
        while self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    print("Сервер закрыл соединение")
                    break

                buffer += data

                # Обрабатываем все полные сообщения
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            message = json.loads(line)
                            self.handle_server_message(message)
                        except json.JSONDecodeError as e:
                            print(f"Неверный JSON: {line}, ошибка: {e}")

            except socket.timeout:
                continue
            except ConnectionAbortedError:
                print("Соединение прервано")
                break
            except ConnectionResetError:
                print("Соединение сброшено сервером")
                break
            except Exception as e:
                if self.connected:
                    print(f"Ошибка приема сообщений: {e}")
                break

        self.connected = False
        print("Поток приема сообщений завершен")

    def handle_server_message(self, message):
        msg_type = message.get('type')
        print(f"Уведомление от сервера: {msg_type}")

        if msg_type == 'new_task':
            task = message.get('task', {})
            conveyor = message.get('conveyor', 0)
            print(f"Получена новая задача для конвейера {conveyor}: {task}")

            # Добавляем задачу в соответствующий конвейер
            if 0 <= conveyor < 2:
                # Проверяем, нет ли уже такой задачи (по ID)
                task_exists = any(t.get('id') == task.get('id') for t in self.current_tasks[conveyor])
                if not task_exists:
                    self.current_tasks[conveyor].append(task)
                    print(f"Задача добавлена в конвейер {conveyor}. Всего задач: {len(self.current_tasks[conveyor])}")

                # Уведомляем GUI
                if hasattr(self, 'on_new_task'):
                    self.on_new_task(message)

        elif msg_type == 'operator_tasks_response':
            # Ответ на запрос задач (может прийти асинхронно)
            tasks = message.get('tasks', [[], []])
            self.current_tasks = tasks
            print(f"Асинхронно получены задачи: конвейер 1 - {len(tasks[0])} задач, конвейер 2 - {len(tasks[1])} задач")

            if hasattr(self, 'on_tasks_updated'):
                self.on_tasks_updated()

    def get_tasks(self):
        """Возвращает текущие задачи"""
        return self.current_tasks

    def update_task_quantity(self, task_id, conveyor, completed_quantity):
        """Обновление выполненного количества задачи"""
        try:
            # Сначала обновляем локально
            for i, task in enumerate(self.current_tasks[conveyor]):
                if task.get('id') == task_id:
                    self.current_tasks[conveyor][i]['completed_quantity'] = completed_quantity

                    # Проверяем, выполнена ли задача полностью
                    planned = task.get('planned_quantity', 0)
                    if planned > 0 and completed_quantity >= planned:
                        self.current_tasks[conveyor][i]['status'] = 'completed'
                        self.current_tasks[conveyor][i]['completed'] = time.strftime("%Y-%m-%d %H:%M:%S")

                    print(f"Количество задачи {task_id} обновлено: {completed_quantity}")

                    # Отправляем обновление на сервер
                    update_message = {
                        'type': 'update_task_quantity',
                        'operator': self.username,
                        'conveyor': conveyor,
                        'task_id': task_id,
                        'completed_quantity': completed_quantity
                    }
                    result = self.send_and_receive(update_message)

                    if result.get('status') == 'success':
                        return True
                    else:
                        print(f"Ошибка отправки на сервер: {result.get('message')}")
                        return False
            return False
        except Exception as e:
            print(f"Ошибка обновления количества: {e}")
            return False

    def set_new_task_callback(self, callback):
        self.on_new_task = callback

    def set_tasks_updated_callback(self, callback):
        self.on_tasks_updated = callback

    def disconnect(self):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None


class OperatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Operator Panel - Production System")
        self.root.geometry("900x700")  # Увеличили размер для отображения количества

        # Создаем основной фрейм
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Клиент без указания host - будет использовать auto-discovery
        self.client = OperatorClient(host=None)  # None для auto-discovery
        self.client.set_new_task_callback(self.handle_new_task)
        self.client.set_tasks_updated_callback(self.handle_tasks_updated)

        self.show_login_screen()

    def handle_new_task(self, message):
        """Обработка новой задачи от сервера с учетом количества"""

        def show_notification():
            task = message.get('task', {})
            conveyor = message.get('conveyor', 0) + 1
            priority = task.get('priority', 'Средний')
            planned = task.get('planned_quantity', 0)
            unit = task.get('unit', 'шт')

            # Цвет заголовка в зависимости от приоритета
            if priority == 'Высокий':
                title = "❗ ВЫСОКИЙ ПРИОРИТЕТ - Новая задача"
            elif priority == 'Средний':
                title = "⚠️ СРЕДНИЙ ПРИОРИТЕТ - Новая задача"
            else:
                title = "✅ НИЗКИЙ ПРИОРИТЕТ - Новая задача"

            messagebox.showinfo(
                title,
                f"Конвейер: {conveyor}\n"
                f"Приоритет: {priority}\n"
                f"Количество: {planned} {unit}\n"
                f"Сырье: {task.get('material', 'N/A')}\n"
                f"Цвет: {task.get('color', 'N/A')}\n"
                f"Скорость: {task.get('speed', 'N/A')}\n"
                f"Температура: {task.get('temperature', 'N/A')}"
            )
            self.refresh_tasks()

        # Вызываем в основном потоке
        self.root.after(0, show_notification)

    def handle_tasks_updated(self):
        """Обработка обновления списка задач"""
        self.root.after(0, self.refresh_tasks)

    def clear_screen(self):
        """Очистка экрана - безопасный метод"""
        for widget in self.main_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass

    def show_login_screen(self):
        """Показ экрана входа с выбором способа подключения"""
        self.clear_screen()

        login_container = ttk.Frame(self.main_frame)
        login_container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        login_frame = ttk.Frame(login_container)
        login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        title_label = ttk.Label(
            login_frame,
            text="Вход оператора",
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        # Поля ввода
        ttk.Label(login_frame, text="Логин:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.login_entry = ttk.Entry(login_frame, width=20)
        self.login_entry.grid(row=1, column=1, pady=5, padx=10)

        ttk.Label(login_frame, text="Пароль:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(login_frame, width=20, show="*")
        self.password_entry.grid(row=2, column=1, pady=5, padx=10)

        # Выбор способа подключения
        connection_frame = ttk.Frame(login_frame)
        connection_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.connection_var = tk.StringVar(value="auto")

        ttk.Radiobutton(connection_frame, text="Автопоиск сервера",
                        variable=self.connection_var, value="auto").pack(anchor=tk.W)

        ttk.Radiobutton(connection_frame, text="Ручной ввод адреса",
                        variable=self.connection_var, value="manual").pack(anchor=tk.W)

        # Поле для ручного ввода адреса
        manual_frame = ttk.Frame(login_frame)
        manual_frame.grid(row=4, column=0, columnspan=2, pady=5)

        ttk.Label(manual_frame, text="Адрес сервера:").pack(side=tk.LEFT)
        self.server_address_entry = ttk.Entry(manual_frame, width=15)
        self.server_address_entry.pack(side=tk.LEFT, padx=5)
        self.server_address_entry.insert(0, "192.168.0.128")

        # Скрываем поле ручного ввода по умолчанию
        manual_frame.grid_remove()

        # Обработчик изменения выбора
        def on_connection_change():
            if self.connection_var.get() == "manual":
                manual_frame.grid()
            else:
                manual_frame.grid_remove()

        self.connection_var.trace('w', lambda *args: on_connection_change())

        # Кнопка входа
        self.login_btn = ttk.Button(
            login_frame,
            text="Войти",
            command=self.do_login
        )
        self.login_btn.grid(row=5, column=0, columnspan=2, pady=20)

        # Статус
        self.status_label = ttk.Label(
            login_frame,
            text="Выберите способ подключения",
            foreground="blue"
        )
        self.status_label.grid(row=6, column=0, columnspan=2, pady=5)

        # Тестовые данные
        test_label = ttk.Label(
            login_frame,
            text="Тест: operator1/pass1, operator2/pass2, operator3/pass3",
            font=('Arial', 9),
            foreground="gray"
        )
        test_label.grid(row=7, column=0, columnspan=2, pady=10)

        # Автозаполнение
        self.login_entry.insert(0, "operator1")
        self.password_entry.insert(0, "pass1")

        # Привязка Enter
        self.root.bind('<Return>', lambda e: self.do_login())
        self.login_entry.focus()

    def do_login(self):
        """Обновленный метод входа с поддержкой auto-discovery"""
        username = self.login_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Ошибка", "Введите логин и пароль")
            return

        # Настраиваем клиент в зависимости от выбранного способа
        if self.connection_var.get() == "manual":
            server_address = self.server_address_entry.get().strip()
            if not server_address:
                messagebox.showwarning("Ошибка", "Введите адрес сервера")
                return
            self.client.host = server_address
        else:
            # Auto-discovery - host остается None
            self.client.host = None

        # Блокируем UI
        self.login_btn.config(state='disabled')
        self.status_label.config(text="Подключение к серверу...", foreground="orange")

        def login_process():
            result = self.client.login(username, password)
            self.root.after(0, lambda: self.process_login_result(result))

        threading.Thread(target=login_process, daemon=True).start()

    def process_login_result(self, result):
        """Обработка результата входа"""
        self.login_btn.config(state='normal')

        if result.get('status') == 'success':
            self.status_label.config(text="Успешный вход!", foreground="green")
            self.root.after(1000, self.show_operator_panel)
        else:
            error_msg = result.get('message', 'Неизвестная ошибка')
            self.status_label.config(text=f"Ошибка: {error_msg}", foreground="red")
            messagebox.showerror("Ошибка входа", error_msg)

    def show_operator_panel(self):
        """Показ основной панели оператора"""
        self.clear_screen()

        # Заголовок
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        user_label = ttk.Label(
            header_frame,
            text=f"Оператор: {self.client.username}",
            font=('Arial', 14, 'bold')
        )
        user_label.pack(side=tk.LEFT)

        # Статус подключения
        conn_status = "Подключен" if self.client.connected else "Не подключен"
        status_color = "green" if self.client.connected else "red"
        status_label = ttk.Label(
            header_frame,
            text=f"Статус: {conn_status}",
            foreground=status_color
        )
        status_label.pack(side=tk.LEFT, padx=20)

        # Информация о задачах
        tasks_info = self.get_tasks_info()
        tasks_label = ttk.Label(
            header_frame,
            text=tasks_info,
            font=('Arial', 10),
            foreground="blue"
        )
        tasks_label.pack(side=tk.LEFT, padx=20)

        # Кнопки управления
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)

        refresh_btn = ttk.Button(btn_frame, text="Обновить задачи", command=self.manual_refresh_tasks)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        logout_btn = ttk.Button(btn_frame, text="Выйти", command=self.logout)
        logout_btn.pack(side=tk.LEFT, padx=5)

        # Конвейеры
        self.setup_conveyors()

        # Загружаем задачи
        self.refresh_tasks()

        # Запускаем периодическое обновление
        self.start_periodic_updates()

    def get_tasks_info(self):
        """Получение информации о задачах для отображения в заголовке"""
        tasks = self.client.get_tasks()
        total_tasks = len(tasks[0]) + len(tasks[1])
        active_tasks = sum(1 for task in tasks[0] + tasks[1] if task.get('status') == 'active')

        # Считаем общий прогресс
        total_planned = 0
        total_completed = 0
        for task in tasks[0] + tasks[1]:
            if task.get('status') == 'active':
                total_planned += task.get('planned_quantity', 0)
                total_completed += task.get('completed_quantity', 0)

        if total_planned > 0:
            progress_percent = (total_completed / total_planned) * 100
            progress_text = f" | Прогресс: {progress_percent:.1f}%"
        else:
            progress_text = ""

        return f"Задачи: {active_tasks} активных / {total_tasks} всего{progress_text}"

    def setup_conveyors(self):
        """Настройка отображения конвейеров"""
        conveyors_frame = ttk.Frame(self.main_frame)
        conveyors_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Конвейер 1
        conv1_frame = ttk.LabelFrame(conveyors_frame, text="Конвейер 1", padding=10)
        conv1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.conv1_canvas = tk.Canvas(conv1_frame)
        conv1_scrollbar = ttk.Scrollbar(conv1_frame, orient=tk.VERTICAL, command=self.conv1_canvas.yview)
        self.conv1_inner = ttk.Frame(self.conv1_canvas)

        self.conv1_canvas.configure(yscrollcommand=conv1_scrollbar.set)
        self.conv1_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conv1_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.conv1_canvas.create_window((0, 0), window=self.conv1_inner, anchor="nw")

        # Конвейер 2
        conv2_frame = ttk.LabelFrame(conveyors_frame, text="Конвейер 2", padding=10)
        conv2_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.conv2_canvas = tk.Canvas(conv2_frame)
        conv2_scrollbar = ttk.Scrollbar(conv2_frame, orient=tk.VERTICAL, command=self.conv2_canvas.yview)
        self.conv2_inner = ttk.Frame(self.conv2_canvas)

        self.conv2_canvas.configure(yscrollcommand=conv2_scrollbar.set)
        self.conv2_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conv2_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.conv2_canvas.create_window((0, 0), window=self.conv2_inner, anchor="nw")

        # Настройка прокрутки
        def configure_scrollregion(event, canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.conv1_inner.bind("<Configure>",
                              lambda e: configure_scrollregion(e, self.conv1_canvas))
        self.conv2_inner.bind("<Configure>",
                              lambda e: configure_scrollregion(e, self.conv2_canvas))

    def start_periodic_updates(self):
        """Периодическое обновление статуса"""

        def update():
            if hasattr(self, 'conv1_inner') and self.client.connected :
                self.client.request_tasks()
                # Обновляем информацию в заголовке
                self.update_header_info()
                 # Автоматически запрашиваем обновление задач каждые 30 секунд


            self.root.after(11000, update)  # Обновление каждые 30 секунд

        self.root.after(11000, update)

    def update_header_info(self):
        """Обновление информации в заголовке"""
        # Находим и обновляем label с информацией о задачах
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Label) and "Задачи:" in child.cget('text'):
                        child.config(text=self.get_tasks_info())
                        break

    def manual_refresh_tasks(self):
        """Ручное обновление задач"""
        if self.client.connected:
            self.client.request_tasks()
        else:
            messagebox.showwarning("Ошибка", "Нет подключения к серверу")

    def refresh_tasks(self):
        """Обновление отображения задач"""
        self.clear_tasks()

        if not self.client.connected:
            self.show_no_connection()
            return

        # Получаем реальные задачи от клиента
        tasks = self.client.get_tasks()
        self.show_real_tasks(tasks)

        # Обновляем информацию в заголовке
        self.update_header_info()

    def clear_tasks(self):
        """Очистка отображения задач"""
        for widget in self.conv1_inner.winfo_children():
            try:
                widget.destroy()
            except:
                pass

        for widget in self.conv2_inner.winfo_children():
            try:
                widget.destroy()
            except:
                pass

    def show_no_connection(self):
        """Показ сообщения об отсутствии подключения"""
        label = ttk.Label(
            self.conv1_inner,
            text="Нет подключения к серверу",
            font=('Arial', 12),
            foreground="red"
        )
        label.pack(pady=50)

    def show_real_tasks(self, tasks):
        """Показ реальных задач с сервера"""
        # Конвейер 1
        if tasks[0]:
            for task in tasks[0]:
                self.create_task_widget(task, 0)
        else:
            self.show_no_tasks_message(0)

        # Конвейер 2
        if tasks[1]:
            for task in tasks[1]:
                self.create_task_widget(task, 1)
        else:
            self.show_no_tasks_message(1)

    def show_no_tasks_message(self, conveyor):
        """Сообщение об отсутствии задач"""
        if conveyor == 0:
            parent = self.conv1_inner
        else:
            parent = self.conv2_inner

        label = ttk.Label(
            parent,
            text="Нет задач",
            font=('Arial', 11),
            foreground="gray"
        )
        label.pack(pady=20)

    def create_task_widget(self, task, conveyor):
        """Создание виджета задачи с управлением количеством"""
        if conveyor == 0:
            parent = self.conv1_inner
        else:
            parent = self.conv2_inner

        # Цвет фона в зависимости от статуса и приоритета
        if task.get('status') == 'completed':
            bg_color = 'lightgray'  # Серый для выполненных
            priority_color = 'darkgray'
        else:
            # Цвет по приоритету для активных задач
            priority = task.get('priority', 'Средний')
            if priority == 'Высокий':
                bg_color = '#FFCCCC'  # Светло-красный
                priority_color = 'red'
            elif priority == 'Средний':
                bg_color = '#FFFFCC'  # Светло-желтый
                priority_color = 'orange'
            else:  # Низкий
                bg_color = '#CCFFCC'  # Светло-зеленый
                priority_color = 'green'

        # Фрейм задачи
        task_frame = tk.Frame(
            parent,
            bg=bg_color,
            relief=tk.RAISED,
            bd=2
        )
        task_frame.pack(fill=tk.X, padx=5, pady=2)

        # Внутренний фрейм для содержимого
        content_frame = tk.Frame(task_frame, bg=bg_color)
        content_frame.pack(fill=tk.X, padx=5, pady=5)

        # Приоритет (выделенный цветом)
        priority_label = tk.Label(
            content_frame,
            text=" Сырье          Цвет          Подача   t°C       План/Факт %",
            bg=bg_color,
            font=('Arial', 10, 'bold'),
            fg="black",#priority_color,
            justify=tk.LEFT
        )
        priority_label.pack(anchor=tk.W)

        # Информация о количестве
        planned = task.get('planned_quantity', 0)
        completed = task.get('completed_quantity', 0)
        unit = task.get('unit', 'шт')

        # Прогресс выполнения
        if planned > 0:
            progress_percent = (completed / planned) * 100
            progress_text = f" ({progress_percent:.1f}%)"
            # Цвет прогресса
            if progress_percent >= 100:
                progress_color = "green"
            elif progress_percent >= 50:
                progress_color = "orange"
            else:
                progress_color = "red"
        else:
            progress_text = ""
            progress_color = "black"

        quantity_text = f"{completed}/{planned} {unit}{progress_text}"
        # Основная информация о задаче
        task_text = (f"{task.get('material', 'N/A'):<15} "
                     f"{task.get('color', 'N/A'):<15}"
                     f"{task.get('speed', 'N/A'):<10}"
                     f"{task.get('temperature', 'N/A'):<10}"+
                     quantity_text)

        # Добавляем информацию о времени создания если есть
        if task.get('created'):
            task_text += f"\nСоздано: {task.get('created')}"
        if task.get('completed'):
            task_text += f"\n✅ Выполнено: {task.get('completed')}"

        task_label = tk.Label(
            content_frame,
            text=task_text,
            bg=bg_color,
            font=('Arial', 9),
            justify=tk.LEFT
        )
        task_label.pack(anchor=tk.W)
        """
        quantity_text = f"Количество: {completed}/{planned} {unit}{progress_text}"
        quantity_label = tk.Label(
            content_frame,
            text=quantity_text,
            bg=bg_color,
            font=('Arial', 9, 'bold'),
            fg=progress_color,
            justify=tk.LEFT
        )
        
        quantity_label.pack(anchor=tk.W)
        """
        # Кнопки управления (только для активных задач)
        if task.get('status') == 'active':
            button_frame = tk.Frame(content_frame, bg=bg_color)
            button_frame.pack(fill=tk.X, pady=(5, 0))

            # Кнопка добавления выполненного количества
            tk.Label(button_frame, text="Добавить:", bg=bg_color).pack(side=tk.LEFT)

            quantity_entry = ttk.Entry(button_frame, width=6)
            quantity_entry.pack(side=tk.LEFT, padx=5)
            quantity_entry.insert(0, "10")  # Значение по умолчанию

            tk.Label(button_frame, text=unit, bg=bg_color).pack(side=tk.LEFT)

            def add_quantity():
                try:
                    add_qty = int(quantity_entry.get())
                    if add_qty <= 0:
                        messagebox.showwarning("Ошибка", "Введите положительное число")
                        return

                    new_completed = completed + add_qty

                    if self.client.update_task_quantity(task.get('id'), conveyor, new_completed):
                        quantity_entry.delete(0, tk.END)
                        quantity_entry.insert(0, "10")  # Сбрасываем на значение по умолчанию
                        self.refresh_tasks()
                    else:
                        messagebox.showerror("Ошибка", "Не удалось обновить количество")
                except ValueError:
                    messagebox.showwarning("Ошибка", "Введите корректное число")

            add_btn = ttk.Button(
                button_frame,
                text="Добавить",
                command=add_quantity
            )
            add_btn.pack(side=tk.LEFT, padx=5)

            # Кнопка полного выполнения
            complete_btn = ttk.Button(
                button_frame,
                text="Выполнить всё",
                command=lambda: self.client.update_task_quantity(task.get('id'), conveyor, planned)
            )
            complete_btn.pack(side=tk.RIGHT, padx=5)

    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Выйти из системы?"):
            self.client.disconnect()
            self.show_login_screen()


def main():
    """Главная функция с обработкой исключений"""
    try:
        root = tk.Tk()
        app = OperatorGUI(root)

        def on_closing():
            if messagebox.askokcancel("Выход", "Закрыть приложение?"):
                app.client.disconnect()
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        messagebox.showerror("Ошибка", f"Не удалось запустить приложение: {e}")


if __name__ == "__main__":
    main()