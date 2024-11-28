from flask_mail import Message
from app import mail, app
from models import Subscription
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time

def send_email(recipient, subject, body):
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient])
        msg.body = body
        mail.send(msg)
        app.logger.info(f"Email sent to {recipient}")
    except Exception as e:
        app.logger.error(f"Failed to send email: {e}")

def check_and_notify_subscriptions():
    while True:
        with app.app_context():
            # Fetch currency rates
            response = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")
            if response.status_code != 200:
                app.logger.error("Failed to fetch currency rates")
                time.sleep(3600)
                continue

            root = ET.fromstring(response.content)
            rates = {currency.find("CharCode").text: float(currency.find("Value").text.replace(",", "."))
                    for currency in root.findall("Valute")}

            subscriptions = Subscription.query.all()
            for sub in subscriptions:
                current_rate = rates.get(sub.currency)
                if current_rate and current_rate <= sub.target_rate:
                    send_email(
                        sub.email,
                        f"Курс валюты {sub.currency} достиг цели!",
                        f"Текущий курс {sub.currency}: {current_rate:.2f}. Ваша цель: {sub.target_rate:.2f}."
                    )

        time.sleep(3600)
