let chart;
let currentData;

document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('chartContainer').getContext('2d');
    
    function initChart() {
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Open Rate',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    initChart();

    // Handle metric selector change
    document.getElementById('metricSelector').addEventListener('change', function(e) {
        updateChart(e.target.value);
    });

    // Handle segmentation toggle
    document.getElementById('segmentationToggle').addEventListener('change', function(e) {
        fetchData(getCurrentTimePeriod(), e.target.checked ? 'daily' : null);
    });

    // Handle time period selection
    document.querySelectorAll('.time-period-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.time-period-btn').forEach(b => b.classList.remove('bg-blue-500', 'text-white'));
            this.classList.add('bg-blue-500', 'text-white');
            fetchData(this.dataset.period, document.getElementById('segmentationToggle').checked ? 'daily' : null);
        });
    });

    // Handle "View Details" button click
    document.getElementById('viewDetailsBtn').addEventListener('click', function() {
        // Implement modal or expanded view here
        console.log('View Details clicked', currentData);
    });

    function getCurrentTimePeriod() {
        return document.querySelector('.time-period-btn.bg-blue-500').dataset.period;
    }

    function fetchData(timePeriod, segmentation) {
        // Replace with your actual API endpoint
        fetch('/api/analytics/metrics/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')  // Implement getCookie function
            },
            body: JSON.stringify({
                time_period: timePeriod,
                segmentation: segmentation
            })
        })
        .then(response => response.json())
        .then(data => {
            currentData = data;
            updateDashboard(data);
        })
        .catch(error => console.error('Error:', error));
    }

    function updateDashboard(data) {
        if (Array.isArray(data)) {
            // Segmented data
            updateMetrics(data[data.length - 1]);  // Use the last (total) segment
            updateChart(document.getElementById('metricSelector').value, data);
        } else {
            // Non-segmented data
            updateMetrics(data);
            updateChart(document.getElementById('metricSelector').value, [data]);
        }
    }

    function updateMetrics(data) {
        document.querySelector('.total-sent').textContent = data.total_sent;
        document.querySelector('.open-rate').textContent = data.read_percentage.toFixed(2) + '%';
        document.querySelector('.click-rate').textContent = data.click_rate.toFixed(2) + '%';
        document.querySelector('.prospect-quality').textContent = data.prospect_quality.toFixed(2) + '%';
    }

    function updateChart(metric, data = currentData) {
        if (!data) return;

        const labels = data.map(d => d.period || 'Total');
        const values = data.map(d => d[metric]);

        chart.data.labels = labels;
        chart.data.datasets[0].data = values;
        chart.data.datasets[0].label = document.getElementById('metricSelector').options[document.getElementById('metricSelector').selectedIndex].text;
        chart.update();
    }

    // Initial data fetch
    fetchData('24hrs', null);
});

// Implement this function to get CSRF token from cookies
function getCookie(name) {
    // ... (CSRF token retrieval logic)
}