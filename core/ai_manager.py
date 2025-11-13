from config import LLM_API_KEY
import google.generativeai as genai
import io
from pathlib import Path
from datetime import datetime
from PIL import Image

# Gemini API の設定
if LLM_API_KEY:
    genai.configure(api_key=LLM_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None
    print("Warning: LLM_API_KEY が設定されていません。AI機能は無効です。")
    
def create_system_prompt(sensor_data, image_filename):
    """システムプロンプトを作成"""
    prompt = """あなたは豆苗栽培の専門AIアシスタントです。
    ユーザーの質問に対して、以下の情報を参考にしながら、正確で親切な回答をしてください。

    **回答時の注意事項:**
    - Markdown形式で回答してください
    - 見出し、箇条書き、表、コードブロックなどを適切に使用してください
    - 具体的な数値やデータがある場合は、それを明示してください
    - ユーザーが理解しやすいように、分かりやすい言葉で説明してください
    - 必要に応じて絵文字（🌱、💧、☀️など）を使って見やすくしてください

    """
    
    # センサーデータを追加
    if sensor_data:
        prompt += "\n**現在のシステム情報:**\n"
        if 'temperature' in sensor_data and sensor_data['temperature']:
            prompt += f"- 温度: {sensor_data['temperature']}℃\n"
        if 'humidity' in sensor_data and sensor_data['humidity']:
            prompt += f"- 湿度: {sensor_data['humidity']}%\n"
        if 'supply_pressure' in sensor_data and sensor_data['supply_pressure']:
            prompt += f"- 給水タンク圧力: {sensor_data['supply_pressure']} kPa\n"
        if 'drain_pressure' in sensor_data and sensor_data['drain_pressure']:
            prompt += f"- 排水タンク圧力: {sensor_data['drain_pressure']} kPa\n"
    
    # 画像情報を追加
    if image_filename:
        prompt += f"\n**添付画像:** {image_filename}\n"
        prompt += "画像を分析して、豆苗の成長状態、健康状態、問題点などを詳しく教えてください。\n"
    
    prompt += "\n---\n\n"
    
    return prompt


def process_ai_chat(user_message, image_filename, sensor_data, app_root_path=None):
    """AIチャットの応答を取得する"""
    if not gemini_model:
        raise ConnectionError('AI機能が無効です。LLM_API_KEYを設定してください。')

    system_prompt = create_system_prompt(sensor_data, image_filename)
    image_data = None
    if image_filename and app_root_path:
        try:
            # web_appのルートパスを基準に画像パスを構築
            image_path = Path(app_root_path).parent / 'plant_images' / 'layer_1' / image_filename
            if image_path.exists():
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                image_data = Image.open(io.BytesIO(image_bytes))
            else:
                print(f"Warning: 画像ファイルが見つかりません: {image_path}")
        except Exception as e:
            print(f"画像読み込みエラー: {e}")

    try:
        if image_data:
            print(f"[AI Chat] 画像付きリクエスト: {user_message[:50]}...")
            response = gemini_model.generate_content([system_prompt + "\n\n" + user_message, image_data])
        else:
            print(f"[AI Chat] テキストリクエスト: {user_message[:50]}...")
            response = gemini_model.generate_content(system_prompt + "\n\n" + user_message)
        
        ai_response = response.text
        print(f"[AI Chat] レスポンス受信: {len(ai_response)}文字")
        return ai_response
    except Exception as e:
        error_msg = str(e)
        print(f"[AI Chat] Gemini API エラー: {error_msg}")
        if 'Timeout' in error_msg or 'DNS' in error_msg:
            raise ConnectionError('Gemini APIへの接続がタイムアウトしました。ネットワーク接続を確認してください。')
        elif '403' in error_msg or 'API key' in error_msg:
            raise ValueError('APIキーが無効です。設定を確認してください。')
        elif '429' in error_msg:
            raise ConnectionError('APIの使用制限に達しました。しばらく待ってから再試行してください。')
        else:
            raise RuntimeError(f'AI処理中にエラーが発生しました: {error_msg}')