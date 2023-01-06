import cv2
import numpy as np
import pyautogui
# import tkinter

'''
作者: CY
軟體名稱: 螢幕錄影
使用方式: 輸入output名稱, 輸出檔案為mp4檔, 預設是錄製9999秒, 如果中途想停止, 只需要在console中ctrl-c即可
'''

# display screen resolution, get it using pyautogui itself
SCREEN_SIZE = tuple(pyautogui.size())
# fourcc = cv2.VideoWriter_fourcc(*"XVID")
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
fps = 20.0
record_seconds = 9999
print('total record_seconds: ' + str(record_seconds))
file_name = input('please input file name: ')
# out = cv2.VideoWriter("output.avi", fourcc, fps, (SCREEN_SIZE))
out = cv2.VideoWriter(file_name+".mp4", fourcc, fps, (SCREEN_SIZE))
try:
    for i in range(int(record_seconds * fps)):
        img = pyautogui.screenshot()
        # convert these pixels to a proper numpy array to work with OpenCV
        frame = np.array(img)
        # convert colors from BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)
        # show the frame
        # cv2.imshow("screenshot", frame)
        # # if the user clicks q, it exits
        # if cv2.waitKey(1) == ord("q"):
        #     break
        print(str(int(i/fps)) + ' ', end='\r')

    # cv2.destroyAllWindows()
    out.release()
    print('stop')
except KeyboardInterrupt:
    out.release()
    print('stop by KeyboardInterrupt')