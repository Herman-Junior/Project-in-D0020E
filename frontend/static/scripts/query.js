document.addEventListener('DOMContentLoaded', () => {
    const dataSelect = document.getElementById('data-select');
    const loadButton = document.getElementById('load-data-btn');
    const resultsDiv = document.getElementById('results-area');
    
    // Select the inputs - using optional chaining to prevent crashes
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const startTimeInput = document.getElementById('start-time'); // Added
    const endTimeInput = document.getElementById('end-time');     // Added

    // --- CORE LOGIC ---
    loadButton.addEventListener('click', fetchData);
    
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
            const rowId = row.id || ''; 
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
        
        updateActionMenu();
    }
});