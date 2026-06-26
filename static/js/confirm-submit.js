document.addEventListener('click', function(event) {
    const trigger = event.target.closest('[data-confirm-message]');
    if (!trigger) {
        return;
    }

    if (!window.confirm(trigger.dataset.confirmMessage)) {
        event.preventDefault();
    }
});
