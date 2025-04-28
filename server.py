from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from db import client, db, notes_collection, users_collection, bible_collection
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
        }
@app.route("/")
def index():
    #return render_template('Versify_front.html')
    
    initialize_session()
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
    
    return render_template('home.html',notes=entries_list, note_content=note_content, curr_id = current_id)

@app.route('/get', methods=["POST"])
def chat():
    # Get the message from the user iAnput
  
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
        return jsonify({'message':'User not logged in'})
    
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
    

    return jsonify({'success': True, 'message': 'Notes submitted successfully','updated_notes':updated_notes_history}), 200
    
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
@app.route('/view_bible', methods=["GET"])
def read_bible():
    
   
    bible_data = bible_collection.find_one({}, {"_id": 0})  # Exclude MongoDB ID

    if not bible_data:
        return jsonify({"success": False, "message": "Bible data not found"}), 404

 
    
    # Return the first chapter of Genesis as an example
    if session['data']['checkpoint'] ==0:
        session['data']['book_number']=65
        session['data']['page']=21
        session.modified = True
    
    first_chapter = bible_data['books'][session['data']['book_number']]['chapters'][session['data']['page']]['verses']
    #result = result.replace("\n", "<br>")
    #print(result)
    session['data']['checkpoint']+=1
    session.modified=True
    all_verses=[]
    for a in range(len(first_chapter)):# one group of verses
            verse_text = first_chapter[a]['text'].replace("¶", "").strip()
            item = f"<span class='verse-number'>{first_chapter[a]['verse']}</span> {verse_text}"
            all_verses.append(item)#each verse added to list of verses in chapter
    
    result = " ".join(all_verses)
  
    result = result.replace(" ", "  ")
    

    current_book = bible_data['books'][session['data']['book_number']]['name']
    current_chapter_number = session['data']['page'] + 1  #
    current_page = f"{current_book}  {current_chapter_number}"

    result = result.replace("\n\n", "<br><br>")
    return jsonify({"success": True, "data": result, "current_chapter": current_page})

@app.route('/next_chapter', methods=["GET"])
def next_chapter():
    print("next chapter check")
    bible_data = bible_collection.find_one({}, {"_id": 0})  # Exclude MongoDB ID

    if not bible_data:
        return jsonify({"success": False, "message": "Bible data not found"}), 404
    #print(bible_data['books'][session['data']['book_number']]['chapters'])
    if(session['data']['page']+1<len(bible_data['books'][session['data']['book_number']]['chapters'])):
        session['data']['page']+=1
    else:
        if session['data']['book_number']+1 >= len(bible_data['books']):
            session['data']['book_number']=0
            session['data']['page']=0
            
        else:
            session['data']['book_number']+=1
            session['data']['page']=0
    session.modified = True

    
    #print(session['data']['books'][0][0])3

    return read_bible()
@app.route('/previous_chapter', methods=["GET"])
def previous_chapter():
    print("next chapter check")
    bible_data = bible_collection.find_one({}, {"_id": 0})  # Exclude MongoDB ID

    if not bible_data:
        return jsonify({"success": False, "message": "Bible data not found"}), 404
    #print(bible_data['books'][session['data']['book_number']]['chapters'])
    if(session['data']['page']>0):
        session['data']['page']-=1
    else:
        if session['data']['book_number'] == 0:
            session['data']['book_number'] = len(bible_data['books']) - 1  # Last book index
            session['data']['page'] = len(bible_data['books'][session['data']['book_number']]['chapters']) - 1  # Last chapter index
        else:
            # Otherwise, move to the last chapter of the previous book
            session['data']['book_number'] -= 1
            session['data']['page'] = len(bible_data['books'][session['data']['book_number']]['chapters']) - 1

    session.modified = True

    
    #print(session['data']['books'][0][0])3

    return read_bible()




@app.route('/send_verses', methods=["POST"])
def send_verses():
    verses = request.json.get('verses', [])
    notes_text = request.json.get('notes_text', "")

    # Fetch the Bible data from MongoDB
    bible_data = bible_collection.find_one({}, {"books": 1})
    
   
   

    # Iterate through each verse reference
    for verse_ref in verses:
        parts = verse_ref.rsplit(' ', 1)
        book_name = parts[0]  # "1 Corinthians"
        chapter_verse = parts[1]
        chapter, verse = chapter_verse.split(":")
        chapter = int(chapter) - 1  # MongoDB is 0-indexed
        if len(verse.split("-"))>1:
            verse1, verse2 = verse.split("-")
            print("verse1 ", verse1, " and ", verse2)

        book_data = bible_collection.find_one({"books.name": book_name})
        if not bible_data:
            print("bible_data not found")
            return jsonify({"success": False, "message": "Book not found"}), 404
        chapters = book_data['chapters']
        chapter_num = chapters.find_one({"chapter": chapter})
        if chapter_num:
            print("found chapter num")
    return jsonify({
        "message": "Verses highlighted successfully!",
        "highlighted_notes": notes_text
    })




if __name__ == '__main__':
    
    app.run(debug=True)
    




