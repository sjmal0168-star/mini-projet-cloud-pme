
from flask import Flask, request, jsonify
from pymongo import MongoClient, ReturnDocument
import os
import requests

app = Flask(__name__)

# =====================================
# CONNEXION A MONGODB
# =====================================

MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client.get_default_database()

# Collection des commandes
orders_collection = db["orders"]

# Collection des compteurs
counters_collection = db["counters"]

# Adresses des microservices
CATALOGUE_URL = os.environ.get(
    "CATALOGUE_URL",
    "http://catalogue:5001"
)

NOTIFICATIONS_URL = os.environ.get(
    "NOTIFICATIONS_URL",
    "http://notifications:5003"
)


# =====================================
# GENERATION AUTOMATIQUE DES IDS
# =====================================

def get_next_id(collection_name):

    counter = counters_collection.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    return counter["sequence_value"]


# =====================================
# INITIALISATION DE MONGODB
# =====================================

def init_db():

    client.admin.command("ping")

    print("Connexion MongoDB réussie pour Commandes")


# =====================================
# PAGE D'ACCUEIL - DASHBOARD
# =====================================

@app.route("/", methods=["GET"])
def home():

    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cloud PME Artisanale</title>

        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f1f5f9;
                color: #1e293b;
            }

            header {
                background: #1e3a8a;
                color: white;
                padding: 35px 20px;
                text-align: center;
            }

            header h1 {
                margin: 0;
                font-size: 32px;
            }

            header p {
                margin-top: 12px;
                color: #dbeafe;
            }

            main {
                max-width: 1100px;
                margin: 45px auto;
                padding: 20px;
                text-align: center;
            }

            main h2 {
                margin-bottom: 10px;
                font-size: 27px;
            }

            .description {
                color: #64748b;
                margin-bottom: 35px;
            }

            .container {
                display: grid;
                grid-template-columns: repeat(
                    auto-fit, minmax(250px, 1fr)
                );
                gap: 25px;
            }

            .card {
                background: white;
                padding: 30px 20px;
                border-radius: 15px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                transition: 0.3s;
            }

            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.12);
            }

            .icon {
                font-size: 45px;
                margin-bottom: 15px;
            }

            .card h3 {
                font-size: 22px;
                margin-bottom: 12px;
            }

            .card p {
                color: #64748b;
                min-height: 45px;
            }

            .card a {
                display: inline-block;
                margin-top: 15px;
                padding: 12px 25px;
                border-radius: 8px;
                color: white;
                text-decoration: none;
                font-weight: bold;
            }

            .products a {
                background: #2563eb;
            }

            .orders a {
                background: #059669;
            }

            .notifications a {
                background: #d97706;
            }

            .card a:hover {
                opacity: 0.85;
            }

            footer {
                text-align: center;
                padding: 25px;
                color: #64748b;
                margin-top: 40px;
            }
        </style>
    </head>

    <body>

        <header>
            <h1>Cloud PME Artisanale</h1>
            <p>Plateforme de gestion des activités de l'entreprise</p>
        </header>

        <main>

            <h2>Bienvenue sur votre espace de gestion</h2>

            <p class="description">
                Choisissez le service auquel vous souhaitez accéder.
            </p>

            <div class="container">

                <div class="card products">
                    <div class="icon">📦</div>
                    <h3>Catalogue</h3>
                    <p>
                        Consulter les produits disponibles
                        et leurs prix.
                    </p>
                    <a href="http://localhost:5001/products">
                        Voir les produits
                    </a>
                </div>

                <div class="card orders">
                    <div class="icon">🛒</div>
                    <h3>Commandes</h3>
                    <p>
                        Consulter et gérer
                        les commandes des clients.
                    </p>
                    <a href="/orders">
                        Voir les commandes
                    </a>
                </div>

                <div class="card notifications">
                    <div class="icon">🔔</div>
                    <h3>Notifications</h3>
                    <p>
                        Consulter les notifications
                        liées aux commandes.
                    </p>
                    <a href="http://localhost:5003/notifications">
                        Voir les notifications
                    </a>
                </div>

            </div>

        </main>

        <footer>
            Cloud PME Artisanale - Architecture Microservices
        </footer>

    </body>
    </html>
    """


# =====================================
# CREER UNE COMMANDE
# =====================================

@app.route("/orders", methods=["POST"])
def create_order():

    data = request.get_json(silent=True)

    if not data:
        return jsonify(
            error="Données JSON manquantes"
        ), 400

    product_id = data.get("product_id")
    quantity = data.get("quantity")

    if (type(product_id) is not int
            or type(quantity) is not int
            or quantity <= 0):

        return jsonify(
            error="product_id et quantity doivent être des entiers valides"
        ), 400

    # Vérifier que le produit existe dans Catalogue
    try:

        response = requests.get(
            f"{CATALOGUE_URL}/products/{product_id}",
            timeout=5
        )

        if response.status_code == 404:
            return jsonify(
                error="Produit introuvable"
            ), 404

        response.raise_for_status()

        product = response.json()

    except requests.RequestException:

        return jsonify(
            error="Service Catalogue indisponible"
        ), 503

    # =====================================
    # ENREGISTRER LA COMMANDE DANS MONGODB
    # =====================================

    order_id = get_next_id("orders")

    order = {
        "id": order_id,
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity
    }

    orders_collection.insert_one(order)

    # =====================================
    # ENVOYER UNE NOTIFICATION
    # =====================================

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

        print("Impossible d'envoyer la notification")

    # =====================================
    # REPONSE
    # =====================================

    return jsonify(
        message="Commande creee avec succes",
        order_id=order_id,
        product=product["name"],
        quantity=quantity
    ), 201


# =====================================
# AFFICHER TOUTES LES COMMANDES
# =====================================

@app.route("/orders", methods=["GET"])
def get_orders():

    orders = list(
        orders_collection.find(
            {},
            {"_id": 0}
        ).sort("id", 1)
    )

    return jsonify(orders), 200


# =====================================
# DEMARRAGE DE L'APPLICATION
# =====================================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5002,
        debug=False
    )
