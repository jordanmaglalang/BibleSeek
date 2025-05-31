"""
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
    if bible_data:
        print("FOUND BIBLE DATA")

   
   

    # Iterate through each verse reference
    for verse_ref in verses:
        parts = verse_ref.rsplit(' ', 1)
        book_name = parts[0].strip()  # "1 Corinthians"
        chapter_verses = parts[1]
        print("book name is ", book_name, " and chapter verses ", chapter_verses)
        
        chapter_num, verse = chapter_verses.split(":")

        print("chapter_num is ", chapter_num, " and verse is ", verse)


        
        #chapter_num = int(chapter) - 1  # MongoDB is 0-indexed
        if len(verse.split("-"))>1:
            verse1, verse2 = map(int, verse.split("-"))
            print("verse1 ", verse1, " and ", verse2)
        else:
            verse1 = chapter_num
            verse2 = -1
        print(f"Looking for book: '{book_name}'")

        i = 0
        print
        for book in bible_data["books"]:
            
            print(book["name"])
            if book["name"] == book_name:
                print("ACTUAL BOOK ", book["name"], " and is book number ", i)
                print("digit is ", bible_data["books"][i]["chapters"][int(chapter_num)-1]["verses"][int(verse1)-1]["text"])
                
                print("verse 2 is ", verse2, " and verse 1 is ", verse1)
                length = int(verse2) - int(verse1)
               
                print("loop here, iterate ", length, " times")

                highlight_verses = []
                for a in range(length+1):
                    
                    highlight_verses.append(bible_data["books"][i]["chapters"][int(chapter_num)-1]["verses"][int(verse1)-1+a]["text"])
                print(highlight_verses)
            i+=1

        
       
        
        
    
    return jsonify({
        "message": "Verses highlighted successfully!",
        "response": highlight_verses
    })


"""