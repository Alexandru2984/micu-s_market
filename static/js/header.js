// Header functionality - Unread messages check
document.addEventListener('DOMContentLoaded', function() {
    // Check for unread messages (only for authenticated users)
    if (document.querySelector('.messages-link')) {
        function checkUnreadMessages() {
            // Get the unread count URL from the data attribute or construct it
            const unreadCountUrl = '/chat/unread-count/'; // Adjust this URL as needed
            
            fetch(unreadCountUrl)
            .then(response => response.json())
            .then(data => {
                const badge = document.getElementById('unread-count');
                if (badge) {
                    if (data.unread_count > 0) {
                        badge.textContent = data.unread_count;
                        badge.style.display = 'flex';
                    } else {
                        badge.style.display = 'none';
                    }
                }
            })
            .catch(error => {
                console.log('Error checking unread messages:', error);
            });
        }
        
        // Check initially
        checkUnreadMessages();
        
        // Check every 30 seconds
        setInterval(checkUnreadMessages, 30000);
    }
});
