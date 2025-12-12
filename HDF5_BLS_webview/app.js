// A global variable to hold the HDF5 file object
let hdf5File = null;

// Selectors for DOM elements
const landingPage = document.getElementById('landing-page');
const mainApp = document.getElementById('main-app');
const dragDropArea = document.getElementById('drag-drop-area');
const fileInput = document.getElementById('file-input');
const fileTree = document.getElementById('file-tree');
const propertiesContent = document.getElementById('properties-content');
const tabButtons = document.querySelectorAll('.tab-button');
const tabPanes = document.querySelectorAll('.tab-pane');

// Event listeners for file input
dragDropArea.addEventListener('click', () => fileInput.click());
dragDropArea.addEventListener('dragover', (e) => {
    e.preventDefault(); // Prevents default behavior to allow a drop
    dragDropArea.classList.add('active');
});
dragDropArea.addEventListener('dragleave', () => {
    dragDropArea.classList.remove('active');
});
dragDropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    dragDropArea.classList.remove('active');
    const file = e.dataTransfer.files[0];
    if (file) {
        handleFile(file);
    }
});
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
});

// Event listener for tab navigation
tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Remove active class from all buttons and panes
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabPanes.forEach(pane => pane.classList.remove('active'));

        // Add active class to the clicked button and corresponding pane
        button.classList.add('active');
        document.getElementById(button.dataset.tab).classList.add('active');
    });
});

/**
 * Handles the selected HDF5 file.
 * @param {File} file The file object from the input.
 */
async function handleFile(file) {
    try {
        propertiesContent.innerHTML = 'Loading file...';

        // Wait for h5wasm to be ready
        await waitForH5wasm();
        await window.h5wasm.ready;
        console.log("h5wasm ready");

        // Read the file as an ArrayBuffer
        const arrayBuffer = await file.arrayBuffer();
        console.log("File read as ArrayBuffer");

        // Remove file if it already exists in the virtual FS
        try { window.h5wasm.FS.unlink(file.name); } catch (e) {}

        // Write the file to the h5wasm virtual filesystem
        window.h5wasm.FS.writeFile(file.name, new Uint8Array(arrayBuffer));
        console.log("File written to virtual FS");

        // Open the file using h5wasm
        const fs = new window.h5wasm.File(file.name, 'r');
        console.log("File opened with h5wasm", fs);

        hdf5File = fs;
        landingPage.style.display = 'none';
        mainApp.style.display = 'flex';
        renderFileTree(fs.root);
        propertiesContent.innerHTML = '<p>Click on an element in the file tree to see its properties.</p>';

    } catch (error) {
        console.error("Error handling file:", error);
        propertiesContent.innerHTML = '<p style="color: red;">Failed to load HDF5 file. Please ensure it is a valid .h5 file.</p>';
        alert('Failed to load file. Check the console for details.');
    }
}

/**
 * Recursively renders the HDF5 file structure as a treeview.
 * @param {object} node The current group or file to render.
 * @param {HTMLElement} parentElement The parent list element to append to.
 */
function renderFileTree(node, parentElement = fileTree) {
    // Clear the tree for a new file
    if (parentElement === fileTree) {
        parentElement.innerHTML = '';
    }

    // Iterate through all items in the current node (group)
    for (const key in node.groups) {
        const group = node.groups[key];
        const groupElement = document.createElement('li');
        groupElement.className = 'group-item';
        groupElement.textContent = `🗂️ ${key} (Group)`;
        groupElement.dataset.path = group.path; // Store the full path for later use
        parentElement.appendChild(groupElement);

        // Add a click event listener to show properties
        groupElement.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevents parent click events from firing
            selectElement(groupElement);
            displayProperties(group.path, 'group');
        });

        // Recursively render subgroups
        if (Object.keys(group.groups).length > 0) {
             const subList = document.createElement('ul');
             groupElement.appendChild(subList);
             renderFileTree(group, subList);
        }
    }

    for (const key in node.datasets) {
        const dataset = node.datasets[key];
        const datasetElement = document.createElement('li');
        datasetElement.className = 'dataset-item';
        datasetElement.textContent = `📊 ${key} (Dataset)`;
        datasetElement.dataset.path = dataset.path; // Store the full path
        parentElement.appendChild(datasetElement);

        // Add a click event listener to show properties
        datasetElement.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevents parent click events from firing
            selectElement(datasetElement);
            displayProperties(dataset.path, 'dataset');
        });
    }
}

/**
 * Handles the selection of a tree item.
 * @param {HTMLElement} element The selected list item element.
 */
function selectElement(element) {
    // Deselect all other elements
    document.querySelectorAll('.file-tree li').forEach(el => el.classList.remove('selected'));
    // Select the current element
    element.classList.add('selected');
}

/**
 * Fetches and displays the properties of a selected group or dataset.
 * @param {string} path The HDF5 path of the element.
 * @param {string} type The type of element ('group' or 'dataset').
 */
async function displayProperties(path, type) {
    if (!hdf5File) return;

    try {
        propertiesContent.innerHTML = 'Loading properties...';
        
        let element;
        // Check if the element is a group or a dataset
        if (type === 'group') {
            element = await hdf5File.get_object(path);
        } else {
            element = await hdf5File.get_object(path);
        }

        // Get attributes from the element's metadata
        const attributes = element.attrs;
        
        // Build the HTML for the properties table
        let html = `<h3>Path: ${path}</h3>`;
        html += `<h3>Type: ${type}</h3>`;
        
        if (Object.keys(attributes).length > 0) {
            html += `<h4>Attributes</h4>`;
            html += `<table style="width:100%; border-collapse: collapse;">`;
            html += `<thead><tr><th style="border: 1px solid #ccc; padding: 8px; text-align: left;">Attribute Name</th><th style="border: 1px solid #ccc; padding: 8px; text-align: left;">Value</th></tr></thead>`;
            html += `<tbody>`;

            // Iterate over each attribute and its value
            for (const key in attributes) {
                // The HDF5 file format allows storing attributes as ASCII-encoded text[cite: 62].
                const value = attributes[key].value;
                html += `<tr>`;
                html += `<td style="border: 1px solid #ccc; padding: 8px;">${key}</td>`;
                html += `<td style="border: 1px solid #ccc; padding: 8px;">${value}</td>`;
                html += `</tr>`;
            }
            
            html += `</tbody></table>`;
        } else {
            html += `<p>This element has no attributes.</p>`;
        }
        
        // Update the properties pane with the generated HTML
        propertiesContent.innerHTML = html;

    } catch (error) {
        console.error("Error fetching properties:", error);
        propertiesContent.innerHTML = '<p style="color: red;">Failed to load properties for this element.</p>';
    }
}

// Add this helper at the top of your file
async function waitForH5wasm() {
    while (!window.h5wasm || !window.h5wasm.ready) {
        await new Promise(r => setTimeout(r, 50));
    }
}