import socket, pickle

class ProcessData:
    def __init__(self) -> None:
        self.process_id = 0
        self.project_id = 0
        self.task_id = 0
        self.start_time = 0
        self.end_time = 0
        self.user_id = 0
        self.weekend_id = 0


HOST = '127.0.0.1'
PORT = 8888
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

conn, addr = s.accept()
print('Connected by', addr)

data = conn.recv(4096)
data_variable = pickle.loads(data)
conn.close()
print(data_variable)
print(data_variable.process_id)
data_variable.process_id = 5
print(data_variable.process_id)
# Access the information by doing data_variable.process_id or data_variable.task_id etc..,
print('Data received from client')