import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import json
import time
from datetime import datetime


class ServerManager:
    def __init__(self):
        self.operators = {
            'operator1': {'password': 'pass1', 'active': False, 'tasks': [[], []]},
            'operator2': {'password': 'pass2', 'active': False, 'tasks': [[], []]},
            'operator3': {'password': 'pass3', 'active': False, 'tasks': [[], []]}
        }
        self.clients = {}
        self.server_socket = None
        self.running = False

    def start_server(self, host='localhost', port=12345):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((host, port))
            self.server_socket.listen(5)
            self.running = True
            print(f"Сервер запущен на {host}:{port}")

            # Запуск потока для принятия подключений
            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()

        except Exception as e:
            print(f"Ошибка запуска сервера: {e}")

    def accept_connections(self):
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Подключение от {address}")

                # Запуск потока для обработки клиента
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()

            except Exception as e:
                if self.running:
                    print(f"Ошибка принятия подключения: {e}")

    def handle_client(self, client_socket):
        try:
            while self.running:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                message = json.loads(data)
                response = self.process_message(message, client_socket)
                client_socket.send(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f"Ошибка обработки клиента: {e}")
        finally:
            client_socket.close()

    def process_message(self, message, client_socket):
        msg_type = message.get('type')

        if msg_type == 'login':
            return self.handle_login(message, client_socket)
        elif msg_type == 'get_operators':
            return self.handle_get_operators()
        elif msg_type == 'add_task':
            return self.handle_add_task(message)
        elif msg_type == 'add_operator':
            return self.handle_add_operator(message)
        elif msg_type == 'update_task_status':
            return self.handle_update_task_status(message)
        elif msg_type == 'heartbeat':
            return {'status': 'alive'}

        return {'status': 'error', 'message': 'Неизвестный тип сообщения'}

    def handle_login(self, message, client_socket):
        username = message.get('username')
        password = message.get('password')

        if username in self.operators and self.operators[username]['password'] == password:
            self.operators[username]['active'] = True
            self.clients[username] = client_socket
            return {'status': 'success', 'user_type': 'operator'}
        elif username == 'manager' and password == 'manager':
            return {'status': 'success', 'user_type': 'manager'}
        else:
            return {'status': 'error', 'message': 'Неверные учетные данные'}

    def handle_get_operators(self):
        operators_data = {}
        for username, data in self.operators.items():
            operators_data[username] = {
                'active': data['active'],
                'tasks': data['tasks']
            }
        return {'status': 'success', 'operators': operators_data}

    def handle_add_task(self, message):
        operator = message.get('operator')
        conveyor = message.get('conveyor')
        task = message.get('task')

        if operator in self.operators:
            task_id = f"task_{int(time.time())}"
            task['id'] = task_id
            task['status'] = 'active'
            task['created'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.operators[operator]['tasks'][conveyor].append(task)

            # Уведомление оператора если он онлайн
            if self.operators[operator]['active'] and operator in self.clients:
                try:
                    notification = {
                        'type': 'new_task',
                        'task': task,
                        'conveyor': conveyor
                    }
                    self.clients[operator].send(json.dumps(notification).encode('utf-8'))
                except:
                    pass

            return {'status': 'success', 'task_id': task_id}
        return {'status': 'error', 'message': 'Оператор не найден'}

    def handle_add_operator(self, message):
        username = message.get('username')
        password = message.get('password')

        if username in self.operators:
            return {'status': 'error', 'message': 'Оператор уже существует'}

        self.operators[username] = {
            'password': password,
            'active': False,
            'tasks': [[], []]
        }
        return {'status': 'success'}

    def handle_update_task_status(self, message):
        operator = message.get('operator')
        conveyor = message.get('conveyor')
        task_id = message.get('task_id')
        status = message.get('status')

        if operator in self.operators:
            for task in self.operators[operator]['tasks'][conveyor]:
                if task.get('id') == task_id:
                    task['status'] = status
                    task['completed'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    return {'status': 'success'}

        return {'status': 'error', 'message': 'Задача не найдена'}


class ManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Manager Panel - Production Control System")
        self.root.geometry("1200x700")

        self.server = ServerManager()
        self.server.start_server()

        self.current_operator = None
        self.current_conveyor = 0

        self.setup_gui()
        self.refresh_operators()

    def setup_gui(self):
        # Верхняя панель с операторами
        operator_frame = ttk.Frame(self.root)
        operator_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(operator_frame, text="Операторы:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)

        # Фрейм для кнопок операторов с прокруткой
        self.operator_canvas = tk.Canvas(operator_frame, height=60)
        self.operator_scrollbar = ttk.Scrollbar(operator_frame, orient=tk.HORIZONTAL,
                                                command=self.operator_canvas.xview)
        self.operator_inner_frame = ttk.Frame(self.operator_canvas)

        self.operator_canvas.configure(xscrollcommand=self.operator_scrollbar.set)
        self.operator_canvas.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.operator_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.operator_canvas.create_window((0, 0), window=self.operator_inner_frame, anchor="nw")
        self.operator_inner_frame.bind("<Configure>", self.on_operator_frame_configure)

        # Основная область с задачами
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Заголовок выбранного оператора
        self.operator_label = ttk.Label(main_frame, text="Выберите оператора", font=('Arial', 14, 'bold'))
        self.operator_label.pack(pady=10)

        # Фрейм для двух конвейеров
        conveyor_frame = ttk.Frame(main_frame)
        conveyor_frame.pack(fill=tk.BOTH, expand=True)

        # Конвейер 1
        conveyor1_frame = ttk.LabelFrame(conveyor_frame, text="Конвейер 1", padding=10)
        conveyor1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.conveyor1_canvas = tk.Canvas(conveyor1_frame)
        conveyor1_scrollbar = ttk.Scrollbar(conveyor1_frame, orient=tk.VERTICAL, command=self.conveyor1_canvas.yview)
        self.conveyor1_inner_frame = ttk.Frame(self.conveyor1_canvas)

        self.conveyor1_canvas.configure(yscrollcommand=conveyor1_scrollbar.set)
        self.conveyor1_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conveyor1_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.conveyor1_canvas.create_window((0, 0), window=self.conveyor1_inner_frame, anchor="nw")

        # Конвейер 2
        conveyor2_frame = ttk.LabelFrame(conveyor_frame, text="Конвейер 2", padding=10)
        conveyor2_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.conveyor2_canvas = tk.Canvas(conveyor2_frame)
        conveyor2_scrollbar = ttk.Scrollbar(conveyor2_frame, orient=tk.VERTICAL, command=self.conveyor2_canvas.yview)
        self.conveyor2_inner_frame = ttk.Frame(self.conveyor2_canvas)

        self.conveyor2_canvas.configure(yscrollcommand=conveyor2_scrollbar.set)
        self.conveyor2_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conveyor2_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.conveyor2_canvas.create_window((0, 0), window=self.conveyor2_inner_frame, anchor="nw")

        # Привязка событий прокрутки
        self.conveyor1_inner_frame.bind("<Configure>", lambda e: self.conveyor1_canvas.configure(
            scrollregion=self.conveyor1_canvas.bbox("all")))
        self.conveyor2_inner_frame.bind("<Configure>", lambda e: self.conveyor2_canvas.configure(
            scrollregion=self.conveyor2_canvas.bbox("all")))

    def on_operator_frame_configure(self, event):
        self.operator_canvas.configure(scrollregion=self.operator_canvas.bbox("all"))

    def refresh_operators(self):
        # Очистка текущих кнопок операторов
        for widget in self.operator_inner_frame.winfo_children():
            widget.destroy()

        operators_data = self.server.handle_get_operators()['operators']

        # Кнопки операторов
        for username, data in operators_data.items():
            color = 'lightblue' if data['active'] else 'lightgray'
            btn = tk.Button(
                self.operator_inner_frame,
                text=username,
                width=15,
                height=2,
                bg=color,
                font=('Arial', 10),
                command=lambda u=username: self.select_operator(u)
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Кнопка добавления оператора
        add_btn = tk.Button(
            self.operator_inner_frame,
            text="+",
            width=5,
            height=2,
            bg='lightgreen',
            font=('Arial', 14, 'bold'),
            command=self.add_operator
        )
        add_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def select_operator(self, username):
        self.current_operator = username
        self.operator_label.config(text=f"Оператор: {username}")
        self.refresh_tasks()

    def refresh_tasks(self):
        if not self.current_operator:
            return

        # Очистка текущих задач
        for widget in self.conveyor1_inner_frame.winfo_children():
            widget.destroy()
        for widget in self.conveyor2_inner_frame.winfo_children():
            widget.destroy()

        operators_data = self.server.handle_get_operators()['operators']
        tasks = operators_data[self.current_operator]['tasks']

        # Отображение задач для конвейера 1
        self.display_tasks_for_conveyor(tasks[0], self.conveyor1_inner_frame, 0)

        # Отображение задач для конвейера 2
        self.display_tasks_for_conveyor(tasks[1], self.conveyor2_inner_frame, 1)

    def display_tasks_for_conveyor(self, tasks, frame, conveyor):
        # Кнопка добавления задачи
        add_task_btn = tk.Button(
            frame,
            text="+",
            height=3,
            bg='lightgreen',
            font=('Arial', 20, 'bold'),
            command=lambda: self.add_task(conveyor)
        )
        add_task_btn.pack(fill=tk.X, padx=5, pady=2)

        # Существующие задачи
        for task in tasks:
            color = 'lightyellow' if task['status'] == 'completed' else 'white'
            task_frame = tk.Frame(frame, bg=color, relief=tk.RAISED, bd=1)
            task_frame.pack(fill=tk.X, padx=5, pady=2)

            info_text = f"Сырье: {task['material']}\nЦвет: {task['color']}\nСкорость: {task['speed']}\nТемпература: {task['temperature']}"
            if task['status'] == 'completed':
                info_text += f"\nВыполнено: {task.get('completed', '')}"

            tk.Label(
                task_frame,
                text=info_text,
                bg=color,
                font=('Arial', 9),
                justify=tk.LEFT
            ).pack(padx=5, pady=5)

    def add_task(self, conveyor):
        if not self.current_operator:
            messagebox.showwarning("Предупреждение", "Сначала выберите оператора")
            return

        self.show_task_dialog(conveyor)

    def show_task_dialog(self, conveyor):
        dialog = tk.Toplevel(self.root)
        dialog.title("Новая задача")
        dialog.geometry("300x250")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Сырье:").pack(pady=5)
        material_entry = ttk.Entry(dialog, width=30)
        material_entry.pack(pady=5)

        ttk.Label(dialog, text="Цвет:").pack(pady=5)
        color_entry = ttk.Entry(dialog, width=30)
        color_entry.pack(pady=5)

        ttk.Label(dialog, text="Скорость подачи:").pack(pady=5)
        speed_entry = ttk.Entry(dialog, width=30)
        speed_entry.pack(pady=5)

        ttk.Label(dialog, text="Температура:").pack(pady=5)
        temp_entry = ttk.Entry(dialog, width=30)
        temp_entry.pack(pady=5)

        def save_task():
            task = {
                'material': material_entry.get(),
                'color': color_entry.get(),
                'speed': speed_entry.get(),
                'temperature': temp_entry.get()
            }

            result = self.server.handle_add_task({
                'operator': self.current_operator,
                'conveyor': conveyor,
                'task': task
            })

            if result['status'] == 'success':
                self.refresh_tasks()
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить задачу")

        ttk.Button(dialog, text="Сохранить", command=save_task).pack(pady=10)

    def add_operator(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить оператора")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Логин:").pack(pady=5)
        login_entry = ttk.Entry(dialog, width=30)
        login_entry.pack(pady=5)

        ttk.Label(dialog, text="Пароль:").pack(pady=5)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.pack(pady=5)

        def save_operator():
            result = self.server.handle_add_operator({
                'username': login_entry.get(),
                'password': password_entry.get()
            })

            if result['status'] == 'success':
                self.refresh_operators()
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", result['message'])

        ttk.Button(dialog, text="Сохранить", command=save_operator).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = ManagerGUI(root)
    root.mainloop()