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
      $.ajax({
        url: `/category/edit`,
        data: {
          "csrfmiddlewaretoken": csrf_token,
          "categories": JSON.stringify([{"id": btn.name, "delete": true}])
        },
        type: "post"
      }).then(response => {
        showToast("Delete category result", response.msg);
        btn.parentElement.parentElement.remove();
      });
    });
  })
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
      $.ajax({
        url: `/vat/edit`,
        data: {
          "csrfmiddlewaretoken": csrf_token,
          "vat": JSON.stringify([{"id": btn.name, "delete": true}])
        },
        type: "post"
      }).then(response => {
        showToast("Delete VAT result", response.msg);
        btn.parentElement.parentElement.remove();
      });
    });
  })
}