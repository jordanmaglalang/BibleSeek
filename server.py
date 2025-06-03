from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from db import client, db, notes_collection, users_collection
from dotenv import load_dotenv
import os
from bson import ObjectId
from user import signup_logic, login_logic
import datetime
import os
from datetime import datetime
from flask import Flask, render_template
from db import notes_collection
from chatbot import initialize_graph
import json
import re
# Load environment variables
_ = load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Used to sign session cookies for persistence



# Flask routes
@app.before_request
def initialize_session():
    if 'data' not in session:
        session['data'] = {
            "user_id": None,
            "curr_id": None,
            "notes_history": [],
            "page":0,
            "book_number":0,
            "checkpoint": 0,
            "start_trial": False,
            "trial_run": 0,
        }
@app.route("/")
def index():
   
    user_id = session['data'].get("user_id")
    initialize_session()
    print("logged users is ", bool(user_id))
    return render_template('home.html',logged_in=bool(user_id))
@app.route('/login')
def login():
    print("login ")
    return render_template('login.html')

@app.route("/submit_signup", methods=["POST"])
def signup():
    print("received")
    session_data = session
    return signup_logic(session_data, request)

@app.route("/submit_login", methods=["POST"])
def submit_login():
    print("received")
    session_data = session
    print(session_data['data']['user_id'])
    return login_logic(session_data, request)


@app.route("/logout", methods=["POST"])
def log_out():
    print("before logged out ", session['data']['user_id'])
    session['data'] = {
            "user_id": None,
            "curr_id": None,
            "notes_history": [],
            "page":0,
            "book_number":0,
            "checkpoint": 0,
            "start_trial": False,
            "trial_run": 0,
        }
    print("Logged out , ", session['data']['user_id'])
    
    return jsonify({"Success": True}), 200



@app.route("/versify_front")
def versify_front():
    
    # Route for the main content page after successful login or signup
    if 'user_id' not in session['data']:
        # Redirect to login if the user isn't logged in
        return redirect(url_for('index'))
    user_id = session['data']['user_id']
    print("username id is ", user_id)
    notes_data = notes_collection.find({"user_id": str(ObjectId(user_id))}).sort("created_at", -1)
    #print("notes data " , notes_data)
    entries_list = list(notes_data)
    """"
    for notes_content in notes_data:
        entries_list.append(notes_content)
    """
    # Now, entries_list contains the most recent note document
    # We will pass the entries_list to render_template
    if entries_list:
        note_content = entries_list[0]['note']
        current_id = str(entries_list[0]['_id'])
        session['data']['curr_id'] = current_id
    else:
        note_content = ""
        current_id = None
        session['data']['curr_id'] = None   
    
    return render_template('home.html',notes=entries_list, note_content=note_content, curr_id = current_id,logged_in=bool(user_id))

@app.route('/get', methods=["POST"])
def chat():
    print("updated trial run, ", session['data']['trial_run'])
    # Get the message from the user input
    if session['data']['user_id']== None and session['data']['start_trial'] == False:
        session['data']['start_trial'] = True
        session['data']['trial_run'] = 3
        print("trial run is ", session['data']['trial_run'])
    if session['data']['user_id']== None and session['data']['start_trial'] == True and session['data']['trial_run'] == 0:
       return jsonify({"redirect":True, "url": url_for('login')})

    if session['data']['user_id'] == None:
        session['data']['trial_run'] -=1
    msg = request.form["msg"]
    
    session_data = session['data']
    response = initialize_graph(session_data, msg)
    session.modified = True
    print("RESPONSE ", response)
    return jsonify(response)

@app.route('/update_notes', methods=["POST"])
def update_notes():
    updated_notes = request.form.get('notes')

    print('######Check request########', updated_notes)
    global notes
    notes = updated_notes.split("\n\n")
    for i in notes:
        print(i)
    
      # Get the updated notes from the request
    session['data']['notes_history'] = notes  # Store it in the session (or save it as needed)
    session.modified = True
    print("UPDATE NOTES ", session['data']['notes_history'])
    # Return a success message to the client
    return jsonify({"message": "Notes updated successfully", "updated_notes": updated_notes})

@app.route('/submit_notes', methods=['POST'])
def submit_notes():
    print("received from back end")
    notes_input = request.form.get('notes')
    
    if not notes_input:
        print("not received")
        return jsonify({'message':'Invalid request, missing notes'}),400
    
    if 'user_id' not in session['data']:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    
    user_id = session['data']['user_id']

    user = users_collection.find_one({'_id': ObjectId(user_id)})
    print(user)
    if user:
        updated_notes_history = user.get('notes_history',[])+[notes_input]
        
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'notes_history': updated_notes_history}}
        )
        

        note_document = {
            "user_id": str(ObjectId(user_id)),  # Store user_id as a string for consistency
            "note_id": str(ObjectId()),  # Unique ID for the note
            "note": notes_input,
            "created_at": datetime.utcnow()  # Store timestamp
        }

        notes_collection.insert_one(note_document)

    session['data']['notes_history']=[]
    session.modified = True
    global notes
    notes = []
    print("NEWST NOTE ", updated_notes_history[len(updated_notes_history) - 1])

    return jsonify({'success': True, 'message': 'Notes submitted successfully','updated_notes':updated_notes_history}), 200

@app.route('/get_latest_notes', methods=['GET'])
def get_latest_notes():
    print("get latest notes")
    if session['data']['user_id'] == None:
        print("not logged in")
        return jsonify({"redirect":True, "url": url_for('login')})
    
    user_id = session['data']['user_id']
    
    try:
        # Get all notes for the current user, sorted by date (newest first)
        notes = list(notes_collection.find(
            {"user_id": str(ObjectId(user_id))},
            {"note": 1, "created_at": 1, "_id": 1}
        ).sort("created_at", -1))

        # Prepare the response with properly serialized data
        response_data = {
            'success': True,
            'notes': [{
                '_id': str(note['_id']),
                'note': note['note'],
                'created_at': note['created_at'].isoformat()
            } for note in notes]
        }
        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error fetching notes: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching notes'}), 500



@app.route('/my_journal', methods=['GET'])
def my_journal():
    user_id = session.get('user_id')

    if not user_id:
        return "User not logged in", 401

    # Fetching the most recent note from the 'notes_history' collection
    notes_data = notes_collection.find({"user_id": str(ObjectId(user_id))}).sort("created_at", -1)
    #print("notes data " , notes_data)
    entries_list = list(notes_data)
   
    # Now, entries_list contains the most recent note document
    # We will pass the entries_list to render_template
    note_content = entries_list[0]['note'] if entries_list else ""
    current_id = str(entries_list[0]['_id'])
    print("current id ", current_id)
    session['data']['curr_id'] = current_id
    session.modified = True
    return render_template('my_journal.html', notes=entries_list, note_content=note_content, curr_id = current_id)

@app.route('/get_note/<note_id>', methods =['GET'])
def get_note(note_id):
    
    
    note = notes_collection.find_one({'_id': ObjectId(note_id)})  # Find a specific note by its ID
   # print("opened note, ", note)
    if note:
        print("sucess")
        session['data']['curr_id']= note_id
        session.modified = True
        return jsonify({"success": True,'content': note['note']}),200
    return jsonify({'error': 'Note not found'}), 404

@app.route('/update_note', methods=['POST'])
def update_note():
    print("received updated note")
    get_note_id = session['data']['curr_id']
    updated_notes = request.form.get('notes')  # The updated notes content
    #ession['user_id']
    # Convert the ID from string to ObjectId (MongoDB uses ObjectId for the _id field)
    updated_notes.split("\n\n")
    #print("getting note id ", get_note_id)
    #print("list updated notes, ", updated_notes)
    if get_note_id:
        print("sucess in id")
    else:
        print("not sucess in id")
    try:
        note_object_id = ObjectId(get_note_id)
    except Exception as e:
        return jsonify({"error": "Invalid note ID"}), 400
    #print(updated_notes)
    # Update the note in the database
    result = notes_collection.update_one(
        {"_id": note_object_id},  # Find the note by its ObjectId
        {"$set": {"note": updated_notes}}  # Update the 'notes' field with the new content
    )

    # Check if the update was successful
    if result:
        return jsonify({"message": "Note updated successfully!"})
    else:
        return jsonify({"error": "Failed to update note"}), 500

@app.route('/delete_note', methods=["POST"])
def delete_note():
    print("####################DELETE RECEIVE#######")
    data = request.get_json()
    print("data is" , data)
    note_id = data.get('id')
    if note_id:
        print("deleted successfuly")
        note_object_id= ObjectId(note_id)
        result_note = notes_collection.delete_one({"_id": note_object_id})
        return jsonify({"success": True, "message": "Note deleted successfully"}), 200
    else:
    
        return jsonify({"success": False, "message": "Invalid ID"}), 400



if __name__ == '__main__':
    
    app.run(debug=True)

    




