import socket
import threading
import json
import time
from datetime import datetime
from server_discovery import ServerDiscovery
from data_manager import data_manager


class ServerManager:
    def __init__(self):
        # Загружаем операторов из файла
        self.operators_list = data_manager.load_operators()
        self.clients = {}
        self.server_socket = None
        self.running = False
        self.discovery = ServerDiscovery()

    def get_operators_dict(self):
        """Конвертирует список операторов в словарь для обратной совместимости"""
        operators_dict = {}
        for operator in self.operators_list:
            operators_dict[operator['username']] = {
                'password': operator['password'],
                'active': operator['active'],
                'tasks': operator['tasks']
            }
        return operators_dict

    def save_operators(self):
        """Сохранение операторов в файл"""
        data_manager.save_operators(self.operators_list)

    def start_server(self, host='0.0.0.0', port=12345):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(5)
            self.running = True

            # Запускаем UDP discovery
            self.discovery.start_server_discovery()

            # Получаем реальный IP
            actual_host = host if host != '0.0.0.0' else socket.gethostbyname(socket.gethostname())
            print(f"=== СЕРВЕР ЗАПУЩЕН ===")
            print(f"TCP: {actual_host}:{port}")
            print(f"UDP Discovery: порт {self.discovery.discovery_port}")
            print(f"Ожидание подключений...")

            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()

        except Exception as e:
            print(f"ОШИБКА запуска сервера: {e}")
            print(f"Проверьте:")
            print(f"1. Firewall разрешает порт {port}")
            print(f"2. Порт {port} не занят другой программой")
            print(f"3. IP адрес корректен")

    def accept_connections(self):
        """Принятие входящих подключений"""
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
        """Обработка клиентского подключения"""
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
            # Удаляем клиента из активных и обновляем статус
            for username, sock in list(self.clients.items()):
                if sock == client_socket:
                    data_manager.update_operator_status(username, False)
                    # Обновляем локальный список
                    self.operators_list = data_manager.load_operators()
                    del self.clients[username]
                    print(f"Оператор {username} отключился")
                    break
            client_socket.close()

    def process_message(self, message, client_socket):
        """Обработка входящих сообщений"""
        msg_type = message.get('type')

        if msg_type == 'login':
            return self.handle_login(message, client_socket)
        elif msg_type == 'get_operators':
            return self.handle_get_operators()
        elif msg_type == 'get_operator_tasks':
            return self.handle_get_operator_tasks(message)
        elif msg_type == 'add_task':
            return self.handle_add_task(message)
        elif msg_type == 'add_operator':
            return self.handle_add_operator(message)
        elif msg_type == 'update_task_status':
            return self.handle_update_task_status(message)
        elif msg_type == 'update_task_quantity':
            return self.handle_update_task_quantity(message)
        elif msg_type == 'heartbeat':
            return {'status': 'alive'}

        return {'status': 'error', 'message': 'Неизвестный тип сообщения'}

    def handle_login(self, message, client_socket):
        """Обработка входа пользователя"""
        username = message.get('username')
        password = message.get('password')

        operator = data_manager.get_operator_by_username(username)
        if operator and operator['password'] == password:
            # Обновляем статус активности
            data_manager.update_operator_status(username, True)
            # Обновляем локальный список
            self.operators_list = data_manager.load_operators()

            self.clients[username] = client_socket
            print(f"Оператор {username} успешно авторизовался")
            return {'status': 'success', 'user_type': 'operator'}
        elif username == 'manager' and password == 'manager':
            print(f"Менеджер успешно авторизовался")
            return {'status': 'success', 'user_type': 'manager'}
        else:
            print(f"Неудачная попытка входа: {username}")
            return {'status': 'error', 'message': 'Неверные учетные данные'}

    def handle_get_operators(self):
        """Возвращает данные операторов для отображения в GUI"""
        operators_data = {}
        for operator in self.operators_list:
            operators_data[operator['username']] = {
                'active': operator['active'],
                'tasks': operator['tasks']
            }
        return {'status': 'success', 'operators': operators_data}

    def handle_get_operator_tasks(self, message):
        """Обработка запроса задач оператора"""
        operator_name = message.get('operator')

        operator = data_manager.get_operator_by_username(operator_name)
        if operator:
            return {
                'status': 'success',
                'type': 'operator_tasks_response',
                'tasks': operator['tasks']
            }
        return {'status': 'error', 'message': 'Оператор не найден'}

    def handle_add_operator(self, message):
        """Добавление нового оператора"""
        username = message.get('username')
        password = message.get('password')

        success, message_text = data_manager.add_operator(username, password)
        if success:
            # Обновляем локальный список
            self.operators_list = data_manager.load_operators()
            print(f"Добавлен новый оператор: {username}")
        else:
            print(f"Ошибка добавления оператора {username}: {message_text}")

        return {'status': 'success' if success else 'error', 'message': message_text}

    def handle_add_task(self, message):
        """Добавление новой задачи"""
        operator_name = message.get('operator')
        conveyor = message.get('conveyor')
        task_data = message.get('task')

        operator = data_manager.get_operator_by_username(operator_name)
        if operator:
            task_id = f"task_{int(time.time())}_{conveyor}"
            task = {
                'id': task_id,
                'material': task_data['material'],
                'color': task_data['color'],
                'speed': task_data['speed'],
                'temperature': task_data['temperature'],
                'priority': task_data.get('priority', 'Средний'),
                'planned_quantity': task_data.get('planned_quantity', 0),
                'completed_quantity': 0,
                'unit': task_data.get('unit', 'шт'),
                'status': 'active',
                'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Добавляем задачу оператору
            operator['tasks'][conveyor].append(task)
            data_manager.update_operator_tasks(operator_name, operator['tasks'])

            # Обновляем локальный список
            self.operators_list = data_manager.load_operators()

            print(f"Задача добавлена для {operator_name}, конвейер {conveyor}: {task}")

            # Уведомление оператора если он онлайн
            if operator['active'] and operator_name in self.clients:
                try:
                    notification = {
                        'type': 'new_task',
                        'task': task,
                        'conveyor': conveyor
                    }
                    notification_str = json.dumps(notification) + '\n'
                    self.clients[operator_name].send(notification_str.encode('utf-8'))
                    print(f"Уведомление отправлено оператору {operator_name}")
                except Exception as e:
                    print(f"Ошибка отправки уведомления: {e}")

            return {'status': 'success', 'task_id': task_id}
        return {'status': 'error', 'message': 'Оператор не найден'}

    def handle_update_task_status(self, message):
        """Обновление статуса задачи"""
        operator_name = message.get('operator')
        conveyor = message.get('conveyor')
        task_id = message.get('task_id')
        status = message.get('status')

        operator = data_manager.get_operator_by_username(operator_name)
        if operator:
            for task in operator['tasks'][conveyor]:
                if task.get('id') == task_id:
                    task['status'] = status
                    task['completed'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    data_manager.update_operator_tasks(operator_name, operator['tasks'])
                    # Обновляем локальный список
                    self.operators_list = data_manager.load_operators()

                    print(f"Статус задачи {task_id} обновлен на {status}")
                    return {'status': 'success'}

        return {'status': 'error', 'message': 'Задача не найдена'}

    def handle_update_task_quantity(self, message):
        """Обновление выполненного количества задачи"""
        operator_name = message.get('operator')
        conveyor = message.get('conveyor')
        task_id = message.get('task_id')
        completed_quantity = message.get('completed_quantity')

        operator = data_manager.get_operator_by_username(operator_name)
        if operator:
            for task in operator['tasks'][conveyor]:
                if task.get('id') == task_id:
                    task['completed_quantity'] = completed_quantity

                    # Проверяем, выполнена ли задача полностью
                    planned = task.get('planned_quantity', 0)
                    if planned > 0 and completed_quantity >= planned:
                        task['status'] = 'completed'
                        task['completed'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"Задача {task_id} выполнена полностью: {completed_quantity}/{planned}")

                    data_manager.update_operator_tasks(operator_name, operator['tasks'])
                    # Обновляем локальный список
                    self.operators_list = data_manager.load_operators()

                    print(f"Количество задачи {task_id} обновлено: {completed_quantity}")
                    return {'status': 'success'}

        return {'status': 'error', 'message': 'Задача не найдена'}

    def send_notification_to_operator(self, operator_name, notification):
        """Отправка уведомления оператору"""
        if operator_name in self.clients and self.operators_dict().get(operator_name, {}).get('active', False):
            try:
                notification_str = json.dumps(notification) + '\n'
                self.clients[operator_name].send(notification_str.encode('utf-8'))
                print(f"Уведомление отправлено оператору {operator_name}")
                return True
            except Exception as e:
                print(f"Ошибка отправки уведомления оператору {operator_name}: {e}")
                return False
        return False

    def get_operator_stats(self):
        """Получение статистики по операторам"""
        stats = {
            'total_operators': len(self.operators_list),
            'online_operators': sum(1 for op in self.operators_list if op['active']),
            'total_tasks': 0,
            'active_tasks': 0,
            'completed_tasks': 0
        }

        for operator in self.operators_list:
            for conveyor_tasks in operator['tasks']:
                stats['total_tasks'] += len(conveyor_tasks)
                stats['active_tasks'] += sum(1 for task in conveyor_tasks if task.get('status') == 'active')
                stats['completed_tasks'] += sum(1 for task in conveyor_tasks if task.get('status') == 'completed')

        return stats

    def broadcast_to_all_operators(self, message):
        """Отправка сообщения всем подключенным операторам"""
        disconnected_operators = []

        for operator_name, client_socket in self.clients.items():
            try:
                message_str = json.dumps(message) + '\n'
                client_socket.send(message_str.encode('utf-8'))
            except Exception as e:
                print(f"Ошибка отправки сообщения оператору {operator_name}: {e}")
                disconnected_operators.append(operator_name)

        # Удаляем отключенных операторов
        for operator_name in disconnected_operators:
            if operator_name in self.clients:
                del self.clients[operator_name]
                data_manager.update_operator_status(operator_name, False)

    def stop_server(self):
        """Остановка сервера"""
        print("Остановка сервера...")
        self.running = False

        # Обновляем статусы всех операторов на неактивные
        for operator in self.operators_list:
            if operator['active']:
                data_manager.update_operator_status(operator['username'], False)

        # Закрываем все клиентские соединения
        for client_socket in self.clients.values():
            try:
                client_socket.close()
            except:
                pass

        # Останавливаем discovery сервер
        self.discovery.stop_discovery()

        # Закрываем серверный сокет
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        print("Сервер остановлен")

    def __del__(self):
        """Деструктор - гарантирует корректное закрытие"""
        self.stop_server()


# Дополнительные утилиты для работы с сервером
class ServerUtils:
    @staticmethod
    def validate_task_data(task_data):
        """Валидация данных задачи"""
        required_fields = ['material', 'color', 'speed', 'temperature']
        for field in required_fields:
            if not task_data.get(field):
                return False, f"Отсутствует обязательное поле: {field}"

        # Проверка числовых полей
        try:
            planned_quantity = int(task_data.get('planned_quantity', 0))
            if planned_quantity < 0:
                return False, "Количество не может быть отрицательным"
        except ValueError:
            return False, "Некорректное значение количества"

        return True, "OK"

    @staticmethod
    def format_task_for_display(task):
        """Форматирование задачи для отображения"""
        return {
            'id': task.get('id', ''),
            'material': task.get('material', 'N/A'),
            'color': task.get('color', 'N/A'),
            'speed': task.get('speed', 'N/A'),
            'temperature': task.get('temperature', 'N/A'),
            'priority': task.get('priority', 'Средний'),
            'planned_quantity': task.get('planned_quantity', 0),
            'completed_quantity': task.get('completed_quantity', 0),
            'unit': task.get('unit', 'шт'),
            'status': task.get('status', 'active'),
            'created': task.get('created', ''),
            'completed': task.get('completed', '')
        }


# Пример использования сервера
if __name__ == "__main__":
    def run_test_server():
        """Запуск тестового сервера"""
        server = ServerManager()

        try:
            server.start_server()
            print("Сервер запущен. Нажмите Enter для остановки...")
            input()
        except KeyboardInterrupt:
            print("\nОстановка сервера...")
        finally:
            server.stop_server()


    run_test_server()