// Favorites functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize favorites functionality
    initializeFavorites();
    
    function initializeFavorites() {
        // Handle remove favorite buttons
        document.querySelectorAll('.remove-favorite-btn').forEach(btn => {
            btn.addEventListener('click', handleRemoveFavorite);
        });
        
        // Handle favorite toggle buttons (for listing pages)
        document.querySelectorAll('.favorite-btn, #favorite-detail-btn').forEach(btn => {
            btn.addEventListener('click', handleToggleFavorite);
        });
    }
    
    // Handle removing a favorite from the favorites list page
    function handleRemoveFavorite(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.currentTarget;
        const favoriteId = btn.dataset.favoriteId;
        
        if (!favoriteId) {
            showToast('Eroare: ID favorit nu a fost găsit', 'error');
            return;
        }
        
        // Confirm removal
        if (!confirm('Ești sigur că vrei să elimini acest anunț din favorite?')) {
            return;
        }
        
        // Show loading state
        btn.classList.add('loading');
        btn.innerHTML = '<i class="fas fa-spinner"></i>';
        
        // Make request to remove favorite
        fetch(`/favorites/remove/${favoriteId}/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.ok) {
                // Remove the listing card with animation
                const listingCard = btn.closest('.listing-card');
                listingCard.style.transform = 'scale(0)';
                listingCard.style.opacity = '0';
                
                setTimeout(() => {
                    listingCard.remove();
                    
                    // Update page if no more favorites
                    const remainingCards = document.querySelectorAll('.listing-card');
                    if (remainingCards.length === 0) {
                        location.reload();
                    }
                }, 300);
                
                showToast('Anunțul a fost eliminat din favorite', 'success');
            } else {
                throw new Error('Network response was not ok');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('A apărut o eroare la eliminarea din favorite', 'error');
            
            // Reset button state
            btn.classList.remove('loading');
            btn.innerHTML = '<i class="fas fa-trash"></i>';
        });
    }
    
    // Handle toggling favorites (for use in listing detail/list pages)
    function handleToggleFavorite(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.currentTarget;
        const listingId = btn.dataset.listing || btn.dataset.listingId;
        
        if (!listingId) {
            showToast('Eroare: ID anunț nu a fost găsit', 'error');
            return;
        }
        
        // Check if user is logged in
        if (!isUserLoggedIn()) {
            showToast('Trebuie să te autentifici pentru a adăuga la favorite', 'error');
            setTimeout(() => {
                window.location.href = '/accounts/login/';
            }, 2000);
            return;
        }
        
        const csrfToken = getCSRFToken();
        if (!csrfToken) {
            showToast('Eroare: Token de securitate nu a fost găsit', 'error');
            return;
        }
        
        // Show loading state
        const originalIcon = btn.querySelector('i');
        const originalClass = originalIcon.className;
        originalIcon.className = 'fas fa-spinner fa-spin';
        btn.disabled = true;
        
        // Make AJAX request
        fetch('/favorites/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `listing_id=${listingId}`
        })
        .then(response => {
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update button state
                const icon = btn.querySelector('i');
                
                if (data.is_favorited) {
                    icon.className = 'fas fa-heart';
                    btn.classList.add('favorited');
                    btn.title = 'Elimină din favorite';
                    // Update text if it exists (detail page)
                    const textNode = Array.from(btn.childNodes).find(node => node.nodeType === Node.TEXT_NODE);
                    if (textNode) {
                        textNode.textContent = ' În favorite';
                    }
                } else {
                    icon.className = 'far fa-heart';
                    btn.classList.remove('favorited');
                    btn.title = 'Adaugă la favorite';
                    // Update text if it exists (detail page)
                    const textNode = Array.from(btn.childNodes).find(node => node.nodeType === Node.TEXT_NODE);
                    if (textNode) {
                        textNode.textContent = ' Adaugă la favorite';
                    }
                }
                
                // Update favorites count if element exists
                const favoritesCount = document.querySelector('.favorites-count');
                if (favoritesCount) {
                    favoritesCount.textContent = data.favorites_count;
                }
                
                showToast(data.message, 'success');
            } else {
                throw new Error(data.error || 'A apărut o eroare');
            }
        })
        .catch(error => {
            showToast(error.message || 'A apărut o eroare la actualizarea favoritelor', 'error');
            
            // Reset icon to original state
            originalIcon.className = originalClass;
        })
        .finally(() => {
            btn.disabled = false;
        });
    }
    
    // Utility functions
    function getCSRFToken() {
        // Try multiple methods to get CSRF token
        let token = null;
        
        // Method 1: From form input
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            token = csrfInput.value;
        }
        
        // Method 2: From meta tag
        if (!token) {
            const metaTag = document.querySelector('meta[name="csrf-token"]');
            if (metaTag) {
                token = metaTag.content;
            }
        }
        
        // Method 3: From cookie
        if (!token) {
            token = getCookie('csrftoken');
        }
        
        return token;
    }
    
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
    
    function isUserLoggedIn() {
        // Check multiple indicators of logged in state
        const userMenu = document.querySelector('.user-menu, .user-dropdown, .user-menu-toggle');
        const authLinks = document.querySelector('.auth-btn, .login-btn, .register-btn');
        const userDataAttr = document.querySelector('[data-user="authenticated"]');
        const csrfToken = getCSRFToken();
        
        // If we have a user menu or CSRF token, probably logged in
        // If we have auth buttons (login/register), probably not logged in
        const isLoggedIn = (userMenu !== null || csrfToken !== null) && authLinks === null;
        
        return isLoggedIn;
    }
    
    function showToast(message, type = 'info') {
        // Remove existing toasts
        document.querySelectorAll('.toast').forEach(toast => toast.remove());
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: #666; margin-left: 10px; cursor: pointer;">&times;</button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Show toast
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
    
    // Initialize favorites status for listing cards
    function initializeFavoritesStatus() {
        // This would be called on listing pages to show current favorite status
        const favoriteButtons = document.querySelectorAll('.favorite-btn');
        
        if (favoriteButtons.length > 0 && isUserLoggedIn()) {
            // Get all listing IDs
            const listingIds = Array.from(favoriteButtons).map(btn => 
                btn.dataset.listing || btn.dataset.listingId
            ).filter(id => id);
            
            if (listingIds.length > 0) {
                // In a real implementation, you might want to batch check favorite status
                // For now, we'll rely on the server-side template to set the initial state
            }
        }
    }
    
    // Call initialization
    initializeFavoritesStatus();
});

// Export functions for use in other scripts
window.FavoritesManager = {
    toggle: function(listingId) {
        const btn = document.querySelector(`[data-listing="${listingId}"], [data-listing-id="${listingId}"]`);
        if (btn) {
            btn.click();
        }
    },
    
    remove: function(favoriteId) {
        const btn = document.querySelector(`[data-favorite-id="${favoriteId}"]`);
        if (btn) {
            btn.click();
        }
    }
};
