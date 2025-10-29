# main.py

import sys
from core.db_manager import init_db 
from core.scheduler import run_scheduler

def main():
    # 1. データベースの確認と初期化を最優先で実行
    init_db() 
    
    # 2. (TODO) スケジューラーの起動ロジックをここに書く
    # scheduler = start_scheduler()
    # scheduler.start()

    print("メインプロセスが起動しました。")
    while True:
        run_scheduler()

if __name__ == '__main__':
    main()