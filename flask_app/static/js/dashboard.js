function showInModal(imgElement) {
    const modal = new bootstrap.Modal(document.getElementById('chartModal'));
    const modalTitle = document.querySelector('#chartModal .modal-title');
    const modalContainer = document.querySelector('#modal-plot-container');
    
    modalTitle.textContent = imgElement.dataset.title;
    modalContainer.innerHTML = '';

    // Check if it's a 3D plot
    const plotDiv = imgElement.closest('.visualization-card').querySelector('.plot-container');
    if (plotDiv && plotDiv.classList.contains('js-plotly-plot')) {
        // Create new div for modal plot
        const modalPlotDiv = document.createElement('div');
        modalPlotDiv.style.width = '100%';
        modalPlotDiv.style.height = '85vh';  // Use viewport height
        modalContainer.appendChild(modalPlotDiv);

        // Get the data from original plot
        const originalPlot = plotDiv.data;
        
        // Modal-specific layout
        const modalLayout = {
            autosize: true,
            margin: {
                l: 20,
                r: 20,
                t: 10,
                b: 10,
                pad: 0
            },
            scene: {
                camera: {
                    eye: {x: 1.8, y: 1.8, z: 1.5},
                    up: {x: 0, y: 0, z: 1}
                },
                aspectratio: {x: 1, y: 1, z: 0.8},
                xaxis: { title: { text: 'X', standoff: 0 } },
                yaxis: { title: { text: 'Y', standoff: 0 } },
                zaxis: { title: { text: 'Z', standoff: 0 } }
            },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            showlegend: false
        };

        Plotly.newPlot(modalPlotDiv, originalPlot, modalLayout, {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToAdd: ['toImage']
        });

        // Adjust plot after modal is shown
        modal._element.addEventListener('shown.bs.modal', function() {
            Plotly.relayout(modalPlotDiv, {
                width: modalContainer.clientWidth,
                height: modalContainer.clientHeight
            });
        });
    } else {
        // Handle 2D images
        const highResImg = new Image();
        highResImg.src = imgElement.src;
        highResImg.style.maxWidth = '98%';
        highResImg.style.maxHeight = '85vh';
        highResImg.style.objectFit = 'contain';
        highResImg.style.margin = 'auto';
        modalContainer.appendChild(highResImg);
    }
    
    modal.show();
}

document.addEventListener('DOMContentLoaded', function() {
    const customVizForm = document.getElementById('customVizForm');
    const visualizationsGrid = document.getElementById('visualizationsGrid');
    const dimensionSelect = document.getElementById('dimension');
    const zAxisContainer = document.getElementById('zAxisContainer');
    const plotTypeSelect = document.getElementById('plotType');
    const vizTypeButtons = document.querySelectorAll('.viz-type-btn');
    
    // Visualization type selection
    vizTypeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update button states
            vizTypeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            const selectedType = this.dataset.type;
            
            // Show/hide custom visualization form
            customVizForm.style.display = selectedType === 'custom' ? 'block' : 'none';
            
            // Show/hide visualizations
            const vizCards = document.querySelectorAll('.viz-card');
            vizCards.forEach(card => {
                if (selectedType === 'all') {
                    card.style.display = 'block';
                } else if (selectedType === 'custom') {
                    card.style.display = 'none';
                } else {
                    card.style.display = card.dataset.type === selectedType ? 'block' : 'none';
                }
            });
        });
    });

    // Dimension change handler
    dimensionSelect.addEventListener('change', function() {
        zAxisContainer.style.display = this.value === '3d' ? 'block' : 'none';
        
        // Update plot types based on dimension
        const plotTypes = this.value === '3d' 
            ? ['scatter', 'line', 'surface']
            : ['scatter', 'line', 'bar', 'box', 'violin', 'heatmap'];
            
        plotTypeSelect.innerHTML = plotTypes
            .map(type => `<option value="${type}">${type.charAt(0).toUpperCase() + type.slice(1)} Plot</option>`)
            .join('');
    });

    // Custom visualization form submission
    customVizForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        try {
            const dimension = dimensionSelect.value;
            const plotType = plotTypeSelect.value;
            const xColumn = document.getElementById('xColumn').value;
            const yColumn = document.getElementById('yColumn').value;
            const columns = [xColumn, yColumn];
            
            if (dimension === '3d') {
                const zColumn = document.getElementById('zColumn').value;
                if (!zColumn) {
                    alert('Please select a Z-axis column for 3D visualization');
                    return;
                }
                columns.push(zColumn);
            }

            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';

            // Create visualization
            fetch('/create_visualization', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    plot_type: plotType,
                    columns: columns,
                    dimension: dimension
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server error: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data.success) {
                    throw new Error(data.error || 'Failed to create visualization');
                }

                const viz = data.visualization;
                const timestamp = Date.now();
                const plotId = `plot-${timestamp}`;

                // Create visualization card
                const newVizHTML = `
                    <div class="col-md-6 mb-4 viz-card" data-type="custom">
                        <div class="card visualization-card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5>${viz.title}</h5>
                                <button class="btn btn-sm btn-outline-primary download-btn" 
                                        ${viz.type !== '3d' ? `data-image="${viz.data}"` : ''}
                                        data-title="${viz.title}"
                                        data-type="${viz.type}">
                                    <i class="bi bi-download"></i> Download
                                </button>
                            </div>
                            <div class="card-body">
                                ${viz.type === '3d' 
                                    ? `<div id="${plotId}" class="plot-container"></div>`
                                    : `<img src="data:image/png;base64,${viz.data}" 
                                           alt="${viz.title}"
                                           class="img-fluid chart-img"
                                           data-title="${viz.title}"
                                           style="cursor: pointer;"
                                           onclick="showInModal(this)">`
                                }
                            </div>
                        </div>
                    </div>`;

                visualizationsGrid.insertAdjacentHTML('afterbegin', newVizHTML);

                // Handle 3D plot creation
                if (viz.type === '3d') {
                    const plotDiv = document.getElementById(plotId);
                    if (!plotDiv) {
                        throw new Error('Plot container not found');
                    }

                    const plotData = JSON.parse(viz.data);
                    const layout = {
                        autosize: true,
                        width: plotDiv.clientWidth,
                        height: 500,
                        margin: {
                            l: 20,
                            r: 20,
                            t: 8,
                            b: 10,
                            pad: 0
                        },
                        scene: {
                            camera: {
                                eye: {x: 1.8, y: 1.8, z: 1.5},
                                up: {x: 0, y: 0, z: 1}
                            },
                            aspectratio: {x: 1, y: 1, z: 0.8},
                            xaxis: { 
                                title: { text: columns[0], standoff: 0 },
                                gridcolor: '#ddd'
                            },
                            yaxis: { 
                                title: { text: columns[1], standoff: 0 },
                                gridcolor: '#ddd'
                            },
                            zaxis: { 
                                title: { text: columns[2], standoff: 0 },
                                gridcolor: '#ddd'
                            }
                        },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        showlegend: false
                    };

                    const config = {
                        responsive: true,
                        displayModeBar: true,
                        displaylogo: false,
                        modeBarButtonsToAdd: ['toImage'],
                        toImageButtonOptions: {
                            format: 'png',
                            filename: 'plot',
                            height: 800,
                            width: 1200,
                            scale: 2
                        }
                    };

                    Plotly.newPlot(plotDiv, plotData, layout, config).catch(error => {
                        console.error('Plotly error:', error);
                        throw new Error(`Error creating 3D plot: ${error.message}`);
                    });

                    plotDiv.addEventListener('click', function() {
                        showInModal(this);
                    });
                }

                // Add download handler
                const newDownloadBtn = visualizationsGrid.querySelector('.viz-card:first-child .download-btn');
                addDownloadHandler(newDownloadBtn);

            })
            .catch(error => {
                console.error('Visualization error:', error);
                alert(`Error creating visualization: ${error.message}`);
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            });
        } catch (error) {
            console.error('Form submission error:', error);
            alert(`Error submitting form: ${error.message}`);
        }
    });

    // Separate function for download handler
    function addDownloadHandler(button) {
        button.addEventListener('click', function() {
            try {
                const type = this.dataset.type;
                const title = this.dataset.title;
                
                if (type === '3d') {
                    const plotDiv = this.closest('.visualization-card').querySelector('.plot-container');
                    if (!plotDiv) {
                        throw new Error('Plot container not found');
                    }
                    
                    Plotly.downloadImage(plotDiv, {
                        format: 'png',
                        width: 1200,
                        height: 800,
                        filename: title.replace(/[^a-z0-9]/gi, '_').toLowerCase(),
                        scale: 2
                    }).catch(error => {
                        throw new Error(`Download failed: ${error.message}`);
                    });
                } else {
                    const imageData = this.dataset.image;
                    if (!imageData) {
                        throw new Error('Image data not found');
                    }
                    
                    const link = document.createElement('a');
                    link.href = `data:image/png;base64,${imageData}`;
                    link.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.png`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }
            } catch (error) {
                console.error('Download error:', error);
                alert(`Error downloading plot: ${error.message}`);
            }
        });
    }

    // Initialize click handlers for existing chart images
    document.querySelectorAll('.chart-img').forEach(img => {
        img.addEventListener('click', function() {
            showInModal(this);
        });
    });

    // Add the download functionality
    document.querySelectorAll('.download-btn').forEach(button => {
        button.addEventListener('click', function() {
            const imageData = this.dataset.image;
            const title = this.dataset.title;
            
            // Create a temporary link element
            const link = document.createElement('a');
            link.href = `data:image/png;base64,${imageData}`;
            link.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.png`;
            
            // Append to body, click, and remove
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    });

    // For custom visualizations created dynamically
    function addDownloadButtonToNewViz(vizElement, viz) {
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'btn btn-sm btn-outline-primary download-btn';
        downloadBtn.innerHTML = '<i class="bi bi-download"></i> Download';
        
        if (viz.type === '3d') {
            downloadBtn.addEventListener('click', function() {
                const plotDiv = vizElement.querySelector('.plot-container');
                Plotly.downloadImage(plotDiv, {
                    format: 'png',
                    filename: viz.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()
                });
            });
        } else {
            downloadBtn.addEventListener('click', function() {
                const link = document.createElement('a');
                link.href = `data:image/png;base64,${viz.data}`;
                link.download = `${viz.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.png`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });
        }
        
        return downloadBtn;
    }

    // Add hover effects for both close and return buttons
    const closeBtn = document.querySelector('#chartModal .btn-close');
    const returnBtn = document.querySelector('.return-btn');
    
    [closeBtn, returnBtn].forEach(btn => {
        btn.addEventListener('mouseover', function() {
            this.style.opacity = '0.8';
            this.style.transform = 'scale(1.1)';
            if (this.classList.contains('return-btn')) {
                this.style.color = 'red';
            }
        });
        
        btn.addEventListener('mouseout', function() {
            this.style.opacity = '1';
            this.style.transform = 'scale(1)';
            if (this.classList.contains('return-btn')) {
                this.style.color = '';
            }
        });
    });
});