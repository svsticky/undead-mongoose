// Add category
const addCategory = document.getElementById("add-category");
if (addCategory) {
  addCategory.addEventListener("click", e => {
    const table = document.getElementById("categories");
    let template = document.getElementById("template-category-item").cloneNode(deep=true);
    template.classList = "category-item";
    template.id = 0;
    table.appendChild(template)
  });
}

// Update categories
const updateCategories = document.getElementById("update-categories");
if (updateCategories) {
  updateCategories.addEventListener("click", e => {
    let items = [];
    
    const categoryItems = Array.from(document.getElementsByClassName("category-item"));
    categoryItems.forEach(category => {
      let name = category.querySelector(".form-control").value.trim();
      if (name) {
        items.push({
          "id": category.id,
          "name": name,
          "checked": category.querySelector("input[type='checkbox']").checked
        });
      }
    });

    $.ajax({
      url: `/category/edit`,
      data: {
        "csrfmiddlewaretoken": csrf_token,
        "categories": JSON.stringify(items)
      },
      type: "post"
    }).then(response => {
      showToast("Update category result", response.msg);
    });
  });
}

// Delete category
const delete_cat_btns = document.getElementsByClassName("delete-category");
if (delete_cat_btns) {
  Array.from(delete_cat_btns).forEach(btn => {
    btn.addEventListener("click", e => {
      showConfirmation(
        "Confirm category delete",
        `Are you sure you want to remove this category?`,
        btn.name
      )
    });
  })
}

function delete_category(id) {
  $.ajax({
    url: `/category/edit`,
    data: {
      "csrfmiddlewaretoken": csrf_token,
      "categories": JSON.stringify([{"id": id, "delete": true}])
    },
    type: "post"
  }).then(response => {
    showToast("Delete category result", response.msg);
    document.querySelector(`#categories [id='${id}']`).remove();
  });
}

// Add VAT
const addVAT = document.getElementById("add-vat");
if (addVAT) {
  addVAT.addEventListener("click", e => {
    const table = document.getElementById("vat");
    let template = document.getElementById("template-vat-item").cloneNode(deep=true);
    template.classList = "vat-item";
    template.id = 0;
    table.appendChild(template)
  });
}

// Update VAT
const updateVAT = document.getElementById("update-vat");
if (updateVAT) {
  updateVAT.addEventListener("click", e => {
    let items = [];
    
    const vatItems = Array.from(document.getElementsByClassName("vat-item"));
    vatItems.forEach(vat => {
      let percentage = vat.querySelector(".form-control").value.trim();
      if (percentage) {
        items.push({
          "id": vat.id,
          "percentage": percentage
        });
      }
    });

    $.ajax({
      url: `/vat/edit`,
      data: {
        "csrfmiddlewaretoken": csrf_token,
        "vat": JSON.stringify(items)
      },
      type: "post"
    }).then(response => {
      showToast("Update VAT result", response.msg);
    });
  });
}

// Delete VAT
const delete_vat_btns = document.getElementsByClassName("delete-vat");
if (delete_vat_btns) {
  Array.from(delete_vat_btns).forEach(btn => {
    btn.addEventListener("click", e => {
      showConfirmation(
        "Confirm VAT delete",
        `Are you sure you want to remove this VAT?`,
        btn.name
      )
    });
  })
}

function delete_vat(id) {
  $.ajax({
    url: `/vat/edit`,
    data: {
      "csrfmiddlewaretoken": csrf_token,
      "vat": JSON.stringify([{"id": id, "delete": true}])
    },
    type: "post"
  }).then(response => {
    showToast("Delete VAT result", response.msg);
    document.querySelector(`#vat [id='${id}']`).remove();
  });
}

// Update settings
const updateSettings = document.getElementById("update-settings");
if (updateSettings) {
  updateSettings.addEventListener("click", e => {
    const data = {
      alc_time: document.getElementById("alc_time").value,
    };

    $.ajax({
      url: `/settings/edit`,
      data: {
        "csrfmiddlewaretoken": csrf_token,
        "settings": JSON.stringify(data)
      },
      type: "post"
    }).then(response => {
      showToast("Updated settings", response.msg);
    });
  });
}

// Export transactions
const exportTransactions = document.getElementById("export-top-ups");
if (exportTransactions) {
  exportTransactions.addEventListener("click", e => {
    const from = document.getElementById("from-date").value;
    const to = document.getElementById("to-date").value;
    const export_dropdown = document.getElementById("export-type")
    const export_type = export_dropdown.options[export_dropdown.selectedIndex].value;
    const url = `/transactions/export?type=${export_type}&start_date=${from}&end_date=${to}`;
    window.open(url, "_blank");
  });
}

if (window.location.pathname.includes("transactions")) {
  if (window.location.search.includes("top_ups")) {
    const top_ups = document.getElementById("top-ups");
    console.log(top_ups)
    if (top_ups) {
      document.getElementById("top-ups-tab").classList.add("active");
      top_ups.classList.add("show");
      top_ups.classList.add("active");
    }
  } else {
    const sales = document.getElementById("sales");
    if (sales) {
      document.getElementById("sales-tab").classList.add("active");
      sales.classList.add("show");
      sales.classList.add("active");
    }
  }
}
