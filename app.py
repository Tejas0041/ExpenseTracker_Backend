from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config["MONGO_URI"] = os.getenv("MONGO_URI")

if not app.config["MONGO_URI"]:
    raise ValueError("Missing MONGO_URI in environment variables!")

mongo = PyMongo(app)

expenses = mongo.db.expenses
categories = mongo.db.categories

@app.route('/expenses', methods=['GET'])
def get_expenses():
    expense_list = []
    for expense in expenses.find():
        expense['_id'] = str(expense['_id']) 
        expense_list.append(expense)
    return jsonify(expense_list)

@app.route('/expenses', methods=['POST'])
def add_expense():
    data = request.get_json()
    if not data or not 'amount' in data or not 'category' in data:
        return jsonify({"error": "Missing required fields"}), 400

    category = categories.find_one({"name": data['category']})
    if not category:
        return jsonify({"error": "Category does not exist"}), 400

    expense = {
        "amount": data['amount'],
        "category": data['category'],
        "note": data.get('note', ''),
        "timestamp": datetime.now()
    }
    result = expenses.insert_one(expense)
    return jsonify({"_id": str(result.inserted_id)}), 201

@app.route('/expenses/<id>', methods=['PUT'])
def update_expense(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if 'category' in data:
        category = categories.find_one({"name": data['category']})
        if not category:
            return jsonify({"error": "Category does not exist"}), 400

    expense = expenses.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": data},
        return_document=True
    )
    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    expense['_id'] = str(expense['_id'])
    return jsonify(expense)

@app.route('/expenses/<id>', methods=['DELETE'])
def delete_expense(id):
    result = expenses.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify({"message": "Expense deleted"}), 200

@app.route('/categories', methods=['GET'])
def get_categories():
    category_list = []
    for category in categories.find():
        category['_id'] = str(category['_id'])  
        category_list.append(category)
    return jsonify(category_list)

@app.route('/categories', methods=['POST'])
def add_category():
    data = request.get_json()
    if not data or not 'name' in data:
        return jsonify({"error": "Missing required fields"}), 400

    if categories.find_one({"name": data['name']}):
        return jsonify({"error": "Category already exists"}), 400

    category = {
        "name": data['name']
    }
    result = categories.insert_one(category)
    return jsonify({"_id": str(result.inserted_id)}), 201

@app.route('/categories/<name>', methods=['DELETE'])
def remove_category(name):
    result = categories.delete_one({"name": name})
    if result.deleted_count == 0:
        return jsonify({"error": "Category not found"}), 404

    expenses.delete_many({"category": name})
    return jsonify({"message": "Category and associated expenses deleted"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)