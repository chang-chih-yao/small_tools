from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import requests
import json

class DICT_DATA:
    def init(self) -> None:
        self.reset()

    def reset(self):
        self.target = {'user_id':1394612480, 'job_time':'', 'method':''}
        self.shutdown = {'shutdown_hour':19, 'shutdown_minute':35, 'delay_min':20, 'wait_time':10}
        self.schedule = [{'title':'吃藥', '':''}, {'title':'帶東西回家', '':''}]
        self.restaurant = ''
        self.cancel = ''

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

    def cancel_dict(self, name):
        self.reset()
        self.target['method'] = 'cancel'
        if name == 'shutdown' or name == 'schedule' or name == 'restaurant':
            self.target['cancel'] = name
        else:
            return None
        print(self.target)
        return self.target

    

dict_data = DICT_DATA()

my_dict = dict_data.shutdown_dict()
# my_dict = dict_data.cancel_dict('shutdown')
json_string = json.dumps(my_dict)
# print(json_string)

result = requests.post('https://www.cyvisionbot.com/for_wanchun', json=json_string)
print(result)
print(result.text)