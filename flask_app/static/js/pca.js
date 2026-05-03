function createChart(ctx, isModal = false) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: window.pcaData.labels,
            datasets: [{
                label: 'Explained Variance Ratio (%)',
                data: window.pcaData.explainedVariance,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 2,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: !isModal,
            plugins: {
                title: {
                    display: true,
                    text: 'Scree Plot - Explained Variance by Principal Component',
                    font: {
                        size: isModal ? 20 : 14,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 30
                    }
                },
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            size: isModal ? 16 : 12
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Explained Variance (%)',
                        font: {
                            size: isModal ? 16 : 12
                        }
                    },
                    ticks: {
                        font: {
                            size: isModal ? 14 : 10
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Principal Components',
                        font: {
                            size: isModal ? 16 : 12
                        }
                    },
                    ticks: {
                        font: {
                            size: isModal ? 14 : 10
                        }
                    }
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Create main chart
    const mainChart = createChart(document.getElementById('screePlot').getContext('2d'));
    
    // Create modal chart when modal is shown
    const graphModal = document.getElementById('graphModal');
    graphModal.addEventListener('shown.bs.modal', function () {
        const modalChart = createChart(
            document.getElementById('modalScreenPlot').getContext('2d'),
            true
        );
    });

    // Handle graph download
    document.getElementById('downloadGraph').addEventListener('click', function() {
        const modalCanvas = document.getElementById('modalScreenPlot');
        const link = document.createElement('a');
        link.download = 'scree_plot.png';
        link.href = modalCanvas.toDataURL('image/png');
        link.click();
    });
});
