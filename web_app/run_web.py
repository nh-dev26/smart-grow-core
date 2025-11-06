# smart-grow-core/web_app/run_web.py

from web_app import create_app

# Gunicornがロードするインスタンス
# コマンド例: gunicorn -w 1 run_web:app
app = create_app()

if __name__ == '__main__':
    # 開発環境でのみ使用
    app.run(host='0.0.0.0', port=8000, debug=True)