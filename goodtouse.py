from PIL import ImageGrab, ImageTk
from tkinter import Tk, Button, Label, Canvas
from tkinter import filedialog
import win32clipboard as clip
import win32con
from io import BytesIO
from os import startfile
from screeninfo import get_monitors
from keyboard import add_hotkey

def screen_button_1(event):
    global screen_x, screen_y ,screen_xstart,screen_ystart
    global screen_rec
    canvas.place_forget()
    screen_x, screen_y = event.x, event.y
    screen_xstart,screen_ystart = event.x, event.y
    #print("event.x, event.y = ", event.x, event.y)
    screen_xstart,screen_ystart = event.x, event.y 
    screen_cv.configure(height=1)
    screen_cv.configure(width=1)
    screen_cv.config(highlightthickness=0) # 無邊框
    screen_cv.place(x=event.x, y=event.y)
    screen_rec = screen_cv.create_rectangle(0,0,0,0)

def screen_b1_Motion(event):
    global screen_x, screen_y, screen_xstart, screen_ystart
    screen_x, screen_y = event.x, event.y
    #print("event.x, event.y = ", event.x, event.y)
    screen_cv.configure(height = event.y - screen_ystart)
    screen_cv.configure(width = event.x - screen_xstart)
    screen_cv.coords(screen_rec,0,0,event.x-screen_xstart,event.y-screen_ystart)

def screen_buttonRelease_1(event):
    global screen_xend, screen_yend, img, img_c
    screen_xend, screen_yend = event.x, event.y
    if screen_xend > screen_xstart and screen_yend > screen_ystart:
        screen_cv.delete(screen_rec)
        screen_cv.place_forget()
        screen_root.attributes("-alpha", 0)
        img_c = img.crop((screen_xstart, screen_ystart, screen_xend, screen_yend))
        #img_c.save('screenshot.png')
        #print('screenshot.png save completely')
        output = BytesIO()
        img_c.convert('RGB').save(output, 'BMP')
        data = output.getvalue()[14:]
        output.close()
        clip.OpenClipboard()
        clip.EmptyClipboard()
        clip.SetClipboardData(win32con.CF_DIB, data)
        clip.CloseClipboard()
        screen_root.destroy()

def mouse_motion(event):
    global screen_x, screen_y ,screen_xstart, screen_ystart, my_text
    canvas.place(x = event.x_root-x_offset+10, y = event.y_root+10)
    s = str(event.x) + ', ' + str(event.y) + ', ESC to exit'
    canvas.itemconfig(my_text, text=s)
    #print(event.x_root, event.y_root, event.x, event.y)

def screen_sys_out(event):
    global end_program
    end_program = 1
    screen_root.destroy()


def browse_button():
    global img_c
    filename = filedialog.asksaveasfilename(parent=root, initialdir='~/', filetypes = (("png files","*.png"),("all files","*.*")))
    if not filename:
        print('no choosen file')
    else:
        print(filename)
        img_c.save(filename + '.png')
    
def repeat():
    global repeat_flag
    repeat_flag = 1
    root.destroy()


repeat_flag = 0
end_program = 0

img = ImageGrab.grab(all_screens=True)
#print(img.size)
x_offset = 999999
for m in get_monitors():
    #print(str(m))
    if x_offset > m.x:
        x_offset = m.x
#print(x_offset)
img_c = ''

add_hotkey('ctrl+n', repeat)

screen_root = Tk()
screen_root.overrideredirect(True)  # 隱藏視窗的標題列
screen_root.attributes("-alpha", 0.3) # 視窗透明度30%
screen_root.geometry("{0}x{1}+{2}+0".format(img.size[0], img.size[1], x_offset))
screen_root.configure(bg="black")

# 再建立1個Canvas用於圈選
screen_cv = Canvas(screen_root)
screen_cv.config(highlightthickness=0) # 無邊框
screen_x, screen_y = 0, 0
screen_xstart,screen_ystart = 0 ,0
screen_xend,screen_yend = 0, 0
screen_rec = ''

canvas = Canvas(screen_root)
canvas.configure(width=180)
canvas.configure(height=25)
canvas.configure(bg="yellow")
canvas.configure(highlightthickness=0)  # 高亮厚度
canvas.place(x=(screen_root.winfo_screenwidth()-500),y=(screen_root.winfo_screenheight()-300))
my_text = canvas.create_text(80, 10,font='Arial -14 bold',text='ESC to exit')

screen_root.bind("<Motion>", mouse_motion)
screen_root.bind('<Escape>',screen_sys_out) # 鍵盤Esc鍵->退出
screen_root.bind("<Button-1>", screen_button_1) # 滑鼠左鍵點選->顯示子視窗 
screen_root.bind("<B1-Motion>", screen_b1_Motion)# 滑鼠左鍵移動->改變子視窗大小
screen_root.bind("<ButtonRelease-1>", screen_buttonRelease_1) # 滑鼠左鍵釋放->記錄最後遊標的位置
screen_root.mainloop()


if end_program == 0:
    root = Tk()
    root.title('goodtouse')
    if img_c.size[0] < 220:
        root.geometry('{0}x{1}'.format(250, img_c.size[1]+50))
    else:
        root.geometry('{0}x{1}'.format(img_c.size[0]+20, img_c.size[1]+50))

    button1 = Button(text="Save img", command=browse_button).place(x=10, y=10)
    button2 = Button(text="Screen again (ctrl + n)", command=repeat).place(x=80, y=10)
    tk_img = ImageTk.PhotoImage(img_c)
    Label(root, image=tk_img).place(x=10, y=40)

    root.mainloop()

    if repeat_flag == 1:
        startfile('goodtouse.exe')