// Add this at the start of your file, before the DOMContentLoaded event
function resetModelPage() {
    // Reset file upload elements
    const uploadProgress = document.querySelector('.upload-progress');
    const progressFill = document.querySelector('.progress-fill');
    const uploadStatus = document.querySelector('.upload-status .filename');
    const uploadSuccess = document.querySelector('.upload-success');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const fileInput = document.getElementById('fileInput');

    if (uploadProgress) uploadProgress.style.display = 'none';
    if (progressFill) progressFill.style.width = '0%';
    if (uploadStatus) uploadStatus.textContent = '';
    if (uploadSuccess) uploadSuccess.style.display = 'none';
    if (loadingSpinner) loadingSpinner.style.display = 'none';
    if (fileInput) fileInput.value = '';

    // Reset target variable elements
    const targetVariableContainer = document.getElementById('target-variable-container');
    const targetVariableInput = document.getElementById('target-variable-input');
    const targetVariableName = document.getElementById('target-variable-name');

    if (targetVariableContainer) targetVariableContainer.style.display = 'none';
    if (targetVariableInput) targetVariableInput.style.display = 'none';
    if (targetVariableName) targetVariableName.innerHTML = '<option value="">Select a column</option>';

    // Reset PCA config if exists
    const pcaConfig = document.getElementById('pca-config-section');
    if (pcaConfig) pcaConfig.remove();

    // Reset task selection
    const taskInputs = document.querySelectorAll('input[name="task"]');
    taskInputs.forEach(input => input.checked = false);

    // Reset task preview
    const taskPreview = document.getElementById('task-preview');
    if (taskPreview) {
        taskPreview.classList.add('d-none');
        const previewText = taskPreview.querySelector('p');
        if (previewText) previewText.textContent = '';
    }

    // Reset continue button
    const continueBtn = document.getElementById('continue-btn');
    if (continueBtn) continueBtn.disabled = true;

    // Reset form hidden inputs
    const form = document.getElementById('task-form');
    if (form) {
        document.getElementById('selected-task').value = '';
        document.getElementById('selected-dataset').value = '';
        document.getElementById('has-target').value = 'false';
        document.getElementById('target-variable-input-name').value = '';
        document.getElementById('file-id').value = '';
    }

    // Reset current file ID
    currentFileId = null;
}

// Add page visibility change handler
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && window.location.pathname.includes('/models')) {
        resetModelPage();
    }
});

// Add page load/reload handler
window.addEventListener('load', function() {
    if (window.location.pathname.includes('/models')) {
        resetModelPage();
    }
});

// Update your existing DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', function() {
    // First reset the page
    if (window.location.pathname.includes('/models')) {
        resetModelPage();
    }

    // Your existing initialization code...
    const taskInputs = document.querySelectorAll('input[name="task"]');
    const targetVariableCheckbox = document.getElementById('target-variable');
    const targetVariableInput = document.getElementById('target-variable-input');
    const taskPreview = document.getElementById('task-preview');
    const continueBtn = document.getElementById('continue-btn');
    const btnContainer = document.querySelector('.btn-conteiner');
    const fileInput = document.getElementById('fileInput');
    const uploadProgress = document.querySelector('.upload-progress');
    const progressFill = document.querySelector('.progress-fill');
    const uploadStatus = document.querySelector('.upload-status .filename');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const uploadSuccess = document.querySelector('.upload-success');
    const uploadedFilename = document.querySelector('.uploaded-filename');
    let currentFileId = null;

    if (!taskInputs || !targetVariableCheckbox || !targetVariableInput || !taskPreview || 
        !continueBtn || !btnContainer || !fileInput || !uploadProgress || !progressFill || 
        !uploadStatus || !loadingSpinner || !uploadSuccess || !uploadedFilename) {
        console.error('Some required elements are missing');
        return;
    }

    const tasks = {
        classification: "Classification helps to categorize data, such as determining if an email is spam or not.",
        regression: "Regression helps predict numerical values, like estimating house prices based on features.",
        clustering: "Clustering groups similar data points together, useful for customer segmentation or anomaly detection.",
        dimensionality_reduction: "Dimensionality reduction simplifies complex data while preserving important information, aiding in visualization and efficiency."
    };

    function checkConditions() {
        const isTaskSelected = Array.from(taskInputs).some(input => input.checked);
        const isFileSelected = fileInput.files.length > 0;
        const hasTarget = targetVariableCheckbox.checked;
        const targetSelected = hasTarget ? document.getElementById('target-variable-name')?.value !== '' : true;
        
        if (isTaskSelected && isFileSelected && targetSelected) {
            btnContainer.style.display = 'flex';
            continueBtn.disabled = false;
        } else {
            btnContainer.style.display = 'none';
            continueBtn.disabled = true;
        }
    }

    function updateTargetVariableVisibility(taskId) {
        if (taskId === 'classification' || taskId === 'regression') {
            // For classification and regression, automatically show target selection
            targetVariableCheckbox.checked = true;
            targetVariableInput.style.display = 'block';
        } else {
            // For clustering and dimensionality reduction, hide target selection
            targetVariableCheckbox.checked = false;
            targetVariableInput.style.display = 'none';
        }
        checkConditions();
    }

    fileInput.addEventListener('change', async function(e) {
        e.preventDefault();
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            
            if (file.size > 100 * 1024 * 1024) {
                alert('File is too large. Maximum size is 100MB');
                return;
            }

            // Hide success message if exists
            if (uploadSuccess) uploadSuccess.style.display = 'none';
            
            // Show progress bar and update filename
            if (uploadProgress) uploadProgress.style.display = 'block';
            if (uploadStatus) uploadStatus.textContent = file.name;
            
            // Simulate progress
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 30;
                if (progress > 90) clearInterval(progressInterval);
                if (progressFill) progressFill.style.width = Math.min(progress, 90) + '%';
            }, 500);

            const formData = new FormData();
            formData.append('file', file);

            if (loadingSpinner) loadingSpinner.style.display = 'block';

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Upload failed');
                }

                // Complete progress bar
                if (progressFill) progressFill.style.width = '100%';
                setTimeout(() => {
                    if (uploadProgress) uploadProgress.style.display = 'none';
                    if (progressFill) progressFill.style.width = '0%';
                    if (uploadedFilename) uploadedFilename.textContent = file.name;
                    if (uploadSuccess) uploadSuccess.style.display = 'flex';
                }, 1000);

                currentFileId = data.file_id;
                const fileIdInput = document.getElementById('file-id');
                if (fileIdInput) fileIdInput.value = currentFileId;

                // Update target variable dropdowns
                if (Array.isArray(data.columns)) {
                    // Update standard target variable dropdown
                    const targetSelect = document.getElementById('target-variable-name');
                    if (targetSelect) {
                        targetSelect.innerHTML = '<option value="">Select a column</option>';
                        data.columns.forEach(column => {
                            const option = document.createElement('option');
                            option.value = column;
                            option.textContent = column;
                            targetSelect.appendChild(option);
                        });
                    }

                    // Update PCA configuration if dimensionality reduction is selected
                    const selectedTask = document.querySelector('input[name="task"]:checked')?.id;
                    if (selectedTask === 'dimensionality_reduction') {
                        const numColumns = data.columns.length;
                        const pcaConfig = document.getElementById('pca-config-section');
                        
                        if (!pcaConfig) {
                            // Create new PCA config
                            const newPcaConfig = document.createElement('div');
                            newPcaConfig.id = 'pca-config-section';
                            newPcaConfig.className = 'mb-4';
                            newPcaConfig.innerHTML = `
                                <div class="card">
                                    <div class="card-body">
                                        <div class="mb-3">
                                            <label for="pca_n_components" class="form-label">Number of Components</label>
                                            <div class="input-group">
                                                <input type="number" 
                                                       class="form-control" 
                                                       id="pca_n_components" 
                                                       name="n_components" 
                                                       min="1" 
                                                       max="${numColumns}"
                                                       value="1"
                                                       required>
                                                <span class="input-group-text">of ${numColumns} maximum</span>
                                            </div>
                                            <div class="form-text">Choose between 1 and ${numColumns} components</div>
                                            <div class="invalid-feedback">
                                                Please enter a number between 1 and ${numColumns}
                                            </div>
                                        </div>

                                        <div class="mb-3">
                                            <div class="form-check form-switch">
                                                <input class="form-check-input" type="checkbox" id="pca_has_target" name="has_target">
                                                <label class="form-check-label" for="pca_has_target">Preserve Target Variable</label>
                                            </div>
                                        </div>

                                        <div class="mb-3" id="pca_target_selection" style="display: none;">
                                            <label for="pca_target_variable" class="form-label">Select Variable to Preserve</label>
                                            <select class="form-select" id="pca_target_variable" name="target_variable">
                                                <option value="">Choose a column...</option>
                                                ${data.columns.map(col => `<option value="${col}">${col}</option>`).join('')}
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            `;

                            // Insert before task preview
                            const taskPreview = document.getElementById('task-preview');
                            if (taskPreview) {
                                taskPreview.parentNode.insertBefore(newPcaConfig, taskPreview);
                            }

                            // Add event listeners
                            const nComponentsInput = newPcaConfig.querySelector('#pca_n_components');
                            if (nComponentsInput) {
                                nComponentsInput.addEventListener('input', function() {
                                    const value = parseInt(this.value);
                                    const max = parseInt(this.max);
                                    
                                    if (isNaN(value) || value < 1) {
                                        this.value = 1;
                                        this.classList.add('is-invalid');
                                        return false;
                                    } else if (value > max) {
                                        this.value = max;
                                        this.classList.add('is-invalid');
                                        return false;
                                    } else {
                                        this.classList.remove('is-invalid');
                                    }
                                });

                                // Add blur event to enforce limits
                                nComponentsInput.addEventListener('blur', function() {
                                    const value = parseInt(this.value);
                                    const max = parseInt(this.max);
                                    
                                    if (isNaN(value) || value < 1) {
                                        this.value = 1;
                                    } else if (value > max) {
                                        this.value = max;
                                    }
                                    this.classList.remove('is-invalid');
                                });
                            }

                            const hasTarget = newPcaConfig.querySelector('#pca_has_target');
                            const targetSelection = newPcaConfig.querySelector('#pca_target_selection');
                            if (hasTarget && targetSelection) {
                                hasTarget.addEventListener('change', function() {
                                    targetSelection.style.display = this.checked ? 'block' : 'none';
                                });
                            }
                        } else {
                            // Update existing PCA config
                            const nComponentsInput = pcaConfig.querySelector('#pca_n_components');
                            const maxSpan = pcaConfig.querySelector('.input-group-text');
                            const helpText = pcaConfig.querySelector('.form-text');
                            const invalidFeedback = pcaConfig.querySelector('.invalid-feedback');
                            const targetSelect = pcaConfig.querySelector('#pca_target_variable');
                            
                            if (nComponentsInput) {
                                nComponentsInput.max = numColumns;
                                if (parseInt(nComponentsInput.value) > numColumns) {
                                    nComponentsInput.value = numColumns;
                                }
                            }
                            if (maxSpan) {
                                maxSpan.textContent = `of ${numColumns} maximum`;
                            }
                            if (helpText) {
                                helpText.textContent = `Choose between 1 and ${numColumns} components`;
                            }
                            if (invalidFeedback) {
                                invalidFeedback.textContent = `Please enter a number between 1 and ${numColumns}`;
                            }
                            if (targetSelect) {
                                targetSelect.innerHTML = `
                                    <option value="">Choose a column...</option>
                                    ${data.columns.map(col => `<option value="${col}">${col}</option>`).join('')}
                                `;
                            }
                        }
                    }
                }

                // Get currently selected task and update target variable visibility
                const selectedTask = document.querySelector('input[name="task"]:checked')?.id;
                if (selectedTask) {
                    updateTargetVariableVisibility(selectedTask);
                }
                
                checkConditions();

            } catch (error) {
                console.error('Error:', error);
                alert('Error: ' + error.message);
                if (uploadSuccess) uploadSuccess.style.display = 'none';
            } finally {
                if (loadingSpinner) loadingSpinner.style.display = 'none';
                clearInterval(progressInterval);
            }
        }
    });

    taskInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (taskPreview) {
                taskPreview.classList.remove('d-none');
                const previewText = taskPreview.querySelector('p');
                if (previewText) previewText.textContent = tasks[this.id];
            }
            // Update target variable visibility based on selected task
            updateTargetVariableVisibility(this.id);

            if (this.id === 'dimensionality_reduction') {
                // Hide standard target variable section
                document.getElementById('target-variable-container').style.display = 'none';
                document.getElementById('target-variable-input').style.display = 'none';
                
                // Show PCA specific configuration
                const pcaConfig = document.createElement('div');
                pcaConfig.id = 'pca-config-section';
                pcaConfig.className = 'mb-4';
                pcaConfig.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            <div class="mb-3">
                                <label for="pca_n_components" class="form-label">Number of Components</label>
                                <input type="number" 
                                       class="form-control" 
                                       id="pca_n_components" 
                                       name="n_components" 
                                       min="1" 
                                       required>
                                <div class="form-text">Choose how many principal components to keep</div>
                            </div>

                            <div class="mb-3">
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="pca_has_target" name="has_target">
                                    <label class="form-check-label" for="pca_has_target">Preserve Target Variable</label>
                                </div>
                            </div>

                            <div class="mb-3" id="pca_target_selection" style="display: none;">
                                <label for="pca_target_variable" class="form-label">Select Variable to Preserve</label>
                                <select class="form-select" id="pca_target_variable" name="target_variable">
                                    <option value="">Choose a column...</option>
                                </select>
                            </div>
                        </div>
                    </div>
                `;

                // Insert PCA config before the task preview
                const existingConfig = document.getElementById('pca-config-section');
                if (!existingConfig) {
                    taskPreview.parentNode.insertBefore(pcaConfig, taskPreview);
                }

                // Add event listener for target variable toggle
                const hasTarget = document.getElementById('pca_has_target');
                const targetSelection = document.getElementById('pca_target_selection');
                const targetVariable = document.getElementById('pca_target_variable');
                
                if (hasTarget && targetSelection) {
                    hasTarget.addEventListener('change', function() {
                        targetSelection.style.display = this.checked ? 'block' : 'none';
                    });
                }

                // Populate the columns in the target variable select
                if (targetVariable) {
                    const columns = Array.from(document.getElementById('target-variable-name')?.options || [])
                        .map(option => option.value)
                        .filter(value => value); // Remove empty values

                    targetVariable.innerHTML = `
                        <option value="">Choose a column...</option>
                        ${columns.map(col => `<option value="${col}">${col}</option>`).join('')}
                    `;
                }
            } else {
                // Remove PCA config if another task is selected
                const pcaConfig = document.getElementById('pca-config-section');
                if (pcaConfig) {
                    pcaConfig.remove();
                }
                // Standard handling for other tasks
                updateTargetVariableVisibility(this.id);
            }
        });
    });

    if (targetVariableCheckbox) {
        targetVariableCheckbox.addEventListener('change', function() {
            // Get currently selected task
            const selectedTask = document.querySelector('input[name="task"]:checked')?.id;
            
            // If classification or regression is selected, prevent unchecking
            if ((selectedTask === 'classification' || selectedTask === 'regression') && !this.checked) {
                this.checked = true;
                return;
            }
            
            // For other tasks, prevent checking
            if ((selectedTask === 'clustering' || selectedTask === 'dimensionality_reduction') && this.checked) {
                this.checked = false;
                return;
            }
            
            if (targetVariableInput) {
                targetVariableInput.style.display = this.checked ? 'block' : 'none';
                if (!this.checked) {
                    const targetSelect = document.getElementById('target-variable-name');
                    if (targetSelect) targetSelect.value = '';
                }
            }
            checkConditions();
        });
    }

    const targetVariableName = document.getElementById('target-variable-name');
    if (targetVariableName) {
        targetVariableName.addEventListener('change', checkConditions);
    }

    if (continueBtn) {
        continueBtn.addEventListener('click', async function(e) {
            e.preventDefault();

            if (!currentFileId) {
                alert('Please upload a dataset first');
                return;
            }

            const selectedTask = document.querySelector('input[name="task"]:checked')?.id;
            if (!selectedTask) {
                alert('Please select a task');
                return;
            }

            // Special handling for PCA
            if (selectedTask === 'dimensionality_reduction') {
                try {
                    // Show loading indicator
                    if (loadingSpinner) loadingSpinner.style.display = 'block';

                    const nComponents = document.getElementById('pca_n_components')?.value;
                    const hasTarget = document.getElementById('pca_has_target')?.checked;
                    const targetVariable = hasTarget ? document.getElementById('pca_target_variable')?.value : null;

                    if (!nComponents) {
                        throw new Error('Please enter the number of components');
                    }

                    if (hasTarget && !targetVariable) {
                        throw new Error('Please select a target variable');
                    }

                    // Create and submit form data
                    const formData = new FormData();
                    formData.append('file_id', currentFileId);
                    formData.append('n_components', nComponents);
                    formData.append('has_target', hasTarget ? 'true' : 'false');
                    if (hasTarget) {
                        formData.append('target_variable', targetVariable);
                    }

                    console.log('Sending PCA request...');

                    try {
                        const response = await fetch('/process_pca', {
                            method: 'POST',
                            body: formData,
                            headers: {
                                'Accept': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            credentials: 'same-origin'
                        });

                        console.log('Response status:', response.status);
                        
                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                        }

                        const data = await response.json();
                        console.log('Response data:', data);

                        if (data.success) {
                            // Store the results in session storage
                            sessionStorage.setItem('pca_metrics', JSON.stringify(data.metrics));
                            sessionStorage.setItem('transformed_file_id', data.transformed_file_id);
                            sessionStorage.setItem('model_id', data.model_id);
                            
                            // Redirect to results page
                            window.location.href = data.redirect_url;
                        } else {
                            throw new Error(data.error || 'Error processing PCA');
                        }
                    } catch (error) {
                        console.error('Fetch error:', error);
                        throw error;
                    }
                } catch (error) {
                    console.error('PCA Error:', error);
                    alert('Error processing PCA: ' + error.message);
                } finally {
                    if (loadingSpinner) loadingSpinner.style.display = 'none';
                }
            } else {
                // Handle other tasks
                const form = document.getElementById('task-form');
                if (form) {
                    document.getElementById('selected-task').value = selectedTask;
                    document.getElementById('selected-dataset').value = fileInput.files[0].name;
                    document.getElementById('has-target').value = targetVariableCheckbox.checked ? 'true' : 'false';
                    document.getElementById('target-variable-input-name').value = document.getElementById('target-variable-name')?.value || '';
                    document.getElementById('file-id').value = currentFileId;

                    if (targetVariableCheckbox.checked && !document.getElementById('target-variable-name')?.value) {
                        alert('Please select a target variable');
                        return;
                    }

                    form.submit();
                }
            }
        });
    }
});