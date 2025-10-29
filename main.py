# main.py

import sys
from core.db_manager import init_db 
# from core.scheduler import start_scheduler # スケジューラーは後で実装

def main():
    # 1. データベースの確認と初期化を最優先で実行
    init_db() 
    
    # 2. (TODO) スケジューラーの起動ロジックをここに書く
    # scheduler = start_scheduler()
    # scheduler.start()

    print("メインプロセスが起動しました。")
    # 先行実装では、すぐに終了しても問題ありませんが、
    # スケジューラが動く際は、ここでプログラムが終了しないように待機処理が必要です。

if __name__ == '__main__':
    main()