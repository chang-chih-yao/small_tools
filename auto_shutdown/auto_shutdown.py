"""
auto_shutdown.py (重構版)
========================
作者: CY
自動關機程式 - 時間到會跳出視窗詢問是否關機，同時傳訊息到 Telegram Bot 讓使用者用手機回覆。

關機時間設定：
  "關機時間設定.txt" 第一行為小時(24小時制)，第二行為分鐘

重構重點：
  1. 所有常數集中在頂部 CONFIG
  2. 用 ShutdownState dataclass 取代四個 global 變數
  3. WebhookClient 負責所有 HTTP 請求，Window class 只做 UI
  4. 修正雙重 JSON 序列化 bug（requests post 時直接傳 dict，不要先 json.dumps）
  5. 修正 get_local_time()：直接讀本機時間，不再手動加 8 小時
  6. 移除未使用的 dead code

執行方式:
  python auto_shutdown.py

打包 exe:
  pyinstaller -F -w auto_shutdown.py
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from os import system
from tkinter import Canvas, Label, Button, Tk, NW
from typing import Optional

from PIL import Image, ImageTk
from requests import get, post, RequestException

# ─── AWS Lambda API Gateway URL ───────────────────────────────────────────────
# 替換成你的 API Gateway URL（部署 auto_shutdown_webhook.py 之後取得）
BASE_URL = 'https://oyimnnjlggbog2otueyc3nn5eq0nukdo.lambda-url.ap-northeast-1.on.aws'

URL_NOTIFY   = f'{BASE_URL}/for_wanchun'           # 發送關機通知 / 回報結果
URL_GET_JSON = f'{BASE_URL}/for_wanchun_get_json'  # 查詢使用者是否回覆
URL_SET_JSON = f'{BASE_URL}/for_wanchun_set_json'  # 清除 DynamoDB 狀態

taiwan_tz = timezone(timedelta(hours=8))

# ─── 設定 ─────────────────────────────────────────────────────────────────────

@dataclass
class Config:
    """從設定檔讀取的關機時間設定，以及程式行為參數。"""
    shutdown_hour:    int   # 關機小時（24小時制）
    shutdown_minute:  int   # 關機分鐘
    delay_min:        int   = 20   # 每次延長的時間長度（分鐘）
    wait_time_min:    int   = 10   # Q_A 視窗等多久自動關機（分鐘）
    win_width:        int   = 400  # 視窗寬度
    win_height:       int   = 500  # 視窗高度
    # telegram_chat_id: int   = 5892597105      # Telegram Bot 的 chat_id（用來發訊息給使用者），但現在不需要了，因為直接在 webhook 內部處理了
    poll_interval_ms: int   = 5000  # 輪詢間隔（毫秒）

    @classmethod
    def from_file(cls, path: str = '關機時間設定.txt') -> 'Config':
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return cls(
            shutdown_hour   = int(lines[0].strip()),
            shutdown_minute = int(lines[1].strip()),
        )


# ─── 狀態物件（取代全域變數）─────────────────────────────────────────────────

@dataclass
class ShutdownState:
    """
    記錄關機流程的狀態，在主迴圈與 Window class 之間共享。
    取代原本散落的四個 global 變數：
      shutdown_flag, active_by_gui, time_out_flag, shutdown_hour/minute
    """
    shutdown_hour:   int
    shutdown_minute: int
    do_shutdown:     bool = False   # True = 確定要關機
    triggered_by:    str  = ''      # 'gui' | 'phone' | 'timeout'


# ─── Webhook / API 客戶端 ─────────────────────────────────────────────────────

class WebhookClient:
    """
    封裝所有對 AWS Lambda 的 HTTP 請求。
    Window class 不應直接呼叫 requests，由這個 class 負責。
    """

    def notify_shutdown(self, state: ShutdownState, delay_min: int, wait_time_min: int) -> None:
        """告知 Lambda 關機時間到了，Lambda 會傳 Telegram 訊息問使用者。"""
        payload = {
            'method': 'shutdown',
            'shutdown': {
                'shutdown_hour':   state.shutdown_hour,
                'shutdown_minute': state.shutdown_minute,
                'delay_min':       delay_min,
                'wait_time_min':   wait_time_min,
            },
        }
        self._post(URL_NOTIFY, payload, label='notify_shutdown')

    def notify_cancel(self, flag: str, delay_min: int) -> None:
        """
        告知 Lambda 最終結果，Lambda 會傳結果通知給使用者。
        flag: 'y'       → 確定關機（使用者自己按）
              'n'       → 延後（使用者自己按）
              'timeout' → 等待逾時，自動關機
        """
        payload = {
            'method': 'cancel',
            'cancel': {'method': 'shutdown', 'flag': flag, 'delay_min': delay_min},
        }
        self._post(URL_NOTIFY, payload, label=f'notify_cancel({flag})')

    def get_user_reply(self) -> Optional[dict]:
        """
        查詢使用者是否在手機 LINE 上回覆了。
        回傳 dict，例如：
          {'is_question': True,  'select': None}  ← 還在等
          {'is_question': False, 'select': 'y'}   ← 使用者確認關機
          {'is_question': False, 'select': 'n'}   ← 使用者要延後
        若請求失敗或回傳空 dict 則回傳 None。
        """
        try:
            resp = post(URL_GET_JSON, json={'get_data': 'shutdown'}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return None
            return data
        except Exception as e:
            print(f'[API] get_user_reply error: {e}')
            return None

    def clear_state(self) -> None:
        """清除 DynamoDB 的狀態，避免下次關機時讀到殘留資料。"""
        self._post(URL_SET_JSON, {'set_data': 'shutdown'}, label='clear_state')

    def _post(self, url: str, payload: dict, label: str = '') -> None:
        """統一的 POST 方法，直接傳 dict（requests 會自動序列化一次）。"""
        try:
            resp = post(url, json=payload, timeout=10)
            print(f'[API] {label} → {resp.status_code}')
            resp.raise_for_status()
        except Exception as e:
            print(f'[API] {label} error: {e}')


# ─── UI 視窗 ──────────────────────────────────────────────────────────────────

class Window:
    """
    Tkinter 視窗，有兩種模式：
      'begin' → 啟動通知視窗，3 分鐘後自動關閉
      'Q_A'   → 詢問是否關機，等待使用者按按鈕或手機回覆
    """

    def __init__(self, mode: str, config: Config, state: ShutdownState, webhook: WebhookClient):
        self.mode    = mode
        self.config  = config
        self.state   = state
        self.webhook = webhook
        self._start_time = time.time()

        self.root = Tk()
        self._setup_window()

        canvas = Canvas(
            self.root,
            bg='#FFFFFF', height=config.win_height, width=config.win_width,
            bd=0, highlightthickness=0, relief='ridge',
        )
        canvas.place(x=0, y=0)

        if mode == 'begin':
            self._build_begin(canvas)
        elif mode == 'Q_A':
            self._build_qa(canvas)

    def _setup_window(self) -> None:
        cfg = self.config
        sw  = self.root.winfo_screenwidth()
        sh  = self.root.winfo_screenheight()
        cx  = int(sw / 2 - cfg.win_width  / 2)
        cy  = int(sh / 2 - cfg.win_height / 2)
        self.root.geometry(f'{cfg.win_width}x{cfg.win_height}+{cx}+{cy}')
        self.root.title('自動關機程式')
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)              # 隱藏視窗的標題列
        self.root.configure(bg='#FFFFFF')
        self.root.resizable(False, False)
        self.root.iconbitmap('2.ico')

    def _build_begin(self, canvas: Canvas) -> None:
        self.img_bg = self._load_image('output_1.png', (self.config.win_width, self.config.win_height))
        canvas.create_image(0, 0, anchor=NW, image=self.img_bg)

        label = Label(
            self.root,
            text=(
                f'賢寶寶自動關機程式已啟動\n'
                f'預計在 {self.state.shutdown_hour:02d}:{self.state.shutdown_minute:02d} 自動關機唷'
            ),
            bg='#aa3333', fg='#ef834e', font=('微軟正黑體 Bold', 18),
        )
        label.place(x=55, y=10)

        self.img_btn = self._load_image('ok_1.png')
        canvas.create_image(150, 90, anchor=NW, image=self.img_btn, tag='btn')
        canvas.tag_bind('btn', '<Button-1>', lambda e: self._close())

        self.root.after(180_000, self._close)   # 3 分鐘後自動關掉

    def _build_qa(self, canvas: Canvas) -> None:
        self.img_bg = self._load_image('output_2.png', (self.config.win_width, self.config.win_height))
        canvas.create_image(0, 0, anchor=NW, image=self.img_bg)

        self.img_btn_ok    = self._load_image('ok.png')
        self.img_btn_delay = self._load_image('delay.png')

        canvas.create_image(60,  427, anchor=NW, image=self.img_btn_ok,    tag='btn_ok')
        canvas.create_image(220, 430, anchor=NW, image=self.img_btn_delay, tag='btn_delay')

        canvas.tag_bind('btn_ok',    '<Button-1>', lambda e: self._on_user_select(do_shutdown=True))
        canvas.tag_bind('btn_delay', '<Button-1>', lambda e: self._on_user_select(do_shutdown=False))

        # 開始輪詢 Lambda，檢查使用者是否在手機上回覆
        self.root.after(self.config.poll_interval_ms, self._poll_user_reply)

    def run(self) -> None:
        self.root.mainloop()

    def _close(self) -> None:
        time.sleep(0.1)
        self.root.destroy()

    def _on_user_select(self, do_shutdown: bool) -> None:
        """使用者點擊 GUI 按鈕（確認關機 or 延後）。"""
        # 防抖：啟動後 2 秒內的點擊忽略
        if time.time() - self._start_time < 2.0:
            return

        self.state.triggered_by = 'gui'
        if do_shutdown:
            print('[GUI] user confirmed shutdown')
            self.state.do_shutdown = True
        else:
            print(f'[GUI] user delayed by {self.config.delay_min} min')
            self.state.do_shutdown    = False
            t                         = get_local_time(delay_min=self.config.delay_min)
            self.state.shutdown_hour  = t.hour
            self.state.shutdown_minute = t.minute

        self._close()

    def _poll_user_reply(self) -> None:
        """每 poll_interval_ms 毫秒查一次 Lambda，看使用者是否在手機回覆。"""
        # 超過 wait_time_min 分鐘還沒回覆 → 自動關機
        elapsed = time.time() - self._start_time
        if elapsed >= self.config.wait_time_min * 60:
            print('[POLL] timeout → auto shutdown')
            self.state.do_shutdown  = True
            self.state.triggered_by = 'timeout'
            self._close()
            return

        data = self.webhook.get_user_reply()
        if data is None:
            print('[POLL] recv error, retry')
            self.root.after(self.config.poll_interval_ms, self._poll_user_reply)
            return

        print(f'[POLL] is_question={data.get("is_question")}, select={data.get("select")}')

        if data.get('is_question') == False and data.get('select') is not None:
            # 使用者在手機回覆了
            self.webhook.clear_state()
            self.state.triggered_by = 'phone'
            select = data['select']   # 'y', 'yes', 'n', 'no'
            if select == 'y' or select == 'yes':
                print('[POLL] phone replied: shutdown')
                self.state.do_shutdown = True
            else:
                print(f'[POLL] phone replied: delay {self.config.delay_min} min')
                self.state.do_shutdown    = False
                t                         = get_local_time(delay_min=self.config.delay_min)
                self.state.shutdown_hour  = t.hour
                self.state.shutdown_minute = t.minute
            self._close()
        else:
            self.root.after(self.config.poll_interval_ms, self._poll_user_reply)

    def _load_image(self, name: str, resize=None) -> ImageTk.PhotoImage:
        img = Image.open(name)
        if resize:
            img = img.resize(resize)
        return ImageTk.PhotoImage(img)


# ─── 時間工具 ─────────────────────────────────────────────────────────────────

def get_accurate_utc() -> datetime:
    '''
    輸出都是 UTC 時間 (aware datetime)，且已含時區資訊。
    '''
    try:
        # Cloudflare 提供的時間 API，絕對準確，且不受本地時鐘影響。但耗時約 1 秒。
        response = get("https://timeapi.io/api/time/current/zone?timeZone=UTC", timeout=5)
        response.raise_for_status()  # 確保請求成功
        data = response.json()   # dict
        # data: {'year': 2026, 'month': 2, 'day': 27, 'hour': 16, 'minute': 48, 'seconds': 3, 'milliSeconds': 439, 'dateTime': '2026-02-27T16:48:03.4396171', 'date': '02/27/2026', 'time': '16:48', 'timeZone': 'UTC', 'dayOfWeek': 'Friday', 'dstActive': False}
        return datetime.fromisoformat(data["dateTime"]).replace(tzinfo=timezone.utc)
    except Exception as e:
        print(f"Error fetching time from API: {e}")
        # 如果 API 請求失敗，回退到本地時間（不推薦，但作為最後手段）
        return datetime.now(timezone.utc)

def get_local_time(delay_min: int = 0) -> datetime:
    """
    回傳目前時間（加上 delay_min 分鐘延遲）。
    """
    taiwan_time = get_accurate_utc().astimezone(taiwan_tz)
    return taiwan_time + timedelta(minutes=delay_min)


# ─── 主程式 ──────────────────────────────────────────────────────────────────

def main() -> None:
    config  = Config.from_file('關機時間設定.txt')
    state   = ShutdownState(
        shutdown_hour=config.shutdown_hour,
        shutdown_minute=config.shutdown_minute,
    )
    webhook = WebhookClient()

    # 啟動通知視窗
    Window('begin', config, state, webhook).run()
    time.sleep(0.2)

    # 主迴圈：每 10 秒檢查時間
    while True:
        now = get_local_time()
        print(f'[MAIN] now={now.hour:02d}:{now.minute:02d}, wait={state.shutdown_hour:02d}:{state.shutdown_minute:02d}')

        if now.hour == state.shutdown_hour and now.minute == state.shutdown_minute:
            # 時間到了，通知 Lambda 傳 Telegram 訊息給使用者
            webhook.notify_shutdown(state, config.delay_min, config.wait_time_min)

            # 顯示 Q_A 視窗（等待 GUI 按鈕或手機回覆）
            Window('Q_A', config, state, webhook).run()
            time.sleep(0.2)

            if state.do_shutdown:
                # 通知 Lambda 關機結果，並執行關機
                if state.triggered_by == 'timeout':
                    webhook.notify_cancel('timeout', config.delay_min)
                else:
                    webhook.notify_cancel('y', config.delay_min)
                print('[MAIN] executing shutdown')
                # system('shutdown -s -f -t 30')
                break
            else:
                # 使用者選擇延後，通知 Lambda 並顯示啟動通知視窗
                # if state.triggered_by == 'gui':
                webhook.notify_cancel('n', config.delay_min)
                Window('begin', config, state, webhook).run()
                time.sleep(0.2)

        time.sleep(10)

    print('[MAIN] finish')


if __name__ == '__main__':
    main()
