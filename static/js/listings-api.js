document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('filtersForm');
    const count = document.querySelector('[data-listings-count]');
    const main = document.querySelector('.listings-main');

    if (!form || !main) return;

    let currentController = null;

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        loadListings(new FormData(form));
    });

    form.querySelectorAll('select').forEach(select => {
        select.addEventListener('change', () => loadListings(new FormData(form)));
    });

    window.addEventListener('popstate', function() {
        const params = new URLSearchParams(window.location.search);
        Array.from(form.elements).forEach(field => {
            if (field.name) field.value = params.get(field.name) || '';
        });
        loadListings(new FormData(form), { pushState: false });
    });

    function loadListings(formData, options = {}) {
        const pushState = options.pushState !== false;
        const params = new URLSearchParams();

        for (const [key, value] of formData.entries()) {
            if (value !== '') params.set(key, value);
        }

        if (!params.has('per_page')) params.set('per_page', '12');

        if (currentController) currentController.abort();
        currentController = new AbortController();
        main.classList.add('is-loading');

        fetch(`/api/listings/?${params.toString()}`, {
            headers: { 'Accept': 'application/json' },
            signal: currentController.signal
        })
            .then(response => {
                if (!response.ok) throw new Error('API response was not ok');
                return response.json();
            })
            .then(data => {
                renderListings(data);
                if (pushState) {
                    const nextUrl = params.toString()
                        ? `${window.location.pathname}?${params.toString()}`
                        : window.location.pathname;
                    window.history.pushState({}, '', nextUrl);
                }
            })
            .catch(error => {
                if (error.name !== 'AbortError') form.submit();
            })
            .finally(() => {
                main.classList.remove('is-loading');
            });
    }

    function renderListings(data) {
        if (count) count.textContent = data.count;
        main.textContent = '';

        if (!data.results.length) {
            main.appendChild(createEmptyState());
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'listings-grid';
        grid.dataset.listingsGrid = '';

        data.results.forEach(listing => {
            grid.appendChild(createListingCard(listing));
        });
        main.appendChild(grid);

        if (data.num_pages > 1) {
            main.appendChild(createPagination(data));
        }
    }

    function createListingCard(listing) {
        const card = document.createElement('a');
        card.className = 'listing-card';
        card.href = listing.url;

        const imageWrap = document.createElement('div');
        imageWrap.className = 'listing-image';

        if (listing.main_image) {
            const img = document.createElement('img');
            img.src = listing.main_image;
            img.alt = listing.title;
            imageWrap.appendChild(img);
        } else {
            const noImage = document.createElement('div');
            noImage.className = 'no-image';
            const icon = document.createElement('i');
            icon.className = 'fas fa-image';
            noImage.appendChild(icon);
            imageWrap.appendChild(noImage);
        }

        if (listing.is_promoted ?? listing.is_featured) {
            const badge = document.createElement('div');
            badge.className = 'featured-badge';
            badge.textContent = 'Recomandat';
            imageWrap.appendChild(badge);
        }

        const content = document.createElement('div');
        content.className = 'listing-content';

        const title = document.createElement('h3');
        title.textContent = listing.title;

        const price = document.createElement('p');
        price.className = 'price';
        price.textContent = `${listing.price} RON`;

        const location = document.createElement('p');
        location.className = 'location';
        location.textContent = [listing.city, listing.county].filter(Boolean).join(', ');

        const meta = document.createElement('div');
        meta.className = 'listing-meta';

        const category = document.createElement('span');
        category.className = 'category';
        category.textContent = listing.category.name || 'Fără categorie';

        const date = document.createElement('span');
        date.className = 'date';
        date.textContent = new Date(listing.created_at).toLocaleDateString('ro-RO');

        meta.appendChild(category);
        meta.appendChild(date);
        content.appendChild(title);
        content.appendChild(price);
        content.appendChild(location);
        content.appendChild(meta);
        card.appendChild(imageWrap);
        card.appendChild(content);

        return card;
    }

    function createPagination(data) {
        const nav = document.createElement('div');
        nav.className = 'pagination';
        nav.dataset.listingsPagination = '';

        if (data.has_previous) {
            nav.appendChild(createPageButton('Anterior', data.page - 1));
        }

        const info = document.createElement('span');
        info.className = 'page-info';
        info.textContent = `Pagina ${data.page} din ${data.num_pages}`;
        nav.appendChild(info);

        if (data.has_next) {
            nav.appendChild(createPageButton('Următoarea', data.page + 1));
        }

        return nav;
    }

    function createPageButton(label, page) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-outline';
        button.textContent = label;
        button.addEventListener('click', function() {
            const data = new FormData(form);
            data.set('page', page);
            loadListings(data);
        });
        return button;
    }

    function createEmptyState() {
        const empty = document.createElement('div');
        empty.className = 'no-listings';
        empty.dataset.listingsEmpty = '';

        const icon = document.createElement('i');
        icon.className = 'fas fa-search';

        const title = document.createElement('h3');
        title.textContent = 'Nu am găsit anunțuri';

        const description = document.createElement('p');
        description.textContent = 'Încearcă să modifici filtrele pentru a găsi mai multe rezultate.';

        empty.appendChild(icon);
        empty.appendChild(title);
        empty.appendChild(description);

        return empty;
    }
});
