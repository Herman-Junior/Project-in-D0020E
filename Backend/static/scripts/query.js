document.addEventListener('DOMContentLoaded', () => {
    const dataSelect = document.getElementById('data-select');
    const loadButton = document.getElementById('load-data-btn');
    const resultsDiv = document.getElementById('results-area');
    const deleteButton = document.getElementById('delete-selected-btn')
    
    // Select the inputs - using optional chaining to prevent crashes
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const startTimeInput = document.getElementById('start-time'); // Added
    const endTimeInput = document.getElementById('end-time');     // Added

    // --- CORE LOGIC ---
    if (loadButton) {
        loadButton.addEventListener('click', fetchData);
    }
    if (deleteButton) {
        deleteButton.addEventListener('click', deleteSelected);
    }
    
    async function fetchData() {
        const selectedData = dataSelect.value;
        const startDate = startDateInput ? startDateInput.value : '';
        const endDate = endDateInput ? endDateInput.value : '';
        const startTime = startTimeInput ? startTimeInput.value : ''; // Added
        const endTime = endTimeInput ? endTimeInput.value : '';     // Added

        if (!selectedData) {
            resultsDiv.innerHTML = '<p class="error">Please select a data source.</p>';
            return;
        }

        const endpointMap = {
            'sensor': '/api/v1/sensors',
            'weather': '/api/v1/weather',
            'combined': '/api/v1/combined'
        };
        
        const endpoint = endpointMap[selectedData];
        const params = new URLSearchParams();

        // Append Date and Time parameters
        if (startDate) params.append('start_date', startDate);
        if (startTime) params.append('start_time', startTime); // Added
        if (endDate) params.append('end_date', endDate);
        if (endTime) params.append('end_time', endTime);     // Added
        
        const url = `${endpoint}?${params.toString()}`;
        resultsDiv.innerHTML = '<p class="loading info">Loading data...</p>';
        
        try {
            const response = await fetch(url);
            if (response.status === 204) {
                resultsDiv.innerHTML = '<p class="info">No data found for the selected criteria.</p>';
                return;
            }

            const data = await response.json();

            if (!response.ok || data.error) {
                resultsDiv.innerHTML = `<p class="error">API Error: ${data.error || 'Failed to fetch data'}</p>`;
                return;
            }

            if (data.length === 0) {
                resultsDiv.innerHTML = '<p class="info">No data found for the selected criteria.</p>';
                return;
            }

            renderTable(data, resultsDiv);
            
        } catch (e) {
            resultsDiv.innerHTML = `<p class="error">Network Error: ${e.message}</p>`;
        }
        
    }
    async function deleteSelected() {
        const selectedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
        const selectedIds = Array.from(selectedCheckboxes).map(cb => cb.value);
        const dataSource = dataSelect.value;

        // Rättad jämförelse (===)
        if (selectedIds.length === 0) {
            alert('No rows selected for deletion.');
            return;
        }

        if (confirm("Are you sure about deleting the selected rows?")) {
            try {
                const response = await fetch('/api/v1/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids: selectedIds, type: dataSource })
                });

                if (response.ok) {
                    alert('Selected rows deleted successfully.');
                    fetchData(); // Ladda om listan direkt
                } else {
                    alert("Något gick fel vid raderingen.");
                }
            } catch (e) {
                alert("Nätverksfel: " + e.message);
            }
        }
    }


    // --- CHECKBOX & POP-UP LOGIC ---
    // We listen for changes globally within the document or results area
    document.addEventListener('change', (e) => {
        if (e.target.id === 'select-all-rows') {
            const checkboxes = document.querySelectorAll('.row-checkbox');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
            updateActionMenu();
        }
        
        if (e.target.classList.contains('row-checkbox')) {
            updateActionMenu();
        }
    });

const toggleBtn = document.getElementById('toggle-filters-btn');
const filterOptions = document.getElementById('filter-options');

toggleBtn.addEventListener('click', () => {
    if (filterOptions.style.display === 'none' || filterOptions.style.display === '') {
        filterOptions.style.display = 'flex'; 
        toggleBtn.textContent = 'Hide Filters';
    } else {
        filterOptions.style.display = 'none';
        toggleBtn.textContent = 'Filter';
    }
});

    function updateActionMenu() {
        const selected = document.querySelectorAll('.row-checkbox:checked');
        const container = document.getElementById('bulk-actions-container');
        const countSpan = document.getElementById('selected-count');
        
        if (container) {
            if (selected.length > 0) {
                container.style.display = 'block';
                if (countSpan) countSpan.textContent = selected.length;
            } else {
                container.style.display = 'none';
            }
        }
    }

    // --- TABLE RENDERING ---
    function renderTable(data, targetElement) {
        targetElement.innerHTML = ''; 

        // 1. Define the order of data columns
        const mandatoryHeaders = ['date', 'time']; 
        const allHeaders = Object.keys(data[0]).filter(h => h !== 'id');
        const remainingHeaders = allHeaders.filter(header => !mandatoryHeaders.includes(header));
        const headers = [...mandatoryHeaders, ...remainingHeaders];

        let tableHTML = '<div class="table-container"><table class="data-table"><thead><tr>';
        
        // HEADER: First column is the checkbox
        tableHTML += '<th class="checkbox-col"><input type="checkbox" id="select-all-rows"></th>';

        // HEADER: Following columns are Date, Time, etc.
        headers.forEach(header => {
            const displayHeader = header.replace(/_/g, ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
            tableHTML += `<th>${displayHeader}</th>`;
        });
        tableHTML += '</tr></thead><tbody>';

        // BODY: Create rows
        data.forEach(row => {
            tableHTML += '<tr>';
            
            // CELL: First column MUST be the checkbox to match the header
            const rowId = row.sensor_id || row.weather_id || row.id || ""; 
            tableHTML += `<td class="checkbox-col"><input type="checkbox" class="row-checkbox" value="${rowId}"></td>`;

            // CELL: Following columns
            headers.forEach(header => {
                const cellValue = row[header] !== undefined && row[header] !== null ? row[header] : 'N/A';
                tableHTML += `<td>${cellValue}</td>`;
            });

            tableHTML += '</tr>';
        });

        tableHTML += '</tbody></table></div>';
        targetElement.innerHTML = tableHTML;
        
        // Reset action menu on new render
        updateActionMenu();
    }

    // --- CSV DOWNLOAD ---
    const downloadButton = document.getElementById('download-csv-btn');
    if (downloadButton) {
        downloadButton.addEventListener('click', downloadCSV);
    }

    function downloadCSV() {
        const selectedData = dataSelect.value;
        const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');

        if (checkedBoxes.length > 0) {
            // Selected rows only: build CSV directly from the table DOM
            const table = document.querySelector('.data-table');
            if (!table) return;

            const headerCells = table.querySelectorAll('thead th');
            const headers = Array.from(headerCells)
                .map(th => th.textContent.trim())
                .filter(h => h !== ''); // skip checkbox column

            const rows = [];
            checkedBoxes.forEach(cb => {
                const row = cb.closest('tr');
                const cells = Array.from(row.querySelectorAll('td'))
                    .filter(td => !td.classList.contains('checkbox-col'));
                rows.push(cells.map(td => `"${td.textContent.trim()}"`));
            });

            const csvContent = [
                headers.map(h => `"${h}"`).join(','),
                ...rows.map(r => r.join(','))
            ].join('\n');

            triggerDownload(csvContent, `${selectedData}_selected_${csvTimestamp()}.csv`);

        } else {
            // Nothing selected: download everything via API using current filters
            const startDate = startDateInput ? startDateInput.value : '';
            const endDate   = endDateInput   ? endDateInput.value   : '';
            const startTime = startTimeInput ? startTimeInput.value : '';
            const endTime   = endTimeInput   ? endTimeInput.value   : '';

            const params = new URLSearchParams({ type: selectedData });
            if (startDate) params.append('start_date', startDate);
            if (startTime) params.append('start_time', startTime);
            if (endDate)   params.append('end_date',   endDate);
            if (endTime)   params.append('end_time',   endTime);

            window.location.href = `/api/v1/export?${params.toString()}`;
        }
    }

    function triggerDownload(csvContent, filename) {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    function csvTimestamp() {
        return new Date().toISOString().slice(0, 19).replace(/[T:-]/g, '');
    }
});