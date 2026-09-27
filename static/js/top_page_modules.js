function ActiveGP() {
    document.querySelector(".g_page").classList.add("da");
    setTimeout(() => document.querySelector(".g_page").classList.add("oa"), 100);

    document.querySelector(".top_page").classList.add("tpa");
}

function DeactivateGP() {
    document.querySelector(".g_page").classList.remove("oa");
    setTimeout(() => document.querySelector(".g_page").classList.remove("da"), 100);

    document.querySelector(".top_page").classList.remove("tpa");
}

function ActiveTP(TP_Obj) {
    TP_Obj.classList.add("da");
    setTimeout(() => TP_Obj.classList.add("oa"), 100);
}

function DeactivateTP(TP_Obj) {
    TP_Obj.classList.remove("oa");
    setTimeout(() => TP_Obj.classList.remove("da"), 100);
}