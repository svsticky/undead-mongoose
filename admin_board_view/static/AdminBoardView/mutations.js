let selectedProducts = [];

function addProduct() {
    let productName = document.getElementById("product").value;
    let amount = document.getElementById("amount").value;

    if (!productName || !amount || amount < 1 || amount > 1000) {
        showMessage("Error", "Amount must be between 1 and 1000.");
        return;
    }

    let productOption = [...document.getElementById("productOptions").options].find(option => option.value === productName);
    if (!productOption) return;

    selectedProducts.push({ id: productOption.id, name: productName, amount: amount });
    updateSelectedProducts();
}

function cancelMutation() {
    selectedProducts = [];
    updateSelectedProducts();
}

function confirmMutation(event) {
    event.preventDefault();  // Prevent default form submission

    let mutationType = document.getElementById("mutation-type").value;

    // Ensure that a valid mutation type is selected (not the placeholder)
    if (!mutationType) {
        showMessage("Error", "Please select a mutation type.");
        return;
    }

    // Proceed with the mutation only if a valid mutation type is selected
    if (selectedProducts.length === 0) {
        showMessage("Error", "Please select products to mutate.");
        return;
    }

    let csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;

    // Disable the confirm button to prevent double submission
    document.getElementById("confirm-mutation").disabled = true;

    fetch("/mutate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ mutation_type: mutationType, products: selectedProducts })
    }).then(response => response.json()).then(data => {
        if (data.success) {
            showMessage("Success", "Mutation saved successfully!");
        } else {
            showMessage("Error", "Error: " + (data.error || "Something went wrong"));
        }
    }).catch(error => {
        showMessage("Error", "An unexpected error occurred. Please try again.");
        console.error("Mutation error:", error);
    }).finally(() => {
        document.getElementById("confirm-mutation").disabled = false;
    });
}

function updateSelectedProducts() {
    const selectedProductsList = document.getElementById("selected-products");
    selectedProductsList.innerHTML = '';

    selectedProducts.forEach((product, index) => {
        const listItem = document.createElement("li");
        listItem.classList.add("list-group-item");
        listItem.innerHTML = `${product.amount}x ${product.name} <button class="btn btn-sm btn-danger float-end remove-product" onclick="removeProduct(${index})">✖</button>`;
        selectedProductsList.appendChild(listItem);
    });
}

function removeProduct(index) {
    selectedProducts.splice(index, 1);
    updateSelectedProducts();
}

function showMessage(title, message) {
    document.getElementById("message-modal-label").innerText = title;
    document.getElementById("modal-message-body").innerText = message;
    
    const messageModal = new bootstrap.Modal(document.getElementById('message-modal'), {
        backdrop: 'static',
        keyboard: false
    });

    messageModal.show();

    messageModal._element.addEventListener('hidden.bs.modal', function () {
        location.reload();  // Reload after user closes the modal
    });
}
