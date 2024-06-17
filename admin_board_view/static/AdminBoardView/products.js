const productModal = new bootstrap.Modal(document.getElementById('product-modal'));
const salesModal = new bootstrap.Modal(document.getElementById('sales-modal'));

// Toggle product
const toggle_btns = document.getElementsByClassName("toggle-product");
if (toggle_btns) {
  Array.from(toggle_btns).forEach(btn => {
    btn.addEventListener("click", e => {
      $.ajax({
        url: `/product/toggle`,
        data: {
          "csrfmiddlewaretoken": csrf_token,
          "id": btn.name
        },
        type: "post"
      }).then(response => {
        showToast("Toggle product result", response.msg);
        document.getElementById(btn.name).querySelector(".product-image").classList.toggle("disabled-product");
        btn.innerHTML = btn.innerHTML == "Deactivate" ? "Reactivate" : "Deactivate";
      });
    });    
  });
}

// Delete product
const delete_btns = document.getElementsByClassName("delete-product");
if (delete_btns) {
  Array.from(delete_btns).forEach(btn => {
    btn.addEventListener("click", e => {
      showConfirmation(
        "Confirm product delete",
        `Are you sure you want to remove this product?`,
        btn.name
      )
    });    
  });
}

function delete_product(id) {
  $.ajax({
    url: `/product/delete`,
    data: {
      "csrfmiddlewaretoken": csrf_token,
      "id": id
    },
    type: "post"
  }).then(response => {
    showToast("Delete product result", response.msg);
    document.querySelector(`[id='${id}']`).remove();
  });
}

// Filter products
const filterInput = document.getElementById("filter-products");
const suggestionsContainer = document.getElementById("autocomplete-suggestions");

// console.log($.getJSON({
//   url: '/product/category',  // URL to your Django view
//   data: {
//     "csrfmiddlewaretoken": csrf_token,
//   }
// })
// )
let categories = []
fetch('/product/category', { data: { csrfmiddlewaretoken: csrf_token } })
  .then(response => response.json())
  .then(data => categories = data.map(cat => cat.toLowerCase()))

const statuses = ["active", "inactive"];
// fetch('/product/category_json').then(response => categories = response.json())


let currFocus = -1;
if (filterInput) {
  filterInput.addEventListener("input", e => {
    // console.log(e.key);
    const filterString = filterInput.value.toLowerCase(); 
    suggestions = suggestionsContainer.getElementsByTagName("div")
    cursorPos = filterInput.selectionStart
   
    if(e.key != "Enter"){
      
      //Get last word before cursor position
      const lastWord = filterString.slice(0,cursorPos).split(" ").pop();
      console.log(lastWord, cursorPos);
      suggestionsContainer.innerHTML = '';
      
      if (lastWord.startsWith("category:")) {
        showSuggestions(categories, lastWord.replace("category:", "").trim());
      } else if (lastWord.startsWith("status:")) {
        showSuggestions(statuses, lastWord.replace("status:", "").trim());
      }
    }
    //On submit
    else {
      
    }
  });

  filterInput.addEventListener("keydown", e => {
    const filterString = filterInput.value.toLowerCase();  
    if(e.key == "ArrowDown"){
      e.preventDefault();
      currFocus++;
      addActive(suggestions)
    } else if(e.key == "ArrowUp"){
      e.preventDefault();
      currFocus--;
      addActive(suggestions)
    } else if (e.key === "Enter") {
      if(currFocus > -1 && suggestions.length > 0){
        suggestions[currFocus].click();
      }
      showFilters(filterString);
    }
    return false;
  })

  //Finish word when element is pressed
  suggestionsContainer.addEventListener("click", e => {
    if (e.target && e.target.matches("div.suggestion")) {
      //Split on cursor position
      firstPart = filterInput.value.slice(0,filterInput.selectionStart)
      lastPart = filterInput.value.slice(filterInput.selectionStart)
      //Trim to last colon and combine
      firstPart = firstPart.slice(0,firstPart.lastIndexOf(':')+1)
      filterInput.value = firstPart + e.target.innerText + lastPart
      suggestionsContainer.innerHTML = '';
      currFocus = -1;
    }
  });
  function addActive(suggestions) {
    if (!suggestions || suggestions.length == 0) return false;
    removeActive(suggestions);
    if (currFocus >= suggestions.length) currFocus = 0;
    if (currFocus < 0) currFocus = (suggestions.length - 1);
    suggestions[currFocus].classList.add("suggestion-active");
  }

  function removeActive(suggestions) {
    for (var i = 0; i < suggestions.length; i++) {
      suggestions[i].classList.remove("suggestion-active");
    }
  }
}

//Hide all elements not matching filter
function showFilters(filterString){
  const filters = getFilters(filterString);
  const products = document.getElementsByClassName("product-row");
  Array.from(products).forEach(product => {
    //Get product properties
    const name = product.querySelector(".product-name").innerHTML.toLowerCase();
    const category = product.querySelector(".product-category").innerHTML.toLowerCase();
    const active = product.getAttribute("data-status").toLowerCase();

    //Convert bool to activity string
    let activeFilter = "";
    if (active == "true") activeFilter = "active";
    if (active == "false") activeFilter = "inactive";

    // Only filter by criteria if they are specified (non-empty)
    const nameMatches = !filters.name || name.includes(filters.name);
    const categoryMatches = !filters.category || category.includes(filters.category);
    const statusMatches = !filters.status || activeFilter == filters.status;

    if (nameMatches && categoryMatches && statusMatches) {
      product.style.display = "";
    } else {
      product.style.display = "none";
    }
  })

  //Turn filter string into filter object
  function getFilters(filterString) {

    const strings = filterString.split(" ");
    const filters = {
    category: "",
    status: "",
    name: ""
    };

    //Check if filter exists then assign value in object
    strings.forEach(string => {
      let [type, value] = string.toLowerCase().split(":");
      if (value != undefined) {
        if (filters.hasOwnProperty(type)) {
          filters[type] = value;
        }
      } else {
        filters.name += type + " ";
      }
    });

    filters.name = filters.name.trim(); // Remove trailing space
    return filters;
  }
}

function showSuggestions(suggestions, input) {
  const filteredSuggestions = suggestions.filter(suggestion =>
    suggestion.startsWith(input)
  );

  filteredSuggestions.forEach(suggestion => {
    const suggestionElement = document.createElement("div");
    suggestionElement.className = "suggestion";
    suggestionElement.innerText = suggestion;
    suggestionsContainer.appendChild(suggestionElement);
  });
}

const params = new URLSearchParams(window.location.search);
if (params.get("edit")) {
  productModal.show()
} else if (params.get("sales")) {
  salesModal.show()
}

document.getElementById('product-modal').addEventListener('hidden.bs.modal', function (event) {
  window.location.search = "";
});

document.getElementById('sales-modal').addEventListener('hidden.bs.modal', function (event) {
  window.location.search = "";
});
