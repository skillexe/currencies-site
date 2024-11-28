from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import Config
from models import db
from routes import bp
import threading
from tasks import check_and_notify_subscriptions

app = Flask(__name__)
app.config.from_object(Config)

# Инициализация модулей
db.init_app(app)
mail = Mail(app)

# Запуск фоновой задачи
threading.Thread(target=check_and_notify_subscriptions, daemon=True).start()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
