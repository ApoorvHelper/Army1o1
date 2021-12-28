const handleUserInput = searchBar => {
    let xhrRequest = new XMLHttpRequest();
    xhrRequest.open("POST", "autocomplete");
    xhrRequest.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhrRequest.onload = function () {
        if (xhrRequest.readyState === 4 && xhrRequest.status !== 200) {
            return;
        }
        let autocompleteResults = JSON.parse(xhrRequest.responseText);
        autocomplete(searchBar, autocompleteResults[1]);
    };

    xhrRequest.send('q=' + searchBar.value);
};

const autocomplete = (searchInput, autocompleteResults) => {
    let currentFocus;
    let originalSearch;

    searchInput.addEventListener("input", function () {
        let autocompleteList, autocompleteItem, i, val = this.value;
        closeAllLists();

        if (!val || !autocompleteResults) {
            return false;
        }

        currentFocus = -1;
        autocompleteList = document.createElement("div");
        autocompleteList.setAttribute("id", this.id + "-autocomplete-list");
        autocompleteList.setAttribute("class", "autocomplete-items");
        this.parentNode.appendChild(autocompleteList);

        for (i = 0; i < autocompleteResults.length; i++) {
            if (autocompleteResults[i].substr(0, val.length).toUpperCase() === val.toUpperCase()) {
                autocompleteItem = document.createElement("div");
                autocompleteItem.innerHTML = "<strong>" + autocompleteResults[i].substr(0, val.length) + "</strong>";
                autocompleteItem.innerHTML += autocompleteResults[i].substr(val.length);
                autocompleteItem.innerHTML += "<input type=\"hidden\" value=\"" + autocompleteResults[i] + "\">";
                autocompleteItem.addEventListener("click", function () {
                    searchInput.value = this.getElementsByTagName("input")[0].value;
                    closeAllLists();
                    document.getElementById("search-form").submit();
                });
                autocompleteList.appendChild(autocompleteItem);
            }
        }
    });

    searchInput.addEventListener("keydown", function (e) {
        let suggestion = document.getElementById(this.id + "-autocomplete-list");
        if (suggestion) suggestion = suggestion.getElementsByTagName("div");
        if (e.keyCode === 40) {
            e.preventDefault();
            currentFocus++;
            addActive(suggestion);
        } else if (e.keyCode === 38) {
            e.preventDefault();
            currentFocus--;
            addActive(suggestion);
        } else if (e.keyCode === 13) {
            e.preventDefault();
            if (currentFocus > -1) {
                if (suggestion) suggestion[currentFocus].click();
            }
        } else {
            originalSearch = document.getElementById("search-bar").value;
        }
    });

    const addActive = suggestion => {
        let searchBar = document.getElementById("search-bar");
        if (!suggestion || !suggestion[currentFocus]) {
            if (currentFocus >= suggestion.length) {
                currentFocus = 0;
            } else if (currentFocus < 0) {
                currentFocus = -1;
                searchBar.value = originalSearch;
                removeActive(suggestion);
                return;
            } else {
                return;
            }
        }

        removeActive(suggestion);
        suggestion[currentFocus].classList.add("autocomplete-active");
        let searchContent = suggestion[currentFocus].textContent;
        if (searchContent.indexOf('(') > 0) {
            searchBar.value = searchContent.substring(0, searchContent.indexOf('('));
        } else {
            searchBar.value = searchContent;
        }

        searchBar.focus();
    };

    const removeActive = suggestion => {
        for (let i = 0; i < suggestion.length; i++) {
            suggestion[i].classList.remove("autocomplete-active");
        }
    };

    const closeAllLists = el => {
        let suggestions = document.getElementsByClassName("autocomplete-items");
        for (let i = 0; i < suggestions.length; i++) {
            if (el !== suggestions[i] && el !== searchInput) {
                suggestions[i].parentNode.removeChild(suggestions[i]);
            }
        }
    };
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
};
