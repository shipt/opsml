
// set active class on nav item
// registry: string
function set_nav_link(registry) {
    var nav_link = document.getElementById("nav-" + registry);
    nav_link.classList.add("active");
}


export {
    set_nav_link
};