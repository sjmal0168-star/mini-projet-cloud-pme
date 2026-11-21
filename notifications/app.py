
from flask import Flask, request, jsonify
from pymongo import MongoClient, ReturnDocument
import os

app = Flask(__name__)

# =========================
# CONNEXION A MONGODB
# =========================

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


# =========================
# GENERATION AUTOMATIQUE DES IDS
# =========================

def get_next_id(collection_name):

    counter = counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    return counter["sequence_value"]


# =========================
# INITIALISATION DE MONGODB
# =========================

def init_db():

    client.admin.command("ping")

    print("Connexion MongoDB reussie pour Notifications")


# =========================
# ROUTE D'ACCUEIL
# =========================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "service": "Notifications",
        "status": "running"
    }), 200


# =========================
# AJOUTER UNE NOTIFICATION
# =========================

@app.route("/notify", methods=["POST"])
def add_notification():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Donnees JSON manquantes"
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

    # Enregistrer la notification dans MongoDB
    notifications.insert_one(notification)

    # CORRECTION :
    # MongoDB ajoute automatiquement un champ _id de type ObjectId.
    # On le supprime avant de retourner le resultat en JSON.
    notification.pop("_id", None)

    return jsonify({
        "message": "Notification enregistree avec succes",
        "notification": notification
    }), 201


# =========================
# RECUPERER TOUTES LES NOTIFICATIONS
# =========================

@app.route("/notifications", methods=["GET"])
def get_notifications():

    result = list(
        notifications.find(
            {},
            {"_id": 0}
        ).sort("id", 1)
    )

    return jsonify(result), 200


# =========================
# LANCEMENT DU SERVICE
# =========================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5003,
        debug=False
    )
