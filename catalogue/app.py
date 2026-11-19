
from flask import Flask, jsonify
import sqlite3
import os

app = Flask(__name__)

DB_PATH = "/data/catalogue.db"

# Création de la base de données
def init_db():
    os.makedirs("/data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    count = conn.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if count == 0:
        conn.executemany(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            [
                ("Savon naturel", 12.0),
                ("Huile essentielle", 25.0),
                ("Creme naturelle", 18.0)
            ]
        )

    conn.commit()
    conn.close()

# Afficher tous les produits
@app.route("/products", methods=["GET"])
def get_products():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    products = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    conn.close()

    return jsonify([dict(p) for p in products])

# Afficher un produit par son identifiant
@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    conn.close()

    if product is None:
        return jsonify(error="Produit introuvable"), 404

    return jsonify(dict(product))

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
