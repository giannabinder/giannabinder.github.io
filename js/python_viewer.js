let pyodide;
let pyodideReady = false;

const filePaths = {
    engine: 'python/rf_math.py',
    config: 'python/rf_plot.py',
    solve: 'python/rf_sim.py'
};

let currentModel = '2port';

/**
 * Switches the active simulation model and synchronizes the UI.
 * @param {string} model - The model key ('2port', 'chebyshev', or 'lna')
 */
function switchConsole(model) {
    // 1. Update the global state tracker
    currentModel = model;
    
    // 2. Update Tab Styles (The buttons in the parameter console header)
    document.querySelectorAll('.console-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    const activeTab = document.getElementById(`tab-${model}`);
    if (activeTab) activeTab.classList.add('active');

    // 3. Toggle Parameter Input Visibility
    // Hide all input groups first
    document.querySelectorAll('.input-grid-container').forEach(div => {
        div.style.display = 'none';
    });
    // Show the one corresponding to the selected model
    const activeInputs = document.getElementById(`inputs-${model}`);
    if (activeInputs) activeInputs.style.display = 'flex';

    // 4. Update Main Content Display (The Diagram/Description area)
    const theoryDisplay = document.getElementById('theory-display');
    const demoDisplay = document.getElementById('demo-display');
    const chebyshevDisplay = document.getElementById('chebyshev-display');
    const codeWindow = document.getElementById('code-display');

    // Always hide code and theory when switching to a live demo
    if (theoryDisplay) theoryDisplay.style.display = 'none';
    if (codeWindow) codeWindow.style.display = 'none';

    // Toggle between the 2-Port diagram and the Chebyshev diagram
    if (model === '2port') {
        if (demoDisplay) demoDisplay.style.display = 'block';
        if (chebyshevDisplay) chebyshevDisplay.style.display = 'none';
    } 
    else if (model === 'chebyshev') {
        if (demoDisplay) demoDisplay.style.display = 'none';
        if (chebyshevDisplay) chebyshevDisplay.style.display = 'block';
    }
    // else if (model === 'lna') {
    //     if (demoDisplay) demoDisplay.style.display = 'block';
    //     if (chebyshevDisplay) chebyshevDisplay.style.display = 'none';
    // }

    console.log(`Switched Workstation context to: ${model}`);
}

async function loadContent(key, element) {
    const codeWindow = document.getElementById('code-display');
    const theoryDisplay = document.getElementById('theory-display');
    const demoDisplay = document.getElementById('demo-display');
    const chebyshevDisplay = document.getElementById('chebyshev-display');
    const filenameLabel = document.getElementById('active-filename');

    // 1. Sidebar Active State styling
    document.querySelectorAll('.file-link').forEach(link => link.classList.remove('active'));
    element.classList.add('active');

    // 2. Default Hide All Main Views
    theoryDisplay.style.display = 'none';
    demoDisplay.style.display = 'none';
    chebyshevDisplay.style.display = 'none';
    codeWindow.style.display = 'none';

    if (key === 'theory') {
        // FIRST: Reset the bottom console to 2-port (this will accidentally show the demo)
        switchConsole('2port'); 
        
        // SECOND: Override switchConsole's behavior to show the ReadMe instead
        demoDisplay.style.display = 'none'; 
        chebyshevDisplay.style.display = 'none';
        theoryDisplay.style.display = 'block'; 
        
        filenameLabel.textContent = 'ReadMe.md';
    } 
    else if (key === 'demo_2port') {
        demoDisplay.style.display = 'block';
        filenameLabel.textContent = 'demo_2port.ipynb';
        switchConsole('2port');
    } 
    else if (key === 'demo_chebyshev') {
        chebyshevDisplay.style.display = 'block';
        filenameLabel.textContent = 'demo_chebyshev.ipynb';
        switchConsole('chebyshev');
    }
    else if (key === 'demo_lna') {
        // Assuming LNA uses a similar layout to 2-port for now
        demoDisplay.style.display = 'block'; 
        filenameLabel.textContent = 'demo_lna.ipynb';
        switchConsole('lna');
    }
    else {
        // SOURCE CODE VIEWING LOGIC
        codeWindow.style.display = 'block';
        const path = filePaths[key];
        filenameLabel.textContent = path.split('/').pop();
        
        try {
            const response = await fetch(path);
            const code = await response.text();
            document.getElementById('code-content').textContent = code;
            Prism.highlightElement(document.getElementById('code-content'));
        } catch (err) {
            document.getElementById('code-content').textContent = "Error loading source code.";
        }
    }
}

async function calculateFilter() {
    if (!pyodideReady) {
        alert("Please wait for the Python engine to finish loading files.");
        return;
    }

    // Inline the Plotly rendering logic to completely prevent ReferenceErrors
    const renderPlot = (containerId, plotData, title) => {
        const placeholderId = `plot-placeholder-${containerId.split('-').pop()}`;
        const placeholder = document.getElementById(placeholderId);
        if (placeholder) placeholder.style.display = 'none';

        const traces = [
            {
                x: plotData.freqs_ghz, y: plotData.s21_db, type: 'scatter', mode: 'lines',
                name: 'S21 (Insertion Loss)', line: { color: '#58a6ff', width: 2 }
            },
            {
                x: plotData.freqs_ghz, y: plotData.s11_db, type: 'scatter', mode: 'lines',
                name: 'S11 (Return Loss)', line: { color: '#f0883e', width: 1.5 }
            }
        ];

        const layout = {
            title: { text: title, font: { color: '#e6edf3', size: 14 }, y: 0.95 },
            paper_bgcolor: '#161b22', 
            plot_bgcolor: '#0d1117', 
            font: { color: '#e6edf3' },
            xaxis: { title: 'Frequency (GHz)', gridcolor: '#30363d', linecolor: '#30363d', zerolinecolor: '#30363d' },
            yaxis: { title: 'Magnitude (dB)', gridcolor: '#30363d', linecolor: '#30363d', zerolinecolor: '#30363d' },
            
            legend: { 
                orientation: 'h',  
                yanchor: 'top', 
                y: -0.5,            
                xanchor: 'center', 
                x: 0.5,               
                bgcolor: 'rgba(13, 17, 23, 0.7)', 
                bordercolor: '#30363d' 
            },
            
            margin: { l: 60, r: 20, b: 80, t: 60, pad: 4 }, 
            shapes: []
        };

        const spot_freq = plotData.spot_freq_ghz || plotData.center_freq_ghz;
        if (spot_freq) {
            layout.shapes.push({
                type: 'line', x0: spot_freq, y0: -200, x1: spot_freq, y1: 100,
                line: { color: '#e6edf3', width: 1, dash: 'dot' }
            });
        }

        Plotly.newPlot(containerId, traces, layout, {responsive: true, displaylogo: false});
    };

    // UI Feedback: Show loaders for both possible plot areas
    const loader2p = document.getElementById('plot-loader');
    const loaderCheb = document.getElementById('plot-loader-cheb');
    if(loader2p) loader2p.style.display = 'block';
    if(loaderCheb) loaderCheb.style.display = 'block';

    try {
        let pyResult = "";

        if (currentModel === '2port') {
            const Zo = parseFloat(document.getElementById('p-zo').value);
            const L = parseFloat(document.getElementById('p-len').value);
            const freq_ghz = parseFloat(document.getElementById('p-freq').value);

            // Run 2-Port Simulation
            pyResult = await pyodide.runPythonAsync(
`import rf_sim
rf_sim.simulate_2port(${Zo}, ${L}, ${freq_ghz})`
            );

            // Single-point Matrix Calculation for the SVG Diagram
            const spotMatrix = await pyodide.runPythonAsync(
`from rf_math import RFNetworks
mat = RFNetworks.abcd_TL(${freq_ghz}*1e9, ${L}, ${Zo}, er=2.2)
f"A: {mat[0,0].real:.2f} | B: {mat[0,1].imag:.2f}j | C: {mat[1,0].imag:.2f}j | D: {mat[1,1].real:.2f}"`
            );

            // Update UI
            const plotData = JSON.parse(pyResult);
            document.getElementById('diag-params').textContent = spotMatrix;
            renderPlot('plot-container-2port', plotData, 'Filter System Response');

        } 

        else if (currentModel === 'chebyshev') {
            const N = parseInt(document.getElementById('c-order').value);
            const ripple = parseFloat(document.getElementById('c-ripple').value);
            const f0 = parseFloat(document.getElementById('c-f0').value);
            const bw_percent = parseFloat(document.getElementById('c-bw').value);
            const bw_frac = bw_percent / 100;

            // 1. Run the simulation (This returns the JSON string containing EVERYTHING)
            const pyResult = await pyodide.runPythonAsync(`
                import rf_sim
                rf_sim.simulate_chebyshev_bpf(${N}, ${ripple}, ${f0}, ${bw_frac})
            `);

            // 2. Parse the JSON string into a JavaScript Object
            const plotData = JSON.parse(pyResult);

            // 3. Update UI Elements
            document.getElementById('cheb-diag-params').textContent = 
                `N=${N} | Ripple=${ripple}dB | BW=${bw_percent}% | f0=${f0}GHz`;
            
            // Plot the data using your Plotly function
            renderPlot('plot-container-cheb', plotData, `Chebyshev BPF: N=${N}, Ripple=${ripple}dB`);

            // 4. Display the J-values dynamically (grabbing them right out of plotData)
            let jText = "Admittance Inverters (J):<br>";
            if (plotData.j_values) {
                plotData.j_values.forEach((j, index) => {
                    jText += `J${index + 1} = ${j.toFixed(5)}<br>`;
                });
            }
            document.getElementById("j-values-container").innerHTML = jText;
        }

    } catch (err) {
        console.error("Execution Error:", err);
        const errType = err.name === "PythonError" ? "Python Error" : "JavaScript Error";
        alert(`${errType}:\n${err.message}`);
    }
}

async function initPython() {
    try {
        pyodide = await loadPyodide();
        // Load the heavy hitters
        await pyodide.loadPackage(["numpy", "matplotlib"]);
        
        // IMPORTANT: Force Matplotlib to use a web-friendly backend
        pyodide.runPython("import matplotlib; matplotlib.use('Agg')");

        // Fetch and write each file to the VIRTUAL file system
        const files = ['rf_math.py', 'rf_plot.py', 'rf_sim.py'];
        
        for (const filename of files) {
            const response = await fetch(`python/${filename}?v=${new Date().getTime()}`);
            const code = await response.text();
            
            // This line "creates" the file inside Pyodide so 'import' works
            pyodide.FS.writeFile(filename, code);
            console.log(`Successfully mounted ${filename}`);
        }

        pyodideReady = true;
        console.log("Python RF Engine and Matplotlib Ready");

    } catch (err) {
        console.error("Critical Init Error:", err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize the UI state
    const firstLink = document.querySelector('.file-link');
    if (firstLink) loadContent('theory', firstLink);

    // 2. Start the Python Engine
    initPython(); 
});