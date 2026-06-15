// Real-time chat over WebSocket (Django Channels), with an AJAX fallback for
// attachments / when the WS is unavailable. Own messages are rendered on the
// server's echo (they have a real id); deduplicated by id so they don't appear twice.
(function () {
    const root = document.getElementById('chatRoot');
    if (!root) return;

    const convId = root.dataset.conversationId;
    const currentUser = root.dataset.currentUser;
    const messagesEl = document.getElementById('chatMessages');
    const typingEl = document.getElementById('chatTyping');
    const form = document.getElementById('chatForm');
    const input = document.getElementById('chatInput');
    const fileInput = document.getElementById('chatFile');
    const preview = document.getElementById('chatPreview');
    const connStatus = document.getElementById('chatConnStatus');
    const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;

    const seen = new Set(
        Array.from(messagesEl.querySelectorAll('[data-message-id]')).map((el) => el.dataset.messageId)
    );

    let socket = null;
    let reconnectDelay = 1000;
    let typingTimer = null;
    let lastTypingSent = 0;

    function escapeHTML(value) {
        return String(value ?? '').replace(/[&<>"']/g, (c) => (
            { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
        ));
    }

    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function attachmentHTML(att) {
        if (att.file_type === 'image') {
            return `<a href="${escapeHTML(att.download_url)}" target="_blank" rel="noopener noreferrer">`
                + `<img class="chat-att-img" src="${escapeHTML(att.download_url)}" alt="${escapeHTML(att.filename)}" loading="lazy"></a>`;
        }
        return `<a class="chat-att-file" href="${escapeHTML(att.download_url)}" target="_blank" rel="noopener noreferrer">`
            + `<i class="fas fa-file"></i> ${escapeHTML(att.filename)}</a>`;
    }

    function renderMessage(msg) {
        const id = String(msg.id);
        if (seen.has(id)) return;
        seen.add(id);

        const mine = msg.sender === currentUser;
        const wrap = document.createElement('div');
        wrap.className = 'chat-msg ' + (mine ? 'chat-msg--sent' : 'chat-msg--received');
        wrap.dataset.messageId = id;

        const atts = (msg.attachments || []).map(attachmentHTML).join('');
        const status = mine ? '<span class="chat-msg__status"><i class="fas fa-check"></i></span>' : '';

        wrap.innerHTML =
            '<div class="chat-msg__bubble">' +
                '<div class="chat-msg__text">' + escapeHTML(msg.content || '').replace(/\n/g, '<br>') + '</div>' +
                (atts ? '<div class="chat-msg__attachments">' + atts + '</div>' : '') +
            '</div>' +
            '<div class="chat-msg__meta"><span class="chat-msg__time">' + escapeHTML(msg.created_at || '') + '</span>' + status + '</div>';

        messagesEl.insertBefore(wrap, typingEl);
        scrollToBottom();
    }

    function markOwnAsRead() {
        messagesEl.querySelectorAll('.chat-msg--sent .chat-msg__status').forEach((el) => {
            el.innerHTML = '<i class="fas fa-check-double read"></i>';
        });
    }

    function showTyping() {
        typingEl.hidden = false;
        scrollToBottom();
        clearTimeout(typingTimer);
        typingTimer = setTimeout(() => { typingEl.hidden = true; }, 3000);
    }

    // ---- WebSocket ----
    function connect() {
        const proto = location.protocol === 'https:' ? 'wss' : 'ws';
        socket = new WebSocket(`${proto}://${location.host}/ws/chat/${convId}/`);

        socket.onopen = function () {
            reconnectDelay = 1000;
            connStatus.hidden = true;
            send({ type: 'read' });
        };

        socket.onmessage = function (event) {
            let data;
            try { data = JSON.parse(event.data); } catch (e) { return; }
            if (data.type === 'message') {
                renderMessage(data.message);
                if (document.hasFocus()) send({ type: 'read' });
            } else if (data.type === 'typing') {
                showTyping();
            } else if (data.type === 'read') {
                markOwnAsRead();
            }
        };

        socket.onclose = function () {
            connStatus.hidden = false;
            setTimeout(connect, reconnectDelay);
            reconnectDelay = Math.min(reconnectDelay * 2, 15000);
        };
    }

    function send(obj) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(obj));
            return true;
        }
        return false;
    }

    // ---- Send message ----
    async function submit() {
        const content = input.value.trim();
        const hasFiles = fileInput.files && fileInput.files.length > 0;
        if (!content && !hasFiles) return;

        // With attachments or without WS → multipart POST (fallback). Otherwise, over WS.
        if (hasFiles || !send({ type: 'message', content: content })) {
            await postFallback(content, hasFiles);
        }

        input.value = '';
        autoGrow();
        fileInput.value = '';
        preview.innerHTML = '';
        input.focus();
    }

    async function postFallback(content, hasFiles) {
        const fd = new FormData();
        fd.append('content', content || ' ');
        fd.append('csrfmiddlewaretoken', csrf);
        if (hasFiles) {
            for (const f of fileInput.files) fd.append('attachments', f);
        }
        try {
            const resp = await fetch(form.action, {
                method: 'POST',
                body: fd,
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (resp.ok) {
                const data = await resp.json();
                if (data && data.message) renderMessage(data.message);
            }
        } catch (e) { /* nothing — the user can retry */ }
    }

    // ---- UI composer ----
    function autoGrow() {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 140) + 'px';
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        submit();
    });

    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submit();
        }
    });

    input.addEventListener('input', function () {
        autoGrow();
        const now = Date.now();
        if (now - lastTypingSent > 2000) {
            lastTypingSent = now;
            send({ type: 'typing' });
        }
    });

    fileInput.addEventListener('change', function () {
        preview.innerHTML = '';
        for (const f of fileInput.files) {
            const chip = document.createElement('span');
            chip.className = 'chat-preview-chip';
            chip.innerHTML = '<i class="fas fa-paperclip"></i><span>' + escapeHTML(f.name) + '</span>';
            preview.appendChild(chip);
        }
    });

    window.addEventListener('focus', function () { send({ type: 'read' }); });

    // ---- Init ----
    scrollToBottom();
    autoGrow();
    connect();
})();
