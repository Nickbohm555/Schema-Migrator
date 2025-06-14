from pymongo import MongoClient
from urllib.parse import quote_plus

if __name__ == "__main__":
    username = quote_plus("nickbohm555")
    password = quote_plus("Yoshiman3106!@")
    
    connection_string = f"mongodb+srv://{username}:{password}@cluster0.ze0xint.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    
    client = MongoClient(connection_string)
    db = client.location_db
    collection = db.ADDRESS

    item_1 = {
        "address": {
            "street": "123 Main Street",
            "city": "New York",
            "state": "NY",
            "zip": "10001"
        }
    }

    item_2 = {
        "address": {
            "street": "456 Oak Avenue",
            "city": "Los Angeles",
            "state": "CA",
            "zip": "90001"
        }
    }

    item_3 = {
        "address": {
            "street": "789 Pine Road",
            "city": "Chicago",
            "state": "IL",
            "zip": "60601"
        }
    }

    item_4 = {
        "address": {
            "street": "321 Maple Drive",
            "city": "Houston",
            "state": "TX",
            "zip": "77001"
        }
    }

    item_5 = {
        "address": {
            "street": "654 Cedar Lane",
            "city": "Miami",
            "state": "FL",
            "zip": "33101"
        }
    }

    documents = [item_1, item_2, item_3, item_4, item_5]
    collection.insert_many(documents)