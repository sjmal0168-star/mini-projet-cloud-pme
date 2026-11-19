
from flask import Flask, request, jsonify
import sqlite3
import os
import requests

app = Flask(__name__)

DB_PATH = "/data/commandes.db"

CATALOGUE_URL = "http://catalogue:5001"
NOTIFICATIONS_URL = "http://notifications:5003"

# Création de la base de données
def init_db():
    os.makedirs("/data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER
        )
    """)
    conn.commit()
    conn.close()

# Créer une commande
@app.route("/orders", methods=["POST"])
def create_order():

    data = request.get_json()

    if not data:
        return jsonify(error="Données JSON manquantes"), 400

    product_id = data.get("product_id")
    quantity = data.get("quantity")

    if not isinstance(product_id, int) or not isinstance(quantity, int) or quantity <= 0:
        return jsonify(error="product_id et quantity doivent être des entiers valides"), 400

    # Vérifier que le produit existe dans Catalogue
    try:
        response = requests.get(
            f"{CATALOGUE_URL}/products/{product_id}",
            timeout=5
        )
        if response.status_code == 404:
            return jsonify(error="Produit introuvable"), 404
        response.raise_for_status()
        product = response.json()

    except requests.RequestException:
        return jsonify(error="Service Catalogue indisponible"), 503

    # Enregistrer la commande
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        "INSERT INTO orders (product_id, product_name, quantity) VALUES (?, ?, ?)",
        (product_id, product["name"], quantity)
    )

    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Envoyer une notification
    try:
        requests.post(
            f"{NOTIFICATIONS_URL}/notify",
            json={
                "order_id": order_id,
                "message": f"Commande {order_id} creee avec succes"
            },
            timeout=5
        )
    except requests.RequestException:
        pass

    return jsonify(
        message="Commande creee avec succes",
        order_id=order_id,
        product=product["name"],
        quantity=quantity
    ), 201

# Afficher toutes les commandes
@app.route("/orders", methods=["GET"])
def get_orders():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    orders = conn.execute(
        "SELECT * FROM orders"
    ).fetchall()

    conn.close()

    return jsonify([dict(o) for o in orders])

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
