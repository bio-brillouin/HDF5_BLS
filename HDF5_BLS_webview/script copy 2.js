// ===============================================================
// 1. GLOBAL VARIABLES & INITIALIZATION
// ===============================================================

let h5wasm;
let currentFile = null;
let selectedElement = null;
let Module;

const DOM = {
    dropZone: null,
    fileInput: null,
    contentArea: null,
    fileTree: null,

    // Main property display elements
    commonPropertiesDisplay: null,
    // datasetVisualization: null, // REMOVE THIS LINE - IT NO LONGER EXISTS IN HTML

    // References for the nested attribute tabs
    attributeTabButtons: [],
    attributeTabPanels: [],
    measureAttributesDisplay: null,
    spectrometerAttributesDisplay: null,
    otherAttributesDisplay: null,

    // Main tab buttons/panels
    mainTabButtons: [],
    mainTabPanels: [],

    // NEW Visualization DOM elements (These are correct)
    visualizationControls: null,
    plotlyGraph: null,
};


// ===============================================================
// 2. MAIN INITIALIZATION FUNCTION
// ===============================================================

async function initializeApp() {
    DOM.dropZone = document.getElementById('drop-zone');
    DOM.fileInput = document.getElementById('file-input');
    DOM.contentArea = document.getElementById('content-area');
    DOM.fileTree = document.getElementById('file-tree');

    DOM.commonPropertiesDisplay = document.getElementById('common-properties-display');
    // DOM.datasetVisualization = document.getElementById('dataset-visualization'); // REMOVE THIS LINE

    DOM.attributeTabButtons = document.querySelectorAll('.attribute-tab-buttons .tab-button');
    DOM.attributeTabPanels = document.querySelectorAll('.attribute-tab-content .tab-panel');
    DOM.measureAttributesDisplay = document.getElementById('measure-attributes-display');
    DOM.spectrometerAttributesDisplay = document.getElementById('spectrometer-attributes-display');
    DOM.otherAttributesDisplay = document.getElementById('other-attributes-display');

    DOM.mainTabButtons = document.querySelectorAll('.tab-buttons:not(.attribute-tab-buttons) .tab-button');
    DOM.mainTabPanels = document.querySelectorAll('.tab-content > .tab-panel');

    DOM.visualizationControls = document.getElementById('visualization-controls');
    DOM.plotlyGraph = document.getElementById('plotly-graph');


    if (window.h5wasm) {
        h5wasm = window.h5wasm;
        try {
            Module = await h5wasm.ready;
            console.log("h5wasm is ready and initialized!");
        } catch (error) {
            console.error("Failed to initialize h5wasm:", error);
            alert("Error loading HDF5 library. Please check your console.");
            return;
        }
    } else {
        console.error("h5wasm global object not found. Is the CDN import correct?");
        alert("Fatal error: HDF5 library not found. Check console for details.");
        return;
    }

    setupDragAndDrop();
    setupFileHandlingEvents();
    setupMainTabSwitching();
    setupAttributeTabSwitching();

    DOM.mainTabButtons[0].click();
    DOM.attributeTabButtons[0].click();
}


// ===============================================================
// 3. FILE HANDLING LOGIC
// ===============================================================

async function handleFile(file) {
    console.log(`Processing file: ${file.name}`);
    clearApp();

    try {
        const arrayBuffer = await file.arrayBuffer();
        const fileNameInFS = file.name;
        Module.FS.writeFile(fileNameInFS, new Uint8Array(arrayBuffer));

        if (currentFile) {
            currentFile.close();
            if (Module.FS.existsSync(currentFile.filename)) {
                Module.FS.unlink(currentFile.filename);
            }
        }

        currentFile = new h5wasm.File(fileNameInFS, 'r');
        console.log("HDF5 file opened successfully:", currentFile);

        DOM.dropZone.classList.add('hidden');
        DOM.contentArea.classList.remove('hidden');

        buildFileTree(currentFile, DOM.fileTree);

        const rootLiElement = DOM.fileTree.querySelector('li');
        if (rootLiElement) {
            selectElement(rootLiElement, currentFile);
            const toggleIcon = rootLiElement.querySelector('.toggle-icon');
            if (toggleIcon) {
                toggleIcon.click();
            }
        }

    } catch (error) {
        console.error("Error processing HDF5 file:", error);
        alert(`Failed to open HDF5 file: ${error.message}. Please ensure it's a valid .h5 or .hdf5 file.`);
        clearApp();
    }
}

function clearApp() {
    if (currentFile) {
        currentFile.close();
        if (Module.FS.existsSync(currentFile.filename)) {
             Module.FS.unlink(currentFile.filename);
        }
    }
    currentFile = null;
    selectedElement = null;

    DOM.dropZone.classList.remove('hidden');
    DOM.contentArea.classList.add('hidden');
    DOM.fileTree.innerHTML = '';
    DOM.commonPropertiesDisplay.innerHTML = '';
    DOM.measureAttributesDisplay.innerHTML = '';
    DOM.spectrometerAttributesDisplay.innerHTML = '';
    DOM.otherAttributesDisplay.innerHTML = '';
    // DOM.datasetVisualization.innerHTML = ''; // REMOVE THIS LINE
    DOM.plotlyGraph.innerHTML = ''; // Keep this, it clears the plot area
    DOM.visualizationControls.innerHTML = ''; // Keep this, it clears the controls
    document.querySelectorAll('#file-tree li.selected').forEach(li => li.classList.remove('selected'));
}


// ===============================================================
// 4. HDF5 TREE BUILDING & NAVIGATION
// ===============================================================

function buildFileTree(h5group, parentElement) {
    if (h5group === currentFile && parentElement === DOM.fileTree) {
        const rootLi = createTreeNode(h5group, true);
        DOM.fileTree.appendChild(rootLi);
        parentElement = rootLi.querySelector('ul.nested') || DOM.fileTree;
    }

    h5group.keys().forEach(key => {
        const h5element = h5group.get(key);
        const li = createTreeNode(h5element);
        parentElement.appendChild(li);
    });
}

function createTreeNode(h5element, isRootFileNode = false) {
    const li = document.createElement('li');
    li.dataset.path = h5element.path;
    li.dataset.type = h5element.type;

    let name;

    if (isRootFileNode) {
        name = currentFile.filename;
    } else {
        const pathSegments = h5element.path.split('/');
        name = pathSegments.pop();
        if (name === '' && h5element.path === '/') {
            name = '/';
        } else if (name === '') {
            name = '(Unnamed Element)';
        }
        h5element.name = name;
    }

    if (h5element.type === 'Group') {
        li.classList.add('collapsible'); // Marks this li as collapsible

        const toggleIcon = document.createElement('span');
        toggleIcon.classList.add('toggle-icon');
        toggleIcon.textContent = '▶ '; // Initial state: collapsed
        li.appendChild(toggleIcon);

        // Wrap the group name in a span so we can differentiate it from the icon
        const groupNameSpan = document.createElement('span');
        groupNameSpan.textContent = name;
        groupNameSpan.classList.add('group-name-text'); // Optional: for specific styling if needed
        li.appendChild(groupNameSpan);

        const nestedUl = document.createElement('ul');
        nestedUl.classList.add('nested', 'hidden'); // Initial state: hidden
        li.appendChild(nestedUl);

        // Helper function to handle the actual toggling of expansion/collapse
        const toggleExpansion = () => {
            nestedUl.classList.toggle('hidden');
            toggleIcon.textContent = nestedUl.classList.contains('hidden') ? '▶ ' : '▼ ';
            // If the group is now visible and has no children loaded yet, load them
            if (!nestedUl.classList.contains('hidden') && nestedUl.children.length === 0) {
                buildFileTree(h5element, nestedUl);
            }
        };

        // Event listener for ONLY the arrow icon
        toggleIcon.addEventListener('click', (e) => {
            e.stopPropagation(); // IMPORTANT: Prevent the click from bubbling up to the li's listener
            toggleExpansion(); // Only toggle expansion
        });

        // Event listener for the entire <li> element (including the name text)
        li.addEventListener('click', (e) => {
            // Stop propagation to prevent clicks on child <li> elements from selecting parent <li> elements.
            e.stopPropagation();

            // Select the element (this happens regardless of click target, except for the icon itself due to stopPropagation above)
            selectElement(li, h5element);

            // If it's a group, and the click was NOT on the toggle icon (which has its own handler), then toggle expansion
            // Because toggleIcon's listener has stopPropagation(), this li listener will only fire if
            // the click originated from the name text or the surrounding padding of the li.
            if (h5element.type === 'Group') {
                toggleExpansion();
            }
            // For datasets, selectElement is sufficient, no expansion to toggle.
        });

    } else { // Dataset (no expansion/collapse for datasets)
        let shapeInfo = '';
        if (h5element.shape && h5element.shape.length > 0) {
            shapeInfo = ` (${h5element.shape.join(', ')}) `;
        }
        li.innerHTML = `${name}${shapeInfo}`;
        li.classList.add('dataset-node'); // Marks this li as a dataset node

        // For datasets, only select the element on click
        li.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent bubbling up to parent <li> elements
            selectElement(li, h5element);
        });
    }

    return li;
}

function selectElement(elementLi, h5element) {
    // Deselect previous item
    const previouslySelected = DOM.fileTree.querySelector('li.selected');
    if (previouslySelected) {
        previouslySelected.classList.remove('selected');
    }

    // Select current item
    selectedElement = h5element;
    elementLi.classList.add('selected');

    // Update main display panels
    displayProperties(selectedElement);

    if (selectedElement.type === 'Dataset') {
        displayVisualization(selectedElement);
        // Enable and switch to visualization tab for datasets
        DOM.mainTabButtons.forEach(btn => {
            if (btn.dataset.tab === 'visualization') btn.disabled = false;
        });
        document.querySelector('.tab-button[data-tab="visualization"]').click(); // Activate visualization tab
    } else { // Group
        // Disable Visualization tab for groups
        DOM.mainTabButtons.forEach(btn => {
            if (btn.dataset.tab === 'visualization') btn.disabled = true;
        });

        // Manually activate Properties tab and show its panel for groups
        DOM.mainTabButtons.forEach(btn => {
            if (btn.dataset.tab === 'properties') {
                btn.classList.add('active'); // Activate Properties button
            } else {
                btn.classList.remove('active'); // Deactivate other main buttons
            }
        });
        DOM.mainTabPanels.forEach(panel => {
            if (panel.id === 'properties-panel') {
                panel.classList.remove('hidden'); // Show Properties panel
            } else {
                panel.classList.add('hidden'); // Hide other main panels
            }
        });

        // Ensure the default attribute sub-tab is active when a group is selected
        DOM.attributeTabButtons.forEach(btn => btn.classList.remove('active'));
        DOM.attributeTabPanels.forEach(panel => panel.classList.add('hidden'));
        if (DOM.attributeTabButtons.length > 0) {
            DOM.attributeTabButtons[0].classList.add('active');
            DOM.attributeTabPanels[0].classList.remove('hidden');
        }
    }
}


// ===============================================================
// 5. DATA DISPLAY FUNCTIONS (Properties & Visualization)
// ===============================================================

const jsonToggleListeners = [];

/**
 * Recursively renders a JSON object/array into an expandable HTML structure.
 * Stores information about toggle elements for later event listener attachment.
 * @param {string | null} key - The key for the current value (or null for array items).
 * @param {any} value - The JSON value to render.
 * @param {number} level - The current nesting level (for indentation).
 * @returns {string} The HTML string for the JSON node.
 */
function renderJsonAsExpandable(key, value, level = 0) {
    let html = '';
    const uniqueId = `json-node-${Math.random().toString(36).substring(2, 11)}`;
    const paddingLeft = level * 15;

    if (typeof value === 'object' && value !== null) {
        const isArray = Array.isArray(value);
        const numMembers = isArray ? value.length : Object.keys(value).length;

        // --- NEW LOGIC: Determine descriptive label ---
        let descriptiveLabel = '';
        if (!isArray) { // Only objects can have 'function' or 'name' keys
            if (value.hasOwnProperty('function') && typeof value.function === 'string') {
                descriptiveLabel = ` (${escapeHTML(value.function)})`;
            } else if (value.hasOwnProperty('name') && typeof value.name === 'string') {
                descriptiveLabel = ` (${escapeHTML(value.name)})`;
            }
            // Add more conditions here if you have other preferred keys, e.g.:
            // else if (value.hasOwnProperty('id') && typeof value.id === 'string') {
            //     descriptiveLabel = ` (${escapeHTML(value.id)})`;
            // }
        }
        // --- END NEW LOGIC ---

        // Node header (toggle icon, key, type/summary)
        html += `<div class="json-node json-object-node" style="padding-left: ${paddingLeft}px;">`;
        html += `<span class="json-toggle" id="toggle-${uniqueId}">▶</span> `; // Toggle icon
        html += `<span class="json-key">${key !== null ? escapeHTML(key) + ': ' : ''}</span>`; // Key, if exists
        // Append the descriptiveLabel to the type/summary
        html += `<span class="json-type">${isArray ? 'Array' : 'Object'} (${numMembers} members)${descriptiveLabel}</span>`;
        html += `</div>`;

        // Children container (initially hidden)
        html += `<div id="content-${uniqueId}" class="json-children hidden">`;
        const members = isArray ? value : Object.keys(value);
        members.forEach((memberKey, index) => {
            const childKey = isArray ? null : memberKey;
            const childValue = isArray ? value[index] : value[memberKey];
            html += renderJsonAsExpandable(childKey, childValue, level + 1);
        });
        html += `</div>`;

        // Store info to attach listener after DOM update
        jsonToggleListeners.push({ toggleId: `toggle-${uniqueId}`, contentId: `content-${uniqueId}` });

    } else { // Primitive value (string, number, boolean, null)
        html += `<div class="json-node json-primitive-node" style="padding-left: ${paddingLeft}px;">`;
        html += `<span class="json-key">${key !== null ? escapeHTML(key) + ': ' : ''}</span>`;
        html += `<span class="json-value json-value-${typeof value}">${escapeHTML(JSON.stringify(value))}</span>`;
        html += `</div>`;
    }
    return html;
}

// Helper function for HTML escaping (important for security)
function escapeHTML(str) {
    if (typeof str !== 'string') return str;
    return str.replace(/[&<>"']/g, function (m) {
        switch (m) {
            case '&': return '&amp;';
            case '<': return '&lt;';
            case '>': return '&gt;';
            case '"': return '&quot;';
            case "'": return '&#039;';
            default: return m;
        }
    });
}

function displayProperties(h5element) { 
    DOM.commonPropertiesDisplay.innerHTML = '';
    DOM.measureAttributesDisplay.innerHTML = '';
    DOM.spectrometerAttributesDisplay.innerHTML = '';
    DOM.otherAttributesDisplay.innerHTML = '';

    let commonPropsHtml = '';

    commonPropsHtml += `<p><strong>Name:</strong> ${h5element.name}</p>`;
    commonPropsHtml += `<p><strong>Path:</strong> ${h5element.path}</p>`;
    commonPropsHtml += `<p><strong>Type:</strong> ${h5element.type}</p>`;

    if (h5element.type === 'Dataset') {
        commonPropsHtml += `<p><strong>Shape:</strong> (${h5element.shape ? h5element.shape.join(', ') : 'Scalar'})</p>`;
        commonPropsHtml += `<p><strong>Data Type:</strong> ${h5element.dtype}</p>`;
        if (h5element.chunk) {
            commonPropsHtml += `<p><strong>Chunking:</strong> (${h5element.chunk.join(', ')})</p>`;
        }
        if (h5element.maxshape) {
            commonPropsHtml += `<p><strong>Max Shape:</strong> (${h5element.maxshape.map(s => s === null ? 'None' : s).join(', ')})</p>`;
        }
        if (h5element.filters && h5element.filters.length > 0) {
            commonPropsHtml += `<p><strong>Filters:</strong> ${h5element.filters.join(', ')}</p>`;
        }

        commonPropsHtml += '<h4>Data Preview:</h4>';
        try {
            let dataContent;
            const MAX_PREVIEW_ELEMENTS = 100;
            if (h5element.shape && h5element.shape.length > 0) {
                const totalElements = h5element.shape.reduce((acc, dim) => acc * dim, 1);
                if (totalElements <= MAX_PREVIEW_ELEMENTS) {
                    dataContent = h5element.value;
                } else {
                    const sliceIndices = h5element.shape.map((dim, i) => {
                        return i === 0 ? [0, Math.min(5, dim)] : [0, Math.min(1, dim)];
                    });
                    dataContent = h5element.slice(sliceIndices).value;
                }

                dataContent = Array.from(dataContent);
                if (dataContent.length > 20) {
                    dataContent = dataContent.slice(0, 20).concat('...');
                }
            } else {
                dataContent = h5element.value;
            }
            commonPropsHtml += `<pre>${JSON.stringify(dataContent, null, 2)}</pre>`;
        } catch (e) {
            commonPropsHtml += `<p><em>Could not read data preview: ${e.message}</em></p>`;
            console.warn("Error reading data preview:", e);
        }

    } else if (h5element.type === 'Group') {
        commonPropsHtml += `<p><strong>Number of Members:</strong> ${h5element.keys().length}</p>`;
    }

    const attrs = h5element.attrs;
    if (attrs && Object.keys(attrs).length > 0) {
        let measureAttrsHtml = '';
        let spectrometerAttrsHtml = '';
        let otherAttrsHtml = '';

        let measureCount = 0;
        let spectrometerCount = 0;
        let otherCount = 0;

        for (const attrName in attrs) {
            if (Object.hasOwnProperty.call(attrs, attrName)) {
                const attrValue = attrs[attrName].value;

                // Categorize attributes based on name (case-insensitive check)
                if (attrName.toLowerCase().startsWith('measure')) {
                    targetDisplayHtml = `<p><strong>${attrName.slice(8).replaceAll("_", " ")}:</strong> ${attrValue}</p>`;
                    measureAttrsHtml += targetDisplayHtml;
                    measureCount++;
                } else if (attrName.toLowerCase().startsWith('spectrometer')) {
                    targetDisplayHtml = `<p><strong>${attrName.slice(13).replaceAll("_", " ")}:</strong> ${attrValue}</p>`;
                    spectrometerAttrsHtml += targetDisplayHtml;
                    spectrometerCount++;
                } else {
                    if (attrName.toLowerCase().startsWith('process')) {
                      targetDisplayHtml = `<p><strong>${attrName}:</strong></p>`;
                      try {
                          const parsedJson = JSON.parse(attrValue);
                          // Render the JSON as an expandable object
                          // We pass null for the root key as the attribute name already serves as its label
                          displayValue = `
                              <div class="json-root-container">
                                  ${renderJsonAsExpandable(null, parsedJson, 0)}
                              </div>
                          `;
                      } catch (e) {
                          // Not valid JSON, or error parsing, display as plain text with a warning
                          console.warn(`Attribute "${attrName}" starts with "Process" but is not valid JSON:`, e);
                          displayValue = `<span class="attr-value attr-value-error" title="Invalid JSON. Displaying as plain text.">${escapeHTML(attrValue)}</span>`;
                      }
                      targetDisplayHtml = targetDisplayHtml+displayValue;
                    }
                    else if (attrName.toLowerCase() == 'brillouin_type') {
                      commonPropsHtml += `<p><strong>Brillouin Type:</strong> ${attrValue}</p>`;
                      targetDisplayHtml = '';
                    }
                    else{
                      targetDisplayHtml = `<p><strong>${attrName.replace("_", " ")}:</strong> ${attrValue}</p>`;
                    }
                    otherAttrsHtml += targetDisplayHtml;
                    otherCount++;
                }
            }
        }

        DOM.measureAttributesDisplay.innerHTML = measureCount > 0 ? measureAttrsHtml : '<p>No "Measure" attributes found.</p>';
        DOM.spectrometerAttributesDisplay.innerHTML = spectrometerCount > 0 ? spectrometerAttrsHtml : '<p>No "Spectrometer" attributes found.</p>';
        DOM.otherAttributesDisplay.innerHTML = otherCount > 0 ? otherAttrsHtml : '<p>No other attributes found.</p>';

    } else {
        DOM.measureAttributesDisplay.innerHTML = '<p>No attributes found for this element.</p>';
        DOM.spectrometerAttributesDisplay.innerHTML = '<p>No attributes found for this element.</p>';
        DOM.otherAttributesDisplay.innerHTML = '<p>No attributes found for this element.</p>';
    }

    // IMPORTANT: Attach event listeners to the dynamically created JSON toggles
    // This must happen *after* DOM.attributesDisplay.innerHTML is set.
    jsonToggleListeners.forEach(({ toggleId, contentId }) => {
        const toggleElement = document.getElementById(toggleId);
        const contentElement = document.getElementById(contentId);
        if (toggleElement && contentElement) {
            toggleElement.addEventListener('click', () => {
                contentElement.classList.toggle('hidden');
                toggleElement.textContent = contentElement.classList.contains('hidden') ? '▶' : '▼';
            });
        }
    });

    DOM.commonPropertiesDisplay.innerHTML = commonPropsHtml;
    DOM.attributeTabButtons[0].click();
}

/**
 * Displays visualizations for datasets based on their dimensions.
 * @param {h5wasm.Dataset} h5dataset - The dataset to visualize.
 */
async function displayVisualization(h5dataset) {
    DOM.plotlyGraph.innerHTML = ''; // Clear previous plot
    DOM.visualizationControls.innerHTML = ''; // Clear previous controls

    if (h5dataset.type !== 'Dataset') {
        DOM.plotlyGraph.innerHTML = '<p>Select a dataset to visualize.</p>';
        return;
    }

    let data;
    try {
        data = Array.from(await h5dataset.value);
    } catch (e) {
        DOM.plotlyGraph.innerHTML = `<p>Error loading dataset data for visualization: ${e.message}. The dataset might be too large or have an unsupported type for direct loading.</p>`;
        DOM.visualizationControls.innerHTML = `<h3>Data Loading Error</h3>`;
        console.error("Error loading dataset data for visualization:", e);
        return;
    }


    if (h5dataset.shape.length === 1) {
        plot1DData(data, DOM.plotlyGraph, `1D Data Plot: ${h5dataset.name}`);
        DOM.visualizationControls.innerHTML = `<h3>1D Data Plot</h3>`;
    } else if (h5dataset.shape.length === 2) {
        const rows = h5dataset.shape[0];
        const cols = h5dataset.shape[1];

        // Create visualization type selection (radio buttons)
        const vizTypeControls = document.createElement('div');
        vizTypeControls.classList.add('viz-type-selector');
        vizTypeControls.innerHTML = `
            <label><input type="radio" name="vizType" value="line"> Line Representation</label>
            <label><input type="radio" name="vizType" value="heatmap" checked> Heat Map</label>
            `;
        DOM.visualizationControls.appendChild(vizTypeControls);

        const lineControlsContainer = document.createElement('div');
        lineControlsContainer.classList.add('line-controls', 'viz-sub-controls', 'hidden'); // Initially hidden
        //                                                                ^^^^^^^^^^
        lineControlsContainer.innerHTML = `
            <label for="rowSelect">Select Row (0-${rows - 1}):</label>
            <select id="rowSelect"></select>
        `;
        DOM.visualizationControls.appendChild(lineControlsContainer);

        const heatmapControlsContainer = document.createElement('div');
        heatmapControlsContainer.classList.add('heatmap-controls', 'viz-sub-controls'); // Initially visible
        //                                                                No 'hidden' class here
        heatmapControlsContainer.innerHTML = `
            <label for="colorScaleSelect">Color Scale:</label>
            <select id="colorScaleSelect">
                <option value="Viridis">Viridis</option>
                <option value="Plasma">Plasma</option>
                <option value="Jet">Jet</option>
                <option value="Hot">Hot</option>
                <option value="Greys">Greys</option>
                <option value="Portland">Portland</option>
                <option value="Blackbody">Blackbody</option>
            </select>
        `;
        DOM.visualizationControls.appendChild(heatmapControlsContainer);

        // Populate row selection dropdown (needed even if not default, in case user switches)
        const rowSelect = lineControlsContainer.querySelector('#rowSelect');
        for (let i = 0; i < rows; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `Row ${i}`;
            rowSelect.appendChild(option);
        }

        // --- Event Listeners for 2D controls ---
        const vizTypeRadios = vizTypeControls.querySelectorAll('input[name="vizType"]');
        let currentVizType = 'heatmap'; // <----- Set initial default to 'heatmap'
        //   ^^^^^^^^^^^^^^^^^^^^^^^^^^

        const render2DPlot = () => {
            if (currentVizType === 'line') {
                lineControlsContainer.classList.remove('hidden');
                heatmapControlsContainer.classList.add('hidden');
                const selectedRowIndex = parseInt(rowSelect.value);
                const rowData = data.slice(selectedRowIndex * cols, (selectedRowIndex + 1) * cols);
                plot1DData(rowData, DOM.plotlyGraph, `Row ${selectedRowIndex} of ${h5dataset.name}`);
            } else { // heatmap
                lineControlsContainer.classList.add('hidden');
                heatmapControlsContainer.classList.remove('hidden');
                const selectedColorScale = heatmapControlsContainer.querySelector('#colorScaleSelect').value;
                plot2DHeatmap(data, h5dataset.shape, DOM.plotlyGraph, selectedColorScale);
            }
        };

        vizTypeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                currentVizType = e.target.value;
                render2DPlot();
            });
        });

        rowSelect.addEventListener('change', render2DPlot);
        heatmapControlsContainer.querySelector('#colorScaleSelect').addEventListener('change', render2DPlot);

        // Initial render for 2D
        render2DPlot();

    } else {
        DOM.plotlyGraph.innerHTML = `<p>Visualization not available for ${h5dataset.shape.length}D arrays.</p>`;
        DOM.visualizationControls.innerHTML = `<h3>Unsupported Dimensionality</h3>`;
    }
}

/**
 * Plots a 1D array as a scatter/line graph.
 * @param {Array} data - The 1D array of numerical data.
 * @param {HTMLElement} targetDiv - The HTML element where the plot should be rendered.
 * @param {string} title - Optional title for the plot.
 */
function plot1DData(data, targetDiv, title = '1D Data Plot') {
    const x = Array.from({ length: data.length }, (_, i) => i); // x-axis as indices

    const trace = {
        x: x,
        y: data,
        mode: 'lines+markers',
        type: 'scatter'
    };

    const layout = {
        title: title,
        xaxis: { title: 'Position' },
        yaxis: { title: 'Value' },
        margin: { t: 50, b: 50, l: 50, r: 20 }
    };

    Plotly.newPlot(targetDiv, [trace], layout, { responsive: true });
}

/**
 * Plots a 2D array as a heatmap.
 * @param {Array} flatData - The 2D array data flattened into a 1D array.
 * @param {Array<number>} shape - The original [rows, cols] shape of the 2D array.
 * @param {HTMLElement} targetDiv - The HTML element where the plot should be rendered.
 * @param {string} colorScale - The Plotly colorscale name (e.g., 'Viridis', 'Jet', 'Hot').
 */
function plot2DHeatmap(flatData, shape, targetDiv, colorScale = 'Viridis') {
    const rows = shape[0];
    const cols = shape[1];

    // Plotly expects 2D data as an array of arrays (matrix), not flat
    const z = [];
    for (let i = 0; i < rows; i++) {
        z.push(flatData.slice(i * cols, (i + 1) * cols));
    }

    const trace = {
        z: z,
        type: 'heatmap',
        colorscale: colorScale
    };

    const layout = {
        title: '2D Heat Map',
        xaxis: { title: 'Columns' },
        yaxis: { title: 'Rows', autorange: 'reversed' }, // Often y-axis for heatmaps is reversed to match matrix indexing
        margin: { t: 50, b: 50, l: 50, r: 20 }
    };

    Plotly.newPlot(targetDiv, [trace], layout, { responsive: true });
}

// ===============================================================
// 6. UI EVENT SETUP FUNCTIONS
// ===============================================================

function setupDragAndDrop() {
    document.addEventListener('dragover', (e) => e.preventDefault());
    document.addEventListener('drop', (e) => e.preventDefault());

    DOM.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        DOM.dropZone.classList.add('hover');
    });

    DOM.dropZone.addEventListener('dragleave', () => {
        DOM.dropZone.classList.remove('hover');
    });

    DOM.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        DOM.dropZone.classList.remove('hover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function setupFileHandlingEvents() {
    DOM.dropZone.addEventListener('click', () => {
        DOM.fileInput.click();
    });

    DOM.fileInput.addEventListener('change', (e) => {
        const files = e.target.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
        e.target.value = '';
    });
}

function setupMainTabSwitching() {
    DOM.mainTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            DOM.mainTabButtons.forEach(btn => btn.classList.remove('active'));
            DOM.mainTabPanels.forEach(panel => panel.classList.add('hidden'));

            button.classList.add('active');
            const targetTabId = button.dataset.tab + '-panel';
            document.getElementById(targetTabId).classList.remove('hidden');
        });
    });
}

function setupAttributeTabSwitching() {
    DOM.attributeTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            DOM.attributeTabButtons.forEach(btn => btn.classList.remove('active'));
            DOM.attributeTabPanels.forEach(panel => panel.classList.add('hidden'));

            button.classList.add('active');
            const targetTabId = button.dataset.tab;
            document.getElementById(targetTabId + '-panel').classList.remove('hidden');
        });
    });
}


// ===============================================================
// 7. EVENT LISTENER FOR DOM CONTENT LOADED
// ===============================================================

document.addEventListener('DOMContentLoaded', initializeApp);