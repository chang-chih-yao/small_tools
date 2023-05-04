import time
from tkinter import messagebox, Toplevel, Label, Tk, Button, Canvas, PhotoImage, NW
from os import system
from PIL import Image, ImageTk

'''
作者: CY
自動關機程式
關機時間在 "關機時間設定.txt" 裡面可以設定，第一行代表小時(24小時制)，第二行代表分鐘

run python script:
activate temp (in RTK computer)

build exe:
pyinstaller -F -w auto_shutdown.py
'''


with open('關機時間設定.txt', 'r') as f:
    lines = f.readlines()
shutdown_hour = int(lines[0].split('\n')[0])    # 第一行代表小時(24小時制)
shutdown_minute = int(lines[1].split('\n')[0])  # 第二行代表分鐘
delay_min = 15                                  # 每次延長的時間長度 (單位:分鐘)
wait_time_min = 10                              # 等多久就自動關機 (單位:分鐘)
w = 400                                         # 視窗寬度
h = 500                                         # 視窗長度
shutdown_flag = False                           # shutdown_flag 是 True 時代表使用者已經按下同意關機


def pop_always_on_top(msg):  # This will be on top of any other window, 但本次程式沒用到
    msg_window = Toplevel()
    msg_window.title("延長關機時間")
    msg_window.attributes('-topmost', True)
    msg_label = Label(msg_window, text=msg)
    msg_label.pack(expand=1, fill='both')
    button = Button(msg_window, text="雞到嚕", command=msg_window.destroy)
    button.pack()

def img_to_tk(img_name, resize=None):    # resize = (w, h)
    img = Image.open(img_name)
    if resize != None:
        img_resize = img.resize(resize)
        return ImageTk.PhotoImage(img_resize)
    else:
        return ImageTk.PhotoImage(img)


class Window():
    def __init__(self, mode):
        self.root = Tk()
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.center_x = int(self.screen_width/2 - w / 2)
        self.center_y = int(self.screen_height/2 - h / 2)
        self.root.geometry(f'{w}x{h}+{self.center_x}+{self.center_y}')
        self.root.title('自動關機程式')
        self.root.attributes('-topmost', True)  # 永遠保持在螢幕最上層
        self.root.overrideredirect(True)        # 隱藏視窗的標題列
        self.root.configure(bg = "#FFFFFF")
        self.root.resizable(False, False)
        self.root.iconbitmap('2.ico')
        # self.root.protocol("WM_DELETE_WINDOW", self.Close)

        canvas = Canvas(self.root, bg = "#FFFFFF", height = h, width = w, bd = 0, highlightthickness = 0, relief = "ridge")
        canvas.place(x = 0, y = 0)
        
        if mode == 'begin':
            img_bg = img_to_tk('output_1.png', (w, h))
            my_bg = canvas.create_image(0, 0, anchor=NW, image=img_bg)
    
            label_1 = Label(self.root, text='賢寶寶自動關機程式已啟動\n預計在' + str(shutdown_hour) + ':' + str(shutdown_minute) + '自動關機唷', bg='#aa3333', fg='#ef834e', font=('微軟正黑體 Bold', 18))
            label_1.place(x = 55, y = 10)

            img_btn = img_to_tk('ok_1.png')
            btn_1 = canvas.create_image(150, 90, anchor=NW, image=img_btn, tag = ('btn'))
            canvas.tag_bind('btn','<Button-1>', lambda e: self.Close(event=e))

            self.root.after(180000, lambda: self.Close())                   # 三分鐘後關掉視窗
    
            self.root.mainloop()
        elif mode == 'Q_A':
            img_bg = img_to_tk('output_2.png', (w, h))
            my_bg = canvas.create_image(0, 0, anchor=NW, image=img_bg)
    
            img_btn_ok = img_to_tk('ok.png')
            btn_ok = canvas.create_image(60, 427, anchor=NW, image=img_btn_ok, tag = ('btn_ok'))
            canvas.tag_bind('btn_ok','<Button-1>', lambda e: self.my_select(select=True, event=e))

            img_btn_delay = img_to_tk('delay.png')
            btn_delay = canvas.create_image(220, 430, anchor=NW, image=img_btn_delay, tag = ('btn_delay'))
            canvas.tag_bind('btn_delay','<Button-1>', lambda e: self.my_select(select=False, event=e))

            self.root.after(wait_time_min*60*1000, lambda: self.my_select(select=True))   # 三分鐘後自動結束程式+關機
    
            self.root.mainloop()
  
    def Close(self, event=None):
        time.sleep(0.1)
        self.root.destroy()
    
    def my_select(self, select, event=None):
        global shutdown_flag, shutdown_hour, shutdown_minute
        time.sleep(0.1)
        # if event != None:
        #     print(event)
        if select:   # 準備關機
            print('going to shutdown ...')
            shutdown_flag = True
        else:        # 延長 delay_min 關機時間
            print('delay', delay_min, 'min')
            hour, minute = get_GMT8_time(delay=delay_min)
            shutdown_hour = hour
            shutdown_minute = minute
            shutdown_flag = False
        
        self.root.destroy()

    # def __del__(self):
    #     print('Destructor called, object deleted.')

def get_GMT8_time(delay=0):
    t0 = time.time()
    t1 = t0 + 60*60*8 + 60*delay
    GMT8_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t1))
    hour = int(GMT8_time.split(' ')[1].split(':')[0])
    minute = int(GMT8_time.split(' ')[1].split(':')[1])
    return hour, minute

if __name__ == '__main__':
    win = Window('begin')
    del win

    while(True):
        time.sleep(10)
        # time.sleep(1)
        hour, minute = get_GMT8_time()
        print('now time:', hour, minute, 'wait for time:', shutdown_hour, shutdown_minute)
        if hour == shutdown_hour and minute == shutdown_minute:
        # if True:
            win_ = Window('Q_A')
            del win_
            if shutdown_flag:
                print('shutdown -s -f -t 10')
                system('shutdown -s -f -t 10')
                break
            else:
                win_delay = Window('begin')
                del win_delay

    print('finish')