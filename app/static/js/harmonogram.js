document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('dzialy-table-body');
    const addBtn = document.getElementById('add-dzial-btn');
    const totalDaysSpan = document.getElementById('total-days-span');
    const statusMessage = document.getElementById('days-status-message');
    const saveBtn = document.getElementById('save-harmonogram-btn');
    
    const updateTotalDays = () => {
        let total = 0;
        const inputs = tableBody.querySelectorAll('.planowane-dni-input');
        inputs.forEach(input => {
            total += parseInt(input.value || '0');
        });
        
        totalDaysSpan.textContent = total;
        
        if (total === 120) {
            statusMessage.innerHTML = '<span class="text-success fw-bold"><i class="bi bi-check-circle-fill me-1"></i> Suma wynosi dokładnie 120 dni.</span>';
            saveBtn.removeAttribute('disabled');
        } else {
            statusMessage.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-exclamation-triangle-fill me-1"></i> Suma musi wynosić dokładnie 120 dni (obecnie: ${total}).</span>`;
            saveBtn.setAttribute('disabled', 'true');
        }
    };
    
    // Add row event listener
    if (addBtn) {
        addBtn.addEventListener('click', function() {
            const index = tableBody.children.length;
            const newRow = document.createElement('tr');
            newRow.innerHTML = `
                <td>
                    <input type="text" class="form-control form-control-sm dzial-nazwa-input" placeholder="Nazwa działu..." required>
                </td>
                <td>
                    <input type="number" class="form-control form-control-sm planowane-dni-input" value="0" min="1" required>
                </td>
                <td class="text-center">
                    <button type="button" class="btn btn-sm btn-outline-danger remove-dzial-btn"><i class="bi bi-trash"></i></button>
                </td>
            `;
            tableBody.appendChild(newRow);
            
            // Re-bind input validation events
            newRow.querySelector('.planowane-dni-input').addEventListener('input', updateTotalDays);
            newRow.querySelector('.remove-dzial-btn').addEventListener('click', function() {
                newRow.remove();
                updateTotalDays();
            });
            
            updateTotalDays();
        });
    }

    // Initial binding for existing rows
    const inputs = tableBody.querySelectorAll('.planowane-dni-input');
    inputs.forEach(input => {
        input.addEventListener('input', updateTotalDays);
    });
    
    const removeBtns = tableBody.querySelectorAll('.remove-dzial-btn');
    removeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            btn.closest('tr').remove();
            updateTotalDays();
        });
    });
    
    // Form submission handler
    const form = document.getElementById('harmonogram-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const rows = tableBody.querySelectorAll('tr');
            const dzialy = [];
            
            rows.forEach(row => {
                const nazwa = row.querySelector('.dzial-nazwa-input').value;
                const dni = parseInt(row.querySelector('.planowane-dni-input').value);
                dzialy.push({
                    nazwa_dzialu: nazwa,
                    planowane_dni: dni
                });
            });
            
            const harmonogramId = form.getAttribute('data-harmonogram-id');
            const payload = {
                dzialy: dzialy
            };
            
            fetch(`/api/v1/harmonogramy/${harmonogramId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            }).then(res => {
                if (res.ok) {
                    window.location.reload();
                } else {
                    res.json().then(data => {
                        alert("Błąd zapisu: " + (data.error?.message || "Nieznany błąd"));
                    });
                }
            });
        });
    }

    updateTotalDays();
});
