import schedule
import time
from core.db_manager import select_schedules
from jobs.camera_jobs import execute_photo_job
# from jobs.pump_jobs import execute_pump_job # 今後実装
from jobs.sensor_jobs import execute_sensor_job 

def load_and_schedule_jobs():
    """
    データベースから有効なスケジュールを読み込み、Pythonのスケジューラに登録する。
    """
    print("--- スケジュール設定を開始します ---")
    schedule.clear() # 既存のスケジュールをクリアして再設定に備える

    schedules = select_schedules()
    
    if not schedules:
        print("DBに有効なスケジュールが見つかりませんでした。")
        return

    for job in schedules:
        job_type = job['job_type']
        exec_time = job['exec_time'] # 例: '09:00:00'
        layer_id = job['layer_id']
        
        # 実行関数を job_type に基づいて決定
        if job_type == 'camera':
            job_func = execute_photo_job
        # elif job_type == 'water':
        #     job_func = execute_pump_job
        elif job_type == 'sensor':
            job_func = execute_sensor_job
        else:
            print(f"警告: 未知のジョブタイプ '{job_type}' をスキップしました。")
            continue
            
        # スケジューラにジョブを登録
        # 毎日、指定された時刻に実行するように設定 (DBの exec_time を利用)
        schedule.every().day.at(exec_time[:5]).do(job_func, layer_id=layer_id)
        
        print(f"✓ スケジュール登録: [Layer {layer_id} / {job_type}] 毎日 {exec_time[:5]} に実行")

    print("--- スケジュール設定が完了しました ---")


def run_scheduler():
    """
    スケジューラを永続的に実行する。
    """
    # スケジュール設定を最初に実行
    load_and_schedule_jobs()

    while True:
        schedule.run_pending()
        time.sleep(1) # CPU負荷軽減のため1秒待機