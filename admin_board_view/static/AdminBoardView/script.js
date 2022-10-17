const csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
const toast_element = document.querySelector('.toast');
const toast = new bootstrap.Toast(toast_element);
const modal_element = document.querySelector('#confirm-modal');
const modal = new bootstrap.Modal(modal_element);

// Set menu button to active
const route = window.location.pathname.split("/")[1];
document.querySelectorAll(`a[href='/${route}']`)[0].classList.add("active");

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
