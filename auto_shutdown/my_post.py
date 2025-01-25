import time
import requests
import json

get_data_dict = {'get_data':'shutdown'}
set_data_dict = {'set_data':'shutdown'}

get_data_json_str = json.dumps(get_data_dict)
set_data_json_str = json.dumps(set_data_dict)

while True:
    result = requests.post('https://www.cyvisionbot.com/for_wanchun_get_json', json=get_data_json_str)
    print(f'get result : {result}')
    print(f'get result.text : {result.text}')
    my_dict = json.loads(result.text)
    # print(my_dict)
    if len(my_dict) == 0:
        print('recv error')
        break
    else:
        print(f'now is_question : {my_dict["is_question"]}')
        if my_dict['is_question'] == False and my_dict['select'] != None:
            result = requests.post('https://www.cyvisionbot.com/for_wanchun_set_json', json=set_data_json_str)
            print(f'set result : {result}')
            print(f'set result.text : {result.text}')
            print(f'recv user select : {my_dict["select"]}')
        # break
        time.sleep(1)