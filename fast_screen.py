import time
import cv2
import numpy

import mss

cap = mss.mss()
monitor = {"top": 0, "left": 0, "width": 1280, "height": 720}

while True:
    last_time = time.perf_counter()

    # Get raw pixels from the screen, save it to a Numpy array
    img = numpy.array(cap.grab(monitor))
    pose_img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

    # Display the picture
    #cv2.imshow("OpenCV/Numpy normal", img)

    # Display the picture in grayscale
    # cv2.imshow('OpenCV/Numpy grayscale', cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY))

    print(f"fps: {1 / (time.perf_counter() - last_time)}")

    # Press "q" to quit
    # if cv2.waitKey(1) & 0xFF == ord("q"):
        # cv2.destroyAllWindows()
        # break