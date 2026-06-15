// Light/dark theme toggle. The initial theme is applied by the inline script in <head>
// (anti-FOUC) before paint; here we only handle the button and persist the choice.
(function () {
    const STORAGE_KEY = 'mm-theme';

    function currentTheme() {
        return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) { /* private mode */ }
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            const isDark = theme === 'dark';
            btn.setAttribute('aria-pressed', String(isDark));
            btn.setAttribute('title', isDark ? 'Comută pe tema deschisă' : 'Comută pe tema întunecată');
            const icon = btn.querySelector('i');
            if (icon) { icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon'; }
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        applyTheme(currentTheme());
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
            });
        });
    });
})();
