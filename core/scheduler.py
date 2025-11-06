# smart-grow-core/core/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import datetime
import time
import sys
from database.db_manager import select_schedules, insert_system_log
from jobs.camera_jobs import execute_photo_job
from jobs.sensor_jobs import execute_sensor_job
from jobs.pump_jobs import execute_pump_job 

# グローバルスケジューラインスタンスを定義
# 最終決定: max_workers=2 で、軽いジョブ（センサー、ポンプ、再読み込み）の並行処理を許可
scheduler = BackgroundScheduler(
    executors={
        'default': {'type': 'threadpool', 'max_workers': 2},
        'manager': {'type': 'threadpool', 'max_workers': 1}
    }
)

def get_job_info(job):
    """DBレコードから実行関数と引数を取得"""
    job_type = job['job_type']
    layer_id = job['layer_id']

    if job_type == 'camera':
        job_func = execute_photo_job
    elif job_type == 'sensor':
        job_func = execute_sensor_job
    elif job_type == 'water':
        job_func = execute_pump_job
    else:
        print(f"警告: 未知のジョブタイプ '{job_type}' をスキップしました。")
        return None, None

    return job_func, {'layer_id': layer_id}


def get_cron_trigger(job_type, exec_time):
    """ジョブタイプと時刻文字列からCronTriggerを生成"""
    try:
        H, M, S = map(int, exec_time.split(':'))
    except ValueError:
        print(f"エラー: 不正な時刻形式 '{exec_time}'")
        return CronTrigger(minute='*')  # フォールバック: 毎分

    # センサー・水ジョブ → 間隔解釈
    if job_type in ['sensor', 'water']:
        total_minutes = M + H * 60
        if total_minutes > 0 and 60 % total_minutes == 0:
            minute_interval = ','.join(str(i) for i in range(0, 60, total_minutes))
            return CronTrigger(minute=minute_interval, hour='*', second=0)
        elif H > 0 or M > 0:
            return CronTrigger(hour=H, minute=M, second=0)

    # カメラなど固定時刻ジョブ
    return CronTrigger(hour=H, minute=M, second=0)


def load_and_schedule_jobs():
    """DBからスケジュールを読み込み、再登録"""
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] --- スケジュール再設定開始 ---")

    # 注意: ここで remove_all_jobs() を実行しても、実行中のジョブは完了まで行われます。
    # ただし、カメラジョブは内部遅延を持つため、この再登録中に開始されることはありません。
    scheduler.remove_all_jobs()  # 全削除 → 再登録
    
    # 再読み込みジョブ自身を再登録（削除されてしまうため）
    # run_scheduler関数内で設定されたjob_reloaderの定義をコピーして再登録する
    scheduler.add_job(
        load_and_schedule_jobs,
        'interval',
        minutes=1,
        id='job_reloader',
        name='Reload schedules from DB every 5 minutes',
        start_date=datetime.datetime.now() + datetime.timedelta(minutes=1),
        replace_existing=True,
        misfire_grace_time=30,
        executor='manager'
    )

    schedules = select_schedules()
    
    if not schedules:
        print("DBに有効なスケジュールが見つかりません。")
        print("--- スケジュール再設定完了 ---")
        return

    for job in schedules:
        schedule_id = job['schedule_id']
        job_type = job['job_type']
        exec_time = job['exec_time']
        layer_id = job['layer_id']

        job_func, job_args = get_job_info(job)
        if not job_func:
            continue

        try:
            trigger = get_cron_trigger(job_type, exec_time)
            
            scheduler.add_job(
                func=job_func,
                trigger=trigger,
                id=f'job_{schedule_id}',
                kwargs=job_args,
                name=f'Layer {layer_id} / {job_type} @ {exec_time[:5]}',
                max_instances=1
                # Executorの指定は不要（すべて 'default' になる）
            )

            # ログ出力
            if job_type in ['sensor', 'water']:
                H, M, S = map(int, exec_time.split(':'))
                total_minutes = M + H * 60
                if total_minutes > 0 and 60 % total_minutes == 0:
                    print(f"✓ [Layer {layer_id}/{job_type}] 毎{total_minutes}分おきに実行")
                else:
                    print(f"✓ [Layer {layer_id}/{job_type}] 毎日 {exec_time[:5]} に実行")
            else:
                print(f"✓ [Layer {layer_id}/{job_type}] 毎日 {exec_time[:5]} に実行")

        except Exception as e:
            print(f"スケジュール登録エラー (ID {schedule_id}): {e}")

    print("--- スケジュール再設定完了 ---")


def run_scheduler():
    """APSchedulerを起動し、メインループ維持"""
    if not scheduler.running:
        scheduler.start()
        print("APSchedulerが起動しました。")

        # 1. 起動時に一度ロード
        # 注意: load_and_schedule_jobs内で job_reloader も再登録されるため、
        # ここでは job_reloader の登録は不要。
        load_and_schedule_jobs()

        insert_system_log(
            layer_id=0,
            log_level='INFO',
            message='Scheduler Started',
            details='APScheduler main loop initiated successfully.'
        )

    try:
        # スケジューラ起動中は time.sleep でプロセスを維持する
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("\nAPSchedulerをシャットダウンします...")
        if scheduler.running:
            scheduler.shutdown(wait=False)
        raise