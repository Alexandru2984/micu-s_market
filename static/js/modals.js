// Modal Management
document.addEventListener('DOMContentLoaded', function() {
    // Get all modal triggers
    const modalTriggers = document.querySelectorAll('[data-modal]');
    const closeBtns = document.querySelectorAll('[data-close]');
    const modals = document.querySelectorAll('.modal');

    // Function to open modal
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        }
    }

    // Function to close modal
    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = ''; // Restore scrolling
        }
    }

    // Function to close all modals
    function closeAllModals() {
        modals.forEach(modal => {
            modal.classList.remove('show');
        });
        document.body.style.overflow = '';
    }

    // Add click event listeners to modal triggers
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.getAttribute('data-modal');
            openModal(modalId);
        });
    });

    // Add click event listeners to close buttons
    closeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.getAttribute('data-close');
            closeModal(modalId);
        });
    });

    // Close modal when clicking outside of modal content
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this.id);
            }
        });
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });

    // Handle nested modal triggers (e.g., contact link in help modal)
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-modal]')) {
            e.preventDefault();
            const currentModal = e.target.closest('.modal');
            if (currentModal) {
                closeModal(currentModal.id);
            }
            const newModalId = e.target.getAttribute('data-modal');
            setTimeout(() => openModal(newModalId), 300); // Small delay for smooth transition
        }
    });
});
