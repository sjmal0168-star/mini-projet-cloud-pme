
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

# Collection des notifications
notifications = db["notifications"]

# Collection des compteurs
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


# Vérifier la connexion MongoDB
def init_db():
    client.admin.command("ping")


# Route d'accueil
@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "service": "Notifications",
        "status": "running"
    })


# Ajouter une notification
@app.route("/notify", methods=["POST"])
def add_notification():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Données JSON manquantes"
        }), 400

    message = data.get("message")
    order_id = data.get("order_id")

    if not message:
        return jsonify({
            "error": "Le message est obligatoire"
        }), 400

    notification = {
        "id": get_next_id("notifications"),
        "order_id": order_id,
        "message": message
    }

    # Enregistrer dans MongoDB
    notifications.insert_one(notification)

    return jsonify({
        "message": "Notification enregistrée avec succès",
        "notification": notification
    }), 201


# Récupérer toutes les notifications
@app.route("/notifications", methods=["GET"])
def get_notifications():

    result = list(
        notifications.find({}, {"_id": 0}).sort("id", 1)
    )

    return jsonify(result), 200


# Lancement du service
if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5003,
        debug=False
    )
