// SOPZ Frontend Components & Utilities

/**
 * Show a toast notification
 * @param {string} message 
 * @param {'success' | 'error' | 'warning' | 'info'} type 
 * @param {number} duration 
 */
function showToast(message, type = 'info', duration = 5000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast-sopz toast-${type}`;
    
    let icon = 'info';
    if (type === 'success') icon = 'check_circle';
    if (type === 'error') icon = 'error';
    if (type === 'warning') icon = 'warning';

    toast.innerHTML = `
        <span class="material-symbols-outlined">${icon}</span>
        <div style="flex: 1; font-size: 14px;">${message}</div>
        <button type="button" class="btn-close" style="font-size: 10px;" onclick="this.parentElement.remove()"></button>
    `;

    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Show a confirmation modal
 * @param {string} title 
 * @param {string} message 
 * @param {function} onConfirm 
 */
function showConfirmModal(title, message, onConfirm) {
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-sopz-backdrop';
    
    const modal = document.createElement('div');
    modal.className = 'modal-sopz';
    modal.innerHTML = `
        <div style="padding: 20px; border-bottom: 1px solid var(--border-light); display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0;">${title}</h3>
            <button type="button" class="btn-close" onclick="this.closest('.modal-sopz-backdrop').remove()"></button>
        </div>
        <div style="padding: 20px; font-size: 14px; color: var(--text-secondary);">
            ${message}
        </div>
        <div style="padding: 16px 20px; background-color: var(--border-light); display: flex; justify-content: flex-end; gap: 12px;">
            <button type="button" class="btn btn-ghost" onclick="this.closest('.modal-sopz-backdrop').remove()">Anuluj</button>
            <button type="button" class="btn btn-primary" id="confirm-modal-btn">Potwierdź</button>
        </div>
    `;
    
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
    
    modal.querySelector('#confirm-modal-btn').addEventListener('click', () => {
        onConfirm();
        backdrop.remove();
    });
}

/**
 * Initialize Client-Side Pagination for a Table
 * @param {string} tableId 
 * @param {number} perPage 
 */
function initPagination(tableId, perPage = 20) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const totalRows = rows.length;
    const totalPages = Math.ceil(totalRows / perPage);
    let currentPage = 1;
    
    // Find or create pagination container after table
    let pagContainer = document.getElementById(`${tableId}-pagination`);
    if (!pagContainer) {
        pagContainer = document.createElement('div');
        pagContainer.id = `${tableId}-pagination`;
        pagContainer.className = 'd-flex justify-content-between align-items-center mt-3 flex-wrap gap-2';
        table.after(pagContainer);
    }
    
    function showPage(page) {
        currentPage = page;
        const start = (page - 1) * perPage;
        const end = start + perPage;
        
        rows.forEach((row, i) => {
            if (i >= start && i < end) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        
        renderControls();
    }
    
    function renderControls() {
        const startIdx = totalRows === 0 ? 0 : (currentPage - 1) * perPage + 1;
        const endIdx = Math.min(currentPage * perPage, totalRows);
        
        let html = `<div style="font-size: 12px; color: var(--text-secondary);">Wyświetlanie ${startIdx}-${endIdx} z ${totalRows}</div>`;
        html += `<nav><ul class="pagination pagination-sm m-0">`;
        
        // Prev button
        html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage - 1}">&laquo;</a>
        </li>`;
        
        for (let i = 1; i <= totalPages; i++) {
            html += `<li class="page-item ${currentPage === i ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>`;
        }
        
        // Next button
        html += `<li class="page-item ${currentPage === totalPages || totalPages === 0 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage + 1}">&raquo;</a>
        </li>`;
        
        html += `</ul></nav>`;
        pagContainer.innerHTML = html;
        
        pagContainer.querySelectorAll('a.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.getAttribute('data-page'));
                if (!isNaN(page) && page >= 1 && page <= totalPages) {
                    showPage(page);
                }
            });
        });
    }
    
    showPage(1);
}

/**
 * Initialize Client-Side Search for a Table
 * @param {string} tableId 
 * @param {string} inputId 
 */
function initTableSearch(tableId, inputId) {
    const table = document.getElementById(tableId);
    const input = document.getElementById(inputId);
    if (!table || !input) return;
    
    input.addEventListener('input', () => {
        const query = input.value.toLowerCase().trim();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.innerText.toLowerCase();
            if (text.includes(query)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        
        // Re-init pagination if active
        const paginationContainer = document.getElementById(`${tableId}-pagination`);
        if (paginationContainer) {
            // Simple filter fallback
            const visibleRows = Array.from(rows).filter(r => r.style.display !== 'none');
            if (query === '') {
                initPagination(tableId);
            }
        }
    });
}

/**
 * Sidebar responsive initialization
 */
function initSidebar() {
    const hamburger = document.querySelector('.hamburger-btn');
    const sidebar = document.querySelector('.sidebar');
    
    if (hamburger && sidebar) {
        hamburger.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar on click outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 992) {
                if (!sidebar.contains(e.target) && !hamburger.contains(e.target) && sidebar.classList.contains('show')) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }
}

/**
 * Wrapper for fetch with toast notifications
 * @param {string} url 
 * @param {object} options 
 */
async function fetchWithToast(url, options = {}) {
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.message || 'Wystąpił błąd podczas operacji', 'error');
            return { ok: false, data };
        }
        
        if (data.message) {
            showToast(data.message, 'success');
        }
        return { ok: true, data };
    } catch (error) {
        showToast('Błąd połączenia z serwerem', 'error');
        return { ok: false, error };
    }
}

/**
 * Zatwierdza dziennik praktyk (UOPZ): ustawia dziennik_status na 'Closed'.
 * @param {number} praktykaId
 */
function zatwierdzDziennik(praktykaId) {
    fetch(`/api/v1/dziennik/${praktykaId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dziennik_status: 'Closed' })
    }).then(res => {
        if (res.ok) {
            showToast('Dziennik zatwierdzony.', 'success');
            setTimeout(() => window.location.reload(), 800);
        } else {
            res.json().then(d => showToast('Błąd: ' + (d.error?.message || 'nie udało się zatwierdzić dziennika.'), 'error'))
                .catch(() => showToast('Błąd zatwierdzania dziennika.', 'error'));
        }
    }).catch(() => showToast('Błąd połączenia z serwerem.', 'error'));
}

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
});
