function changeMainImage(imageSrc, thumbnail) {
    document.getElementById('mainImage').src = imageSrc;
    
    // Update active thumbnail
    document.querySelectorAll('.thumbnail').forEach(thumb => {
        thumb.classList.remove('active');
    });
    thumbnail.classList.add('active');
}

// Contact button functionality
document.querySelector('.contact-btn')?.addEventListener('click', function() {
    alert('Funcționalitatea de contact va fi implementată în curând!');
});

// Favorite functionality
document.querySelector('.favorite-btn')?.addEventListener('click', function() {
    const icon = this.querySelector('i');
    const textSpan = this.querySelector('span'); // Selecționează elementul <span>
    
    if (icon.classList.contains('fas')) {
        // Logica pentru a elimina din favorite
        icon.classList.remove('fas');
        icon.classList.add('far');
        textSpan.textContent = 'Adaugă la favorite';
    } else {
        // Logica pentru a adăuga la favorite
        icon.classList.remove('far');
        icon.classList.add('fas');
        textSpan.textContent = 'În favorite';
    }
});

// Share functionality
document.querySelector('.share-btn')?.addEventListener('click', function() {
    if (navigator.share) {
        navigator.share({
            title: document.title,
            url: window.location.href
        });
    } else {
        // Fallback - copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('Link-ul a fost copiat în clipboard!');
        });
    }
});