// AI Trends Analyzer - Charts and Visualization

// Chart configuration and management
const ChartsManager = {
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20,
                    font: {
                        family: 'Roboto, sans-serif',
                        size: 12
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: '#0d6efd',
                borderWidth: 1,
                cornerRadius: 8,
                displayColors: false,
                callbacks: {
                    title: function(tooltipItems) {
                        return tooltipItems[0].label;
                    },
                    label: function(context) {
                        const label = context.dataset.label || '';
                        const value = typeof context.parsed.y === 'number' 
                            ? context.parsed.y.toFixed(2) 
                            : context.parsed.y;
                        return `${label}: ${value}`;
                    }
                }
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: {
                        family: 'Roboto, sans-serif',
                        size: 11
                    },
                    color: '#6c757d'
                }
            },
            y: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)',
                    borderDash: [5, 5]
                },
                ticks: {
                    font: {
                        family: 'Roboto, sans-serif',
                        size: 11
                    },
                    color: '#6c757d'
                }
            }
        }
    },

    colors: {
        primary: '#0d6efd',
        secondary: '#6c757d',
        success: '#198754',
        danger: '#dc3545',
        warning: '#ffc107',
        info: '#0dcaf0',
        light: '#f8f9fa',
        dark: '#212529'
    },

    charts: new Map()
};

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAllCharts();
});

function initializeAllCharts() {
    // Initialize trend score charts
    initializeTrendScoreCharts();
    
    // Initialize mini charts in trend cards
    initializeMiniCharts();
    
    // Initialize dashboard overview charts
    initializeDashboardCharts();
    
    console.log('All charts initialized successfully');
}

// Trend Score Charts (for detail pages)
function initializeTrendScoreCharts() {
    const trendScoreCanvas = document.getElementById('trendScoreChart');
    if (!trendScoreCanvas) return;

    const ctx = trendScoreCanvas.getContext('2d');
    
    // Get data from global scope (should be set by the template)
    const scoreHistory = window.scoreHistory || [];
    
    if (scoreHistory.length === 0) {
        showEmptyChartState(ctx, 'No score history available');
        return;
    }

    // Prepare data
    const labels = scoreHistory.map(item => {
        const date = new Date(item[0]);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric' 
        });
    });
    
    const data = scoreHistory.map(item => parseFloat(item[1]) || 0);
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(13, 110, 253, 0.2)');
    gradient.addColorStop(1, 'rgba(13, 110, 253, 0.02)');

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Trend Score',
                data: data,
                borderColor: ChartsManager.colors.primary,
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: ChartsManager.colors.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8,
                pointHoverBackgroundColor: ChartsManager.colors.primary,
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 3
            }]
        },
        options: {
            ...ChartsManager.defaultOptions,
            plugins: {
                ...ChartsManager.defaultOptions.plugins,
                legend: {
                    display: false
                },
                tooltip: {
                    ...ChartsManager.defaultOptions.plugins.tooltip,
                    callbacks: {
                        title: function(tooltipItems) {
                            return `Date: ${tooltipItems[0].label}`;
                        },
                        label: function(context) {
                            return `Score: ${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                ...ChartsManager.defaultOptions.scales,
                y: {
                    ...ChartsManager.defaultOptions.scales.y,
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Trend Score',
                        font: {
                            family: 'Roboto, sans-serif',
                            size: 12,
                            weight: 'bold'
                        }
                    }
                },
                x: {
                    ...ChartsManager.defaultOptions.scales.x,
                    title: {
                        display: true,
                        text: 'Date',
                        font: {
                            family: 'Roboto, sans-serif',
                            size: 12,
                            weight: 'bold'
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });

    ChartsManager.charts.set('trendScore', chart);
}

// Mini Charts for Trend Cards
function initializeMiniCharts() {
    const miniChartCanvases = document.querySelectorAll('.trend-mini-chart');
    
    miniChartCanvases.forEach((canvas, index) => {
        const scoresData = canvas.dataset.scores;
        if (!scoresData) return;

        const scores = scoresData.split(',').map(num => parseFloat(num.trim()) || 0);
        if (scores.length < 2) return;

        const ctx = canvas.getContext('2d');
        
        // Create sparkline chart
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: scores.map((_, i) => i + 1),
                datasets: [{
                    data: scores,
                    borderColor: ChartsManager.colors.success,
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                scales: {
                    x: { display: false },
                    y: { display: false }
                },
                elements: {
                    point: { radius: 0 }
                },
                animation: {
                    duration: 800,
                    delay: index * 100,
                    easing: 'easeInOutCubic'
                }
            }
        });

        ChartsManager.charts.set(`miniChart_${index}`, chart);
    });
}

// Dashboard Overview Charts
function initializeDashboardCharts() {
    // This could be extended to show overall trend statistics
    // For now, we'll prepare the structure
    initializeOverviewStatsChart();
}

function initializeOverviewStatsChart() {
    const overviewCanvas = document.getElementById('overviewChart');
    if (!overviewCanvas) return;

    const ctx = overviewCanvas.getContext('2d');
    
    // Mock data for demonstration - in real app this would come from API
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['AI Models', 'AI Tools', 'AI Ethics', 'AI News', 'Other'],
            datasets: [{
                data: [30, 25, 15, 20, 10],
                backgroundColor: [
                    ChartsManager.colors.primary,
                    ChartsManager.colors.success,
                    ChartsManager.colors.warning,
                    ChartsManager.colors.info,
                    ChartsManager.colors.secondary
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const percentage = ((context.parsed / context.dataset.data.reduce((a, b) => a + b, 0)) * 100).toFixed(1);
                            return `${context.label}: ${percentage}%`;
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                duration: 1200
            }
        }
    });

    ChartsManager.charts.set('overview', chart);
}

// Chart Utility Functions
function showEmptyChartState(ctx, message = 'No data available') {
    const canvas = ctx.canvas;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw empty state
    ctx.fillStyle = '#6c757d';
    ctx.font = '16px Roboto, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(message, canvas.width / 2, canvas.height / 2);
}

function updateChart(chartId, newData) {
    const chart = ChartsManager.charts.get(chartId);
    if (!chart) return;

    // Update data
    chart.data = newData;
    chart.update('active');
}

function destroyChart(chartId) {
    const chart = ChartsManager.charts.get(chartId);
    if (chart) {
        chart.destroy();
        ChartsManager.charts.delete(chartId);
    }
}

function resizeAllCharts() {
    ChartsManager.charts.forEach(chart => {
        chart.resize();
    });
}

// Chart Color Utilities
function generateColors(count, baseColor = ChartsManager.colors.primary) {
    const colors = [];
    const hsl = hexToHsl(baseColor);
    
    for (let i = 0; i < count; i++) {
        const hue = (hsl.h + (i * 360 / count)) % 360;
        colors.push(hslToHex(hue, hsl.s, hsl.l));
    }
    
    return colors;
}

function hexToHsl(hex) {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;

    if (max === min) {
        h = s = 0;
    } else {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }

    return { h: h * 360, s: s * 100, l: l * 100 };
}

function hslToHex(h, s, l) {
    l /= 100;
    const a = s * Math.min(l, 1 - l) / 100;
    const f = n => {
        const k = (n + h / 30) % 12;
        const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
        return Math.round(255 * color).toString(16).padStart(2, '0');
    };
    return `#${f(0)}${f(8)}${f(4)}`;
}

// Responsive chart handling
window.addEventListener('resize', debounce(resizeAllCharts, 250));

// Export global functions
window.ChartsManager = ChartsManager;
window.initializeTrendScoreCharts = initializeTrendScoreCharts;
window.initializeMiniCharts = initializeMiniCharts;
window.updateChart = updateChart;
window.destroyChart = destroyChart;

console.log('Charts.js loaded successfully');
