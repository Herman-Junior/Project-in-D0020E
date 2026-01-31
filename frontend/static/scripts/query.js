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

        // 1. Mandatory order: Checkbox, then Date, then Time
        const mandatoryHeaders = ['date', 'time']; 
        const allHeaders = Object.keys(data[0]).filter(h => h !== 'id'); // Hide 'id' from view

        const remainingHeaders = allHeaders.filter(header => 
            !mandatoryHeaders.includes(header)
        );

        const headers = [...mandatoryHeaders, ...remainingHeaders];

        let tableHTML = '<div class="table-container"><table class="data-table"><thead><tr>';
        
        // Add Checkbox "Select All" header
        tableHTML += '<th><input type="checkbox" id="select-all-rows"></th>';

        headers.forEach(header => {
            const displayHeader = header.replace(/_/g, ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
            tableHTML += `<th>${displayHeader}</th>`;
        });
        tableHTML += '</tr></thead><tbody>';

        data.forEach(row => {
            tableHTML += '<tr>';
            
            // Add Row Checkbox
            const rowId = row.sensor_id || row.weather_id || row.id || "";
            tableHTML += `<td><input type="checkbox" class="row-checkbox" value="${rowId}"></td>`;

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
});