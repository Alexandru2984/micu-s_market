document.addEventListener('DOMContentLoaded', function() {
    const badge = document.getElementById('unread-count');
    if (!badge) {
        return;
    }

    const unreadCountUrl = badge.dataset.unreadCountUrl;
    if (!unreadCountUrl) {
        return;
    }

    function checkUnreadMessages() {
        fetch(unreadCountUrl)
            .then(response => response.json())
            .then(data => {
                if (data.unread_count > 0) {
                    badge.textContent = data.unread_count;
                    badge.style.display = 'flex';
                } else {
                    badge.style.display = 'none';
                }
            })
            .catch(error => {
                console.log('Error checking unread messages:', error);
            });
    }

    checkUnreadMessages();
    setInterval(checkUnreadMessages, 30000);
});
