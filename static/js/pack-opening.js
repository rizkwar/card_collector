(() => {
    const packButton = document.querySelector(".pack-button");
    const packForm = packButton?.closest("form");

    if (!packButton || !packForm) {
        return;
    }

    let startX = 0;
    let isDragging = false;
    let hasOpened = false;

    const submitPack = () => {
        if (hasOpened) {
            return;
        }

        hasOpened = true;
        isDragging = false;
        packButton.classList.remove("is-zoomed");
        packButton.classList.add("is-opening");
        packButton.setAttribute("aria-label", "Opening pack");
        window.setTimeout(() => packForm.submit(), 720);
    };

    const beginInteraction = (event) => {
        if (hasOpened) {
            return;
        }

        packButton.classList.add("is-zoomed");
        isDragging = true;
        startX = event.clientX;
        packButton.setPointerCapture?.(event.pointerId);
    };

    const updateInteraction = (event) => {
        if (!isDragging || hasOpened) {
            return;
        }

        const progress = Math.max(0, Math.min(1, (event.clientX - startX) / 120));
        packButton.style.setProperty("--open-progress", progress);

        if (progress >= 1) {
            submitPack();
        }
    };

    const endInteraction = () => {
        if (!hasOpened) {
            isDragging = false;
            packButton.style.setProperty("--open-progress", "0");
        }
    };

    packButton.addEventListener("pointerdown", beginInteraction);
    packButton.addEventListener("pointermove", updateInteraction);
    packButton.addEventListener("pointerup", endInteraction);
    packButton.addEventListener("pointercancel", endInteraction);
    packButton.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            submitPack();
        }
    });
})();