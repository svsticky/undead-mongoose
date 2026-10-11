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
const filter_input = document.getElementById("filter-products");
if (filter_input) {
  filter_input.addEventListener("keyup", e => {
    const filter = filter_input.value.toLowerCase();
    const products = document.getElementsByClassName("product-row");
    Array.from(products).forEach(product => {
      const name = product.querySelector(".product-name").innerHTML.toLowerCase();
      if (name.includes(filter)) {
        product.style.display = "";
      } else {
        product.style.display = "none";
      }
    });
  });
}

// Keep the scroll position when the page reloads itself (edit, sales, save, closing a modal)
// The page scrolls inside <main> (see base.html), not the window
const SCROLL_KEY = "products-scroll";
const scrollContainer = document.querySelector("main");
window.addEventListener("pagehide", () => {
  try {
    sessionStorage.setItem(SCROLL_KEY, scrollContainer.scrollTop);
  } catch (e) {}
});
try {
  const savedScroll = sessionStorage.getItem(SCROLL_KEY);
  const referrer = document.referrer ? new URL(document.referrer) : null;
  if (savedScroll !== null && referrer && referrer.origin === location.origin && referrer.pathname === location.pathname) {
    scrollContainer.scrollTop = parseInt(savedScroll);
  }
} catch (e) {}

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
