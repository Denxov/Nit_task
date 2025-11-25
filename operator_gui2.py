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

        return self.send_and_receive(message)

    def send_and_receive(self, message):
        try:
            with self.lock:
                # Отправляем сообщение
                message_str = json.dumps(message) + '\n'
                self.socket.send(message_str.encode('utf-8'))
                print(f"Отправлено: {message['type']}")

                # Ждем ответ
                response = self.socket.recv(1024).decode('utf-8').strip()
                if response:
                    return json.loads(response)
                else:
                    return {'status': 'error', 'message': 'Пустой ответ от сервера'}

        except socket.timeout:
            return {'status': 'error', 'message': 'Таймаут ожидания ответа'}
        except json.JSONDecodeError:
            return {'status': 'error', 'message': 'Неверный формат ответа'}
        except Exception as e:
            print(f"Ошибка обмена данными: {e}")
            return {'status': 'error', 'message': str(e)}

    def receive_messages(self):
        while self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break

                # Обрабатываем входящие сообщения (уведомления)
                messages = data.strip().split('\n')
                for msg in messages:
                    if msg:
                        try:
                            message = json.loads(msg)
                            self.handle_notification(message)
                        except json.JSONDecodeError:
                            print(f"Неверный JSON: {msg}")

            except socket.timeout:
                continue
            except Exception as e:
                if self.connected:
                    print(f"Ошибка приема: {e}")
                break

        self.connected = False
        print("Поток приема завершен")

    def handle_notification(self, message):
        msg_type = message.get('type')
        print(f"Уведомление: {msg_type}")

        if msg_type == 'new_task':
            print(f"Новая задача: {message}")
            if hasattr(self, 'on_new_task'):
                self.on_new_task(message)

    def set_new_task_callback(self, callback):
        self.on_new_task = callback

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
                f"Цвет: {task.get('color', 'N/A')}"
            )
            self.refresh_tasks()

        # Вызываем в основном потоке
        self.root.after(0, show_notification)

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
            text="Тест: operator1/pass1",
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

        # Кнопки управления
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)

        refresh_btn = ttk.Button(btn_frame, text="Обновить", command=self.refresh_tasks)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        logout_btn = ttk.Button(btn_frame, text="Выйти", command=self.logout)
        logout_btn.pack(side=tk.LEFT, padx=5)

        # Конвейеры
        self.setup_conveyors()

        # Загружаем задачи
        self.refresh_tasks()

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

    def refresh_tasks(self):
        """Обновление отображения задач"""
        self.clear_tasks()

        if not self.client.connected:
            self.show_no_connection()
            return

        self.show_demo_tasks()

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

    def show_demo_tasks(self):
        """Показ демонстрационных задач"""
        tasks = [
            {
                'material': 'Пластик ABS',
                'color': 'Красный',
                'speed': '100 мм/с',
                'temperature': '220°C',
                'status': 'active',
                'id': '1'
            },
            {
                'material': 'Поликарбонат',
                'color': 'Прозрачный',
                'speed': '80 мм/с',
                'temperature': '280°C',
                'status': 'completed',
                'id': '2'
            }
        ]

        for i, task in enumerate(tasks):
            conveyor = 0 if i % 2 == 0 else 1
            self.create_task_widget(task, conveyor)

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
            f"Сырье: {task['material']}\n"
            f"Цвет: {task['color']}\n"
            f"Скорость: {task['speed']}\n"
            f"Температура: {task['temperature']}"
        )

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
                command=lambda t=task: self.complete_task(t)
            )
            complete_btn.pack(side=tk.RIGHT, padx=5, pady=5)

    def complete_task(self, task):
        """Отметка задачи как выполненной"""
        result = messagebox.askyesno(
            "Подтверждение",
            f"Задача выполнена?\n{task['material']} - {task['color']}"
        )

        if result:
            messagebox.showinfo("Успех", "Задача отмечена как выполненная")
            self.refresh_tasks()

    def logout(self):
        """Выход из системы"""
        self.client.disconnect()
        self.show_login_screen()


def main():
    """Главная функция с обработкой исключений"""
    try:
        root = tk.Tk()
        app = OperatorGUI(root)

        def on_closing():
            app.client.disconnect()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        messagebox.showerror("Ошибка", f"Не удалось запустить приложение: {e}")


if __name__ == "__main__":
    main()