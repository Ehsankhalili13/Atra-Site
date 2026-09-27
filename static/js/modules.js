function ActiveNavLinkPage(ObjSelector) {
    document.querySelector(ObjSelector).classList.add("nla")
}

function DeactivateNavLinkPage(ObjSelector) {
    document.querySelector(ObjSelector).classList.remove("nla")
}

function showAlert(message, type) {
    const alertElement = document.querySelector("#alert")
    if (alertElement) {
        alertElement.innerHTML = message;
        alertElement.style.display = "block"
        alertElement.className = `alert alert-${type}`
        setTimeout(() => { alertElement.classList.add("show") }, 10)
        setTimeout(() => { alertElement.classList.remove('show'); setTimeout(() => { alertElement.style.display = "none"; }, 100) }, 5000);
    } else {
        console.error('Element with class "alert" not found!');
    }
}

function toPersianDigits(str) {
    return String(str).replace(/[0-9]/g, function (w) {
        return String.fromCharCode(w.charCodeAt(0) + 1728);
    });
}

function changeLangRoot(event, lang) {
    if (event) {
        event.preventDefault();
    }
  
    const currentPath = window.location.pathname;
    let cleanPath = currentPath.replace(/^\/(en|ar)(\/|$)/, '/');
  
    let prefix = '';
    if (lang === '/en' || lang === '/ar') {
        prefix = '/' + lang;
    }
  
    let newPath = (prefix + cleanPath).replace(/\/+/g, '/');
  
    if (!newPath) {
        newPath = '/';
    }
  
    const targetUrl = newPath + window.location.search + window.location.hash;
    
    if (window.location.pathname + window.location.search + window.location.hash !== targetUrl) {
        window.location.href = targetUrl;
    }
  }