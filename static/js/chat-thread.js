function escapeHTML(value) {
    return String(value || '').replace(/[&<>"']/g, function(char) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[char];
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('messagesList');
    const messageForm = document.getElementById('messageForm');
    const messageContent = document.getElementById('messageContent');
    const fileInput = document.getElementById('fileInput');
    const attachmentPreview = document.getElementById('attachmentPreview');
    if (!messagesContainer || !messageForm || !messageContent || !fileInput || !attachmentPreview) {
        return;
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function renderAttachmentPreview() {
        attachmentPreview.textContent = '';
        if (fileInput.files.length === 0) {
            attachmentPreview.style.display = 'none';
            return;
        }

        attachmentPreview.style.display = 'block';
        Array.from(fileInput.files).forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'attachment-item';

            const icon = document.createElement('i');
            icon.className = 'fas fa-' + (file.type.startsWith('image/') ? 'image' : 'file');
            item.appendChild(icon);
            item.appendChild(document.createTextNode(' ' + file.name + ' '));

            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.className = 'remove-attachment';
            removeButton.dataset.attachmentIndex = String(index);
            removeButton.textContent = 'x';
            item.appendChild(removeButton);

            attachmentPreview.appendChild(item);
        });
    }

    setTimeout(scrollToBottom, 100);
    fileInput.addEventListener('change', renderAttachmentPreview);

    attachmentPreview.addEventListener('click', function(event) {
        const button = event.target.closest('[data-attachment-index]');
        if (!button) {
            return;
        }

        const index = parseInt(button.dataset.attachmentIndex, 10);
        const dataTransfer = new DataTransfer();
        Array.from(fileInput.files).forEach((file, fileIndex) => {
            if (fileIndex !== index) {
                dataTransfer.items.add(file);
            }
        });
        fileInput.files = dataTransfer.files;
        fileInput.dispatchEvent(new Event('change'));
    });

    messageForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const formData = new FormData(messageForm);
        const content = messageContent.value.trim();
        if (!content && fileInput.files.length === 0) {
            return;
        }

        const sendButton = messageForm.querySelector('.send-btn');
        sendButton.disabled = true;
        sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        fetch(messageForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    window.alert('Eroare la trimiterea mesajului: ' + (data.error || 'Eroare necunoscută'));
                    return;
                }

                addMessageToUI(data.message);
                messageContent.value = '';
                fileInput.value = '';
                attachmentPreview.textContent = '';
                attachmentPreview.style.display = 'none';
                scrollToBottom();
            })
            .catch(error => {
                console.error('Error:', error);
                window.alert('Eroare la trimiterea mesajului');
            })
            .finally(() => {
                sendButton.disabled = false;
                sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
            });
    });

    messageContent.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            messageForm.dispatchEvent(new Event('submit'));
        }
    });

    messageContent.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
});

function addMessageToUI(message) {
    const messagesContainer = document.getElementById('messagesList');
    const attachments = message.attachments || [];
    const messageHTML = `
        <div class="message sent">
            <div class="message-avatar">
                <div class="small-avatar">
                    <i class="fas fa-user"></i>
                </div>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <p>${escapeHTML(message.content).replace(/\n/g, '<br>')}</p>
                    ${attachments.map(att => {
                        const attachmentUrl = escapeHTML(att.download_url || att.url || '#');
                        const attachmentName = escapeHTML(att.filename || 'attachment');
                        return att.file_type === 'image'
                            ? `<div class="message-attachments"><img src="${attachmentUrl}" alt="${attachmentName}" class="attachment-image" loading="lazy" decoding="async"></div>`
                            : `<div class="message-attachments"><a href="${attachmentUrl}" target="_blank" rel="noopener noreferrer" class="attachment-file"><i class="fas fa-file"></i> ${attachmentName}</a></div>`;
                    }).join('')}
                </div>
                <div class="message-time">
                    ${escapeHTML(message.created_at)}
                    <i class="fas fa-check"></i>
                </div>
            </div>
        </div>
    `;

    messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
}
