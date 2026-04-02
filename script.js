const fileNameDisplay = document.getElementById('file-name-display');
const codeImage = document.getElementById('code-image');
const defaultView = document.getElementById('default-view'); // Added this line

document.querySelectorAll('.carbon-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        
        // 1. Hide the intro blurb
        defaultView.style.display = 'none';
        
        const imgPath = link.getAttribute('data-img');
        const fileName = link.innerText;
        
        fileNameDisplay.innerText = fileName;
        codeImage.src = imgPath;
        codeImage.style.display = 'block';
        
        // Optional: Reset scroll to top of image
        document.querySelector('.image-viewport').scrollTop = 0;
    });
});

const overviewLink = document.getElementById('overview-link');

overviewLink.addEventListener('click', (e) => {
    e.preventDefault();
    
    // 1. Show the intro blurb again
    if(defaultView) defaultView.style.display = 'block';
    
    // 2. Hide the code image
    codeImage.src = "";
    codeImage.style.display = 'none';
    
    // 3. Reset the header text
    fileNameDisplay.innerText = "Project Overview";
    fileNameDisplay.style.color = "var(--text-dim)";
    
    // 4. Clear any highlighted sidebar links
    document.querySelectorAll('.carbon-link').forEach(l => l.style.color = "");
});