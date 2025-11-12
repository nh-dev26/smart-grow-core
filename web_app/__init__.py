# web_app/__init__.py

from flask import Flask

def create_app(config_object='config'):
    """
    Flaskアプリケーションのインスタンスを生成するファクトリ関数
    """
    app = Flask('web_app', 
                template_folder='templates',
                static_folder='static')
    
    # config.py から設定を読み込む（プロジェクトのconfig.pyを想定）
    app.config.from_object(config_object) 

    # ルーティングを登録
    from .routes.ui_routes import ui_bp
    from .routes.api_routes import api_bp
    
    app.register_blueprint(ui_bp)
    app.register_blueprint(api_bp)

    # 必要な拡張機能（DBなど）をここで初期化・登録

    return app


