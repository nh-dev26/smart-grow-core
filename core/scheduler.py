# smart-grow-core/core/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import datetime
import time
from database.db_manager import select_schedules, insert_system_log
from jobs.camera_jobs import execute_photo_job
from jobs.sensor_jobs import execute_sensor_job
from jobs.pump_jobs import execute_pump_job 
from config import SCHEDULE_RELOAD_INTERVAL

# グローバルスケジューラインスタンスを定義
scheduler = BackgroundScheduler(
    job_defaults={
        'coalesce': True,       # 複数のmissed runを1回にまとめる
        'max_instances': 1,     # 各ジョブタイプにつき最大1インスタンスのみ
        'misfire_grace_time': 60 # CRITICAL: 遅延を許容する時間を60秒に設定
    },
    executors={
        'default': {'type': 'threadpool', 'max_workers': 10},
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
        print(f"警告: 未知のジョブタイプ '{job_type}' をスキップしました。", flush=True)
        return None, None

    return job_func, {'layer_id': layer_id}


def get_cron_trigger(job_type, exec_time):
    """ジョブタイプと時刻文字列からCronTriggerを生成"""
    try:
        H, M, S = map(int, exec_time.split(':'))
    except ValueError:
        print(f"エラー: 不正な時刻形式 '{exec_time}'", flush=True)
        return CronTrigger(minute='*', second=0)  # フォールバック: 毎分

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
    print(f"[{now}] --- スケジュール再設定開始 ---", flush=True)

    # 注意: ここで remove_all_jobs() を実行しても、実行中のジョブは完了まで行われます。
    # ただし、カメラジョブは内部遅延を持つため、この再登録中に開始されることはありません。
    scheduler.remove_all_jobs()  # 全削除 → 再登録
    
    # 再読み込みジョブ自身を再登録（削除されてしまうため）
    # run_scheduler関数内で設定されたjob_reloaderの定義をコピーして再登録する
    
    # scheduler.add_job(
    #     load_and_schedule_jobs,
    #     'interval',
    #     minutes=SCHEDULE_RELOAD_INTERVAL,
    #     id='job_reloader',
    #     name=f'Reload schedules from DB every {SCHEDULE_RELOAD_INTERVAL} minutes',
    #     #start_date=datetime.datetime.now() + datetime.timedelta(minutes=SCHEDULE_RELOAD_INTERVAL),
    #     replace_existing=True,
    #     executor='manager'
    # )
    
    scheduler.add_job(
        load_and_schedule_jobs,
        'cron', 
        minute=f'*/{SCHEDULE_RELOAD_INTERVAL}',
        second='0',
        id='job_reloader',
        name=f'Reload schedules from DB every {SCHEDULE_RELOAD_INTERVAL} minutes',
        replace_existing=True,
        executor='manager'
    )

    schedules = select_schedules()
    
    if not schedules:
        print("DBに有効なスケジュールが見つかりません。", flush=True)
        print("--- スケジュール再設定完了 ---", flush=True)
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
                    print(f"✓ [Layer {layer_id}/{job_type}] 毎{total_minutes}分おきに実行", flush=True)
                else:
                    print(f"✓ [Layer {layer_id}/{job_type}] 毎日 {exec_time[:5]} に実行", flush=True)
            else:
                print(f"✓ [Layer {layer_id}/{job_type}] 毎日 {exec_time[:5]} に実行", flush=True)

        except Exception as e:
            print(f"スケジュール登録エラー (ID {schedule_id}): {e}", flush=True)

    print("--- スケジュール再設定完了 ---", flush=True)


def run_scheduler():
    """APSchedulerを起動し、メインループ維持"""
    if not scheduler.running:
        scheduler.start()
        print("APSchedulerが起動しました。", flush=True)

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
        print("\nAPSchedulerをシャットダウンします...", flush=True)
        if scheduler.running:
            scheduler.shutdown(wait=False)
        raise