// script.js
$(document).ready(function(){
    // Dynamic message area state tracking
    let isFirstMessage = true;
    let messageAreaContainer = $('#messageAreaContainer');
    let welcomeMessage = $('#welcomeMessage');
    let textArea = $('#text');

    function convertBibleVersesToLinks(text) {
        var verses=[];
        const verseRegex = /(\d?\s?[A-Za-z]+(?:\s[A-Za-z]+)* \d+:\d+(-\d+)?)/g;
        var full_string = text.replace(verseRegex, function(match) {
            verses.push(match);
            let url = `https://www.biblegateway.com/passage/?search=${encodeURIComponent(match)}`;
            return `<a href="${url}" target="_blank">${match}</a>`;
        })
        .replace(/\n/g, "<br>"); 
        
        return full_string
    }
    $(document).on("click", "#journal-page a", function(e) {
        // Prevent default browser behavior inside contenteditable
        e.preventDefault();
        window.open($(this).attr("href"), "_blank");
    });

    // Dynamic message area initialization
    function initializeDynamicMessageArea() {
        // Check if there are existing messages
        if ($("#messageFormeight").children().length > 0) {
            // If messages exist, keep message area at bottom
            isFirstMessage = false;
            if (messageAreaContainer.length) {
                messageAreaContainer.removeClass('centered');
            }
            if (welcomeMessage.length) {
                welcomeMessage.addClass('hidden');
            }
        } else {
            // If no messages, center the message area
            isFirstMessage = true;
            if (messageAreaContainer.length) {
                messageAreaContainer.addClass('centered');
            }
        }
    }

    // Focus effects for dynamic message area
    textArea.focus(function() {
        if (messageAreaContainer.length) {
            messageAreaContainer.addClass('focused');
        }
    });

    textArea.blur(function() {
        if (messageAreaContainer.length) {
            messageAreaContainer.removeClass('focused');
        }
    });

    // Auto-resize textarea
    textArea.on('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Initialize dynamic behavior on page load
    initializeDynamicMessageArea();

    $(document).on("click", ".menu-btn", function (e) {
        e.stopPropagation(); // Prevent click from bubbling up
        // Close other dropdowns
        $(".menu-dropdown").not($(this).siblings(".menu-dropdown")).hide();
        // Toggle this one
        $(this).siblings(".menu-dropdown").toggle();
    });
    
    $(document).on("click", function () {
        $(".menu-dropdown").hide();
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
        
        // Reset textarea height
        textArea.css('height', 'auto');
        
        // Handle dynamic message area transition
        if (isFirstMessage && rawText.trim()) {
            // Hide welcome message if it exists
            if (welcomeMessage.length) {
                welcomeMessage.addClass('hidden');
            }
            
            // Move message area to bottom with smooth transition
            setTimeout(() => {
                if (messageAreaContainer.length) {
                    messageAreaContainer.removeClass('centered');
                }
            }, 300);
            
            isFirstMessage = false;
        }
        
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
            if (data.redirect) {
                const alertHtml = `
                    <div class="d-flex justify-content-start mb-4">
                        <div class="msg_cotainer alert-message">
                            You've reached your trial limit. Please <a href="${data.url}" class="alert-link">log in</a> or sign up to continue.
                        </div>
                    </div>`;
                $("#messageFormeight").append(alertHtml);
                
                var messageFormeight = $("#messageFormeight")[0];
                messageFormeight.scrollTop = messageFormeight.scrollHeight;

                return;
            }
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
            function typeText(element, text, index = 0, speed = -4) {
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
        var updatedNotes = $("#notesHistory").val();
        $.ajax({
            type: "POST",
            url: "/submit_notes",
            data: { notes: updatedNotes },
            success: function(response) {
                if (response.success && response.updated_notes) {
                    Swal.fire({
                        title: '✅ Notes Saved!',
                        text: 'Your Bible notes were submitted successfully.',
                        icon: 'success',
                        confirmButtonText: 'OK'
                    });

                    $("#notesHistory").val("");  // Clear the notes history
                    
                    // Clear existing notes first
                    var journalContent = $("#journal-content").detach();

                    journalContent.empty();
                    
                    // Add all notes including the new one
                    response.updated_notes.forEach(function(note) {
                        var newNoteHtml = createNoteElement(note);
                        $("#journal-content").append(newNoteHtml);
                    });

                    $("<div style='display:none'></div>").append(journalContent).appendTo("body");
                    
                    $("#journal-header").after(journalContent);
                   
                } else {
                    Swal.fire({
                        title: '❌ Error occured',
                        text: 'Sorry you are unabled to submit notes.',
                        icon: 'error',
                        confirmButtonText: 'OK'
                    });

                }
        },
        error: function(xhr, status, error) {
            console.log("Error:", error);

            let msg = "You must log in or sign up!";

            // Custom message for 401 (not logged in)
            if (xhr.status === 401) {
                msg = "You are not logged in. Please log in to submit notes.";
            }

            Swal.fire({
                title: '❌ Error',
                text: msg,
                icon: 'error',
                confirmButtonText: 'OK'
            });
                    



            
        }
        });
    });

    function createNoteElement(note) {
        // Create the main note container
        var noteItem = $('<div></div>')
         .addClass('note-item')
         .attr('data-id', note._id);
    
        // Create and add the note title
        var noteTitle = $('<span></span>')
            .addClass('note-title')
            .text((note.note || '').slice(0, 30));
    
         // Create the menu container
        var noteMenu = $('<div></div>').addClass('note-menu');
    
        // Create menu button
        var menuBtn = $('<div></div>')
            .addClass('menu-btn')
            .append($('<i></i>').addClass('fas fa-trash-alt'));
    
        // Create dropdown menu
        var menuDropdown = $('<div></div>')
            .addClass('menu-dropdown').append($('<button></button>').addClass('delete-note').text('Delete'));
    
        // Assemble the menu
        noteMenu.append(menuBtn).append(menuDropdown);
    
        // Assemble the complete note item
        noteItem.append(noteTitle).append(noteMenu);
    
        return noteItem;
    }

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

    $(document).on('click', '.note-item', function() {
        $('.note-item').removeClass('selected');
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
                    // Hide chat and show journal
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
    $(document).on("click", ".delete-note", function () {
        var noteId = $(this).closest('.note-item').data('id');

        Swal.fire({
            title: 'Are you sure?',
            text: "This note will be permanently deleted.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, delete it!',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                $.ajax({
                    type: "POST",
                    url: "/delete_note",
                    data: JSON.stringify({ id: noteId }),
                    contentType: "application/json",
                    success: function (response) {
                        $("div.note-item[data-id='" + noteId + "']").remove();
                        $("#journal-content").removeClass('collapsed');


                        Swal.fire({
                            icon: 'success',
                            title: 'Deleted!',
                            text: 'Your note was successfully deleted.',
                            confirmButtonColor: '#3085d6'
                        });
                    },
                    error: function (xhr, status, error) {
                        console.log("Error:", error);
                        Swal.fire({
                            icon: 'error',
                            title: 'Oops!',
                            text: 'There was an error deleting the note.',
                            confirmButtonColor: '#d33'
                        });
                    }
                });
            } else {
                console.log("User cancelled deletion.");
            }
        });
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

   $("#journal-header").on("click", function() {
        const isLoggedIn = $("#user-status").data("logged-in") === "true";

     



        var content = $("#journal-content");
        var arrow = $(this).find("span");
        
        // Check if the dropdown is currently collapsed (arrow pointing right)
        const isCollapsed = content.hasClass("collapsed");
        
        // Only fetch notes if we're expanding the dropdown (arrow will point down)
        
        fetchLatestNotes();
        
        
        // Toggle the collapsed state
        content.toggleClass("collapsed");
        arrow.css("transform", isCollapsed ? "rotate(0deg)" : "rotate(-90deg)");
    });

    function fetchLatestNotes() {
        $.ajax({
            type: "GET",
            url: "/get_latest_notes",
            success: function(response) {
                if(response.redirect){
                       
                        window.location.href = "/login?form=login";
                        return;
                }
                if (response.success) {
                    // Clear existing notes
                    console.log("fetch LATEST NOTES");
                  
                    console.log("go pass the login")
                    $("#journal-content").empty();
                    
                    // Add all notes including any new ones
                    response.notes.forEach(function(note) {
                        var noteHtml = createNoteElement(note);
                        $("#journal-content").append(noteHtml);
                    });
                }
            },
            error: function(xhr, status, error) {
                
                console.log("Error fetching notes:", error);
            }
        });
    }

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

   $(document).ready(function() {
        $("#sign-out").on("click", function(e){
            e.preventDefault();

            $.ajax({
                type: "POST",
                url: "/logout",
                success: function(response){
                    console.log("Successfully signed out");
                    window.location.href = "/login";
                },
                error: function(xhr, status, error) {
                    console.log("Error:", error);
                }
            });
        });
    });

    // Function to reset to center state (for testing or clearing chat)
    function resetMessageAreaToCenter() {
        isFirstMessage = true;
        if (messageAreaContainer.length) {
            messageAreaContainer.addClass('centered');
        }
        if (welcomeMessage.length) {
            welcomeMessage.removeClass('hidden');
        }
        $("#messageFormeight").empty();
    }

    // Expose reset function globally if needed
    window.resetMessageAreaToCenter = resetMessageAreaToCenter;

     const placeholders = [
        "What would you like to know about the Bible?",
        "Ask a question about a Bible verse...",
        "Type a topic like 'faith', 'hope', or 'Genesis 1'...",
        "Curious about Jesus' parables? Ask away!",
        "Need help understanding a scripture?",
        "Would you like me to create a devotional for you?"

    ];

    let index = 0;

    setInterval(function () {
        if ($("#text").val() === "") {
            $("#text").attr("placeholder", placeholders[index]);
            index = (index + 1) % placeholders.length;
        }
    }, 3000); // Change every 3 seconds
});

