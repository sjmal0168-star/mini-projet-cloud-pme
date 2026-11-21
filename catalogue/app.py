
from flask import Flask, request, jsonify
from pymongo import MongoClient, ReturnDocument
import os

app = Flask(__name__)

# Connexion à MongoDB
MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client.get_default_database()

# Collection des produits
products = db["products"]

# Collection pour gérer les identifiants
counters = db["counters"]


# Génération automatique des IDs
def get_next_id(collection_name):
    counter = counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return counter["sequence_value"]


# Initialisation de la base de données
def init_db():

    client.admin.command("ping")

    # Ajouter les produits de départ si la collection est vide
    if products.count_documents({}) == 0:

        initial_products = [
            {
                "id": 1,
                "name": "Savon naturel",
                "price": 12.0
            },
            {
                "id": 2,
                "name": "Huile essentielle",
                "price": 25.0
            },
            {
                "id": 3,
                "name": "Creme naturelle",
                "price": 18.0
            }
        ]

        products.insert_many(initial_products)

        # Initialiser le compteur des produits
        counters.update_one(
            {"_id": "products"},
            {"$max": {"sequence_value": 3}},
            upsert=True
        )


# Route d'accueil
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Catalogue",
        "status": "running"
    })


# Récupérer tous les produits
@app.route("/products", methods=["GET"])
def get_products():

    result = list(
        products.find({}, {"_id": 0}).sort("id", 1)
    )

    return jsonify(result), 200


# Récupérer un produit par son ID
@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):

    product = products.find_one(
        {"id": product_id},
        {"_id": 0}
    )

    if product is None:
        return jsonify({
            "error": "Produit introuvable"
        }), 404

    return jsonify(product), 200


# Ajouter un nouveau produit
@app.route("/products", methods=["POST"])
def add_product():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Données JSON manquantes"
        }), 400

    name = data.get("name")
    price = data.get("price")

    if not name or price is None:
        return jsonify({
            "error": "Le nom et le prix sont obligatoires"
        }), 400

    try:
        price = float(price)

        if price < 0:
            raise ValueError()

    except (ValueError, TypeError):
        return jsonify({
            "error": "Prix invalide"
        }), 400

    product = {
        "id": get_next_id("products"),
        "name": name,
        "price": price
    }

    products.insert_one(product)

    return jsonify({
        "message": "Produit ajouté avec succès",
        "product": product
    }), 201


# Lancement du service
if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )
