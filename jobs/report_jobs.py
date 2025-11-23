from core.ai_manager import generate_ai_report_from_image
from database.db_manager import select_ai_report

def run_ai_report_job(report_id: int):
    """
    指定された report_id のAI解析を実行し、結果をDBに保存する。
    """
    report = select_ai_report(report_id)
    if not report:
        print(f"[AI JOB] report_id {report_id} がDBに見つかりません。")
        return

    image_path = report['image_path']
    print(f"[AI JOB] Layer {report['layer_id']} の画像 {image_path} を解析中...")

    generate_ai_report_from_image(image_path, report_id=report_id)
   

    print(f"[AI JOB] report_id {report_id} の解析結果をDBに保存しました。")

    
    #TODO: slack通知
    
