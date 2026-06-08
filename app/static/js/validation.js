// SOPZ Client-Side Validation System (Premium & Modern Bootstrap 5 Integration)
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Enforce Bootstrap 5 needs-validation styling
        if (!form.classList.contains('needs-validation')) {
            form.classList.add('needs-validation');
        }
        
        form.addEventListener('submit', function(event) {
            let isValid = true;
            
            // 1. Traditional Bootstrap validation checks
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                isValid = false;
            }
            
            // 2. Custom validations
            
            // Date range validation: termin_od & termin_do
            const dateStart = form.querySelector('input[name="termin_od"]');
            const dateEnd = form.querySelector('input[name="termin_do"]');
            if (dateStart && dateEnd && dateStart.value && dateEnd.value) {
                const start = new Date(dateStart.value);
                const end = new Date(dateEnd.value);
                if (start >= end) {
                    showInlineError(dateEnd, 'Data zakończenia musi być późniejsza niż data rozpoczęcia.');
                    isValid = false;
                } else {
                    clearInlineError(dateEnd);
                }
            }

            // Min characters validation (e.g. sprawozdanie sections)
            const minCharTextareas = form.querySelectorAll('textarea[data-min-chars]');
            minCharTextareas.forEach(textarea => {
                const minChars = parseInt(textarea.getAttribute('data-min-chars') || '0');
                if (textarea.value.length < minChars) {
                    showInlineError(textarea, `To pole musi zawierać minimum ${minChars} znaków (obecnie: ${textarea.value.length}).`);
                    isValid = false;
                } else {
                    clearInlineError(textarea);
                }
            });

            // Grades range validation (oceny 2-5)
            const gradeInputs = form.querySelectorAll('input[type="number"][name*="ocena"], select[name*="ocena"]');
            gradeInputs.forEach(input => {
                const val = parseFloat(input.value);
                if (!isNaN(val) && (val < 2.0 || val > 5.0)) {
                    showInlineError(input, 'Ocena musi być w przedziale od 2.0 do 5.0.');
                    isValid = false;
                } else {
                    clearInlineError(input);
                }
            });

            // Scale 1-5 validation (ankieta answers)
            const scaleInputs = form.querySelectorAll('input[type="number"][name*="pytanie"], select[name*="pytanie"]');
            scaleInputs.forEach(input => {
                const val = parseInt(input.value);
                if (!isNaN(val) && (val < 1 || val > 5)) {
                    showInlineError(input, 'Odpowiedź musi być w skali 1-5.');
                    isValid = false;
                } else {
                    clearInlineError(input);
                }
            });

            // Harmonogram sum validation (total 120 days)
            const harmonogramTable = form.querySelector('#harmonogram-table');
            if (harmonogramTable) {
                const daysInputs = harmonogramTable.querySelectorAll('input[name*="planowane_dni"]');
                let totalDays = 0;
                daysInputs.forEach(input => {
                    const days = parseInt(input.value) || 0;
                    totalDays += days;
                });
                
                const sumFeedback = form.querySelector('#harmonogram-sum-feedback');
                if (totalDays !== 120) {
                    if (sumFeedback) {
                        sumFeedback.textContent = `Suma dni musi wynosić dokładnie 120 (obecnie: ${totalDays}).`;
                        sumFeedback.classList.add('text-danger');
                        sumFeedback.classList.remove('text-success');
                    }
                    isValid = false;
                } else if (sumFeedback) {
                    sumFeedback.textContent = `Suma dni: 120/120`;
                    sumFeedback.classList.add('text-success');
                    sumFeedback.classList.remove('text-danger');
                }
            }

            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
});

function showInlineError(element, message) {
    element.classList.add('is-invalid');
    element.classList.remove('is-valid');
    
    // Find or create invalid-feedback element
    let feedback = element.parentNode.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.classList.add('invalid-feedback', 'd-block');
        element.parentNode.appendChild(feedback);
    }
    feedback.textContent = message;
    feedback.style.display = 'block';
}

function clearInlineError(element) {
    element.classList.remove('is-invalid');
    element.classList.add('is-valid');
    
    const feedback = element.parentNode.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.style.display = 'none';
    }
}
