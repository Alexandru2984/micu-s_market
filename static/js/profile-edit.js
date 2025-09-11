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
                    preview.innerHTML = `
                        <div class="mt-3">
                            <p class="mb-2"><strong>Preview:</strong></p>
                            <img src="${e.target.result}" class="preview-image" alt="Preview">
                        </div>
                    `;
                };
                reader.readAsDataURL(file);
            }
        });
    }
});
