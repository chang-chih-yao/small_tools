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
# Create a socket connection.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

# Create an instance of ProcessData() to send to server.
variable = ProcessData()
variable.process_id = 3
print(variable)
# Pickle the object and send it to the server
data_string = pickle.dumps(variable)
s.send(data_string)

s.close()
print('Data Sent to Server')