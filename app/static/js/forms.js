// Global forms helpers
document.addEventListener('DOMContentLoaded', function() {
    // Character counter for textarea
    const textareas = document.querySelectorAll('.char-count-textarea');
    textareas.forEach(textarea => {
        const targetId = textarea.getAttribute('data-counter-target');
        const counter = document.getElementById(targetId);
        const minChars = parseInt(textarea.getAttribute('data-min-chars') || '0');
        
        if (counter) {
            const updateCounter = () => {
                const len = textarea.value.length;
                counter.textContent = len;
                if (len < minChars) {
                    counter.classList.add('text-danger');
                    counter.classList.remove('text-success');
                } else {
                    counter.classList.add('text-success');
                    counter.classList.remove('text-danger');
                }
            };
            
            textarea.addEventListener('input', updateCounter);
            updateCounter(); // initial load
        }
    });

    // Date range validation
    const dateStart = document.getElementById('termin_od');
    const dateEnd = document.getElementById('termin_do');
    if (dateStart && dateEnd) {
        const validateDates = () => {
            const start = new Date(dateStart.value);
            const end = new Date(dateEnd.value);
            if (dateStart.value && dateEnd.value && start >= end) {
                dateEnd.setCustomValidity('Data zakończenia musi być późniejsza niż data rozpoczęcia.');
            } else {
                dateEnd.setCustomValidity('');
            }
        };
        dateStart.addEventListener('change', validateDates);
        dateEnd.addEventListener('change', validateDates);
    }
});
