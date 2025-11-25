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
            # Удаляем клиента из активных
            for username, sock in list(self.clients.items()):
                if sock == client_socket:
                    self.operators[username]['active'] = False
                    del self.clients[username]
                    break
            client_socket.close()

    def process_message(self, message, client_socket):
        msg_type = message.get('type')

        if msg_type == 'login':
            return self.handle_login(message, client_socket)
        elif msg_type == 'get_operators':
            return self.handle_get_operators()
        elif msg_type == 'get_operator_tasks':  # Добавляем новый тип
            return self.handle_get_operator_tasks(message)
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
        task_data = message.get('task')

        if operator in self.operators:
            task_id = f"task_{int(time.time())}_{conveyor}"
            task = {
                'id': task_id,
                'material': task_data['material'],
                'color': task_data['color'],
                'speed': task_data['speed'],
                'temperature': task_data['temperature'],
                'status': 'active',
                'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            self.operators[operator]['tasks'][conveyor].append(task)
            print(f"Задача добавлена для {operator}, конвейер {conveyor}: {task}")

            # Уведомление оператора если он онлайн
            if self.operators[operator]['active'] and operator in self.clients:
                try:
                    notification = {
                        'type': 'new_task',
                        'task': task,
                        'conveyor': conveyor
                    }
                    self.clients[operator].send(json.dumps(notification).encode('utf-8'))
                except Exception as e:
                    print(f"Ошибка отправки уведомления: {e}")

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

    def handle_get_operator_tasks(self, message):
        """Обработка запроса задач оператора"""
        operator = message.get('operator')

        if operator in self.operators:
            tasks = self.operators[operator]['tasks']
            return {
                'status': 'success',
                'type': 'operator_tasks_response',
                'tasks': tasks
            }
        return {'status': 'error', 'message': 'Оператор не найден'}
