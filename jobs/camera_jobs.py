import cv2
import datetime
from time import sleep
import os
import glob
from database.db_manager import insert_initial_ai_report, insert_system_log, select_layer_info
from config import *
from jobs.report_jobs import run_ai_report_job

def get_file_name(job_timestamp):
    """ファイル名を生成（例: 20250910_100000.jpg）"""
    return job_timestamp.strftime("%Y%m%d_%H%M%S.jpg")

def save_image(frame, file_path):
    """画像をJPEG形式で保存"""
    # [int(cv2.IMWRITE_JPEG_QUALITY), 95] は画像品質設定です
    cv2.imwrite(file_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

def delete_old_images(save_dir):
    """指定期間より古い画像を自動削除"""
    today = datetime.datetime.now()
    cutoff_date = today - datetime.timedelta(days=RETENTION_DAYS)
    
    image_files = glob.glob(os.path.join(save_dir, "*.jp*g"))
    
    for file_path in image_files:
        try:
            timestamp = os.path.getctime(file_path)
            file_date = datetime.datetime.fromtimestamp(timestamp)
            
            if file_date < cutoff_date:
                os.remove(file_path)
        except Exception as e:
            # 削除エラーはCRITICALではないため、システムログには記録せず、コンソール出力のみ
            print(f"警告: 古い画像ファイル {file_path} の削除中にエラー: {e}")


# --- メインジョブ関数 ---
def execute_photo_job(layer_id: int):
    """
    指定された層 (layer_id) のカメラを起動し、撮影、保存、DB記録を行う。
    """
    from core.scheduler import scheduler
    job_timestamp = datetime.datetime.now()
    job_timestamp_str = job_timestamp.isoformat()
    SAVE_DIR = os.path.join(BASE_SAVE_DIR, f"layer_{layer_id}")
        
    # 1. 保存ディレクトリを作成
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    layer_info = select_layer_info(layer_id)
    
    if not layer_info:
        error_msg = f"Layer {layer_id} の情報がDBに見つかりません。"
        insert_system_log(
            layer_id=layer_id, 
            log_level='ERROR', 
            message=error_msg, 
            details='Layer ID not found in layers table.',
            timestamp_str=job_timestamp_str)
        print(f"エラー: {error_msg}")
        return
        
    camera_id = layer_info['cam_id'] # cam_id (例: '/dev/video0' または 0) を使用
    
    # 撮影前のディレイ処理
    # layer_id が 1 なら 0秒、2なら 2秒、3なら 4秒待つ (2秒間隔)
    delay_sec = (layer_id - 1) * 2 
    
    if delay_sec > 0:
        print(f"[{datetime.now()}] [CAMERA JOB] Layer {layer_id} は、リソース競合を避けるため {delay_sec} 秒待機します。")
        sleep(delay_sec)
    
    cap = cv2.VideoCapture(camera_id)

    if not cap.isOpened():
        error_msg = f"カメラ(ID:{camera_id})接続失敗。"
        insert_system_log(
            layer_id=layer_id, 
            log_level='ERROR', 
            message=error_msg, 
            details=f'VideoCapture({camera_id}) failed to open.',
            timestamp_str=job_timestamp_str)
        print(f"エラー: {error_msg}")
        return

    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)

        ret, frame = cap.read()

        if not ret:
            error_msg = f"Layer {layer_id} のフレーム読み込み失敗。"
            insert_system_log(
                layer_id=layer_id, 
                log_level='ERROR', 
                message=error_msg, 
                details='cap.read() returned False.',
                timestamp_str=job_timestamp_str)
            print(f"エラー: {error_msg}")
            return
        
        file_name = get_file_name(job_timestamp)
        image_full_path = os.path.join(SAVE_DIR, file_name) 
        
        save_image(frame, image_full_path)
        
        report_id = insert_initial_ai_report(layer_id, job_timestamp_str, image_full_path)
        
        if report_id:
            # 取得した report_id を使って、AIジョブを即時実行するように登録
            scheduler.add_job(
                run_ai_report_job,
                trigger='date',
                args=[report_id],
                id=f'ai_report_{report_id}', # ジョブIDが一意になるように設定
                name=f'AI Report for Layer {layer_id} - Image {report_id}',
                replace_existing=True, # 万が一同じIDのジョブがあれば上書き
                misfire_grace_time=300 # 5分以内の遅延なら実行を許可
            )
            print(f"[CAMERA JOB] AIレポートジョブ (ID: ai_report_{report_id}) をスケジュールに登録しました。")

        insert_system_log(
            layer_id=layer_id, 
            log_level='INFO', 
            message='Camera job finished successfully.', 
            details=f'Path: {image_full_path}',
            timestamp_str=job_timestamp_str)
        
        delete_old_images(SAVE_DIR)
        
        print(f"[CAMERA JOB] Layer {layer_id} の画像を {image_full_path} に保存しました。")

    except Exception as e:
        insert_system_log(
            layer_id=layer_id, 
            log_level='ERROR', 
            message='Unexpected error during photo job.', 
            details=str(e),
            timestamp_str=job_timestamp_str)
        print(f"[CRITICAL ERROR] Photo job failed: {e}")
    finally:
        if cap.isOpened():
            cap.release()