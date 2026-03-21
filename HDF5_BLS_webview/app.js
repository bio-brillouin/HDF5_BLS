// Global state
let hdf5File = null;
let Module = null;

// DOM Elements
const landingPage = document.getElementById('landing-page');
const mainApp = document.getElementById('main-app');
const dragDropArea = document.getElementById('drag-drop-area');
const fileInput = document.getElementById('file-input');
const fileTree = document.getElementById('file-tree');
const propertiesContent = document.getElementById('properties-content');
const tabButtons = document.querySelectorAll('.tab-button');
const tabPanes = document.querySelectorAll('.tab-pane');

/**
 * Initializes the application.
 */
async function initialize() {
    console.log("Initializing app...");

    // Setup drag and drop
    dragDropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dragDropArea.classList.add('active');
    });

    dragDropArea.addEventListener('dragleave', () => {
        dragDropArea.classList.remove('active');
    });

    dragDropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dragDropArea.classList.remove('active');
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFile(files[0]);
    });

    dragDropArea.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    // Setup tabs
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            showTab(tabId);
        });
    });

    // Check for h5wasm
    if (!window.h5wasm) {
        console.error("h5wasm not found!");
        alert("Fatal: h5wasm library not loaded. Check lib/h5wasm.js");
        return;
    }

    try {
        console.log("Waiting for h5wasm ready...");
        Module = await window.h5wasm.ready;
        console.log("h5wasm is ready!", Module);
    } catch (err) {
        console.error("h5wasm failed to initialize:", err);
        alert("Error: h5wasm failed to initialize. " + err.message);
    }
}

/**
 * Global Tab switching function.
 */
window.showTab = function (tabId) {
    const tabPanes = document.querySelectorAll('.tab-pane');
    const tabButtons = document.querySelectorAll('.tab-button');

    tabPanes.forEach(pane => {
        pane.classList.remove('active');
        if (pane.id === tabId) pane.classList.add('active');
    });

    tabButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabId) btn.classList.add('active');
    });
};

/**
 * Handles the selected HDF5 file.
 */
async function handleFile(file) {
    console.log("handleFile called for:", file.name);

    try {
        if (!Module) {
            alert("HDF5 engine not ready yet. Please wait a moment for the viewer to initialize.");
            return;
        }

        // UI transition
        landingPage.style.display = 'none';
        mainApp.style.display = 'flex';
        propertiesContent.innerHTML = '<div class="loading-state">Opening ' + file.name + '...</div>';

        // Read file
        console.log("Reading file bytes...");
        const arrayBuffer = await file.arrayBuffer();
        console.log("File read into buffer, size:", arrayBuffer.byteLength);

        // Filesystem operations
        const h5 = window.h5wasm;
        try { Module.FS.unlink(file.name); } catch (e) { }
        Module.FS.writeFile(file.name, new Uint8Array(arrayBuffer));
        console.log("File written to virtual FS");

        // Open file
        hdf5File = new h5.File(file.name, 'r');
        console.log("HDF5 file object created:", hdf5File);

        // Render Tree
        fileTree.innerHTML = '';
        console.log("Beginning tree render...");
        await renderFileTree(hdf5File, fileTree);
        console.log("Tree render complete.");

        propertiesContent.innerHTML = '<p>Select an element from the structure on the left to explore its metadata and data.</p>';

    } catch (error) {
        console.error("Critical error in handleFile:", error);
        alert("Failed to process file: " + error.message + "\nCheck console for details.");
        landingPage.style.display = 'flex';
        mainApp.style.display = 'none';
    }
}

/**
 * Renders the tree structure.
 */
async function renderFileTree(groupObj, parentElement) {
    try {
        const keys = groupObj.keys();
        console.log(`Rendering ${keys.length} keys for path ${groupObj.path}`);

        if (keys.length === 0 && groupObj.path === '/') {
            parentElement.innerHTML = '<li class="no-data">Empty HDF5 file</li>';
            return;
        }

        for (const name of keys) {
            const child = groupObj.get(name);
            const li = document.createElement('li');
            li.dataset.path = child.path;

            // Container for the item content (icon + label)
            const itemContent = document.createElement('div');
            itemContent.className = 'tree-item-content';

            const icon = document.createElement('span');
            icon.className = 'item-icon';

            const label = document.createElement('span');
            label.className = 'item-label';
            label.textContent = name;

            if (child.type === 'Group') {
                li.className = 'group-item';
                icon.textContent = '▶';
                itemContent.appendChild(icon);
                itemContent.appendChild(label);

                itemContent.onclick = (e) => {
                    e.stopPropagation();
                    selectElement(li);
                    displayProperties(child.path, 'Group');
                    toggleGroup(li, child, icon);
                };
            } else {
                li.className = 'dataset-item';
                icon.textContent = '📊';
                itemContent.appendChild(icon);
                itemContent.appendChild(label);

                itemContent.onclick = (e) => {
                    e.stopPropagation();
                    selectElement(li);
                    displayProperties(child.path, 'Dataset');
                };
            }

            li.appendChild(itemContent);
            parentElement.appendChild(li);
        }
    } catch (err) {
        console.error("Tree render error at path " + groupObj.path + ":", err);
    }
}

async function toggleGroup(li, group, icon) {
    let ul = li.querySelector('ul');
    if (ul) {
        ul.remove();
        li.classList.remove('expanded');
        icon.textContent = '▶';
        console.log("Collapsed group:", group.path);
    } else {
        ul = document.createElement('ul');
        li.appendChild(ul);
        li.classList.add('expanded');
        icon.textContent = '▼';
        console.log("Expanding group:", group.path);
        await renderFileTree(group, ul);
    }
}

function selectElement(li) {
    document.querySelectorAll('.file-tree li').forEach(el => el.classList.remove('selected'));
    li.classList.add('selected');
}

async function displayProperties(path, type) {
    try {
        if (!hdf5File) return;
        const element = hdf5File.get(path);
        const attrs = element.attrs;
        const name = nameFromPath(path);

        // --- Tab Visibility Logic ---
        const vizTab = document.querySelector('[data-tab="visualization"]');
        const treatTab = document.querySelector('[data-tab="treatment"]');

        // Reset visibility
        vizTab.classList.add('hidden');
        treatTab.classList.add('hidden');

        // Visualization Visibility
        const brillouinType = attrs['Brillouin_type'] ? attrs['Brillouin_type'].value : null;
        if (type === 'Dataset' || (type === 'Group' && brillouinType === 'Measure')) {
            vizTab.classList.remove('hidden');
        }

        // Treatment Visibility
        const hasTreatment = checkTreatmentAvailability(element, path, type);
        if (hasTreatment) {
            treatTab.classList.remove('hidden');
        }

        // Update Properties Content
        let html = `<div class="properties-header">
                        <h3>${name}</h3>
                        <span class="badge ${type.toLowerCase()}">${type}</span>
                    </div>`;
        html += `<div class="path-display"><code>${path}</code></div>`;

        if (type === 'Dataset') {
            html += `<div class="dataset-info">
                        <div><strong>Shape:</strong> [${element.shape.join(', ')}]</div>
                        <div><strong>Dtype:</strong> ${element.dtype}</div>
                     </div>`;

            // Data Preview
            try {
                const val = element.value;
                if (val !== undefined) {
                    html += `<h4>Data Preview</h4>`;
                    const previewData = Array.from(val.slice ? val.slice(0, 50) : [val]);
                    html += `<pre class="data-preview">${JSON.stringify(previewData, null, 2)}${val.length > 50 ? '\n...' : ''}</pre>`;
                }
            } catch (previewErr) {
                console.warn("Preview failed:", previewErr);
            }
        }

        const attrKeys = Object.keys(attrs);
        if (attrKeys.length > 0) {
            html += '<h4>Attributes</h4><table><thead><tr><th>Name</th><th>Value</th></tr></thead><tbody>';
            for (const k of attrKeys) {
                let val = attrs[k].value;

                // Special handling for Process_PSD JSON content
                if (k === 'Process_PSD' && typeof val === 'string') {
                    try {
                        const jsonObj = JSON.parse(val);
                        val = renderJsonAsExpandable(jsonObj, k);
                    } catch (e) {
                        console.warn("Process_PSD is not valid JSON:", e);
                    }
                }

                html += `<tr><td><strong>${k}</strong></td><td>${val}</td></tr>`;
            }
            html += '</tbody></table>';
        } else {
            html += '<p class="no-data">This element has no attributes.</p>';
        }

        propertiesContent.innerHTML = html;

        // Update Visualization Logic
        if (!vizTab.classList.contains('hidden')) {
            renderVisualization(path, type);
        }

        showTab('properties');
    } catch (e) {
        console.error("Display props error:", e);
        propertiesContent.innerHTML = `<p class="no-data" style="color: #ef4444;">Error loading properties: ${e.message}</p>`;
    }
}

/**
 * Renders the visualization tab content.
 */
async function renderVisualization(path, type) {
    const vizControls = document.getElementById('viz-controls');
    const plotlyGraph = document.getElementById('plotly-graph');

    // Clear previous
    vizControls.innerHTML = '';
    Plotly.purge(plotlyGraph);

    if (type === 'Dataset') {
        vizControls.innerHTML = '<p class="json-summary">Plotting dataset...</p>';
        await plotDataset(path, plotlyGraph);
    } else if (type === 'Group') {
        await plotGroup(path, vizControls, plotlyGraph);
    }
}

async function plotDataset(path, graphDiv) {
    try {
        const dataset = hdf5File.get(path);
        const value = dataset.value;
        const shape = dataset.shape;
        const name = nameFromPath(path);

        // Handle 1D Data
        if (shape.length === 1) {
            let x = null;
            let y = value;
            let layout = {
                title: name,
                margin: { t: 40, r: 20, b: 40, l: 60 },
                xaxis: { title: 'Index' },
                yaxis: { title: 'Amplitude' }
            };

            // Check for Frequency axis (for PSD or similar)
            // Heuristic: Check for 'frequency' dataset in parent group
            const parentPath = path.substring(0, path.lastIndexOf('/')) || '/';
            const parent = hdf5File.get(parentPath);
            if (parent.keys().includes('frequency')) {
                const freqDs = parent.get('frequency');
                if (freqDs.shape.length === 1 && freqDs.shape[0] === shape[0]) {
                    x = freqDs.value;
                    layout.xaxis.title = 'Frequency (GHz)';
                }
            } else if (parent.keys().includes('Frequency')) {
                const freqDs = parent.get('Frequency');
                if (freqDs.shape.length === 1 && freqDs.shape[0] === shape[0]) {
                    x = freqDs.value;
                    layout.xaxis.title = 'Frequency (GHz)';
                }
            }

            Plotly.newPlot(graphDiv, [{
                x: x,
                y: y,
                type: 'scatter',
                mode: 'lines',
                line: { color: '#38bdf8' }
            }], layout, { responsive: true, displayModeBar: true });
        }
        // Handle 2D Data (Heatmap)
        else if (shape.length === 2) {
            Plotly.newPlot(graphDiv, [{
                z: [value], // Plotly expects array of arrays, but typed array needs handling? 
                // h5wasm returns a flat TypedArray for value usually? 
                // Actually h5wasm .value returns a nested array for strings, but TypedArray for numbers?
                // No, h5wasm returns a flat TypedArray. We need to reshape it.
                // We need to reshape the flat array to 2D for Plotly heatmap
                // shape is [rows, cols]
                z: reshapeArray(value, shape[0], shape[1]),
                type: 'heatmap',
                colorscale: 'Viridis'
            }], {
                title: name,
                margin: { t: 40, r: 20, b: 40, l: 60 }
            }, { responsive: true });
        }
        else {
            graphDiv.innerHTML = '<p class="no-data">Dimensionality not supported for auto-plot (Only 1D and 2D supported).</p>';
        }

    } catch (e) {
        console.error("Plot error:", e);
        graphDiv.innerHTML = `<p class="no-data" style="color: #ef4444;">Error plotting data: ${e.message}</p>`;
    }
}

/**
 * Helper to reshape flat array to 2D array [rows][cols]
 */
function reshapeArray(flatArray, rows, cols) {
    const result = [];
    for (let i = 0; i < rows; i++) {
        // Slice creates a view or copy depending on implementation, 
        // Array.from is safest for Plotly compatibility
        result.push(Array.from(flatArray.slice(i * cols, (i + 1) * cols)));
    }
    return result;
}

async function plotGroup(path, controlsDiv, graphDiv) {
    const group = hdf5File.get(path);
    const keys = group.keys();

    // Filter for datasets only
    const datasets = keys.filter(k => {
        const child = group.get(k);
        return child.type === 'Dataset' && child.shape && child.shape.length <= 2; // Only 1D/2D
    });

    if (datasets.length === 0) {
        controlsDiv.innerHTML = '<p class="no-data">No plottable datasets found in this group.</p>';
        return;
    }

    // Create UI
    let html = `<div class="group-plot-controls">
        <h4>Select Datasets to Plot</h4>
        <div class="dataset-select-container">`;

    datasets.forEach(name => {
        html += `<label class="plot-checkbox-label">
            <input type="checkbox" value="${path}/${name}" class="plot-checkbox">
            <span>${name}</span>
        </label>`;
    });

    html += `</div>
        <button id="btn-plot-group" class="tab-button active">Plot Selected</button>
    </div>`;

    controlsDiv.innerHTML = html;

    // Add Event Listener
    document.getElementById('btn-plot-group').addEventListener('click', async () => {
        const checked = Array.from(controlsDiv.querySelectorAll('.plot-checkbox:checked')).map(cb => cb.value);
        if (checked.length === 0) {
            alert("Please select at least one dataset.");
            return;
        }

        // Multi-plot logic
        const traces = [];
        let layout = {
            title: `Comparison in ${nameFromPath(path)}`,
            margin: { t: 40, r: 20, b: 40, l: 60 },
            showlegend: true
        };

        for (const dsPath of checked) {
            const ds = hdf5File.get(dsPath);
            const val = ds.value; // Flat array

            if (ds.shape.length === 1) {
                // Check if this is likely a PSD that needs Frequency
                let x = null;
                // Similar frequency logic
                try {
                    const pName = nameFromPath(dsPath);
                    if (pName.includes('PSD') || pName.includes('spectrum')) {
                        const parent = hdf5File.get(path);
                        if (parent.keys().includes('frequency')) {
                            x = parent.get('frequency').value;
                        }
                    }
                } catch (e) { }

                traces.push({
                    x: x,
                    y: val,
                    type: 'scatter',
                    mode: 'lines',
                    name: nameFromPath(dsPath)
                });
            }
        }

        Plotly.newPlot(graphDiv, traces, layout, { responsive: true });
    });
}

// ... existing renderJsonAsExpandable ...
function renderJsonAsExpandable(obj, key) {
    if (typeof obj !== 'object' || obj === null) {
        return `<span class="json-value">${JSON.stringify(obj)}</span>`;
    }

    const isArray = Array.isArray(obj);
    const keys = Object.keys(obj);
    if (keys.length === 0) return isArray ? '[]' : '{}';

    let html = `<div class="json-tree-container">
        <div class="json-toggle" onclick="this.parentElement.classList.toggle('expanded')">
            <span class="json-arrow">▶</span>
            <span class="json-key">${key}</span>
            <span class="json-summary">${isArray ? `Array(${keys.length})` : `Object(${keys.length})`}</span>
        </div>
        <div class="json-children">`;

    for (const k of keys) {
        html += `<div class="json-item">
            <span class="json-child-key">${k}:</span>
            ${renderJsonAsExpandable(obj[k], k)}
        </div>`;
    }

    html += `</div></div>`;
    return html;
}

/**
 * Checks if the Treatment tab should be visible for the current element.
 */
function checkTreatmentAvailability(element, path, type) {
    const name = nameFromPath(path);

    // 1. If it's the Treatment group itself
    if (type === 'Group' && name === 'Treatment') return true;

    // 2. If it's a dataset inside a Treatment group
    if (type === 'Dataset') {
        const parentPath = path.substring(0, path.lastIndexOf('/')) || '/';
        const parentName = nameFromPath(parentPath);
        if (parentName === 'Treatment') return true;

        // Check if parent has a Treatment child
        try {
            const parent = hdf5File.get(parentPath);
            if (parent.keys().includes('Treatment')) return true;
        } catch (e) { }
    }

    // 3. If it's a Measure group that has a Treatment child
    if (type === 'Group') {
        const brillouinType = element.attrs['Brillouin_type'] ? element.attrs['Brillouin_type'].value : null;
        if (brillouinType === 'Measure' && element.keys().includes('Treatment')) return true;
    }

    return false;
}

function nameFromPath(path) {
    if (path === '/') return 'Root';
    const parts = path.split('/');
    return parts[parts.length - 1];
}

// Start
document.addEventListener('DOMContentLoaded', initialize);