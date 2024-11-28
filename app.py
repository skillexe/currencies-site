from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv  # Импортируем dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import threading
import time

# Загрузка данных из файла .env
load_dotenv()

# Использование переменных из .env
api_key = os.getenv("EXCHANGERATE_API_KEY")
mail_username = os.getenv("MAIL_USERNAME")
mail_password = os.getenv("MAIL_PASSWORD")

# Инициализация Flask-приложения
app = Flask(__name__)

# Настройка базы данных SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройки SMTP для отправки писем
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = mail_username  # Используем данные из .env
app.config['MAIL_PASSWORD'] = mail_password  # Используем данные из .env

# Инициализация SQLAlchemy и Flask-Mail
db = SQLAlchemy(app)
mail = Mail(app)

# Маппинг кодов валют (ISO -> ЦБ РФ)
CURRENCY_MAPPING = {
    "USD": "R01235",
    "EUR": "R01239",
    "GBP": "R01035",
    "JPY": "R01820",
    "CNY": "R01375"
}

# Модель для подписок
class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    target_rate = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Subscription {self.email}, {self.currency}, {self.target_rate}>"

# Главная страница
@app.route("/")
def index():
    return render_template("index.html")

# Страница конвертера валют
@app.route("/converter")
def converter():
    return render_template("converter.html")

# Страница графиков изменений курсов
@app.route("/history")
def history():
    return render_template("history.html")

# Страница уведомлений о курсе
@app.route("/notifications")
def notifications():
    return render_template("notifications.html")

# API для получения текущих курсов валют
@app.route("/api/rates")
def get_rates():
    response = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")
    if response.status_code != 200:
        return jsonify({"status": "error", "message": "Failed to fetch rates"}), 500

    root = ET.fromstring(response.content)
    rates = []
    for currency in root.findall("Valute"):
        rates.append({
            "code": currency.find("CharCode").text,
            "name": currency.find("Name").text,
            "value": float(currency.find("Value").text.replace(",", ".")),
            "nominal": int(currency.find("Nominal").text)
        })

    return jsonify({"status": "success", "base_currency": "RUB", "data": rates})

# API для получения исторических данных курсов валют
@app.route("/api/rates_history")
def get_rates_history():
    currency_code = request.args.get("currency", default="USD")
    cbr_currency_code = CURRENCY_MAPPING.get(currency_code)

    if not cbr_currency_code:
        return jsonify({"status": "error", "message": f"Unsupported currency: {currency_code}"}), 400

    # Получаем пользовательские или стандартные даты
    raw_start_date = request.args.get("start_date", default=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
    raw_end_date = request.args.get("end_date", default=datetime.now().strftime("%Y-%m-%d"))

    # Преобразуем даты в формат дд/мм/гггг
    start_date = datetime.strptime(raw_start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    end_date = datetime.strptime(raw_end_date, "%Y-%m-%d").strftime("%d/%m/%Y")

    url = f"https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={start_date}&date_req2={end_date}&VAL_NM_RQ={cbr_currency_code}"
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"status": "error", "message": "Failed to fetch data from CBR"}), 500

    root = ET.fromstring(response.content)
    dates = []
    rates = []
    for record in root.findall("Record"):
        date = record.attrib["Date"]
        value = float(record.find("Value").text.replace(",", "."))
        dates.append(date)
        rates.append(value)

    return jsonify({"status": "success", "dates": dates, "rates": rates})

@app.route("/api/rates_exchangerate")
def get_rates_exchangerate():
    api_key = "6d07e521efbf674c53d4cd68"  # Ваш API-ключ
    response = requests.get(f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD")
    
    if response.status_code != 200:
        return jsonify({"status": "error", "message": "Failed to fetch rates"}), 500

    data = response.json()
    if "conversion_rates" not in data:
        return jsonify({"status": "error", "message": "Invalid response from API"}), 500

    # Преобразуем данные в список
    rates = [
        {"code": code, "value": value, "name": f"{code}"}
        for code, value in data["conversion_rates"].items()
    ]

    return jsonify({"status": "success", "base_currency": "USD", "data": rates})

# API для конвертации валют
@app.route("/api/convert", methods=["GET"])
def convert_currency():
    from_currency = request.args.get("from")
    to_currency = request.args.get("to")
    amount = float(request.args.get("amount", 0))

    if not from_currency or not to_currency or amount <= 0:
        return jsonify({"status": "error", "message": "Invalid parameters"}), 400

    response = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")
    if response.status_code != 200:
        return jsonify({"status": "error", "message": "Failed to fetch rates"}), 500

    root = ET.fromstring(response.content)
    rates = {"RUB": 1.0}
    for currency in root.findall("Valute"):
        code = currency.find("CharCode").text
        value = float(currency.find("Value").text.replace(",", "."))
        nominal = int(currency.find("Nominal").text)
        rates[code] = value / nominal

    if from_currency not in rates or to_currency not in rates:
        return jsonify({"status": "error", "message": "Unsupported currency"}), 400

    converted = amount * rates[from_currency] / rates[to_currency]
    return jsonify({"status": "success", "converted": round(converted, 2)})

# API для подписки на уведомления
@app.route("/api/notify", methods=["POST"])
def notify():
    data = request.json
    email = data.get("email")
    currency = data.get("currency")
    target_rate = float(data.get("rate"))

    new_subscription = Subscription(email=email, currency=currency, target_rate=target_rate)
    db.session.add(new_subscription)
    db.session.commit()

    return jsonify({"status": "success", "message": "Subscription saved"})

# Функция для отправки email
def send_email(recipient, subject, body):
    try:
        # msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient])
        # msg.body = body
        # mail.send(msg)
        print(f"(DEBUG) Email sent to {recipient} (но фактически не отправлено)")
    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")

# Фоновая задача для проверки подписок
def check_and_notify_subscriptions():
    while True:
        with app.app_context():
            response = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")
            if response.status_code != 200:
                time.sleep(3600)
                continue

            root = ET.fromstring(response.content)
            rates = {}
            for currency in root.findall("Valute"):
                code = currency.find("CharCode").text
                value = float(currency.find("Value").text.replace(",", "."))
                nominal = int(currency.find("Nominal").text)
                rates[code] = value / nominal

            subscriptions = Subscription.query.all()
            for sub in subscriptions:
                current_rate = rates.get(sub.currency)
                if current_rate and current_rate <= sub.target_rate:
                    subject = f"Курс валюты {sub.currency} достиг цели!"
                    body = f"Текущий курс {sub.currency}: {current_rate:.2f}. Ваша цель: {sub.target_rate:.2f}."
                    # send_email(sub.email, subject, body)
                    print(f"(DEBUG) Email для {sub.email}: {body} (но не отправлено)")

            time.sleep(3600)

if __name__ == "__main__":
    # threading.Thread(target=check_and_notify_subscriptions, daemon=True).start()
    app.run(debug=True)

    



