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

function toggleDetails(id, btn) {
    const details = document.getElementById(id);
    const isExpanded = details.classList.contains('expanded');
    
    // Toggle the class
    details.classList.toggle('expanded');
    
    // Update button text and icon
    if (isExpanded) {
        btn.innerHTML = 'Show Details <i class="fas fa-chevron-down"></i>';
    } else {
        btn.innerHTML = 'Hide Details <i class="fas fa-chevron-up"></i>';
    }
}

function toggleNav() {
    const nav = document.getElementById("side-nav");
    if (nav.style.width === "280px") {
        nav.style.width = "0";
    } else {
        nav.style.width = "280px";
    }
}

// Optional: Close menu if user clicks outside of it
window.onclick = function(event) {
    const nav = document.getElementById("side-nav");
    if (event.target == nav) {
        nav.style.width = "0";
    }
}