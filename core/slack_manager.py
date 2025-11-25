from datetime import datetime
from config import SLACK_WEBHOOK_URL, DASHBOARD_URL
import requests, json
from database.db_manager import update_ai_report_status, insert_system_log

def send_report_slack_notification(layer_id: int, text: str, report_id: int = None):
    today_str = datetime.now().strftime("%Y-%m-%d")
    layer_emoji = f"🌱 Layer {layer_id}"
    
    message_text = f"""
📅 {today_str} の通知
{layer_emoji} のレポート

{text}
"""
    if DASHBOARD_URL:
        message_text += f"\n💻 ダッシュボードはこちら: {DASHBOARD_URL}"

    payload = {"text": message_text.strip()}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
        if response.status_code == 200 and response.text == "ok":
            print(f"[Slack] Layer {layer_id} 通知送信成功")
            update_ai_report_status(report_id, slack_sent=1)
            
            insert_system_log(
                    layer_id=layer_id, 
                    log_level='INFO', 
                    message='Report Slack notification sent successfully.', 
                    details=f'AI report notification for Report ID {report_id} delivered to Slack.' 
            )
        else:
            print(f"[Slack] 通知失敗: status={response.status_code}, response={response.text}")
            
            insert_system_log(
                layer_id=layer_id, 
                log_level='ERROR', 
                message='Slack notification delivery failed.',
                details=f'Report ID {report_id}. HTTP Status: {response.status_code}, Response: "{response.text}"' 
            )
    except Exception as e:
        print(f"[Slack] 送信中に例外発生: {e}")
        insert_system_log(
            layer_id=layer_id, 
            log_level='ERROR', 
            message='Exception during Report Slack notification attempt.',
            details=f'Report ID {report_id}. Error details: {e}' 
        )