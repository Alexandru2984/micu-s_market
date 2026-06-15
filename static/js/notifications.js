// Real-time unread-message badge over WebSocket. The server sends the count
// on connect and on every new message. The header polling script remains as a
// fallback (e.g. to decrement the counter after reading / when the WS is unavailable).
(function () {
    const badge = document.getElementById('unread-count');
    if (!badge) return; // only authenticated users have a badge

    function setCount(n) {
        if (n > 0) {
            badge.textContent = n;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }

    let delay = 1000;

    function connect() {
        const proto = location.protocol === 'https:' ? 'wss' : 'ws';
        const socket = new WebSocket(`${proto}://${location.host}/ws/notifications/`);

        socket.onopen = function () { delay = 1000; };
        socket.onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'unread') setCount(data.count);
            } catch (e) { /* ignore */ }
        };
        socket.onclose = function () {
            setTimeout(connect, delay);
            delay = Math.min(delay * 2, 15000);
        };
    }

    connect();
})();
