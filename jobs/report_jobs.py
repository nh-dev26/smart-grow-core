from core.ai_manager import generate_ai_report_from_image
from database.db_manager import select_ai_report, update_ai_report_status, insert_system_log
import os

def run_ai_report_job(report_id: int, layer_id: int):
    """
    指定された report_id のAI解析を実行し、結果をDBに保存する。
    """

    try:
        report = select_ai_report(report_id)
    except Exception as e:
        print(f"[AI JOB] DBからreport_id {report_id} の取得中にエラー: {e}")
        insert_system_log(
            layer_id=layer_id, 
            log_level='CRITICAL', 
            message='Failed to fetch report from DB.', 
            details=f'Report ID {report_id}. Database error during select operation: {e}'
        )
        return

    if not report:
        print(f"[AI JOB] report_id {report_id} がDBに見つかりません。")
        insert_system_log(
            layer_id=layer_id, 
            log_level='WARNING', 
            message='Report data not found in DB.', 
            details=f'No data found for Report ID {report_id}. Job aborted.'
        )
        return

    image_path = report.get('image_path')
    
    if not image_path:
        print(f"[AI JOB] report_id {report_id} に画像パスが設定されていません。")
        insert_system_log(
            layer_id=layer_id, 
            log_level='ERROR', 
            message='Image file path missing for AI job.', 
            details=f'Report ID {report_id} aborted. image_path is null or empty.'
        )
        return
        
    print(f"[AI JOB] Layer {layer_id} の画像 {image_path} を解析中...")

    try:
    
        if not os.path.exists(image_path):
             raise FileNotFoundError(f"File not found at {image_path}")

        generate_ai_report_from_image(image_path, report_id=report_id)
        
        print(f"[AI JOB] report_id {report_id} の解析が正常に完了しました。")
        insert_system_log(
            layer_id=layer_id, 
            log_level='INFO', 
            message='AI Report generation completed successfully.', 
            details=f'Report ID {report_id}. AI model finished processing image at {image_path}.'
        )

    except FileNotFoundError as e:
        print(f"[AI JOB] 画像ファイルが見つかりません: {image_path}")
        insert_system_log(
            layer_id=layer_id, # layer_id は確定済み
            log_level='ERROR', 
            message='Image file not found (FileNotFoundError).', 
            details=f'Report ID {report_id}. Path: {image_path}'
        )
    except Exception as e:
        error_msg = f'AI analysis failed: {type(e).__name__}'
        print(f"[AI JOB] AI解析中に予期せぬエラーが発生: {e}")
        insert_system_log(
            layer_id=layer_id, 
            log_level='ERROR', 
            message='AI report generation failed unexpectedly.', 
            details=f'Report ID {report_id}. Exception: {e}'
        )
        
    print(f"[AI JOB] report_id {report_id} の処理が終了しました。")