document.addEventListener('DOMContentLoaded', function() {
    // -------------------------------------------------------------
    // Student: Submit diary entry form
    // -------------------------------------------------------------
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
                        if (window.showToast) {
                            window.showToast("Błąd: " + (data.error?.message || "Nie udało się dodać wpisu."), "error");
                        } else {
                            alert("Błąd: " + (data.error?.message || "Nie udało się dodać wpisu."));
                        }
                    });
                }
            });
        });
    }

    // -------------------------------------------------------------
    // Filtering System: Search opis & Status select (DOM-based)
    // -------------------------------------------------------------
    const searchOpis = document.getElementById('search-opis');
    const filterStatus = document.getElementById('filter-status');
    const tableRows = document.querySelectorAll('#dziennik-table-body tr:not(#empty-row)');

    function filterTable() {
        const searchText = searchOpis ? searchOpis.value.toLowerCase() : "";
        const selectedStatus = filterStatus ? filterStatus.value : "";

        let visibleCount = 0;

        tableRows.forEach(row => {
            const opisText = row.querySelector('.opis-text')?.textContent.toLowerCase() || "";
            const rowStatus = row.getAttribute('data-status') || "";

            const matchesSearch = opisText.includes(searchText);
            const matchesStatus = selectedStatus === "" || rowStatus === selectedStatus;

            if (matchesSearch && matchesStatus) {
                row.classList.remove('d-none');
                visibleCount++;
            } else {
                row.classList.add('d-none');
            }
        });

        // Toggle empty row visibility if all filtered out
        const emptyRow = document.getElementById('empty-row');
        if (emptyRow) {
            if (visibleCount === 0) {
                emptyRow.classList.remove('d-none');
            } else {
                emptyRow.classList.add('d-none');
            }
        }
    }

    if (searchOpis) searchOpis.addEventListener('input', filterTable);
    if (filterStatus) filterStatus.addEventListener('change', filterTable);

    // -------------------------------------------------------------
    // ZOPZ: Batch & Single Verification
    // -------------------------------------------------------------
    const selectAllCheckbox = document.getElementById('select-all-wpisy');
    const wpisCheckboxes = document.querySelectorAll('.wpis-select');
    const batchBar = document.getElementById('batch-verify-bar');
    const selectedCountSpan = document.getElementById('selected-count');
    
    const btnBatchApprove = document.getElementById('btn-batch-approve');
    const btnBatchReject = document.getElementById('btn-batch-reject');
    const batchCommentInput = document.getElementById('batch-comment');

    const singleApproveButtons = document.querySelectorAll('.btn-action-approve');
    const singleRejectButtons = document.querySelectorAll('.btn-action-reject');

    // Reject Modal References
    const rejectModalEl = document.getElementById('rejectWpisModal');
    const rejectModal = rejectModalEl ? new bootstrap.Modal(rejectModalEl) : null;
    const btnSubmitReject = document.getElementById('btn-submit-reject');
    const rejectWpisIdInput = document.getElementById('reject-wpis-id');
    const rejectKomentarzInput = document.getElementById('reject-komentarz');

    function updateBatchBar() {
        if (!batchBar) return;
        const checkedCount = document.querySelectorAll('.wpis-select:checked').length;
        if (checkedCount > 0) {
            batchBar.classList.remove('d-none');
            selectedCountSpan.innerHTML = `<span class="material-symbols-outlined align-middle me-1" style="font-size: 20px;">checklist</span>Wybrano: <strong>${checkedCount}</strong> wpisów`;
        } else {
            batchBar.classList.add('d-none');
        }
    }

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            wpisCheckboxes.forEach(cb => {
                // Only select visible ones to prevent selecting filtered-out rows
                const row = cb.closest('tr');
                if (row && !row.classList.contains('d-none')) {
                    cb.checked = isChecked;
                }
            });
            updateBatchBar();
        });
    }

    wpisCheckboxes.forEach(cb => {
        cb.addEventListener('change', updateBatchBar);
    });

    // Single Actions: Approve
    singleApproveButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            patchWpisStatus(id, 'Approved', '', (success) => {
                if (success) {
                    updateRowUI(id, 'Approved', 'Zatwierdzony', 'check_circle');
                }
            });
        });
    });

    // Single Actions: Reject (Open Modal)
    singleRejectButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            if (rejectWpisIdInput) rejectWpisIdInput.value = id;
            if (rejectKomentarzInput) rejectKomentarzInput.value = "";
            if (rejectModal) rejectModal.show();
        });
    });

    if (btnSubmitReject) {
        btnSubmitReject.addEventListener('click', function() {
            const id = rejectWpisIdInput.value;
            const comment = rejectKomentarzInput.value.trim();
            if (!comment) {
                if (window.showToast) {
                    window.showToast("Komentarz jest wymagany!", "warning");
                } else {
                    alert("Komentarz jest wymagany!");
                }
                return;
            }
            if (rejectModal) rejectModal.hide();
            patchWpisStatus(id, 'Rejected', comment, (success) => {
                if (success) {
                    updateRowUI(id, 'Rejected', 'Odrzucony', 'cancel', comment);
                }
            });
        });
    }

    // Batch Actions: Approve
    if (btnBatchApprove) {
        btnBatchApprove.addEventListener('click', function() {
            const selectedIds = Array.from(document.querySelectorAll('.wpis-select:checked')).map(cb => cb.getAttribute('data-id'));
            const comment = batchCommentInput ? batchCommentInput.value.trim() : "";
            
            if (selectedIds.length === 0) return;
            
            btnBatchApprove.disabled = true;
            btnBatchApprove.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Zatwierdzanie...`;

            executeBatchStatus(selectedIds, 'Approved', comment)
                .then(() => {
                    if (window.showToast) {
                        window.showToast(`Pomyślnie zatwierdzono ${selectedIds.length} wpisów!`, "success");
                    }
                    setTimeout(() => window.location.reload(), 1000);
                })
                .catch(err => {
                    if (window.showToast) {
                        window.showToast("Wystąpił błąd podczas masowego zatwierdzania.", "error");
                    }
                    btnBatchApprove.disabled = false;
                    btnBatchApprove.innerHTML = `<span class="material-symbols-outlined" style="font-size: 16px;">check_circle</span> Zatwierdź zaznaczone`;
                });
        });
    }

    // Batch Actions: Reject
    if (btnBatchReject) {
        btnBatchReject.addEventListener('click', function() {
            const selectedIds = Array.from(document.querySelectorAll('.wpis-select:checked')).map(cb => cb.getAttribute('data-id'));
            const comment = batchCommentInput ? batchCommentInput.value.trim() : "";
            
            if (selectedIds.length === 0) return;
            if (!comment) {
                if (window.showToast) {
                    window.showToast("Podanie komentarza jest wymagane przy masowym odrzucaniu!", "warning");
                } else {
                    alert("Podanie komentarza jest wymagane przy masowym odrzucaniu!");
                }
                if (batchCommentInput) batchCommentInput.focus();
                return;
            }

            btnBatchReject.disabled = true;
            btnBatchReject.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Odrzucanie...`;

            executeBatchStatus(selectedIds, 'Rejected', comment)
                .then(() => {
                    if (window.showToast) {
                        window.showToast(`Odrzucono ${selectedIds.length} wpisów.`, "info");
                    }
                    setTimeout(() => window.location.reload(), 1000);
                })
                .catch(err => {
                    if (window.showToast) {
                        window.showToast("Wystąpił błąd podczas masowego odrzucania.", "error");
                    }
                    btnBatchReject.disabled = false;
                    btnBatchReject.innerHTML = `<span class="material-symbols-outlined" style="font-size: 16px;">cancel</span> Odrzuć zaznaczone`;
                });
        });
    }

    // -------------------------------------------------------------
    // Helper Functions
    // -------------------------------------------------------------
    function patchWpisStatus(id, status, comment, callback) {
        const payload = {
            status: status
        };
        if (comment) {
            payload.komentarz_zopz = comment;
        }

        fetch(`/api/v1/dziennik/wpisy/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                callback(true);
            } else {
                if (window.showToast) {
                    window.showToast("Błąd: " + (data.error?.message || "Wystąpił błąd"), "error");
                }
                callback(false);
            }
        })
        .catch(err => {
            if (window.showToast) {
                window.showToast("Błąd połączenia z serwerem.", "error");
            }
            callback(false);
        });
    }

    function executeBatchStatus(ids, status, comment) {
        // Send sequential PATCH requests to prevent sqlite locking
        let chain = Promise.resolve();
        ids.forEach(id => {
            chain = chain.then(() => new Promise((resolve, reject) => {
                const payload = { status: status };
                if (comment) payload.komentarz_zopz = comment;
                
                fetch(`/api/v1/dziennik/wpisy/${id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) resolve();
                    else reject(data.error);
                })
                .catch(reject);
            }));
        });
        return chain;
    }

    function updateRowUI(id, status, statusTextPl, iconClass, comment = '') {
        const row = document.getElementById(`wpis-row-${id}`);
        if (!row) return;

        // Update attribute
        row.setAttribute('data-status', status);

        // Update status badge cell
        const badgeCell = row.querySelector('.badge-status');
        if (badgeCell) {
            badgeCell.className = `badge-status badge-status-${status.toLowerCase()}`;
            badgeCell.innerHTML = `
                <span class="material-symbols-outlined" style="font-size: 14px;">${iconClass}</span> ${statusTextPl}
            `;
        }

        // Disable checkbox
        const cb = row.querySelector('.wpis-select');
        if (cb) {
            cb.checked = false;
            cb.disabled = true;
            cb.classList.add('d-none');
        }

        // Remove actions buttons
        const actionCell = row.querySelector('td:last-child');
        if (actionCell) {
            actionCell.innerHTML = `<span class="text-secondary small d-flex align-items-center gap-1 justify-content-center"><span class="material-symbols-outlined text-success" style="font-size: 16px;">verified</span> Zweryfikowany</span>`;
        }

        // Add comment to description cell if present
        if (comment) {
            const opisCell = row.querySelector('.opis-cell');
            if (opisCell) {
                // Check if comment already shown, if so remove
                const oldComment = opisCell.querySelector('.text-danger');
                if (oldComment) oldComment.remove();

                const commentDiv = document.createElement('div');
                commentDiv.className = 'text-danger small mt-1 py-1 px-2 bg-danger-light rounded d-inline-block';
                commentDiv.innerHTML = `<span class="material-symbols-outlined align-middle me-1" style="font-size: 14px;">chat_bubble</span>Komentarz ZOPZ: ${comment}`;
                opisCell.appendChild(commentDiv);
            }
        } else {
            // If approved, remove comment if it was rejected previously
            const opisCell = row.querySelector('.opis-cell');
            if (opisCell) {
                const oldComment = opisCell.querySelector('.text-danger');
                if (oldComment) oldComment.remove();
            }
        }

        updateBatchBar();
    }
});
