    $(document).ready(function() {       
        var currentlySelectedConversationId = null;
        let knownConversationIds = new Set();
        let unreadConversations = new Set();
        let unreadMessageCounts = {};
    
        function initializeUnreadConversations() {
            const storedUnread = localStorage.getItem('unreadConversations');
            if (storedUnread) {
                unreadConversations = new Set(JSON.parse(storedUnread));
            }
        }
    
        function saveUnreadConversations() {
            localStorage.setItem('unreadConversations', JSON.stringify([...unreadConversations]));
        }
    
        function markConversationAsUnread(conversationId) {
            unreadConversations.add(conversationId);
            saveUnreadConversations();
        }
    
        function markConversationAsRead(conversationId) {
            unreadConversations.delete(conversationId);
            saveUnreadConversations();
        }
    
        function updateUnreadMessageCount(conversationId, count) {
            unreadMessageCounts[conversationId] = count;
            saveUnreadMessageCounts();
        }
    
        function saveUnreadMessageCounts() {
            localStorage.setItem('unreadMessageCounts', JSON.stringify(unreadMessageCounts));
        }
    
        function loadUnreadMessageCounts() {
            const stored = localStorage.getItem('unreadMessageCounts');
            if (stored) {
                unreadMessageCounts = JSON.parse(stored);
            }
        }
    
        function handleConversationClick(conversationId) {
            currentlySelectedConversationId = conversationId;
            loadConversation(conversationId);
            
            $('.email-item').removeClass('active');
            const $clickedItem = $(`.email-item[data-conversation-id="${conversationId}"]`);
            $clickedItem.addClass('active').removeClass('new-email unread');
            $clickedItem.find('.unread-badge').remove();
            
            markConversationAsRead(conversationId);
            updateUnreadMessageCount(conversationId, 0);
        }
        
        $(document).on('click', '.email-item', function(e) {
            e.preventDefault();
            var conversationId = $(this).data('conversation-id');
            handleConversationClick(conversationId);
        });
    
        // Handle reply form submission
        $(document).on('click', '.send-reply-btn', function(e) {
            e.preventDefault();
            var $replyForm = $(this).closest('.email-reply');
            var $textarea = $replyForm.find('textarea');
            var replyContent = $textarea.val();
        
            if (!replyContent.trim()) {
                alert('Please enter a reply before sending.');
                return;
            }
        
            // Get the CSRF token
            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            const csrftoken = getCookie('csrftoken');
        
            // Gather all the necessary data
            var replyData = {
                conversation_id: $replyForm.find('input[name="conversation_id"]').val(),
                recipient: $replyForm.find('input[name="recipient"]').val(),
                subject: $replyForm.find('input[name="subject"]').val(),
                last_email_id: $replyForm.find('input[name="last_email_id"]').val(),
                sendOrRec: $replyForm.find('input[name="sendOrRec"]').val(),
                body: replyContent
            };
        
            $.ajax({
                url: `/frontend/reply-send-tracked-email/`,
                type: 'POST',
                data: replyData,
                headers: {
                    'X-CSRFToken': csrftoken
                },
                success: function(response) {
                    if (response.status === 'success') {
                        // Clear the textarea after successful submission
                        $textarea.val('');
                        // Reload the conversation to show the new reply
                        loadConversation(replyData.conversation_id);
                    } else {
                        alert('Error: ' + response.message);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("An error occurred: " + error);
                    alert("An error occurred while sending the reply. Please try again.");
                }
            });
        });
    
        function formatDate(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const yesterday = new Date(now);
            yesterday.setDate(now.getDate() - 1);
            yesterday.setHours(0, 0, 0, 0);
        
            const timeString = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
            if (date >= new Date(now.setHours(0, 0, 0, 0))) {
                return `Today at ${timeString}`;
            } else if (date >= yesterday) {
                return `Yesterday at ${timeString}`;
            } else if (date >= new Date(now.setDate(now.getDate() - 6))) {
                return `${date.toLocaleDateString([], { weekday: 'long' })} at ${timeString}`;
            } else if (date.getFullYear() === now.getFullYear()) {
                return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ` at ${timeString}`;
            } else {
                return date.toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' }) + ` at ${timeString}`;
            }
        }
    
        function loadConversation(conversationId) {
            $.ajax({
                url: `/frontend/conversations/${conversationId}/`,
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    updateConversationView(data);
                    currentlySelectedConversationId = conversationId;
                    
                    // Reset unread count for this conversation
                    resetConversationUnreadCount(conversationId);
                    
                    // Update the conversation list to reflect changes
                    pollForNewConversations();
                },
                error: function(xhr, status, error) {
                    console.error("An error occurred: " + error);
                    updateConversationView({}); // This will show the error message
                }
            });
        }
    
        function fetchEmails(buttonPressed=false) {
            $.ajax({
                url: `/frontend/fetch-emails/`,
                type: 'POST',
                dataType: 'json',
                success: function(response) {
                    if (response.status === 'success') {
                        console.log("Fetching emails every 30 seconds");
                        if (buttonPressed){
                            alert('Fetched ' + response.new_emails_count + ' new emails');
                        }
                        if (response.new_emails_count > 0) {
                            var activeConversationId = $('.email-item.active').data('conversation-id');
                            if (activeConversationId) {
                                loadConversation(activeConversationId);
                            }
                            pollForNewConversations();
                        }
                    } else {
                        alert('Error: ' + response.message);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("An error occurred: " + error);
                    alert("An error occurred while fetching emails. Please try again.");
                }
            });
        }
        
        $('.compose-emails-btn').click(function(e) {
            e.preventDefault();
            window.open('/frontend/compose/', '_blank');
            //composeEmails(true);
            //fetchEmails(true);
        });
    
        // Object to store reply form content for each conversation
        let replyFormContents = {};
        
        function updateConversationView(data) {
            var $emailContent = $('.email-content');
            
            if (data.conversation) {
                var headerHtml = `
                    <div class="email-header">
                    <h2 class="email-subject">${data.conversation.subject}</h2>
                    <div class="email-meta">
                    <span class="email-participants">Participants: ${data.conversation.participants.join(", ")}</span>
                    </div>
                    </div>
                `;
                
                var messagesHtml = '<div class="email-messages">';
                
                data.conversation.messages.forEach(function(message) {
                    var formattedTime = formatDate(message.timestamp);
                    var messageClass = message.sendOrRec === 'send' ? 'message sent' : 'message received';
                    
                    messagesHtml += `
                        <div class="${messageClass}">
                        <span class="message-sender">${message.sender}</span>
                        <p class="message-content">${message.content}</p>
                        <span class="message-time">${formattedTime}</span>
                        </div>
                    `;
                });
                
                messagesHtml += '</div>';
                
                var replyFormHtml = `
                    <div class="email-reply">
                        <input type="hidden" name="conversation_id" value="${data.conversation.id}">
                        <input type="hidden" name="recipient" value="${data.recipient_email}">
                        <input type="hidden" name="subject" value="Re: ${data.conversation.subject}">
                        <input type="hidden" name="last_email_id" value="${data.last_email_id}">
                        <input type="hidden" name="sendOrRec" value="${data.sendOrRec}">
                        <textarea placeholder="Type your reply here..."></textarea>
                        <button class="send-reply-btn">Send Reply</button>
                    </div>
                `;
        
                $emailContent.html(headerHtml + messagesHtml + replyFormHtml);
        
                // Scroll to the bottom of the conversation
                var $emailMessages = $('.email-messages');
                $emailMessages.scrollTop($emailMessages[0].scrollHeight);
                
            } else {
                $emailContent.html(`
                    <div class="email-header">
                        <h2 class="email-subject">Error</h2>
                    </div>
                    <div class="email-messages">
                        <p>The selected conversation could not be loaded.</p>
                    </div>
                `);
            }
        }
    
        function updateConversationList(conversations) {
            var $emailList = $('.email-list');
            
            if (conversations && conversations.length > 0) {
            
                // Store the ID of the conversation item being hovered, if any
                var hoveredItemId = null //$emailList.find('.email-item:hover').data('conversation-id');
                
                conversations.sort((a, b) => new Date(b.last_updated) - new Date(a.last_updated));
                
                $emailList.empty();
                
                conversations.forEach(function(conversation) {
                    var isNew = conversation.is_new;
                    var isActive = conversation.id == currentlySelectedConversationId;
                    var unreadCount = conversation.unread_count || 0;
                    
                    var $existingItem = $emailList.find(`[data-conversation-id="${conversation.id}"]`);
                    var isHovered = conversation.id === hoveredItemId;
                    
                    var unreadClass = (!isActive && unreadCount > 0) ? 'unread' : '';
                    
                    var tags = ["Work", "Important", "Meeting", "personal", "budget"];
                    const numOfTags = Math.floor(Math.random() * tags.length) + 1;
                    const shuffledTags = tags.sort(() => 0.5 - Math.random());
                    tags = shuffledTags.slice(0, numOfTags);
                    
                    if (conversation.tags) {
                        tags = conversation.tags.map(tag => `<span class="tag ${tag}">${tag}</span>`).join('');
                    }
                    tags = tags.map(tag => `<span class="tag ${tag}">${tag}</span>`).join('');
                    
                    // NEED TO FIX participants as participants[0] can be a sender or receiver depending upon if the first email was MO or MT

                    var emailItemHtml = `
                        <div class="email-item ${isNew ? 'new-email' : ''} ${unreadClass} ${isActive ? 'active' : ''}" data-conversation-id="${conversation.id}">
                            <div class="email-item-content">
                                <div class="email-sender">${conversation.participants[0]}</div>
                                <div class="email-subject">${conversation.subject}</div>
                                <div class="email-preview">${conversation.preview || ''}</div>
                                <div class="email-tags">${tags}</div>
                            </div>
                            <div class="email-time">${formatDate(conversation.last_updated)}</div>
                            ${(!isActive && unreadCount > 0) ? `<span class="unread-badge">${unreadCount}</span>` : ''}
                        </div>
                    `;
                    if ($existingItem.length) {
                        $existingItem.replaceWith($(emailItemHtml));
                    } else {
                        $emailList.append($(emailItemHtml));
                    }
                    
                    // If the conversation is active, reset its unread count
                    if (isActive && unreadCount > 0) {
                        resetConversationUnreadCount(conversation.id);
                    }
                });
    
                // Remove conversations that no longer exist
                $emailList.find('.email-item').each(function() {
                    var id = $(this).data('conversation-id');
                    if (!conversations.some(c => c.id === id)) {
                        $(this).remove();
                        unreadConversations.delete(id);
                        delete unreadMessageCounts[id];
                        saveUnreadConversations();
                        saveUnreadMessageCounts();
                    }
                });
            
                $('#email-list-placeholder').hide(); // Hide the placeholder
            } else if ($emailList.children().length === 0 || $emailList.children().length === 1 && $emailList.children().first().is('#email-list-placeholder')) {
                // If the list is empty or only contains the placeholder, show the placeholder
                $('#email-list-placeholder').show().text('No emails to display.');
            }
        }
        
        function resetConversationUnreadCount(conversationId) {
            $.ajax({
                url: `/frontend/conversations/reset_conversation_unread/${conversationId}/`,
                method: 'POST',
                success: function(response) {
                    if (response.success) {
                        console.log(`Unread count reset for conversation ${conversationId}`);
                    } else {
                        console.error('Failed to reset unread count');
                    }
                },
                error: function(xhr, status, error) {
                    console.error(`Error resetting unread count: ${error}`);
                }
            });
        }

           
        function initializeConversations() {
            pollForNewConversations(true); // true flag indicates it's the initial poll
        }
        
        let lastPollTime = 0; // Initialize to 0 to ensure first poll always updates
        
        function pollForNewConversations(isInitialPoll = false) {
            $.ajax({
                url: `/frontend/get-latest-conversations/`,
                type: 'GET',
                dataType: 'json',
                success: function(response) {
                    if (response.conversations && response.conversations.length > 0) {
                        let mostRecentUpdate = Math.max(...response.conversations.map(conv => new Date(conv.last_updated).getTime()));
                        let hasUpdates = isInitialPoll || mostRecentUpdate > lastPollTime;
                               
                        if (hasUpdates) {
                            updateConversationList(response.conversations); // Always update the list
                            console.log('Conversation list updated');
                            lastPollTime = mostRecentUpdate;
                        } else {
                            console.log('No new updates');
                        }
                    } else {
                        updateConversationList([]); // Update with an empty array to show the placeholder
                        console.log('No conversations available');
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error fetching conversations: " + error);
                    updateConversationList([]); // Show placeholder on error
                },
            });
        }
        
        function syncUnreadStatus() {
            $.ajax({
                url: `/frontend/conversations/sync_unreadlist/`,                
                type: 'GET',
                success: function(response) {
                    console.log("Syncing unread status");
                    unreadConversations = new Set(response.unread_conversations);
                    saveUnreadConversations();
                    updateConversationList(response.conversations);
                },
                error: function(xhr, status, error) {
                    console.error("Error syncing unread status: " + error);
                }
            });
        }
    
        // Initialize
        loadUnreadMessageCounts();
        initializeUnreadConversations();
        $('.conversation-item').each(function() {
            knownConversationIds.add($(this).data('conversation-id'));
        });
        
        initializeConversations();
        pollForNewConversations(true);
        // Poll for updates every 10 seconds
        setInterval(pollForNewConversations, 10000);  // Poll every 10 seconds    
        // Fetch emails periodically fromt he imap server and update list
        setInterval(fetchEmails, 30000);
        // Sync unread status periodically
        setInterval(syncUnreadStatus, 60000); // Every 1 minute
    });
