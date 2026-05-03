// Initialize styles once at the start
const modelStyles = document.createElement('style');
modelStyles.textContent = `
    .cluster-modal {
        display: none;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
        overflow-y: auto;
    }

    .cluster-modal-content {
        background-color: #fefefe;
        margin: 20px auto;
        padding: 20px;
        width: 95%;
        max-width: 1200px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        position: relative;
    }

    .cluster-modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        position: relative;
    }

    .cluster-modal-header h2 {
        margin: 0;
        color: #333;
        font-size: 1.5rem;
        width: 100%;
        text-align: center;
    }

    .close-btn {
        position: absolute;
        right: 0;
        top: 0;
        font-size: 24px;
        font-weight: bold;
        border: none;
        background: none;
        cursor: pointer;
        color: #666;
        padding: 0;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1;
    }

    .close-btn:hover {
        color: #000;
    }

    .cluster-modal-body {
        text-align: center;
        margin: 20px 0;
        overflow-x: hidden;
    }

    .cluster-modal-body img {
        max-width: 100%;
        width: auto;
        height: auto;
        display: block;
        margin: 0 auto;
    }

    .cluster-modal-footer {
        text-align: center;
        margin-top: 20px;
        padding: 15px;
    }

    .download-plot-btn {
        margin-top: 10px;
    }
`;
document.head.appendChild(modelStyles);

// Add polling functionality
async function pollTrainingStatus() {
    try {
        const response = await fetch(`/training_status/${window.currentTask}/${window.currentFileId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (data.status === 'error') {
            console.error('Error from server:', data.message);
            return;
        }

        if (data.model_statuses) {
            let allComplete = true;
            let anyError = false;
            let completedCount = 0;
            const totalModels = Object.keys(data.model_statuses).length;

            Object.entries(data.model_statuses).forEach(([modelId, modelStatus]) => {
                updateModelStatus(
                    modelId, 
                    modelStatus.status, 
                    modelStatus.message,
                    modelStatus.step
                );

                if (modelStatus.status === 'complete') {
                    completedCount++;
                } else if (modelStatus.status === 'error') {
                    anyError = true;
                    completedCount++;
                } else if (modelStatus.status !== 'complete') {
                    allComplete = false;
                }
            });

            // Update progress bar
            const percentage = Math.round((completedCount / totalModels) * 100);
            const progressBar = document.getElementById('training-progress-bar');
            if (progressBar) {
                progressBar.style.width = `${percentage}%`;
                progressBar.setAttribute('aria-valuenow', percentage);
                progressBar.textContent = `${percentage}%`;
            }

            if (allComplete || anyError) {
                document.getElementById('training-alert').style.display = 'none';
                
                try {
                    const resultsResponse = await fetch(`/model_results/${window.currentTask}/${window.currentFileId}`);
                    const resultsData = await resultsResponse.json();
                    
                    if (resultsData.success && resultsData.models) {
                        const resultsContainer = document.getElementById('results-table');
                        if (resultsContainer) {
                            resultsContainer.style.display = 'block';
                        }
                        updateResultsTable(resultsData.models);
                    }
                } catch (error) {
                    console.error('Error fetching results:', error);
                }
            } else {
                setTimeout(pollTrainingStatus, 2000);
            }
        }
    } catch (error) {
        console.error('Error polling training status:', error);
        setTimeout(pollTrainingStatus, 5000);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Start polling if we have valid parameters
    if (window.currentTask && window.currentTask !== 'null' && 
        window.currentFileId && window.currentFileId !== 'null') {
        pollTrainingStatus();
    }

    // Add toggle functionality
    document.querySelectorAll('.model-header').forEach(header => {
        header.addEventListener('click', function(e) {
            e.preventDefault();
            const stepsId = this.getAttribute('data-steps-id');
            const steps = document.getElementById(stepsId);
            const icon = this.querySelector('.toggle-icon');
            
            if (steps) {
                if (steps.style.display === 'none' || !steps.style.display) {
                    steps.style.display = 'block';
                    icon.classList.add('fa-rotate-90');
                } else {
                    steps.style.display = 'none';
                    icon.classList.remove('fa-rotate-90');
                }
            }
        });
    });

    // Add search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tbody = document.querySelector('#results-table tbody');
            const rows = tbody.getElementsByTagName('tr');

            Array.from(rows).forEach(row => {
                const modelName = row.cells[0].textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});

// Function to update model status
function updateModelStatus(modelId, status, message, step) {
    const statusElement = document.getElementById(`${modelId}-status`);
    if (!statusElement) return;

    let icon, text;
    switch (status) {
        case 'error':
            icon = 'fas fa-times-circle text-danger';
            text = `Error: ${message}`;
            break;
        case 'complete':
            icon = 'fas fa-check-circle text-success';
            text = 'Complete';
            break;
        case 'loading':
            icon = 'fas fa-circle-notch fa-spin text-primary';
            text = message || `Step ${step}: Processing...`;
            break;
        default:
            icon = 'fas fa-spinner fa-spin';
            text = 'Waiting...';
    }
    statusElement.innerHTML = `<i class="${icon}"></i> ${text}`;

    // Update steps
    for (let i = 1; i <= 3; i++) {
        updateStepStatus(
            `${modelId}-step-${i}`,
            i < step ? 'complete' : i === step ? status : 'waiting'
        );
    }
}

// Function to update step status
function updateStepStatus(stepId, status) {
    const stepElement = document.getElementById(stepId);
    if (!stepElement) return;

    let statusClass, iconClass;
    switch (status) {
        case 'error':
            statusClass = 'error';
            iconClass = 'fas fa-times-circle text-danger';
            break;
        case 'complete':
            statusClass = 'complete';
            iconClass = 'fas fa-check-circle text-success';
            break;
        case 'loading':
            statusClass = 'loading';
            iconClass = 'fas fa-circle-notch fa-spin text-primary';
            break;
        default:
            statusClass = 'waiting';
            iconClass = 'fas fa-circle text-muted';
    }

    stepElement.className = `step ${statusClass}`;
    const icon = stepElement.querySelector('i');
    if (icon) {
        icon.className = iconClass;
    }
}

// Function to update results table
function updateResultsTable(models) {
    const tbody = document.querySelector('#results-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    models.forEach(model => {
        const row = document.createElement('tr');
        
        if (window.currentTask === 'clustering') {
            const visualizationCell = model.metrics.visualization ? 
                `<button class="btn btn-sm btn-outline-primary view-clusters-btn" onclick="showClusterVisualization('${model.id}', '${model.name}', '${model.metrics.visualization}')">
                    <i class="fas fa-chart-scatter"></i> View Plot
                </button>` :
                '<span class="text-muted">Processing visualization...</span>';

            row.innerHTML = `
                <td>${model.name}</td>
                <td>${Number(model.metrics.silhouette).toFixed(4)}</td>
                <td>${Number(model.metrics.calinski_harabasz).toFixed(4)}</td>
                <td>${Number(model.metrics.davies_bouldin).toFixed(4)}</td>
                <td>${model.metrics.n_clusters}</td>
                <td>${visualizationCell}</td>
                <td>
                    <a href="/download_model/${model.id}" 
                       class="btn btn-sm btn-outline-primary"
                       download="${model.name.toLowerCase().replace(/\s+/g, '_')}.pkl">
                        <i class="fas fa-download"></i> Download
                    </a>
                </td>
            `;
        } else if (window.currentTask === 'classification') {
            row.innerHTML = `
                <td>${model.name}</td>
                <td>${(model.metrics.accuracy * 100).toFixed(2)}%</td>
                <td>${(model.metrics.precision * 100).toFixed(2)}%</td>
                <td>${(model.metrics.recall * 100).toFixed(2)}%</td>
                <td>${(model.metrics.f1 * 100).toFixed(2)}%</td>
                <td>
                    <a href="/download_model/${model.id}" 
                       class="btn btn-sm btn-outline-primary"
                       download="${model.name.toLowerCase().replace(/\s+/g, '_')}.pkl">
                        <i class="fas fa-download"></i> Download
                    </a>
                </td>
            `;
        } else if (window.currentTask === 'regression') {
            row.innerHTML = `
                <td>${model.name}</td>
                <td>${(model.metrics.r2 * 100).toFixed(2)}%</td>
                <td>${model.metrics.mse.toFixed(4)}</td>
                <td>${model.metrics.rmse.toFixed(4)}</td>
                <td>${model.metrics.mae.toFixed(4)}</td>
                <td>
                    <a href="/download_model/${model.id}" 
                       class="btn btn-sm btn-outline-primary"
                       download="${model.name.toLowerCase().replace(/\s+/g, '_')}.pkl">
                        <i class="fas fa-download"></i> Download
                    </a>
                </td>
            `;
        }
        tbody.appendChild(row);
    });

    // Show the results container
    const resultsContainer = document.getElementById('results-table');
    if (resultsContainer) {
        resultsContainer.style.display = 'block';
    }
}

// Function to show cluster visualization
function showClusterVisualization(modelId, modelName, plotData) {
    let modal = document.getElementById('clusterModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'clusterModal';
        modal.className = 'cluster-modal';
        modal.innerHTML = `
            <div class="cluster-modal-content">
                <div class="cluster-modal-header">
                    <button class="close-btn">&times;</button>
                    <h2>Cluster Visualization - ${modelName}</h2>
                </div>
                <div class="cluster-modal-body">
                    <img src="data:image/png;base64,${plotData}" 
                         alt="Cluster visualization">
                </div>
                <div class="cluster-modal-footer">
                    <a href="data:image/png;base64,${plotData}" 
                       download="${modelName.toLowerCase().replace(/\s+/g, '_')}_clusters.png"
                       class="btn btn-outline-primary">
                        <i class="fas fa-download"></i> Download Plot
                    </a>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        modal.querySelector('.close-btn').onclick = () => modal.style.display = 'none';
        window.onclick = (event) => {
            if (event.target === modal) modal.style.display = 'none';
        };
    } else {
        modal.querySelector('h2').textContent = `Cluster Visualization - ${modelName}`;
        modal.querySelector('img').src = `data:image/png;base64,${plotData}`;
        modal.querySelector('a').href = `data:image/png;base64,${plotData}`;
        modal.querySelector('a').download = `${modelName.toLowerCase().replace(/\s+/g, '_')}_clusters.png`;
    }

    modal.style.display = 'block';
}

// Add some CSS for search styling
const searchStyles = document.createElement('style');
searchStyles.textContent = `
    .search-container {
        position: relative;
        margin-bottom: 20px;
    }

    .search-input {
        width: 100%;
        padding: 10px 40px;
        border: 1px solid #ddd;
        border-radius: 5px;
        font-size: 14px;
        transition: border-color 0.3s ease;
    }

    .search-input:focus {
        outline: none;
        border-color: #365486;
        box-shadow: 0 0 0 2px rgba(54, 84, 134, 0.1);
    }

    .search-icon {
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        color: #666;
    }

    .search-input::placeholder {
        color: #999;
    }
`;
document.head.appendChild(searchStyles);