//function to toggle nav
function ready_nav() {
    const links = document.querySelectorAll('.nav-link');
        
        if (links.length) {
        links.forEach((link) => {
            link.addEventListener('click', (e) => {
            links.forEach((link) => {
                link.classList.remove('active');
            });
            e.preventDefault();
            link.classList.add('active');
            });
        });
        }
}

export {ready_nav};
