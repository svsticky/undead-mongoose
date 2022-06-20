const route = window.location.pathname.split("/")[1];
document.querySelectorAll(`a[href='/${route}']`)[0].classList.add("active")
