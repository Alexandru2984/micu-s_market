// Badge de mesaje necitite în timp real prin WebSocket. Serverul trimite numărul
// la conectare și la fiecare mesaj nou. Scriptul de polling din header rămâne ca
// fallback (ex. pentru scăderea contorului după citire / când WS-ul e indisponibil).
(function () {
    const badge = document.getElementById('unread-count');
    if (!badge) return; // doar utilizatorii autentificați au badge

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
