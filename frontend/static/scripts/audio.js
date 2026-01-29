document.addEventListener('DOMContentLoaded', () => {
    const content = document.getElementById('correlation-content');
    const title = document.getElementById('selected-audio-title');

    // --- 1. LIST PAGE LOGIC ---
    // This only runs if we are on the page with audio items
    const audioItems = document.querySelectorAll('.audio-item');
    audioItems.forEach(item => {
        item.addEventListener('click', () => {
            const audioId = item.getAttribute('data-audio-id');
            const filename = item.getAttribute('data-filename');
            window.location.href = `/audio/details?id=${audioId}&name=${encodeURIComponent(filename)}`;
        });
    });

    // --- 2. DETAILS PAGE LOGIC ---
    const urlParams = new URLSearchParams(window.location.search);
    const idFromUrl = urlParams.get('id');
    const nameFromUrl = urlParams.get('name');

    if (idFromUrl && content) {
        loadDetailData(idFromUrl, nameFromUrl);
    }

    async function loadDetailData(audioId, filename) {
        if (title) title.innerText = filename; // Sets header to audio name
        content.innerHTML = '<p class="status-message info">Fetching environmental data...</p>';

        try {
            const response = await fetch(`/api/v1/audio/environmental?audio_id=${audioId}`);
            if (!response.ok) throw new Error(`Status: ${response.status}`);
            const data = await response.json();
            
            renderData(data); 
        } catch (error) {
            content.innerHTML = `<p class="status-message error">Error: ${error.message}</p>`;
        }
    }

function renderData(data) {
    let html = '';

    if (!data.sensor_data?.length && !data.weather_data?.length) {
        content.innerHTML = '<p class="status-message info">No correlated data found for this recording.</p>';
        return;
    }

    // --- SENSOR TABLE ---
    if (data.sensor_data?.length > 0) {
        html += '<h2 class="section-title">Correlated Sensor Data</h2>';
        html += '<div class="table-container"><table class="data-table"><thead><tr>';
        html += '<th>Date</th><th>Time</th><th>Moisture</th>'; // Split header
        html += '</tr></thead><tbody>';
        
        data.sensor_data.forEach(s => {
            const [date, time] = s.timestamp.split(' '); // Split "YYYY-MM-DD HH:MM:SS"
            html += `<tr>
                <td>${date}</td>
                <td>${time}</td>
                <td>${s.moisture}%</td>
            </tr>`;
        });
        html += '</tbody></table></div>';
    }

    // --- WEATHER TABLE ---
    if (data.weather_data?.length > 0) {
        html += '<h2 class="section-title">Correlated Weather Data</h2>';
        html += '<div class="table-container"><table class="data-table"><thead><tr>';
        // Headers matching your request
        html += '<th>Date</th><th>Time</th><th>Daily Rain</th><th>In Hum</th><th>In Temp</th><th>Out Hum</th><th>Out Temp</th><th>Rain Rate</th><th>Wind Dir</th><th>Wind Speed</th>';
        html += '</tr></thead><tbody>';
        
        data.weather_data.forEach(w => {
            const [date, time] = w.timestamp.split(' ');
            html += `<tr>
                <td>${date}</td>
                <td>${time}</td>
                <td>${w.daily_rain || 0} mm</td>
                <td>${w.in_humidity || 0}%</td>
                <td>${w.in_temperature || 0}°C</td>
                <td>${w.out_humidity || 0}%</td>
                <td>${w.out_temperature || 0}°C</td>
                <td>${w.rain_rate || 0} mm/h</td>
                <td>${w.wind_direction || 'N/A'}</td>
                <td>${w.wind_speed || 0} m/s</td>
            </tr>`;
        });
        html += '</tbody></table></div>';
    }

    content.innerHTML = html; 
}
});