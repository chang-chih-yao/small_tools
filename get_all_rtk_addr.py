import requests
import time
import os
import sys

def get_address_book_data(output_file, user):
    url = f"https://intra.realtek.com/AddressBook/Search?key={user}&cmpy_id=&deptCode=&_=1739430395511"
    
    try:
        response = requests.get(url)  # 發送 GET 請求
        response.raise_for_status()   # 若狀態碼非 200-399，會拋出錯誤
        
        # 將回應內容轉成 JSON（回應是一個陣列）
        datas = response.json()
        
        # 這裡 datas 就是一個 array，您可以直接取用
        # print("取得的資料如下:")
        # print(datas)

        # 如果要查看第一筆裡面的某些欄位可以這樣做
        has_data = False
        result = ''
        if datas:
            for data in datas:
                if data.get('Id') == user:
                    has_data = True
                    # print("Name:", data.get("Name"))
                    # print("UserAccount:", data.get("UserAccount"))
                    # print("Mail:", data.get("Mail"))
                    result = f'{user}, {data.get("Name")}, {data.get("UserAccount")}, {data.get("Mail")}, {data.get("FirstDept")}'
        if has_data == False:
            result = f'{user}, None, None, None, None'
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f'{result}\n')
    except requests.exceptions.RequestException as e:
        print("Error:", e)


if __name__ == "__main__":
    gmtime = time.gmtime(time.time() + 8*60*60)
    now_time_str = time.strftime("%Y%m%d_%H%M%S", gmtime)
    output_file = f'{now_time_str}.txt'
    if os.path.isfile(output_file):
        c = input(f'{output_file} file exist, remove? (y/n)')
        if c in ['y', 'Y']:
            os.remove(output_file)
        else:
            sys.exit()
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'{now_time_str}\n')
    for i in range(1, 9800):
        get_address_book_data(output_file, f'R{i}')
