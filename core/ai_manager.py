from config import LLM_API_KEY
import google.generativeai as genai
#最新バージョンの場合import文は以下のようになります
#import google.genai as genai
import io
from pathlib import Path
from datetime import datetime
from PIL import Image

# Gemini API の設定
if LLM_API_KEY:
    genai.configure(api_key=LLM_API_KEY)
    gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")
else:
    gemini_model = None
    print("Warning: LLM_API_KEY が設定されていません。AI機能は無効です。")
    
# ai_manager.py

# ... (既存の import, genai の設定は変更なし) ...

def create_system_prompt(sensor_data, image_filename, quick_action_type=None):
    """
    システムプロンプトを作成。クイックアクションの指示を含む。
    quick_action_typeが指定された場合は、DB保存用の厳密なJSON出力を要求する。
    """
    
    # 役割と基本設定 (常に共通)
    prompt = """あなたは豆苗栽培の専門AIアシスタントです。
ユーザーの質問に対して、以下の情報を参考にしながら、正確で親切な回答をしてください。
"""
    
    # センサーデータと画像情報 (常に共通)
    # ------------------------------------------
    if sensor_data:
        prompt += "\n**現在のシステム情報:**\n"
        if 'temperature' in sensor_data and sensor_data['temperature'] is not None:
            prompt += f"- 温度: {sensor_data['temperature']}℃\n"
        if 'humidity' in sensor_data and sensor_data['humidity'] is not None:
            prompt += f"- 湿度: {sensor_data['humidity']}%\n"
        # タンク圧力は chat-form で除外されている前提ですが、もしあれば含める
        # if 'supply_pressure' in sensor_data and sensor_data['supply_pressure']:
        #     prompt += f"- 給水タンク圧力: {sensor_data['supply_pressure']} kPa\n"
    
    if image_filename:
        prompt += f"\n**添付画像:** {image_filename}\n"
        prompt += "画像を分析して、豆苗の成長状態、健康状態、問題点などを詳しく教えてください。\n"
    # ------------------------------------------
    
    # クイックアクションごとの特別指示 (メインロジック)
    # ------------------------------------------
    
    if quick_action_type:
        # JSON出力を要求する場合の共通指示
        prompt += "\n---\n**【応答形式に関する特別厳命事項】**\n"
        prompt += "あなたの応答は、**以下の指定されたJSON形式のみ**で構成してください。前後の説明、Markdown、コメント、補足テキストは一切含めないでください。\n"
        prompt += f"分析タイプ: `{quick_action_type}`\n"
        
        # 1. 成長率分析
        if quick_action_type == '成長率分析':
            prompt += "分析に基づき、以下のDB保存用JSON形式で出力してください。\n"
            prompt += "```json\n{\n  \"analysis_type\": \"成長率分析\",\n  \"growth_stage\": \"現在の成長段階（例：初期、中期、収穫前）\",\n  \"color_rating\": 1〜5の評価（5が最高）, \n  \"health_comment\": \"生育状況に関する詳細なコメント\",\n  \"recommendation\": \"成長を促進するための具体的な提案\"\n}\n```\n"
        
        # 2. 収穫判断
        elif quick_action_type == '収穫判断':
            prompt += "分析に基づき、以下のDB保存用JSON形式で出力してください。\n"
            prompt += "```json\n{\n  \"analysis_type\": \"収穫判断\",\n  \"ready_for_harvest\": true/false,\n  \"current_height_cm\": 予測される現在の豆苗の高さ (cm),\n  \"reason\": \"収穫可能と判断した根拠（高さ、葉の密度など）\",\n  \"suggested_date\": \"YYYY-MM-DD (具体的な収穫推奨日、または N/A)\"\n}\n```\n"
            
        # 3. 病気診断
        elif quick_action_type == '病気診断':
            prompt += "分析に基づき、以下のDB保存用JSON形式で出力してください。\n"
            prompt += "```json\n{\n  \"analysis_type\": \"病気診断\",\n  \"disease_status\": \"異常なし / 軽度の異常 / 緊急対応が必要\",\n  \"diagnosed_issue\": \"特定された病名または害虫名（例：カビ、葉の変色）\",\n  \"severity\": \"low / medium / high\",\n  \"treatment\": \"特定の薬剤の使用、または環境改善策\"\n}\n```\n"
            
        # 4. 栽培アドバイス
        elif quick_action_type == '栽培アドバイス':
            prompt += "分析に基づき、以下のDB保存用JSON形式で出力してください。\n"
            prompt += "```json\n{\n  \"analysis_type\": \"栽培アドバイス\",\n  \"main_topic\": \"今回のメインアドバイスの要約（例：光の当て方、水やり頻度）\",\n  \"advice_detail\": \"実行すべき具体的なアドバイスや手順を詳細に記載\",\n  \"check_list\": [\"項目1 (例：水は毎日交換する)\", \"項目2 (例：日中の温度を25℃に保つ)\"]\n}\n```\n"

        # quick_action_type が指定されたが、上記に該当しない場合
        else:
             prompt += "\n---\n**【回答時の注意事項】**\n- Markdown形式で、通常のチャットとして応答してください。\n"


    else:
        # quick_action_type が指定されていない場合は、通常のMarkdown応答を要求
        prompt += """**回答時の注意事項:**
    - 回答は**Markdown形式**で、見出し、箇条書き、表などを適切に使用してください。
    - 具体的な数値やデータがある場合は、それを明示してください。
    - 必要に応じて絵文字（🌱、💧、☀️など）を使って見やすくしてください。
    """
    
    prompt += "\n---\n\n"
    
    return prompt


def process_ai_chat(user_message, image_filename, sensor_data, app_root_path=None, quick_action_type=None):
    """
    AIチャットの応答を取得する。
    クイックアクションが指定された場合は、それをプロンプト生成に反映させる。
    """
    if not gemini_model:
        raise ConnectionError('AI機能が無効です。LLM_API_KEYを設定してください。')

    # 💡 修正点: quick_action_type を引数として渡す
    system_prompt = create_system_prompt(sensor_data, image_filename, quick_action_type) 
    
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