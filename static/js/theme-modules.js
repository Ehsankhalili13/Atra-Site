// Site Theme Mode : Light , Dark

document.addEventListener("DOMContentLoaded", async () => {
    function changeThemeModeBtn(colorMode) {
        let switchBtn = document.querySelector("#ts-img");
        if (!switchBtn) return;

        if (colorMode === "Light") {
            switchBtn.setAttribute("src", urlMoonIcon);
            document.body.className = "light";
        } else if (colorMode === "Dark") {
            switchBtn.setAttribute("src", urlSunIcon);
            document.body.className = "dark";
        }
    }

    function getColorMode() {
        if (localStorage.getItem("ColorMode") === null) {
            localStorage.setItem("ColorMode", "Dark");
            return "Dark";
        } else {
            return localStorage.getItem("ColorMode");
        }
    }

    // --- Initial Theme Setup ---
    const initialColorMode = getColorMode();
    changeThemeModeBtn(initialColorMode);

    const themeSwitcher = document.querySelector("#theme-switcher");
    if (themeSwitcher) {
        themeSwitcher.addEventListener("click", () => {
            const body = document.body;

            let currentMode = localStorage.getItem("ColorMode");
            let newMode;

            if (currentMode === "Light") {
                newMode = "Dark";
                localStorage.setItem("ColorMode", newMode);
                changeThemeModeBtn(newMode);
            } else {
                newMode = "Light";
                localStorage.setItem("ColorMode", newMode);
                changeThemeModeBtn(newMode);
            }
        });
    } else {
        console.error("Theme switcher element (#theme-switcher) not found.");
    }
})
