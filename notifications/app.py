
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

DB_PATH = "/data/notifications.db"

# Création de la base de données
def init_db():
    os.makedirs("/data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()

# Recevoir et enregistrer une notification
@app.route("/notify", methods=["POST"])
def notify():

    data = request.get_json()

    if not data or "order_id" not in data or "message" not in data:
        return jsonify(error="Donnees manquantes"), 400

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        "INSERT INTO notifications (order_id, message) VALUES (?, ?)",
        (data["order_id"], data["message"])
    )

    notification_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify(
        message="Notification enregistree",
        notification_id=notification_id
    ), 201

# Afficher les notifications
@app.route("/notifications", methods=["GET"])
def get_notifications():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    notifications = conn.execute(
        "SELECT * FROM notifications"
    ).fetchall()

    conn.close()

    return jsonify([dict(n) for n in notifications])

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)

