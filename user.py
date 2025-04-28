from db import db, users_collection
from flask import jsonify, redirect, url_for
import bcrypt
def signup_logic(session, request):
    user_email = request.form['email']
    user_password = request.form['password']
    
    # Perform user verification and database insertion
    # Example pseudocode: check if user already exists, create new user, etc.
    if users_collection.find_one({'email': user_email}):
        return jsonify({'message': 'Email already exists'}), 400
    
    
    
    hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt())
    user_data = {
        "email": user_email,
        "password": hashed_password.decode('utf-8'),  # Store hashed password as string
        "notes_history": []  # Initialize an empty notes history for the user
    }

    user = users_collection.insert_one(user_data)
    user_id = str(user.inserted_id)
    session['data']['user_id'] = user_id
    session['data']['notes_history'] = []  # Initialize an empty notes history in the session
    session.modified = True 
    print("User successfully added with user ID:", user_id)
    
    print("successfully added")
    #return jsonify({'message': 'User registered successfully'})
    return redirect(url_for('index'))


def login_logic(session, request):
    user_email = request.form['email']
    user_password = request.form['password'].encode('utf-8')
    
    user = users_collection.find_one({'email': user_email})
    if user and bcrypt.checkpw(user_password, user['password'].encode('utf-8')):
        # Create user session or token here
        print("mongo db id ", str(user['_id']))
        session['data']['user_id'] = str(user['_id'])
        session.modified = True 
        print("SUCCESS IN LOGIN", session['data']['user_id'],"and user password ", user['password'])
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 400
