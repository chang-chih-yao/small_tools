import cv2
import numpy as np
# import pyautogui
import mss
import time
import os
import sys
# import tkinter

'''
作者: CY
軟體名稱: 螢幕錄影
使用方式: 輸入output名稱, 輸出檔案為mp4檔, 預設是錄製9999秒, 如果中途想停止, 只需要在console中ctrl-c即可
'''

# display screen resolution, get it using pyautogui itself
# SCREEN_SIZE = tuple(pyautogui.size())
SCREEN_SIZE = (1920, 1080)
monitor = {"top": 0, "left": 0, "width": SCREEN_SIZE[0], "height": SCREEN_SIZE[1]}
cap = mss.mss()

# fourcc = cv2.VideoWriter_fourcc(*"XVID")
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
fps = 30.0
record_seconds = 9999
print(f'Max record seconds: {record_seconds}, ctrl-c to stop')
file_name = input('please input file name(dont inlucde .mp4): ')
full_file_name = f'{file_name}.mp4'
if os.path.isfile(full_file_name):
    print(f'Error, file "{full_file_name}" exist!!!')
    sys.exit()
# out = cv2.VideoWriter("output.avi", fourcc, fps, (SCREEN_SIZE))
out = cv2.VideoWriter(full_file_name, fourcc, fps, (SCREEN_SIZE))
try:
    for i in range(int(record_seconds * fps)):
        start = time.perf_counter()
        img = cap.grab(monitor)
        # img = pyautogui.screenshot()
        
        # convert these pixels to a proper numpy array to work with OpenCV
        frame = np.array(img)
        
        # convert colors from BGR to RGB
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        out.write(frame)
        # print(1/(time.perf_counter() - start))
        
        # cv2.imshow("screenshot", frame)
        # # if the user clicks q, it exits
        # if cv2.waitKey(1) == ord("q"):
        #     break
        # print(str(int(i/fps)) + ' ', end='\r')
        if i % 5 == 0:
            cost_time = 1/(time.perf_counter() - start)
            print(f'sec: {int(i/fps)}, fps: {cost_time:.2f}', end='\r')

    # cv2.destroyAllWindows()
    out.release()
    print('stop')
except KeyboardInterrupt:
    out.release()
    print('stop by KeyboardInterrupt')