document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchData();

    // Refresh every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchData();
    }, 30000);

    document.getElementById('refresh-btn').addEventListener('click', async () => {
        const btn = document.getElementById('refresh-btn');
        const icon = btn.querySelector('i');

        // Animation
        icon.classList.add('fa-spin');
        btn.disabled = true;
        btn.style.opacity = '0.7';

        try {
            const response = await fetch('/api/refresh', { method: 'POST' });
            const res = await response.json();
            if (res.status === 'success') {
                // Wait a bit for the pipeline to likely finish (it's async, but give UI feedback)
                // In a real app, we'd poll for status. Here we just wait 2s then refresh data.
                setTimeout(() => {
                    fetchStats();
                    fetchData();
                    icon.classList.remove('fa-spin');
                    btn.disabled = false;
                    btn.style.opacity = '1';
                }, 2000);
            } else {
                alert('Refresh failed: ' + res.message);
                icon.classList.remove('fa-spin');
                btn.disabled = false;
                btn.style.opacity = '1';
            }
        } catch (error) {
            console.error('Error refreshing:', error);
            icon.classList.remove('fa-spin');
            btn.disabled = false;
            btn.style.opacity = '1';
        }
    });
});

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('stat-risk').textContent = data.high_risk;
        document.getElementById('stat-opportunity').textContent = data.opportunity;
        document.getElementById('stat-events').textContent = data.major_events;
        document.getElementById('stat-total').textContent = data.total_articles;
        if (data.last_updated) {
            document.getElementById('last-updated').textContent = 'Last Updated: ' + data.last_updated;
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

let impactChart = null;
let opsChart = null;

async function fetchData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();

        updateFeed(data);
        updateCharts(data);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function updateFeed(data) {
    const container = document.getElementById('feed-container');
    container.innerHTML = '';

    if (!data || data.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--text-secondary);">
                <i class="fa-solid fa-spinner fa-spin" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>Waiting for intelligence data... Click "Refresh" to trigger an immediate scan.</p>
            </div>
        `;
        return;
    }

    // Sort by impact score absolute value descending (most important first)
    const sortedData = data.sort((a, b) => Math.abs(b.impact_score) - Math.abs(a.impact_score)).slice(0, 20);

    sortedData.forEach(item => {
        const div = document.createElement('div');
        div.className = 'feed-item';

        const impactClass = `impact-${item.impact_level.toLowerCase().replace(' ', '-')}`;

        div.innerHTML = `
            <div class="feed-header">
                <span class="source-badge">${item.Source}</span>
                <span class="impact-badge ${impactClass}">${item.impact_level}</span>
            </div>
            <div class="feed-title">${item.Title}</div>
            <div class="feed-summary">${item.Summary}</div>
            <div class="feed-footer">
                <div class="tags">
                    <span class="tag">${item.operational_tag}</span>
                    ${item.event_flag !== 'Normal' ? `<span class="tag" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b;">${item.event_flag}</span>` : ''}
                </div>
                <a href="${item.Link}" target="_blank" style="color: var(--accent); text-decoration: none;"><i class="fa-solid fa-external-link-alt"></i></a>
            </div>
        `;
        container.appendChild(div);
    });
}

function updateCharts(data) {
    // Impact Distribution
    const impactCounts = {};
    data.forEach(d => {
        impactCounts[d.impact_level] = (impactCounts[d.impact_level] || 0) + 1;
    });

    const impactLabels = ["High Risk", "Risk", "Neutral", "Opportunity", "High Opportunity"];
    const impactValues = impactLabels.map(l => impactCounts[l] || 0);

    const ctxImpact = document.getElementById('impactChart').getContext('2d');

    if (impactChart) {
        impactChart.data.datasets[0].data = impactValues;
        impactChart.update();
    } else {
        impactChart = new Chart(ctxImpact, {
            type: 'doughnut',
            data: {
                labels: impactLabels,
                datasets: [{
                    data: impactValues,
                    backgroundColor: [
                        '#ef4444', // High Risk
                        'rgba(239, 68, 68, 0.6)', // Risk
                        '#94a3b8', // Neutral
                        'rgba(34, 197, 94, 0.6)', // Opportunity
                        '#22c55e'  // High Opportunity
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#94a3b8' }
                    }
                }
            }
        });
    }

    // Operational Categories
    const opsCounts = {};
    data.forEach(d => {
        const tags = d.operational_tag.split(', ');
        tags.forEach(t => {
            if (t !== 'general') {
                opsCounts[t] = (opsCounts[t] || 0) + 1;
            }
        });
    });

    const opsLabels = Object.keys(opsCounts);
    const opsValues = Object.values(opsCounts);

    const ctxOps = document.getElementById('opsChart').getContext('2d');

    if (opsChart) {
        opsChart.data.labels = opsLabels;
        opsChart.data.datasets[0].data = opsValues;
        opsChart.update();
    } else {
        opsChart = new Chart(ctxOps, {
            type: 'bar',
            data: {
                labels: opsLabels,
                datasets: [{
                    label: 'Count',
                    data: opsValues,
                    backgroundColor: '#3b82f6',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}
