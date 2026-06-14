// Profile Edit JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Adaugă funcționalitate pentru preview avatar
    const avatarInput = document.getElementById('id_avatar');
    if (avatarInput) {
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('avatar-preview');
                    preview.textContent = '';

                    const wrapper = document.createElement('div');
                    wrapper.className = 'mt-3';

                    const label = document.createElement('p');
                    label.className = 'mb-2';
                    const strong = document.createElement('strong');
                    strong.textContent = 'Preview:';
                    label.appendChild(strong);

                    const image = document.createElement('img');
                    image.src = e.target.result;
                    image.className = 'preview-image';
                    image.alt = 'Preview';

                    wrapper.appendChild(label);
                    wrapper.appendChild(image);
                    preview.appendChild(wrapper);
                };
                reader.readAsDataURL(file);
            }
        });
    }
});
