import pydirectinput
import time

def move_to(x, y):
    pydirectinput.moveTo(x, y)

if __name__ == '__main__':
    x = 100
    while True:
        move_to(x, 500)
        x += 10
        if x >= 500:
            x = 100
        time.sleep(5)