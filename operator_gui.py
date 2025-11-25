import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import threading
import time


class OperatorClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.username = None
        self.connected = False
        self.receive_thread = None
        self.lock = threading.Lock()
        self.current_tasks = [[], []]  # Задачи для двух конвейеров

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(0.5)
            self.connected = True

            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            print("Успешное подключение к серверу")
            return True

        except Exception as e:
            print(f"Ошибка подключения: {e}")
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

                # Получаем ответ
                response_data = b""
                start_time = time.time()

                while time.time() - start_time < 10:  # Таймаут 10 секунд
                    try:
                        # Устанавливаем короткий таймаут для recv
                        self.socket.settimeout(0.1)
                        chunk = self.socket.recv(1024)
                        if chunk:
                            response_data += chunk

                            # Пробуем декодить JSON
                            try:
                                response_str = response_data.decode('utf-8').strip()
                                if response_str:
                                    # Ищем полный JSON (до новой строки)
                                    if '\n' in response_str:
                                        response_str = response_str.split('\n')[0]
                                    response = json.loads(response_str)
                                    self.socket.settimeout(0.5)  # Возвращаем обычный таймаут
                                    return response
                            except json.JSONDecodeError:
                                # Неполный JSON, продолжаем читать
                                continue
                        else:
                            # Сервер закрыл соединение
                            break

                    except socket.timeout:
                        # Таймаут recv - продолжаем цикл
                        continue
                    except BlockingIOError:
                        # Нет данных - продолжаем цикл
                        continue

                # Таймаут основного цикла
                self.socket.settimeout(0.5)
                if response_data:
                    try:
                        response_str = response_data.decode('utf-8').strip()
                        if response_str:
                            if '\n' in response_str:
                                response_str = response_str.split('\n')[0]
                            response = json.loads(response_str)
                            return response
                    except:
                        pass

                return {'status': 'error', 'message': 'Таймаут ожидания ответа'}

        except Exception as e:
            if hasattr(self, 'socket') and self.socket:
                self.socket.settimeout(0.5)
            print(f"Ошибка обмена данными: {e}")
            return {'status': 'error', 'message': f'Ошибка связи: {str(e)}'}

    def receive_messages(self):
        buffer = ""
        while self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break

                buffer += data

                # Обрабатываем полные сообщения
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            message = json.loads(line)
                            self.handle_server_message(message)
                        except json.JSONDecodeError:
                            print(f"Неверный JSON: {line}")

            except socket.timeout:
                continue
            except Exception as e:
                if self.connected:
                    print(f"Ошибка приема: {e}")
                break

        self.connected = False
        print("Поток приема завершен")

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

    def update_task_status(self, task_id, conveyor, status='completed'):
        """Обновление статуса задачи"""
        try:
            # Ищем задачу и обновляем статус
            for i, task in enumerate(self.current_tasks[conveyor]):
                if task.get('id') == task_id:
                    self.current_tasks[conveyor][i]['status'] = status
                    self.current_tasks[conveyor][i]['completed'] = time.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"Статус задачи {task_id} обновлен на {status}")

                    # Отправляем обновление на сервер
                    update_message = {
                        'type': 'update_task_status',
                        'operator': self.username,
                        'conveyor': conveyor,
                        'task_id': task_id,
                        'status': status
                    }
                    self.send_and_receive(update_message)

                    return True
            return False
        except Exception as e:
            print(f"Ошибка обновления задачи: {e}")
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
        self.root.geometry("800x600")

        # Создаем основной фрейм
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.client = OperatorClient()
        self.client.set_new_task_callback(self.handle_new_task)
        self.client.set_tasks_updated_callback(self.handle_tasks_updated)

        self.show_login_screen()

    def handle_new_task(self, message):
        """Обработка новой задачи от сервера"""

        def show_notification():
            task = message.get('task', {})
            conveyor = message.get('conveyor', 0) + 1
            messagebox.showinfo(
                "Новая задача",
                f"Получена новая задача на конвейере {conveyor}:\n"
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
        """Показ экрана входа"""
        self.clear_screen()

        # Создаем фреймы безопасно
        login_container = ttk.Frame(self.main_frame)
        login_container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        login_frame = ttk.Frame(login_container)
        login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Заголовок
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

        # Кнопка входа
        self.login_btn = ttk.Button(
            login_frame,
            text="Войти",
            command=self.do_login
        )
        self.login_btn.grid(row=3, column=0, columnspan=2, pady=20)

        # Статус
        self.status_label = ttk.Label(
            login_frame,
            text="Готов к подключению",
            foreground="green"
        )
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)

        # Тестовые данные
        test_label = ttk.Label(
            login_frame,
            text="Тест: operator1/pass1, operator2/pass2, operator3/pass3",
            font=('Arial', 9),
            foreground="gray"
        )
        test_label.grid(row=5, column=0, columnspan=2, pady=10)

        # Автозаполнение
        self.login_entry.insert(0, "operator1")
        self.password_entry.insert(0, "pass1")

        # Привязка Enter
        self.root.bind('<Return>', lambda e: self.do_login())
        self.login_entry.focus()

    def do_login(self):
        """Выполнение входа"""
        username = self.login_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Ошибка", "Введите логин и пароль")
            return

        # Блокируем UI
        self.login_btn.config(state='disabled')
        self.status_label.config(text="Подключение...", foreground="orange")

        # Запускаем в отдельном потоке
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
        status_label = ttk.Label(
            header_frame,
            text=f"Статус: {conn_status}",
            foreground="green" if self.client.connected else "red"
        )
        status_label.pack(side=tk.LEFT, padx=20)

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
            if hasattr(self, 'conv1_inner') and self.client.connected:
                # Автоматически запрашиваем обновление задач каждые 30 секунд
                self.client.request_tasks()
            self.root.after(30000, update)  # Обновление каждые 30 секунд

        self.root.after(30000, update)

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
        """Создание виджета задачи"""
        if conveyor == 0:
            parent = self.conv1_inner
        else:
            parent = self.conv2_inner

        # Цвет фона в зависимости от статуса
        bg_color = 'lightyellow' if task.get('status') == 'completed' else 'white'

        # Фрейм задачи
        task_frame = tk.Frame(
            parent,
            bg=bg_color,
            relief=tk.RAISED,
            bd=1
        )
        task_frame.pack(fill=tk.X, padx=5, pady=2)

        # Текст задачи
        task_text = (
            f"Сырье: {task.get('material', 'N/A')}\n"
            f"Цвет: {task.get('color', 'N/A')}\n"
            f"Скорость: {task.get('speed', 'N/A')}\n"
            f"Температура: {task.get('temperature', 'N/A')}"
        )

        # Добавляем информацию о времени создания если есть
        if task.get('created'):
            task_text += f"\nСоздано: {task.get('created')}"
        if task.get('completed'):
            task_text += f"\nВыполнено: {task.get('completed')}"

        task_label = tk.Label(
            task_frame,
            text=task_text,
            bg=bg_color,
            font=('Arial', 9),
            justify=tk.LEFT
        )
        task_label.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        # Кнопка выполнения
        if task.get('status') == 'active':
            complete_btn = ttk.Button(
                task_frame,
                text="Выполнено",
                command=lambda t=task, c=conveyor: self.complete_task(t, c)
            )
            complete_btn.pack(side=tk.RIGHT, padx=5, pady=5)

    def complete_task(self, task, conveyor):
        """Отметка задачи как выполненной"""
        if not self.client.connected:
            messagebox.showwarning("Нет подключения", "Нет подключения к серверу")
            return

        result = messagebox.askyesno(
            "Подтверждение",
            f"Отметить задачу как выполненную?\n"
            f"Сырье: {task.get('material', 'N/A')}\n"
            f"Цвет: {task.get('color', 'N/A')}"
        )

        if result:
            task_id = task.get('id')
            if task_id and self.client.update_task_status(task_id, conveyor, 'completed'):
                messagebox.showinfo("Успех", "Задача отмечена как выполненная")
                self.refresh_tasks()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить статус задачи")

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