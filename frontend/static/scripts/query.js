document.addEventListener('DOMContentLoaded', () => {
    const dataSelect = document.getElementById('data-select');
    const loadButton = document.getElementById('load-data-btn');
    const resultsDiv = document.getElementById('results-area');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');

    // NOTE: Removed the code that set the default date to 'today'. 
    // This allows the API to return all data when the fields are empty.
    
    // --- CORE LOGIC ---
    loadButton.addEventListener('click', fetchData);
    
    async function fetchData() {
        const selectedData = dataSelect.value;
        const startDate = startDateInput.value; 
        const endDate = endDateInput.value;

        if (!selectedData) {
            resultsDiv.innerHTML = '<p class="error">Please select a data source.</p>';
            return;
        }

        // Determine the correct API endpoint
        const endpointMap = {
            'sensor': '/api/v1/sensors',
            'weather': '/api/v1/weather',
            'combined': '/api/v1/combined' // Pre-existing endpoint name
        };
        
        const endpoint = endpointMap[selectedData];
        
        // Construct query parameters
        const params = new URLSearchParams();
        // Only append parameters if they have a value (i.e., not an empty string)
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        const url = `${endpoint}?${params.toString()}`;
        
        resultsDiv.innerHTML = '<p class="loading info">Loading data...</p>';
        
        try {
            const response = await fetch(url);
            
            // NOTE: The previous special "Combined" error handling has been removed.
            
            // Handle successful response with no data (204 No Content)
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
            // General catch for network or parsing errors (applies to all endpoints now)
            resultsDiv.innerHTML = `<p class="error">Network Error: ${e.message}. Check your server and API endpoints.</p>`;
        }
    }
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
    
    if (selected.length > 0) {
        container.style.display = 'block';
        countSpan.textContent = selected.length;
    } else {
        container.style.display = 'none';
    }
}

    // --- TABLE RENDERING (MODIFIED TO ENFORCE DATE/TIME ORDER) ---
    function renderTable(data, targetElement) {
        targetElement.innerHTML = ''; // Clear previous content

        // 1. Define the fixed order for the leading columns (must match API keys)
        const mandatoryHeaders = ['date', 'time']; 

        // 2. Get all unique headers from the first data row 
        const allHeaders = Object.keys(data[0]);

        // 3. Filter out the mandatory headers from the full list
        // This ensures they are not duplicated later.
        const remainingHeaders = allHeaders.filter(header => 
            !mandatoryHeaders.includes(header)
        );

        // 4. Combine: mandatory headers first, then the rest of the data columns
        const headers = [...mandatoryHeaders, ...remainingHeaders];

        let tableHTML = '<div class="table-container"><table class="data-table"><thead><tr>';
        
        // Create header row
        headers.forEach(header => {
            // Simple formatting: replace underscores with spaces, then capitalize first letter
            const displayHeader = header.replace(/_/g, ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
            tableHTML += `<th>${displayHeader}</th>`;
        });
        tableHTML += '</tr></thead><tbody>';

        // 5. Create data rows using the fixed 'headers' array for consistent cell ordering
        data.forEach(row => {
            tableHTML += '<tr>';

            headers.forEach(header => {
                const cellValue = row[header] !== undefined && row[header] !== null ? row[header] : 'N/A';
                tableHTML += `<td>${cellValue}</td>`;
            });

            const rowId = row.id || ''; 
            tableHTML += `<td><input type="checkbox" class="row-checkbox" value="${rowId}"></td>`;

            tableHTML += '</tr>';
        });

        tableHTML += '</tbody></table></div>';
        
        targetElement.innerHTML = tableHTML;
        
        updateActionMenu();
    }
});