// script.js
$(document).ready(function(){
    function convertBibleVersesToLinks(text) {
        var verses=[];
        const verseRegex = /(\d?\s?[A-Za-z]+(?:\s[A-Za-z]+)* \d+:\d+(-\d+)?)/g;
        var full_string = text.replace(verseRegex, function(match) {
            verses.push(match);
            let url = `https://www.biblegateway.com/passage/?search=${encodeURIComponent(match)}`;
            return `<a href="${url}" target="_blank">${match}</a>`;
        })
        .replace(/\n/g, "<br>"); 
        $.ajax({
            type: "POST",
            url: "/send_verses",  // Adjust this URL to the route where you want to send the data
            contentType:"application/json",
            data: JSON.stringify({ verses: verses }),
            success: function(response) {
                // Handle success
                console.log("Verses sent successfully!", response);
            },
            error: function(xhr, status, error) {
                // Handle error
                console.log("Error sending verses:", error);
            }
        });
    
        
        
        return full_string

    }

    
    

    $(".menu-btn").on("click", function(event) {
        event.stopPropagation();  // Prevent the click event from propagating to the document
        let $dropdown = $(this).siblings(".menu-dropdown");
        $dropdown.toggle();  // Toggle the dropdown visibility

        $(".menu-dropdown").not(dropdown).hide();
        $dropdown.toggle();
    });

    // Function to close the dropdown
    function closeDropdown(event) {
        // Check if the click is outside the dropdown or button
        if (!$(event.target).closest(".menu-btn").length && !$(event.target).closest(".menu-dropdown").length) {
            $(".menu-dropdown").hide();  // Hide the dropdown
            $(document).off("click", closeDropdown);  // Remove the document-level event listener
        }
    }

    $("#messageArea").on("submit", function (event) {
        event.preventDefault(); // Prevent form from refreshing the page
        
        var rawText = $("#text").val(); // Get user input
        $("#text").val(""); // Clear input field
        // Display user message in the chat window
        var userHtml = `
            <div class="d-flex justify-content-end mb-4">
                <div class="msg_cotainer_send">
                    ${rawText}
                    <span class="msg_time_send"></span>
                </div>
                
            </div>`;

        $("#messageFormeight").append(userHtml); // Append user message
        var messageFormeight = $("#messageFormeight")[0];
        messageFormeight.scrollTop = messageFormeight.scrollHeight;
        // Send message to backend via AJAX
        $.ajax({
            data: { msg: rawText }, // Send user input in POST request
            type: "POST",
            url: "/get", // Ensure this matches your Flask route URL
        }).done(function (data) {
            console.log("Data:", data);

            // Bot message container (empty at first)
            var botHtml = `
                <div class="d-flex justify-content-start mb-4">
                    
                    <div class="msg_cotainer typing-effect">
                        <span class="typing-indicator">...</span>
                        <span class="msg_time"></span>
                    </div>
                </div>`;

            // Append bot message container
            var $botMessage = $(botHtml);
            $("#messageFormeight").append($botMessage);
            
            // Typing animation function
            function typeText(element, text, index = 0, speed = 1) {
                if (index === 0) {
                    element.find(".typing-indicator").remove(); // Remove typing indicator
                    element.html(""); // Clear previous content before typing starts
                }
            
                let formattedText = text.replace(/\n/g, "<br>"); // Ensure all newlines convert to <br>
            
                if (index < formattedText.length) {
                    let nextChar = formattedText[index];
                    
                    // Handle <br> tags separately to prevent breaking the HTML structure
                    if (nextChar === "<" && formattedText.substring(index, index + 4) === "<br>") {
                        element.append("<br>");
                        setTimeout(() => typeText(element, formattedText, index + 4, speed), speed);
                    } else {
                        element.append(nextChar);
                        setTimeout(() => typeText(element, formattedText, index + 1, speed), speed);
                    }
                    var messageFormeight = $("#messageFormeight")[0];
                    messageFormeight.scrollTop = messageFormeight.scrollHeight;
                }
            }
            

            // Start typing effect
            var $typingContainer = $botMessage.find(".msg_cotainer");
            typeText($typingContainer, data.response);

            
            



           


            if (data.notes_history) {
                console.log('Notes History:', data.notes_history);  // Debugging output
                var formattedNotes = data.notes_history.join('\n\n');  
                
                $("#notesHistory").val(formattedNotes);  // Update the textarea
            } else {
                console.log('No notes history available');
                $("#notesHistory").val('No additional notes history available.');
            }
        });




      




        
    });

    $("#editButton").on("click", function() {
        // Make the notes textarea editable
        $("#notesHistory").prop("readonly", false);
        $("#saveButton").show();  // Show Save button
                $("#submitButton").show();  // Show Submit button
                $("#editButton").hide(); 
        $("#saveButton").show();  // Show the save button
    });

    // When the user clicks the 'Save' button
    $("#saveButton").on("click", function() {
        // Get the updated notes content
        var updatedNotes = $("#notesHistory").val();
        console.log(updatedNotes);
        // Send the updated notes to the backend via an AJAX POST request
        $.ajax({
            type: "POST",
            url: "/update_notes",  // Ensure this matches your Flask route
            data: 
            { notes: updatedNotes },  // Send the updated notes content to the backend
            success: function(response) {
                console.log(response.message);  // Log the success message from the server
                $("#saveButton").hide();  // Hide the 'Save' button
                $("#editButton").show();  // Show the 'Edit' button again
                $("#notesHistory").prop("readonly", true);  // Make the notes textarea readonly again
            },
            error: function(xhr, status, error) {
                console.log("Error:", error);  // Log any errors that occur
            }
        });
    });

    $("#submitButton").on("click", function() {
        var updatedNotes = $("#notesHistory").val();  // Get the current notes content
        $.ajax({
            type: "POST",
            url: "/submit_notes",  // The route to handle submission
            data: { notes: updatedNotes},
            success: function(response) {
                if (response.success) {
                    alert("Notes submitted successfully!");
                    $("#notesHistory").val("");  // Clear the notes history
                   
                
                    if(response.updated_notes) {
                        var newNoteHtml = `<div class="note-item">${response.updated_notes[-1]}</div>`;
                        $("#journal-content").append(newNoteHtml);  // Append to #journal-content

                        // Optional: Ensure the content is visible
                        $("#journal-content").removeClass("collapsed");
                        $("#journal-header span").css("transform", "rotate(0deg)");
                    } else {
                        alert("No notes content returned!");
                    } // Reset any rotation of arrow
                } else {
                    alert("There was an issue submitting the notes.");
                }
                
            },
            error: function(xhr, status, error) {
                console.log("Error:", error);
            }
        });
    });


    $("#toggleNotesButton").on("click", function() {
         // Get the current notes content
        $.ajax({
            type: "GET",
            url: "/submit_notes",  // The route to handle submission
            data: { notes: updatedNotes},
            success: function(response) {
                console.log("yay")
                var formattedNotes = response.notes_content.join('\n\n');  // Join items with a newline
                
                // Fill the 'notesHistory' text box with the formatted notes (each item on a new line)
                $("#journal-page").val(formattedNotes);

            },
            error: function(xhr, status, error) {
                console.log("Error:", error);
            }
        });
    });



    $('.note-item').on('click', function() {
        // Get the note ID from the 'data-id' attribute
        var noteId = $(this).data('id');
        console.log("Note ID clicked: " + noteId); // Debugging log
        $(this).addClass("selected");
        // Call the scrollToNote function with the note ID
        scrollToNote(noteId);
    });
    $('#bible-button').on('click', function() {
        // Get the note ID from the 'data-id' attribute
        $(".chat").hide()
        $("#journal-page").hide()
        $("#bible-container").show();
        $("#bible-page").show();
        $.ajax({
            type: "GET",
            url: "/view_bible",  // The route to handle submission
            
            success: function(response) {
                console.log('Bible response:', response.data);
                $('#bible-page').html(response.data)
                $('#bible-chapter-title').html(response.current_chapter)
            },
            error: function(xhr, status, error) {
                console.log("Error:", error);
            }
        });
        
       
        
        
    });

    function scrollToNote(noteId) {
        console.log("Fetching note with ID: " + noteId); // Debugging log

        $.ajax({
            url: '/get_note/' + noteId,  // Make an AJAX call to fetch the note content by ID
            method: 'GET',
            success: function(response) {
                console.log("Fetched note content:", response);  // Debugging log
                if (response.success) {
                    console.log("Note content:", response.content);
                    // Assuming 'response.content' is the content you want to display
                    $(".chat").hide()
                    $("#bible-container").hide()
                    $("#journal-container").css({
                        'display': 'block',  // Ensure it is visible
                        'position': 'absolute',
                        'top': '0',
                        'right': '0',
                        'left': 'auto',
                        'width': '75vw',
                        'height': '100vh',
                        'background-color':'white', // Adjust opacity if needed
                        'z-index': '999',
                        'margin-left': 'auto',
                    }); // Make the journal container visible
                    var formattedNoteContent = convertBibleVersesToLinks(response.content);  // Convert Bible verses to links
                    $("#journal-page").html(formattedNoteContent);
                    $("#journal-page").css({
                        'display': 'block',
                        'width': '90%', // Adjust width to make it look better
                        'margin': '0 auto',
                        'padding': '20px',
                        'border': '1px solid #ccc',
                        'height': 'calc(100% - 20px)',
                        'font-size': '16px',
                        'top':'10',
                    });
                   
                    
                } else {
                    alert("Note content not found.");
                }
               
            },
            error: function(error) {
                console.log("Error fetching note:", error);  // Debugging log
                alert("Error loading note.");
            }
        });
    }

    $("#editButton_journal").on("click", function() {
        // Make the notes textarea editable
       
        $("#saveButton_journal").show();  // Show the save button
    });

    $("#journal-page").on("input", function(){
        
        const updatedNotes = $(this)[0].innerHTML; 
        const formattedHTML = convertBibleVersesToLinks(updatedNotes); 
        var noteId = $("#sidebar .note-item.selected").data("id");  // Example: selecting the note from sidebar
        
        console.log("save button")
        
        // Send the updated notes to the backend via an AJAX POST request
        $.ajax({
            type: "POST",
            url: "/update_note",  // The route for updating the note
            data: {
                id: noteId,
                notes: updatedNotes  // Send the updated content
            },
            success: function(response) {
                //alert("Note updated successfully!");
                 // Show the edit button
                $("#journal-page").prop("readonly", false); 
                $(this).html(formattedHTML);  // Make textarea readonly again
            },
            error: function(xhr, status, error) {
                console.log("Error:", error);
                alert("There was an error updating the note.");
            }
        });
    });

  
    

    $("#sidebar").on("click", ".delete-note", function() {
        var noteId = $(this).closest('.note-item').data('id');
        if(confirm("Are you sure you want to delete this note?")) {
            $.ajax({
                type: "POST",
                url: "/delete_note",
                
                data: JSON.stringify({ id: noteId }),  // Send data as JSON
                contentType: "application/json",
                success: function(response) {
                    $("div.note-item[data-id='" + noteId + "']").remove();
                    alert("Note deleted successfully!");
                },
                error: function(xhr, status, error) {
                    console.log("Error:", error);
                    alert("There was an error deleting the note.");
                }
            });
        }else{
            console.log("Not working")
        }
    });
    $("#toggleSidebar").on("click", function () {
        $("#sidebar").toggleClass("sidebar-collapsed");
        if ($('#sidebar').hasClass('sidebar-collapsed')) {
            $('.card').addClass('sidebar-collapsed-state'); 
            $('#sidebar .note-item').hide();  // Hide note items
            $('#sidebar #notesHistoryHeader').hide();  // Hide notes history header
            $('#sidebar #notesHistoryContent').hide();  // Hide notes history content
            $('#sidebar #journal-header').hide();  // Hide journal header
            $('#sidebar #journal-content').hide();  // Hide journal content
            $('#sidebar h2').hide(); 
        }else {
            $('.card').removeClass('sidebar-collapsed-state'); 
            $('#sidebar .note-item').show();  // Show note items
            $('#sidebar #notesHistoryHeader').show();  // Show notes history header
            $('#sidebar #notesHistoryContent').show();  // Show notes history content
            $('#sidebar #journal-header').show();  // Show journal header
            $('#sidebar #journal-content').show();  // Show journal content
            $('#sidebar h2').show();
        }
        
        
    });

    $("#notesHistoryHeader").on("click", function () {
        var content = $("#notesHistoryContent");
        var arrow = $(this).find("span");
        $("#journal-container").hide()
        $("#journal-page").hide();
        $("#bible-container").hide()
        $("#bible-page").hide();
        $(".chat").show();
        content.toggleClass("collapsed");
        arrow.css("transform", content.hasClass("collapsed") ? "rotate(-90deg)" : "rotate(0deg)");
    });

    $("#journal-header").on("click", function () {
        var content = $("#journal-content");
        var arrow = $(this).find("span");

        content.toggleClass("collapsed");
        arrow.css("transform", content.hasClass("collapsed") ? "rotate(-90deg)" : "rotate(0deg)");
    });
    
    $("#bible-header").on("click", function () {
        var content = $("#bible-item");
        var arrow = $(this).find("span");


        content.toggleClass("collapsed");
        arrow.css("transform", content.hasClass("collapsed") ? "rotate(-90deg)" : "rotate(0deg)");
        
    });

    $("#right-arrow").on("click", function(){
        $.ajax({
            type: "GET",
            url: "/next_chapter",  // The route to handle submission
            
            success: function(response) {
                $('#bible-page').html(response.data)
                $('#bible-chapter-title').html(response.current_chapter)
            },
            error: function(xhr, status, error) {
                console.log("Error:", error);
            }
        });
    });

    $("#left-arrow").on("click", function(){
        $.ajax({
            type: "GET",
            url: "/previous_chapter",  // The route to handle submission
            
            success: function(response) {
                $('#bible-page').html(response.data)
                $('#bible-chapter-title').html(response.current_chapter)

            },
            error: function(xhr, status, error) {
                console.log("Error:", error);
            }
        });
    });




});

