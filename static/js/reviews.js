document.addEventListener('DOMContentLoaded', function() {
    const ratingInput = document.getElementById('id_rating');
    const ratingStars = document.querySelector('.rating-stars');
    if (ratingInput && ratingStars) {
        const stars = ratingStars.querySelectorAll('span');
        const labels = document.querySelectorAll('.rating-labels span');

        function updateStarsDisplay(rating) {
            stars.forEach((star, index) => {
                star.textContent = '';
                const icon = document.createElement('i');
                icon.className = index < rating ? 'fas fa-star' : 'far fa-star';
                star.appendChild(icon);
                star.classList.toggle('active', index < rating);
            });

            labels.forEach((label, index) => {
                label.classList.toggle('active', index + 1 === rating);
            });
        }

        updateStarsDisplay(parseInt(ratingInput.value, 10) || 0);

        stars.forEach((star, index) => {
            star.addEventListener('click', function() {
                const rating = index + 1;
                ratingInput.value = rating;
                updateStarsDisplay(rating);
            });

            star.addEventListener('mouseenter', function() {
                updateStarsDisplay(index + 1);
            });
        });

        ratingStars.addEventListener('mouseleave', function() {
            updateStarsDisplay(parseInt(ratingInput.value, 10) || 0);
        });
    }

    const textarea = document.getElementById('id_response_text');
    const charCount = document.getElementById('charCount');
    if (textarea && charCount) {
        const maxLength = parseInt(charCount.dataset.maxLength || '1000', 10);

        function updateCharCount() {
            const currentLength = textarea.value.length;
            charCount.textContent = currentLength;
            charCount.parentElement.classList.toggle('over-limit', currentLength > maxLength);
        }

        updateCharCount();
        textarea.addEventListener('input', updateCharCount);
    }
});
