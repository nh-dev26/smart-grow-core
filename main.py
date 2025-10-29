import sys
from core.db_manager import init_db 
from core.scheduler import run_scheduler

def main():
    # データベースの確認と初期化
    init_db() 

    try:
        run_scheduler() 
    except KeyboardInterrupt:
        # Ctrl+C などで終了した場合のクリーンアップ処理
        print("\nメインスケジューラを停止しました。")

if __name__ == '__main__':
    main()