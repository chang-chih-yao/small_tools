"""
auto_shutdown_webhook.py - AWS Lambda Function
==============================================
部署在 AWS Lambda，搭配 API Gateway 使用。
處理自動關機程式的三個 API 端點，並透過 Telegram Bot 傳送通知給使用者。

API 端點（對應 API Gateway 路由）：
  POST /for_wanchun          → 發送關機通知 / 回報關機結果
  POST /for_wanchun_get_json → 查詢使用者是否已回覆
  POST /for_wanchun_set_json → 清除 DynamoDB 狀態（已讀取，重置）
  POST /telegram_webhook     → 接收 Telegram Bot Webhook（使用者在手機回覆 y/n）

DynamoDB Table: auto_shutdown_state
  pk (String, Partition Key): "shutdown_state"  ← 固定唯一一筆
  is_question (Boolean)     : 是否正在等待使用者回覆
  select (String or null)   : 使用者回覆 "y" 或 "n"，尚未回覆時為 null
  method (String)           : "shutdown"
  shutdown_hour (Number)    : 關機小時
  shutdown_minute (Number)  : 關機分鐘
  timestamp (Number)        : Unix timestamp，建立時間
  ttl (Number)              : Unix timestamp，DynamoDB TTL 自動過期（預設1小時）

全局變數 (Global Variables):
  NOTIFY_BOT_TOKEN    : 用於發送通知的 Telegram Bot Token（從 @BotFather 取得）
  CY_BOT_TOKEN        : CY_BOT 的 Telegram Bot Token（從 @BotFather 取得）
  TELEGRAM_CHAT_ID    : 要傳訊息的 Telegram Chat ID（使用者或群組）
  DYNAMODB_TABLE_NAME : DynamoDB table 名稱（預設 "auto_shutdown_state"）
"""

import json
import os
import sys
import time
import boto3
from boto3.dynamodb.conditions import Key
import requests

# ─── 設定 ─────────────────────────────────────────────────────────────────────

NOTIFY_BOT_TOKEN = os.getenv('NOTIFY_BOT_TOKEN')
if NOTIFY_BOT_TOKEN is None:
    print("Warning: NOTIFY_BOT_TOKEN is not set in environment variables.")
    sys.exit(1)
CY_BOT_TOKEN = os.getenv('CY_BOT_TOKEN')
if CY_BOT_TOKEN is None:
    print("Warning: CY_BOT_TOKEN is not set in environment variables.")
    sys.exit(1)

# TELEGRAM_CHAT_ID    = 5892597105  # 淳的 Telegram Chat ID
TELEGRAM_CHAT_ID    = 1394612480  # cychang1994 的 Telegram Chat ID
DYNAMODB_TABLE_NAME = 'auto_shutdown_state'
PK_NAME             = 'shutdown_state'       # 固定 primary key，只存一筆狀態

# ─── DynamoDB ─────────────────────────────────────────────────────────────────

dynamodb = boto3.resource('dynamodb')
table    = dynamodb.Table(DYNAMODB_TABLE_NAME)

# ─── Telegram Bot 工具函式 ───────────────────────────────────────────────────

def send_telegram_message(chat_id: int, message: str) -> bool:
    """
    透過 Telegram Bot sendMessage API 傳送文字訊息給指定 chat_id。
    回傳 True 表示成功，False 表示失敗。
    API 文件：https://core.telegram.org/bots/api#sendmessage
    """
    body_dict={'chat_id': chat_id, 'text': message}
    try:
        response = requests.post(f'https://api.telegram.org/bot{CY_BOT_TOKEN}/sendMessage', json=body_dict, timeout=10)
        response.raise_for_status()  # 檢查請求是否成功，如果不成功會引發 HTTPError
        # self.logger.info(f'{response.json()}')
    except Exception as e:
        print(f'Error sending message to Telegram: {e}')
        return False
    return True

# ─── 路由處理函式 ─────────────────────────────────────────────────────────────

def handle_for_wanchun(body: dict) -> dict:
    """
    POST /for_wanchun
    
    method='shutdown':
        - 在 DynamoDB 寫入等待狀態（is_question=True, select=null）
        - 透過 Telegram Bot 傳問題訊息給使用者
        - body 範例:
            {"method": "shutdown", "shutdown": {"shutdown_hour": 19, "shutdown_minute": 30}}

    method='cancel':
        - 透過 Telegram Bot 傳關機結果通知給使用者
        - body 範例:
            {"method": "cancel", "cancel": {"method": "shutdown", "flag": "y"|"n"|"timeout"}}
    """
    method = body.get('method', '')

    if method == 'shutdown':
        shutdown_info   = body.get('shutdown', {})
        shutdown_hour   = shutdown_info.get('shutdown_hour', 0)
        shutdown_minute = shutdown_info.get('shutdown_minute', 0)
        delay_min       = shutdown_info.get('delay_min', 20)
        wait_time_min   = shutdown_info.get('wait_time_min', 10)
        ttl             = int(time.time()) + 43200  # 12 小時後 DynamoDB 自動刪除

        # 寫入 DynamoDB：標記正在等待使用者回覆
        table.put_item(Item={
            'shutdown_state':  PK_NAME,
            'is_question':     True,
            'select':          None,
            'method':          'shutdown',
            'shutdown_hour':   shutdown_hour,
            'shutdown_minute': shutdown_minute,
            'timestamp':       int(time.time()),
            'ttl':             ttl,
        })
        print(f'[DDB] put item: waiting for user reply, shutdown at {shutdown_hour:02d}:{shutdown_minute:02d}')

        # 傳 Telegram 訊息問使用者
        msg = (
            f'賢寶寶的電腦準備關機嚕！\n'
            f'請於 {wait_time_min} 分鐘內回覆 (逾時則自動關機)：\n'
            f'  y → 立刻關機\n'
            f'  n → 延長 {delay_min} 分鐘'
        )
        send_telegram_message(TELEGRAM_CHAT_ID, msg)
        return ok_response({'status': 'ok', 'action': 'shutdown_question_sent'})

    elif method == 'cancel':
        cancel_info   = body.get('cancel', {})
        cancel_method = cancel_info.get('method', '')
        flag          = cancel_info.get('flag', '')
        delay_min     = cancel_info.get('delay_min', 20)

        print(f'[cancel] method={cancel_method} flag={flag} delay_min={delay_min}')

        messages = {
            ('shutdown', 'y'):       f'✅ 確認關機，電腦將在 1 分鐘內自動關機',
            ('shutdown', 'n'):       f'⏰ 已延長關機時間 {delay_min} 分鐘',
            ('shutdown', 'timeout'): f'⚠️ 等待逾時，電腦已自動關機',
        }
        msg = messages.get((cancel_method, flag))
        if msg:
            send_telegram_message(TELEGRAM_CHAT_ID, msg)
            return ok_response({'status': 'ok', 'action': 'cancel_notified', 'flag': flag})
        else:
            return error_response(400, f'unknown cancel method={cancel_method} flag={flag}')

    else:
        return error_response(400, f'unknown method: {method}')


def handle_for_wanchun_get_json(body: dict) -> dict:
    """
    POST /for_wanchun_get_json
    
    從 DynamoDB 讀取目前狀態。
    auto_shutdown.py 每5秒輪詢這個端點，檢查使用者是否在手機上回覆了。
    
    回傳範例：
        {"is_question": true,  "select": null}   ← 還在等待
        {"is_question": false, "select": "y"}    ← 使用者同意關機
        {"is_question": false, "select": "n"}    ← 使用者要延後
        {}                                       ← DynamoDB 無資料（異常）
    """
    try:
        response = table.get_item(Key={'shutdown_state': PK_NAME})
        item     = response.get('Item')
        if not item:
            print('[DDB] no item found')
            return ok_response({})  # 回傳空 dict，client 端認定為 recv error

        result = {
            'is_question': item.get('is_question', False),
            'select':      item.get('select'),   # None → JSON null
        }
        print(f'[DDB] get item: {result}')
        return ok_response(result)

    except Exception as e:
        print(f'[DDB] get error: {e}')
        return error_response(500, str(e))


def handle_for_wanchun_set_json(body: dict) -> dict:
    """
    POST /for_wanchun_set_json
    
    auto_shutdown.py 讀取到使用者回覆後呼叫此端點，清除 DynamoDB 狀態。
    避免下一次關機時讀到上一次的殘留資料。
    """
    try:
        table.delete_item(Key={'shutdown_state': PK_NAME})
        print('[DDB] state cleared')
        return ok_response({'status': 'cleared'})
    except Exception as e:
        print(f'[DDB] delete error: {e}')
        return error_response(500, str(e))


def handle_telegram_webhook(event_body: dict) -> dict:
    """
    POST /telegram_webhook

    接收 Telegram Bot 的 Webhook 更新（Update）。
    使用者在 Telegram 回覆 "y" 或 "n" 時，更新 DynamoDB 的 select 欄位。

    需在 Telegram 設定 Webhook URL：
        https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://<API_GATEWAY_URL>/telegram_webhook

    Telegram Update 格式參考：
        {
          "update_id": 123456789,
          "message": {
            "chat": {"id": 987654321},
            "from": {"id": 987654321, "first_name": "User"},
            "text": "y"
          }
        }
    """
    message = event_body.get('message', {})
    if not message:
        # 其他 Update 類型（edited_message、callback_query 等），忽略
        return ok_response({'status': 'ok'})

    text    = message.get('text', '').strip().lower()
    chat_id = message.get('chat', {}).get('id', 0)   # int
    print(f'[Telegram webhook] chat_id={chat_id} text={text!r}')

    if text in ('y', 'yes', 'n', 'no'):
        try:
            # 先確認 DynamoDB 裡有正在等待的問題
            response = table.get_item(Key={'shutdown_state': PK_NAME})
            item     = response.get('Item')
            if item and item.get('is_question') == True:
                table.update_item(
                    Key={'shutdown_state': PK_NAME},
                    UpdateExpression='SET #sel = :sel, is_question = :q',
                    ExpressionAttributeNames={'#sel': 'select'},
                    ExpressionAttributeValues={':sel': text, ':q': False},
                )
                print(f'[DDB] user replied: {text}')
            else:
                print('[DDB] no active question, ignoring reply')
        except Exception as e:
            print(f'[DDB] update error: {e}')

    return ok_response({'status': 'ok'})

# ─── 工具函式 ─────────────────────────────────────────────────────────────────

def ok_response(body: dict) -> dict:
    return {
        'statusCode': 200,
        'headers':    {'Content-Type': 'application/json'},
        'body':       json.dumps(body),
    }

def error_response(code: int, message: str) -> dict:
    return {
        'statusCode': code,
        'headers':    {'Content-Type': 'application/json'},
        'body':       json.dumps({'error': message}),
    }

def parse_body(event: dict) -> dict:
    """
    解析 Lambda event 的 body。
    
    注意：舊版 auto_shutdown.py 有雙重 JSON 序列化的 bug：
      json_string = json.dumps(my_dict)           # dict → str
      post(url, json=json_string)                  # requests 再 json.dumps 一次
    所以 Lambda 收到的 body 是 "\"{\\"method\\": ...}\"" 這種格式。
    這裡會自動處理這個情況，double decode 直到得到 dict 為止。
    
    新版 auto_shutdown.py 已修正此 bug，直接 post(url, json=my_dict)。
    """
    import base64
    raw = event.get('body', '{}') or '{}'
    if event.get('isBase64Encoded', False):
        raw = base64.b64decode(raw).decode('utf-8')

    # 最多額外解析一次，相容舊版 double-serialization bug
    parsed = json.loads(raw)
    if isinstance(parsed, str):
        parsed = json.loads(parsed)

    return parsed if isinstance(parsed, dict) else {}

# ─── Lambda 進入點 ────────────────────────────────────────────────────────────

def lambda_handler(event: dict, context) -> dict:
    """
    AWS Lambda 進入點，透過 Lambda Function URL 接收 HTTP 請求。
    僅支援 Lambda Function URL 格式（與 API Gateway HTTP API v2 相同）。
    """
    # print(f'[event] {json.dumps(event)}')

    # 取得 path 和 HTTP method（Lambda Function URL 格式）
    path        = event.get('rawPath', '')
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')

    if http_method != 'POST':
        return error_response(405, 'Method Not Allowed')

    body = parse_body(event)

    route_map = {
        '/for_wanchun':          handle_for_wanchun,
        '/for_wanchun_get_json': handle_for_wanchun_get_json,
        '/for_wanchun_set_json': handle_for_wanchun_set_json,
        '/telegram_webhook':     handle_telegram_webhook,
    }

    handler = route_map.get(path)
    if handler is None:
        return error_response(404, f'path not found: {path}')

    return handler(body)
