from flask import Flask, jsonify, request, session
from pymongo import MongoClient
import os
import json
from pymongo import ASCENDING

app = Flask(__name__)

client = MongoClient('mongodb+srv://jmangz_12:nPTPrIt6cadofjUT@deploy1.acfeo.mongodb.net/')
db = client['user_database']
users_collection = db['users']
notes_collection = db['notes_history']
bible_collection = db['bible_text']
with open('bible_text/kjv.json', 'r', encoding='utf-8') as file:
    bible_data = json.load(file)
bible_collection.insert_one(bible_data)

def create_indexes():
    # Index for book names (e.g., "Genesis", "Exodus", etc.)
    bible_collection.create_index([("books.name", ASCENDING)])

    # Index for chapters within each book
    bible_collection.create_index([("books.chapters.chapter", ASCENDING)])

    # Index for verses within each chapter
    bible_collection.create_index([("books.chapters.verses.verse", ASCENDING)])

# Call the function to create indexes when the application starts
create_indexes()
if __name__ == '__main__':
    app.run(debug=True)