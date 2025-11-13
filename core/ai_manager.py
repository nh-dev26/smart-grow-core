from config import LLM_API_KEY
import google.generativeai as genai

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
