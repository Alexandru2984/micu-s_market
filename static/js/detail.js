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
    if (icon.classList.contains('fas')) {
        icon.classList.remove('fas');
        icon.classList.add('far');
        this.style.color = '#4a5568';
        this.innerHTML = '<i class="far fa-heart"></i> Salvează în favorite';
    } else {
        icon.classList.remove('far');
        icon.classList.add('fas');
        this.style.color = '#e53e3e';
        this.innerHTML = '<i class="fas fa-heart"></i> Salvat în favorite';
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