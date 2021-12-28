const setupSearchLayout = () => {
    
    const searchBar = document.getElementById("search-bar");
    const searchBtn = document.getElementById("search-submit");

    
    searchBar.focus();
    searchBar.select();

    searchBar.addEventListener("keyup", function(event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            searchBtn.click();
        } else {
            handleUserInput(searchBar);
        }
    });
};

const setupConfigLayout = () => {
    
    const collapsible = document.getElementById("config-collapsible");
    collapsible.addEventListener("click", function() {
        this.classList.toggle("active");
        let content = this.nextElementSibling;
        if (content.style.maxHeight) {
            content.style.maxHeight = null;
        } else {
            content.style.maxHeight = "400px";
        }

        content.classList.toggle("open");
    });
};

const loadConfig = event => {
    event.preventDefault();
    let config = prompt("Enter name of config:");
    if (!config) {
        alert("Must specify a name for the config to load");
        return;
    }

    let xhrPUT = new XMLHttpRequest();
    xhrPUT.open("PUT", "config?name=" + config + ".conf");
    xhrPUT.onload = function() {
        if (xhrPUT.readyState === 4 && xhrPUT.status !== 200) {
            alert("Error loading Whoogle config");
            return;
        }

        location.reload(true);
    };

    xhrPUT.send();
};

const saveConfig = event => {
    event.preventDefault();
    let config = prompt("Enter name for this config:");
    if (!config) {
        alert("Must specify a name for the config to save");
        return;
    }

    let configForm = document.getElementById("config-form");
    configForm.action = 'config?name=' + config + ".conf";
    configForm.submit();
};

document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        document.getElementById("main").style.display = "block";
    }, 100);

    setupSearchLayout();
    setupConfigLayout();

    document.getElementById("config-load").addEventListener("click", loadConfig);
    document.getElementById("config-save").addEventListener("click", saveConfig);

    
    
    setTimeout(function() { document.getElementById("search-bar").focus(); }, 250);
});
