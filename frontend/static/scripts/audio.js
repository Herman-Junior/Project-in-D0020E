document.addEventListener('DOMContentLoaded', () => {
    // Select the panel elements
    const panel = document.getElementById('correlation-panel');
    const content = document.getElementById('correlation-content');
    const title = document.getElementById('selected-audio-title');

    // 1. Attach click events to all audio items in the list
    const audioItems = document.querySelectorAll('.audio-item');
    
    audioItems.forEach(item => {
        item.addEventListener('click', async () => {
            const audioId = item.getAttribute('data-audio-id');
            const filename = item.getAttribute('data-filename');

            // UI: Show the panel and a loading state
            panel.style.display = 'block';
            title.innerText = `Correlated Data for: ${filename}`;
            content.innerHTML = '<p class="status-message info">Fetching environmental data...</p>';

            try {
                // 2. Fetch data from the endpoint we updated in routes.py
                const response = await fetch(`/api/v1/audio/environmental?audio_id=${audioId}`);
                
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }

                const data = await response.json();

                // 3. Logic Check: Does the returned object have any data in either list?
                const hasSensorData = data.sensor_data && data.sensor_data.length > 0;
                const hasWeatherData = data.weather_data && data.weather_data.length > 0;

                if (hasSensorData || hasWeatherData) {
                    renderData(data, content);
                } else {
                    content.innerHTML = '<p class="status-message info">No matching environmental data found for this specific timeframe.</p>';
                }
                
                // Smooth scroll to the results
                panel.scrollIntoView({ behavior: 'smooth' });

            } catch (error) {
                console.error("Fetch Error:", error);
                content.innerHTML = `<p class="status-message error">Error fetching data: ${error.message}</p>`;
            }
        });
    });

    /**
     * Renders both Sensor and Weather data into the container
     */
function renderData(data, container) {
    let html = '';

    // 1. SENSOR DATA TABLE
    if (data.sensor_data && data.sensor_data.length > 0) {
        html += '<h3 class="data-section-title">Correlated Sensor Data</h3>';
        html += '<div class="table-container"><table class="data-table"><thead><tr>';
        html += '<th>Timestamp</th><th>Moisture</th>';
        html += '</tr></thead><tbody>';
        
        data.sensor_data.forEach(s => {
            html += `<tr>
                <td>${s.timestamp}</td>
                <td>${s.moisture}%</td>
            </tr>`;
        });
        html += '</tbody></table></div>';
    }

    // 2. WEATHER DATA TABLE (All values included)
    if (data.weather_data && data.weather_data.length > 0) {
        html += '<h3 class="data-section-title">Correlated Weather Data</h3>';
        html += '<div class="table-container"><table class="data-table"><thead><tr>';
        html += '<th>Timestamp</th><th>In Temp</th><th>Out Temp</th><th>In Hum</th><th>Out Hum</th><th>Wind Speed</th><th>Direction</th><th>Rain Rate</th>';
        html += '</tr></thead><tbody>';
        
        data.weather_data.forEach(w => {
            html += `<tr>
                <td>${w.timestamp}</td>
                <td>${w.in_temperature || 0}°C</td>
                <td>${w.out_temperature || 0}°C</td>
                <td>${w.in_humidity || 0}%</td>
                <td>${w.out_humidity || 0}%</td>
                <td>${w.wind_speed || 0} m/s</td>
                <td>${w.wind_direction || 'N/A'}</td>
                <td>${w.rain_rate || 0} mm/h</td>
            </tr>`;
        });
        html += '</tbody></table></div>';
    }

    container.innerHTML = html;
}
});