from flask import Blueprint, jsonify, render_template, request
from models import db, Subscription
from app import app
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

bp = Blueprint('routes', __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/api/rates")
def get_rates():
    response = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")
    if response.status_code != 200:
        return jsonify({"status": "error", "message": "Failed to fetch rates"}), 500

    root = ET.fromstring(response.content)
    rates = [{"code": currency.find("CharCode").text, "value": float(currency.find("Value").text.replace(",", "."))}
            for currency in root.findall("Valute")]

    return jsonify({"status": "success", "data": rates})

@bp.route("/api/notify", methods=["POST"])
def notify():
    data = request.json
    new_subscription = Subscription(
        email=data.get("email"),
        currency=data.get("currency"),
        target_rate=float(data.get("rate"))
    )
    db.session.add(new_subscription)
    db.session.commit()

    return jsonify({"status": "success", "message": "Subscription saved"})

app.register_blueprint(bp)
