import time
from tkinter import messagebox, Toplevel, Label, Tk, Button, Canvas, PhotoImage, NW
from os import system
from PIL import Image, ImageTk
from threading import Thread
# import requests
from requests import post
import json

'''
作者: CY
自動關機程式
關機時間在 "關機時間設定.txt" 裡面可以設定，第一行代表小時(24小時制)，第二行代表分鐘

run python script:
activate temp (in RTK computer)

build exe:
pyinstaller -F -w auto_shutdown.py
'''

# 我: 1394612480
# 淳: 5892597105

class DICT_DATA:
    def init(self) -> None:
        self.reset()

    def reset(self):
        self.target = {'user_id':5892597105, 'job_time':'', 'method':''}
        self.shutdown = {'shutdown_hour':19, 'shutdown_minute':35, 'delay_min':20, 'wait_time':10}
        self.schedule = [{'title':'吃藥', '':''}, {'title':'帶東西回家', '':''}]
        self.restaurant = ''
        self.cancel = {'method':'', 'flag':''}

    def shutdown_dict(self):
        self.reset()
        self.target['method'] = 'shutdown'
        self.target['shutdown'] = self.shutdown
        print(self.target)
        return self.target

    def schedule_dict(self):
        self.reset()
        self.target['method'] = 'schedule'
        self.target['schedule'] = self.schedule
        print(self.target)
        return self.target

    def restaurant_dict(self):
        self.reset()
        self.target['method'] = 'restaurant'
        self.target['restaurant'] = self.restaurant
        print(self.target)
        return self.target

    def cancel_dict(self, name, flag=''):
        self.reset()
        self.target['method'] = 'cancel'
        if name == 'shutdown' or name == 'shutdown_timeout' or name == 'schedule' or name == 'restaurant':
            self.target['cancel'] = self.cancel
            self.target['cancel']['method'] = name
            self.target['cancel']['flag'] = flag
        else:
            return None
        print(self.target)
        return self.target
    
    def shutdown_post(self):
        my_dict = self.shutdown_dict()
        json_string = json.dumps(my_dict)
        result = post('https://www.cyvisionbot.com/for_wanchun', json=json_string)
        print(result)
        # print(result.text)

    def cancel_shutdown_question_y(self):
        my_dict = self.cancel_dict('shutdown', 'y')
        json_string = json.dumps(my_dict)
        result = post('https://www.cyvisionbot.com/for_wanchun', json=json_string)
        print(result)
        # print(result.text)
        
    def cancel_shutdown_question_n(self):
        my_dict = self.cancel_dict('shutdown', 'n')
        json_string = json.dumps(my_dict)
        result = post('https://www.cyvisionbot.com/for_wanchun', json=json_string)
        print(result)
        # print(result.text)
        
    def cancel_shutdown_question_timeout(self):
        my_dict = self.cancel_dict('shutdown', 'timeout')
        json_string = json.dumps(my_dict)
        result = post('https://www.cyvisionbot.com/for_wanchun', json=json_string)
        print(result)
        # print(result.text)

with open('關機時間設定.txt', 'r') as f:
    lines = f.readlines()
shutdown_hour = int(lines[0].split('\n')[0])    # 第一行代表小時(24小時制)
shutdown_minute = int(lines[1].split('\n')[0])  # 第二行代表分鐘
delay_min = 20                                  # 每次延長的時間長度 (單位:分鐘)
wait_time_min = 10                              # 等多久就自動關機 (單位:分鐘)
w = 400                                         # 視窗寬度
h = 500                                         # 視窗長度
shutdown_flag = False                           # shutdown_flag 是 True 時代表使用者已經按下同意關機
active_by_gui = True
time_out_flag = False


def pop_always_on_top(msg):  # This will be on top of any other window, 但本次程式沒用到
    msg_window = Toplevel()
    msg_window.title("延長關機時間")
    msg_window.attributes('-topmost', True)
    msg_label = Label(msg_window, text=msg)
    msg_label.pack(expand=1, fill='both')
    button = Button(msg_window, text="雞到嚕", command=msg_window.destroy)
    button.pack()
    

class Window():
    def __init__(self, mode):
        self.mode = mode
        self.now_time = time.time()
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
        
        self.t = None
        
        if self.mode == 'begin':
            self.img_bg = self.img_to_tk('output_1.png', (w, h))
            my_bg = canvas.create_image(0, 0, anchor=NW, image=self.img_bg)
    
            label_1 = Label(self.root, text='賢寶寶自動關機程式已啟動\n預計在' + str(shutdown_hour) + ':' + str(shutdown_minute) + '自動關機唷', bg='#aa3333', fg='#ef834e', font=('微軟正黑體 Bold', 18))
            label_1.place(x = 55, y = 10)

            self.img_btn = self.img_to_tk('ok_1.png')
            btn_1 = canvas.create_image(150, 90, anchor=NW, image=self.img_btn, tag = ('btn'))
            canvas.tag_bind('btn','<Button-1>', lambda e: self.Close(event=e))

            self.root.after(180000, lambda: self.Close())                   # 3分鐘後關掉視窗
    
        elif self.mode == 'Q_A':
            self.img_bg = self.img_to_tk('output_2.png', (w, h))
            my_bg = canvas.create_image(0, 0, anchor=NW, image=self.img_bg)
    
            self.img_btn_ok = self.img_to_tk('ok.png')
            btn_ok = canvas.create_image(60, 427, anchor=NW, image=self.img_btn_ok, tag = ('btn_ok'))
            canvas.tag_bind('btn_ok','<Button-1>', lambda e: self.my_select(select=True, event=e))

            self.img_btn_delay = self.img_to_tk('delay.png')
            btn_delay = canvas.create_image(220, 430, anchor=NW, image=self.img_btn_delay, tag = ('btn_delay'))
            canvas.tag_bind('btn_delay','<Button-1>', lambda e: self.my_select(select=False, event=e))

            # self.root.after(wait_time_min*60*1000, lambda: self.my_select(select=True))   # wait_time_min 分鐘後自動結束程式+關機
            self.root.after(5000, self.check_json_data)
    
    def app_start(self):
        # self.t = Thread(target=self.check_json_data, daemon=True)
        # self.t.start()
        self.root.mainloop()
        
    def img_to_tk(self, img_name, resize=None):    # resize = (w, h)
        img = Image.open(img_name)
        if resize != None:
            img_resize = img.resize(resize)
            return ImageTk.PhotoImage(img_resize)
            # return img_resize
        else:
            return ImageTk.PhotoImage(img)
            # return img
            
    def check_json_data(self):
        global shutdown_flag, shutdown_hour, shutdown_minute, active_by_gui, time_out_flag
        if time.time() - self.now_time >= wait_time_min*60:
            print('going to shutdown ...')
            shutdown_flag = True
            active_by_gui = True
            time_out_flag = True
            self.root.destroy()
        else:
            get_data_dict = {'get_data':'shutdown'}
            set_data_dict = {'set_data':'shutdown'}

            get_data_json_str = json.dumps(get_data_dict)
            set_data_json_str = json.dumps(set_data_dict)
            
            result = post('https://www.cyvisionbot.com/for_wanchun_get_json', json=get_data_json_str)
            # print(f'get result : {result}')
            # print(f'get result.text : {result.text}')
            my_dict = json.loads(result.text)
            # print(my_dict)
            if len(my_dict) == 0:
                print('recv error')
                self.root.after(5000, self.check_json_data)
            else:
                print(f'now is_question : {my_dict["is_question"]}')
                if my_dict['is_question'] == False and my_dict['select'] != None:
                    result = post('https://www.cyvisionbot.com/for_wanchun_set_json', json=set_data_json_str)
                    print(f'set result : {result}')
                    print(f'set result.text : {result.text}')
                    print(f'recv user select : {my_dict["select"]}')
                    active_by_gui = False
                    time_out_flag = False
                    if my_dict["select"] == 'y':
                        print('going to shutdown ...')
                        shutdown_flag = True
                    else:
                        print('delay', delay_min, 'min')
                        hour, minute = get_GMT8_time(delay=delay_min)
                        shutdown_hour = hour
                        shutdown_minute = minute
                        shutdown_flag = False
                        
                    print('end of thread')
                    self.root.destroy()
                else:
                    self.root.after(5000, self.check_json_data)
            
            
            
            
  
    def Close(self, event=None):
        time.sleep(0.1)
        self.root.destroy()
    
    def my_select(self, select, event=None):
        global shutdown_flag, shutdown_hour, shutdown_minute, active_by_gui, time_out_flag
        active_by_gui = True
        time_out_flag = False
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
        
    def destroy_all_components(self):
        if self.t != None:
            while(True):
                if self.t.is_alive():
                    print('wait timeout thread')
                    time.sleep(0.2)
                else:
                    break

        print('going to destroy')
        self.root.destroy()
        print('destroy complete')
        return active_by_gui

    def __del__(self):
        print('Destructor called, object deleted.')


def get_GMT8_time(delay=0):
    t0 = time.time()
    t1 = t0 + 60*60*8 + 60*delay
    GMT8_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t1))
    hour = int(GMT8_time.split(' ')[1].split(':')[0])
    minute = int(GMT8_time.split(' ')[1].split(':')[1])
    return hour, minute

if __name__ == '__main__':
    dict_data = DICT_DATA()
    win = Window('begin')
    win.app_start()
    time.sleep(0.2)
    del win

    while(True):
        # time.sleep(1)
        hour, minute = get_GMT8_time()
        print('now time:', hour, minute, 'wait for time:', shutdown_hour, shutdown_minute)
        if hour == shutdown_hour and minute == shutdown_minute:
        # if True:
            dict_data.shutdown_post()
            
            win_ = Window('Q_A')
            win_.app_start()
            print('out of win_')
            time.sleep(0.2)
            del win_
            
            if shutdown_flag:
                print(f'active_by_gui:{active_by_gui}')
                if active_by_gui:
                    if time_out_flag:
                        dict_data.cancel_shutdown_question_timeout()
                    else:
                        dict_data.cancel_shutdown_question_y()
                print('shutdown -s -f -t 10')
                system('shutdown -s -f -t 10')
                break
            else:
                print(f'active_by_gui:{active_by_gui}')
                if active_by_gui:
                    dict_data.cancel_shutdown_question_n()
                win_delay = Window('begin')
                win_delay.app_start()
                time.sleep(0.2)
                del win_delay
        
        time.sleep(10)

    print('finish')