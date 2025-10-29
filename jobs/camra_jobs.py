import cv2
import datetime
import os
import glob
from core.db_manager import insert_camera_log, insert_system_log 

# TODO: config.pyから読み込むように変更
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720
RETENTION_DAYS = 90
BASE_SAVE_DIR = "plant_images" 


def get_file_name():
    """ファイル名を生成（例: 20250910_100000.jpg）"""
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d_%H%M%S.jpg")

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
    SAVE_DIR = os.path.join(BASE_SAVE_DIR, f"layer_{layer_id}")
    
    # 1. 保存ディレクトリを作成
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    
    # 2. カメラの準備 (layersテーブルからcam_idを取得するロジックは後で追加)
    camera_id = 0 # 仮のカメラID (Raspberry Piの最初のUSBカメラ)
    cap = cv2.VideoCapture(camera_id)

    if not cap.isOpened():
        error_msg = f"カメラ(ID:{camera_id})接続失敗。"
        insert_system_log(layer_id, 'ERROR', error_msg, f'VideoCapture({camera_id}) failed to open.')
        print(f"エラー: {error_msg}")
        return

    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)

        ret, frame = cap.read()
        cap.release() 

        if not ret:
            error_msg = f"Layer {layer_id} のフレーム読み込み失敗。"
            insert_system_log(layer_id, 'ERROR', error_msg, 'cap.read() returned False.')
            print(f"エラー: {error_msg}")
            return
        
        file_name = get_file_name()
        relative_file_path = os.path.join(SAVE_DIR, file_name) 
        
        save_image(frame, relative_file_path)
        
        insert_camera_log(layer_id, relative_file_path)
        
        # 5. DBに成功を記録 (system_logs)
        insert_system_log(layer_id, 'INFO', 'Camera job finished successfully.', f'Path: {relative_file_path}')
        
        # 6. 古い画像を削除
        delete_old_images(SAVE_DIR)
        
        print(f"[CAMERA JOB] Layer {layer_id} の画像を {relative_file_path} に保存しました。")

    except Exception as e:
        # 予期せぬ実行時エラーを記録
        insert_system_log(layer_id, 'ERROR', 'Unexpected error during photo job.', str(e))
        print(f"[CRITICAL ERROR] Photo job failed: {e}")
    finally:
        if cap.isOpened():
            cap.release()