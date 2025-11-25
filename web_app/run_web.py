from web_app import create_app

# 起動コマンド python -m web_app.run_web
app = create_app()

if __name__ == '__main__':
    # 本番環境で実行するコードからは「必ず」denug = Falseに
    app.run(host='0.0.0.0', port=8000, debug=True)