document.addEventListener('DOMContentLoaded', function() {
    const wpisForm = document.getElementById('wpis-form');
    if (wpisForm) {
        wpisForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const efektySelected = [];
            const checkboxes = this.querySelectorAll('.efekty-checkbox:checked');
            checkboxes.forEach(cb => {
                efektySelected.push(parseInt(cb.value));
            });
            
            const payload = {
                praktyka_id: parseInt(formData.get('praktyka_id')),
                dzien_nr: parseInt(formData.get('dzien_nr')),
                data_wpisu: formData.get('data_wpisu'),
                opis_prac: formData.get('opis_prac'),
                efekty: efektySelected
            };
            
            fetch('/api/v1/dziennik/wpisy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            }).then(res => {
                if (res.status === 201) {
                    window.location.reload();
                } else {
                    res.json().then(data => {
                        alert("Błąd: " + (data.error?.message || "Nie udało się dodać wpisu."));
                    });
                }
            });
        });
    }
});
