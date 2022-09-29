const csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
const toast_element = document.querySelector('.toast');
const toast = new bootstrap.Toast(toast_element);
const modal_element = document.querySelector('#confirm-modal');
const modal = new bootstrap.Modal(modal_element);

// Set menu button to active
const route = window.location.pathname.split("/")[1];
document.querySelectorAll(`a[href='/${route}']`)[0].classList.add("active");

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

// Show toast
function showToast(title, body) {
  document.getElementById("toast-title").innerHTML = title
  document.getElementById("toast-body").innerHTML = body
  toast.show();
}

document.getElementById("confirm-func").addEventListener("click", e => {
  if (document.getElementById("confirm-title").innerHTML.indexOf("VAT") != -1)
    delete_vat(document.getElementById("confirm-title").name)
  else if (document.getElementById("confirm-title").innerHTML.indexOf("category") != -1)
    delete_category(document.getElementById("confirm-title").name)
  else if (document.getElementById("confirm-title").innerHTML.indexOf("product") != -1)
    delete_product(document.getElementById("confirm-title").name)

  modal.hide()
});

function showConfirmation(title, body, id) {
  document.getElementById("confirm-title").innerHTML = title
  document.getElementById("confirm-title").name = id
  document.getElementById("confirm-body").innerHTML = body
  modal.show();
}
