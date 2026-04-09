let pyodide;

const filePaths = {
    engine: 'python/rf_math.py',
    config: 'python/plot_config.py',
    solve: 'python/solve_filter.py'
};

async function loadContent(key, element) {
    const codeWindow = document.getElementById('code-display'); // The <pre> tag
    const codeContent = document.getElementById('code-content'); // The <code> tag
    const theoryDisplay = document.getElementById('theory-display');
    const demoDisplay = document.getElementById('demo-display');
    const filenameLabel = document.getElementById('active-filename');
    
    // 1. Sidebar Active State styling
    document.querySelectorAll('.file-link').forEach(link => link.classList.remove('active'));
    element.classList.add('active');

    if (key === 'theory') {
        // TOGGLE VISIBILITY
        demoDisplay.style.display = 'none';
        theoryDisplay.style.display = 'block';
        codeWindow.style.display = 'none';
        filenameLabel.textContent = 'ReadMe.md';
    } 

    else if (key === 'demo') {
        // TOGGLE VISIBILITY
        theoryDisplay.style.display = 'none';
        demoDisplay.style.display = 'block';
        filenameLabel.textContent = 'demo_2port.ipynb';
        codeWindow.style.display = 'none';
    } 
    
    else {
        // TOGGLE VISIBILITY
        theoryDisplay.style.display = 'none';
        demoDisplay.style.display = 'none';
        codeWindow.style.display = 'block';
        
        const path = filePaths[key];
        filenameLabel.textContent = path;
        
        // Show a temporary loading state
        codeContent.textContent = "Fetching source code...";
        
        try {
            const response = await fetch(path);
            if (!response.ok) throw new Error("File not found");
            const code = await response.text();
            
            // 2. Inject the raw text into the <code> tag
            codeContent.textContent = code;
            
            // 3. Trigger Prism to highlight the new content
            Prism.highlightElement(codeContent);
            
        } catch (err) {
            codeContent.textContent = `Error: ${err.message}`;
        }
    }
    
    // Reset Scroll position to the top of the window
    document.querySelector('.code-body').scrollTop = 0;
}

async function calculateFilter() {
    if (!pyodide) return;

    // Automatically switch to the demo view when executed
    const demoLink = Array.from(document.querySelectorAll('.file-link')).find(el => el.textContent.includes('demo'));
    if (demoLink) loadContent('demo', demoLink);

    // Grab the specific "Spot Check" frequency
    const freq_ghz = parseFloat(document.getElementById('p-freq').value);
    const L = parseFloat(document.getElementById('p-len').value);
    const Zo = parseFloat(document.getElementById('p-zo').value);

    try {
        // 1. Generate the wide-band Plot (the current logic)
        const plotStr = await pyodide.runPythonAsync(`
            import solve_filter
            solve_filter.run_simulation(${Zo}, ${L})
        `);
        document.getElementById('live-plot').src = plotStr;

        // 2. NEW: Calculate the EXACT Matrix for the user's input frequency
        const spotMatrix = await pyodide.runPythonAsync(`
            import numpy as np
            from rf_math import RFMath
            f_spot = ${freq_ghz} * 1e9
            # Calculate single point ABCD
            mat = RFMath.abcd_TL(f_spot, ${L}, ${Zo}, er=2.2)
            # Format for the UI
            f"A: {mat[0,0].real:.3f} | B: {mat[0,1].imag:.3f}j\\nC: {mat[1,0].imag:.3f}j | D: {mat[1,1].real:.3f}"
        `);

        // Update the SVG and a small text overlay
        document.getElementById('diag-params').textContent = `ABCD Matrix @ ${freq_ghz} GHz: ${spotMatrix.replace('\\n', ' ')}`;
        
        // Ensure the plot area shows up
        document.getElementById('live-plot').style.display = 'block';
        document.getElementById('plot-loader').style.display = 'none';

    } catch (err) {
        console.error(err);
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
        const files = ['rf_math.py', 'plot_config.py', 'solve_filter.py'];
        
        for (const filename of files) {
            const response = await fetch(`python/${filename}`);
            const code = await response.text();
            
            // This line "creates" the file inside Pyodide so 'import' works
            pyodide.FS.writeFile(filename, code);
            console.log(`Successfully mounted ${filename}`);
        }

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