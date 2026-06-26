document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-focus-class]').forEach(element => {
        const focusClass = element.dataset.focusClass;
        element.addEventListener('focus', function() {
            element.classList.add(focusClass);
        });
        element.addEventListener('blur', function() {
            element.classList.remove(focusClass);
        });
    });

    document.querySelectorAll('[data-main-image-src]').forEach(thumbnail => {
        thumbnail.addEventListener('click', function() {
            const mainImage = document.getElementById('mainImage');
            if (!mainImage) {
                return;
            }
            mainImage.src = thumbnail.dataset.mainImageSrc;
            document.querySelectorAll('.thumbnail').forEach(item => item.classList.remove('active'));
            thumbnail.classList.add('active');
        });
    });

    document.querySelectorAll('[data-delete-image-redirect]').forEach(button => {
        button.addEventListener('click', function() {
            if (window.confirm(button.dataset.confirmMessage || 'Ești sigur că vrei să ștergi această imagine?')) {
                window.location.href = button.dataset.deleteImageRedirect;
            }
        });
    });

    const checkbox = document.getElementById('confirm-delete');
    const deleteButton = document.getElementById('delete-button');
    if (checkbox && deleteButton) {
        checkbox.addEventListener('change', function() {
            deleteButton.disabled = !checkbox.checked;
            deleteButton.classList.toggle('btn-disabled', !checkbox.checked);
            deleteButton.classList.toggle('btn-delete-final-active', checkbox.checked);
        });
    }

    const modal = document.getElementById('imageModal');
    const previewContainer = document.querySelector('[data-open-image-modal]');
    if (modal && previewContainer) {
        const modalImage = document.getElementById('modalImage');
        const modalTitle = document.getElementById('modalTitle');
        const modalPrice = document.getElementById('modalPrice');
        const closeButtons = modal.querySelectorAll('[data-close-image-modal]');

        function openImageModal() {
            const previewImage = document.getElementById('preview-image');
            if (!previewImage) {
                return;
            }

            modal.style.display = 'block';
            modalImage.src = previewImage.src;
            modalImage.alt = previewImage.alt;
            modalTitle.textContent = modal.dataset.title || '';
            modalPrice.textContent = modal.dataset.price || '';
            document.body.style.overflow = 'hidden';

            setTimeout(() => {
                modal.classList.add('show');
            }, 10);
        }

        function closeImageModal() {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }, 300);
        }

        previewContainer.addEventListener('click', openImageModal);
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeImageModal();
            }
        });
        closeButtons.forEach(button => button.addEventListener('click', closeImageModal));
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeImageModal();
            }
        });
    }
});
