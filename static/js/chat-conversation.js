// Chat Conversation JavaScript - Dynamic Height Version
document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('messagesList');
    const messageForm = document.getElementById('messageForm');
    const messageContent = document.getElementById('messageContent');
    const fileInput = document.getElementById('fileInput');
    const attachmentPreview = document.getElementById('attachmentPreview');
    const sendBtn = document.querySelector('.send-btn');
    const conversationContainer = document.querySelector('.conversation-container');
    
    // Initialize chat features
    initializeChatFeatures();
    
    function initializeChatFeatures() {
        // Setup dynamic height management
        setupDynamicHeight();
        
        // Scroll to bottom with smooth animation
        setTimeout(scrollToBottomSmooth, 100);
        
        // Add typing indicators
        setupTypingIndicator();
        
        // Add message animations
        animateExistingMessages();
        
        // Add better file upload UX
        enhanceFileUpload();
        
        // Add message status indicators
        updateMessageStatuses();
        
        // Setup window resize handler
        window.addEventListener('resize', debounce(setupDynamicHeight, 250));
    }
    
    // Dynamic height management
    function setupDynamicHeight() {
        if (!conversationContainer) return;
        
        const header = document.querySelector('header');
        const footer = document.querySelector('footer');
        const conversationHeader = document.querySelector('.conversation-header');
        const messageFormContainer = document.querySelector('.message-form-container');
        
        let availableHeight = window.innerHeight;
        
        // Subtract header height
        if (header) {
            availableHeight -= header.offsetHeight;
        }
        
        // Subtract footer height with some margin
        if (footer) {
            availableHeight -= footer.offsetHeight + 20; // 20px margin
        }
        
        // Subtract conversation header height
        if (conversationHeader) {
            availableHeight -= conversationHeader.offsetHeight;
        }
        
        // Subtract message form height
        if (messageFormContainer) {
            availableHeight -= messageFormContainer.offsetHeight;
        }
        
        // Set conversation container height
        conversationContainer.style.height = Math.max(availableHeight, 300) + 'px';
        
        // Ensure messages container takes remaining space
        if (messagesContainer) {
            const containerPadding = 32; // 2rem padding
            messagesContainer.style.height = (availableHeight - containerPadding) + 'px';
            messagesContainer.style.maxHeight = (availableHeight - containerPadding) + 'px';
        }
        
        // Scroll to bottom after height adjustment
        setTimeout(scrollToBottomSmooth, 50);
    }
    
    // Debounce function for performance
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Enhanced scroll to bottom with smooth animation
    function scrollToBottomSmooth() {
        if (messagesContainer) {
            messagesContainer.scrollTo({
                top: messagesContainer.scrollHeight,
                behavior: 'smooth'
            });
        }
    }
    
    // Setup typing indicator
    function setupTypingIndicator() {
        let typingTimer;
        const typingIndicator = createTypingIndicator();
        
        if (messageContent) {
            messageContent.addEventListener('input', function() {
                clearTimeout(typingTimer);
                showTypingIndicator(typingIndicator);
                
                typingTimer = setTimeout(() => {
                    hideTypingIndicator(typingIndicator);
                }, 1000);
            });
            
            messageContent.addEventListener('blur', function() {
                clearTimeout(typingTimer);
                hideTypingIndicator(typingIndicator);
            });
        }
    }
    
    function createTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = `
            <div class="typing-avatar">
                <div class="small-avatar">
                    <i class="fas fa-user"></i>
                </div>
            </div>
            <div class="typing-bubble">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        indicator.style.display = 'none';
        return indicator;
    }
    
    function showTypingIndicator(indicator) {
        if (messagesContainer && !messagesContainer.contains(indicator)) {
            messagesContainer.appendChild(indicator);
        }
        indicator.style.display = 'flex';
        scrollToBottomSmooth();
    }
    
    function hideTypingIndicator(indicator) {
        if (indicator && indicator.parentNode) {
            indicator.style.display = 'none';
        }
    }
    
    // Animate existing messages on load
    function animateExistingMessages() {
        const messages = document.querySelectorAll('.message');
        messages.forEach((message, index) => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                message.style.transition = 'all 0.3s ease';
                message.style.opacity = '1';
                message.style.transform = 'translateY(0)';
            }, index * 30); // Faster animation
        });
    }
    
    // Enhance file upload with better UX
    function enhanceFileUpload() {
        if (fileInput && attachmentPreview) {
            // Add drag and drop
            setupDragAndDrop();
            
            // Enhanced file preview
            fileInput.addEventListener('change', function() {
                handleFileUpload(this.files);
            });
        }
    }
    
    function setupDragAndDrop() {
        const dropZone = messageForm;
        if (!dropZone) return;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });
        
        dropZone.addEventListener('drop', handleDrop, false);
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        function highlight() {
            dropZone.classList.add('drag-over');
        }
        
        function unhighlight() {
            dropZone.classList.remove('drag-over');
        }
        
        function handleDrop(e) {
            const files = e.dataTransfer.files;
            handleFileUpload(files);
        }
    }
    
    function handleFileUpload(files) {
        if (!attachmentPreview) return;
        
        attachmentPreview.innerHTML = '';
        
        if (files.length > 0) {
            attachmentPreview.style.display = 'block';
            
            Array.from(files).forEach((file, index) => {
                const item = createFilePreviewItem(file, index);
                attachmentPreview.appendChild(item);
            });
        } else {
            attachmentPreview.style.display = 'none';
        }
    }
    
    function createFilePreviewItem(file, index) {
        const item = document.createElement('div');
        item.className = 'attachment-item';
        
        const fileIcon = file.type.startsWith('image/') ? 'image' : 'file';
        const fileSize = formatFileSize(file.size);
        
        item.innerHTML = `
            <div class="file-info">
                <i class="fas fa-${fileIcon}"></i>
                <div class="file-details">
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">${fileSize}</span>
                </div>
            </div>
            <button type="button" class="remove-attachment" onclick="removeAttachment(${index})">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add image preview for images
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const preview = document.createElement('img');
                preview.src = e.target.result;
                preview.className = 'file-preview-image';
                item.insertBefore(preview, item.firstChild);
            };
            reader.readAsDataURL(file);
        }
        
        return item;
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Update message statuses with animations
    function updateMessageStatuses() {
        const sentMessages = document.querySelectorAll('.message.sent');
        sentMessages.forEach(message => {
            const timeElement = message.querySelector('.message-time');
            if (timeElement && !timeElement.querySelector('.status-icon')) {
                const statusIcon = document.createElement('i');
                statusIcon.className = 'fas fa-check status-icon';
                timeElement.appendChild(statusIcon);
                
                // Animate icon appearance
                setTimeout(() => {
                    statusIcon.style.opacity = '1';
                    statusIcon.style.transform = 'scale(1)';
                }, 300);
            }
        });
    }
    
    // Enhanced form submission with better UX
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const content = messageContent ? messageContent.value.trim() : '';
            
            if (!content && (!fileInput || fileInput.files.length === 0)) {
                // Shake animation for empty message
                shakeElement(messageContent);
                return;
            }
            
            // Disable form with loading state
            setFormLoadingState(true);
            
            // Add sending message to UI immediately
            const tempMessage = addTemporaryMessage(content);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remove temporary message and add real one
                    if (tempMessage) tempMessage.remove();
                    addMessageToUI(data.message);
                    
                    // Clear form
                    clearForm();
                    
                    // Scroll to bottom
                    scrollToBottomSmooth();
                    
                    // Show success feedback
                    showSuccessFeedback();
                } else {
                    // Remove temporary message
                    if (tempMessage) tempMessage.remove();
                    showErrorMessage('Eroare la trimiterea mesajului: ' + (data.error || 'Eroare necunoscută'));
                }
            })
            .catch(error => {
                // Remove temporary message
                if (tempMessage) tempMessage.remove();
                console.error('Error:', error);
                showErrorMessage('Eroare la trimiterea mesajului');
            })
            .finally(() => {
                setFormLoadingState(false);
            });
        });
    }
    
    function addTemporaryMessage(content) {
        if (!messagesContainer || !content) return null;
        
        const tempMessage = document.createElement('div');
        tempMessage.className = 'message sent temporary';
        tempMessage.innerHTML = `
            <div class="message-avatar">
                <div class="small-avatar">
                    <i class="fas fa-user"></i>
                </div>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <p>${content.replace(/\n/g, '<br>')}</p>
                </div>
                <div class="message-time">
                    Trimite...
                    <i class="fas fa-clock sending-icon"></i>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(tempMessage);
        scrollToBottomSmooth();
        
        return tempMessage;
    }
    
    function setFormLoadingState(loading) {
        if (sendBtn) {
            sendBtn.disabled = loading;
            sendBtn.innerHTML = loading 
                ? '<i class="fas fa-spinner fa-spin"></i>' 
                : '<i class="fas fa-paper-plane"></i>';
        }
        
        if (messageContent) {
            messageContent.disabled = loading;
        }
    }
    
    function clearForm() {
        if (messageContent) messageContent.value = '';
        if (fileInput) fileInput.value = '';
        if (attachmentPreview) {
            attachmentPreview.innerHTML = '';
            attachmentPreview.style.display = 'none';
        }
        
        // Reset textarea height
        if (messageContent) {
            messageContent.style.height = 'auto';
        }
    }
    
    function shakeElement(element) {
        if (!element) return;
        element.classList.add('shake');
        setTimeout(() => element.classList.remove('shake'), 500);
    }
    
    function showSuccessFeedback() {
        // Brief success animation on send button
        if (sendBtn) {
            sendBtn.classList.add('success');
            setTimeout(() => sendBtn.classList.remove('success'), 200);
        }
    }
    
    function showErrorMessage(message) {
        // Simple console log instead of toast to avoid positioning issues
        console.error(message);
        
        // Optional: Add error class to form for visual feedback
        if (messageForm) {
            messageForm.classList.add('error');
            setTimeout(() => messageForm.classList.remove('error'), 2000);
        }
    }
    
    // Handle Enter key with better UX
    if (messageContent) {
        messageContent.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (messageForm) {
                    messageForm.dispatchEvent(new Event('submit'));
                }
            }
        });
        
        // Auto-resize textarea with smooth animation
        messageContent.addEventListener('input', function() {
            this.style.height = 'auto';
            const newHeight = Math.min(this.scrollHeight, 120);
            this.style.height = newHeight + 'px';
            
            // Recalculate container height when textarea changes
            setTimeout(setupDynamicHeight, 10);
        });
    }
});

function addMessageToUI(message) {
    const messagesContainer = document.getElementById('messagesList');
    if (!messagesContainer) return;
    
    const messageHTML = `
        <div class="message sent new-message">
            <div class="message-avatar">
                <div class="small-avatar">
                    <i class="fas fa-user"></i>
                </div>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <p>${message.content.replace(/\n/g, '<br>')}</p>
                    ${message.attachments ? message.attachments.map(att => 
                        att.file_type === 'image' 
                            ? `<div class="message-attachments"><img src="${att.url}" alt="${att.filename}" class="attachment-image"></div>`
                            : `<div class="message-attachments"><a href="${att.url}" target="_blank" class="attachment-file"><i class="fas fa-file"></i> ${att.filename}</a></div>`
                    ).join('') : ''}
                </div>
                <div class="message-time">
                    ${message.created_at}
                    <i class="fas fa-check status-icon"></i>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
    
    // Animate new message
    const newMessage = messagesContainer.lastElementChild;
    newMessage.style.opacity = '0';
    newMessage.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        newMessage.style.transition = 'all 0.3s ease';
        newMessage.style.opacity = '1';
        newMessage.style.transform = 'translateY(0)';
    }, 50);
    
    // Scroll to bottom
    setTimeout(() => {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

function removeAttachment(index) {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput) return;
    
    const dt = new DataTransfer();
    
    Array.from(fileInput.files).forEach((file, i) => {
        if (i !== index) {
            dt.items.add(file);
        }
    });
    
    fileInput.files = dt.files;
    fileInput.dispatchEvent(new Event('change'));
}
