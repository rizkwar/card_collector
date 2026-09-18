(() => {
    const homepage = document.querySelector(".opening-screen");

    if (!homepage) {
        return;
    }

    const renderResponse = async (form) => {
        const response = await fetch(form.action, {
            method: "POST",
            body: new FormData(form),
            headers: { "X-Requested-With": "XMLHttpRequest" },
        });

        if (!response.ok) {
            throw new Error("Pack opening failed.");
        }

        homepage.classList.add("is-transitioning");
        homepage.innerHTML = await response.text();
        requestAnimationFrame(() => {
            homepage.classList.remove("is-transitioning");
            homepage.classList.add("has-result");
        });
        initializeReveal();
    };

    const submitForm = (form) => {
        form.dataset.submitting = "true";
        renderResponse(form).catch(() => form.submit());
    };

    const initializePackOpening = () => {
        const packButton = homepage.querySelector(".pack-button");
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
            window.setTimeout(() => submitForm(packForm), 720);
        };

        packButton.addEventListener("pointerdown", (event) => {
            if (hasOpened) {
                return;
            }

            packButton.classList.add("is-zoomed");
            isDragging = true;
            startX = event.clientX;
            packButton.setPointerCapture?.(event.pointerId);
        });

        packButton.addEventListener("pointermove", (event) => {
            if (!isDragging || hasOpened) {
                return;
            }

            const progress = Math.max(0, Math.min(1, (event.clientX - startX) / 120));
            packButton.style.setProperty("--open-progress", progress);
            if (progress >= 1) {
                submitPack();
            }
        });

        const resetDrag = () => {
            if (!hasOpened) {
                isDragging = false;
                packButton.style.setProperty("--open-progress", "0");
            }
        };

        packButton.addEventListener("pointerup", resetDrag);
        packButton.addEventListener("pointercancel", resetDrag);
        packButton.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                submitPack();
            }
        });
    };

    const initializeReveal = () => {
        const stack = homepage.querySelector(".card-stack");
        const revealedArea = homepage.querySelector(".revealed-cards");
        if (!stack || !revealedArea) {
            initializePackOpening();
            return;
        }

        const remainingCards = [...stack.querySelectorAll(".reveal-card")];
        const revealView = homepage.querySelector(".reveal-view");

        const moveToRevealed = (card, distance, velocity) => {
            card.classList.add("is-pulling");
            card.style.setProperty("--swipe-distance", `${distance}px`);
            card.style.setProperty(
                "--pull-duration",
                `${Math.max(260, Math.min(520, 460 - Math.abs(velocity) * 700))}ms`,
            );
            window.setTimeout(() => {
                revealedArea.append(card);
                card.classList.remove("is-pulling", "is-dragging");
                card.classList.add("is-revealed");
                card.style.removeProperty("--swipe-distance");
                card.style.removeProperty("--pull-duration");
                card.style.removeProperty("--swipe-rotation");
                const nextCard = remainingCards[0];
                nextCard?.focus({ preventScroll: true });
                if (!nextCard) {
                    revealView?.classList.add("is-complete");
                    initializePackOpening();
                }
            }, 520);
        };

        const swipeCard = (card, distance, velocity) => {
            if (remainingCards[0] !== card) {
                return;
            }
            remainingCards.shift();
            moveToRevealed(card, distance, velocity);
        };

        remainingCards.forEach((card) => {
            const image = card.querySelector("img");
            image?.setAttribute("draggable", "false");

            let startY = 0;
            let lastY = 0;
            let lastTime = 0;
            let dragging = false;
            const maxPull = 360;
            const revealThreshold = 0.62;

            const resistedDistance = (distance) => {
                const clamped = Math.min(distance, maxPull);
                if (clamped < 48) {
                    return clamped * 0.78;
                }
                return 37 + (clamped - 48) * 0.94;
            };

            const setDragPosition = (distance) => {
                const visibleDistance = resistedDistance(distance);
                const progress = Math.min(1, distance / maxPull);
                card.style.setProperty("--swipe-distance", `${visibleDistance}px`);
                card.style.setProperty("--swipe-rotation", `${progress * 4}deg`);
            };

            card.addEventListener("pointerdown", (event) => {
                if (remainingCards[0] !== card) {
                    return;
                }
                event.preventDefault();
                startY = event.clientY;
                lastY = startY;
                lastTime = performance.now();
                dragging = true;
                card.setPointerCapture?.(event.pointerId);
                card.classList.add("is-dragging");
            });

            card.addEventListener("pointermove", (event) => {
                if (!dragging || remainingCards[0] !== card) {
                    return;
                }
                event.preventDefault();
                const distance = Math.max(0, event.clientY - startY);
                setDragPosition(distance);
                lastY = event.clientY;
                lastTime = performance.now();
            });

            const finishDrag = (event) => {
                if (!dragging || remainingCards[0] !== card) {
                    return;
                }
                dragging = false;
                card.classList.remove("is-dragging");
                const distance = event.clientY - startY;
                const elapsed = Math.max(1, performance.now() - lastTime);
                const velocity = (event.clientY - lastY) / elapsed;
                const progress = Math.max(0, Math.min(1, distance / maxPull));

                if (progress >= revealThreshold) {
                    const completionDistance = Math.min(
                        620,
                        Math.max(500, resistedDistance(distance) + velocity * 180),
                    );
                    swipeCard(card, completionDistance, velocity);
                } else {
                    card.classList.add("is-returning");
                    card.style.setProperty("--swipe-distance", "0px");
                    card.style.setProperty("--swipe-rotation", "0deg");
                    window.setTimeout(() => card.classList.remove("is-returning"), 360);
                }
            };

            card.addEventListener("pointerup", finishDrag);
            card.addEventListener("pointercancel", () => {
                dragging = false;
                card.classList.remove("is-dragging");
                card.style.setProperty("--swipe-distance", "0px");
                card.style.setProperty("--swipe-rotation", "0deg");
            });
            card.addEventListener("keydown", (event) => {
                if (remainingCards[0] === card && (event.key === "Enter" || event.key === " ")) {
                    event.preventDefault();
                    swipeCard(card, 480);
                }
            });
        });

        initializePackOpening();
    };

    homepage.addEventListener("submit", (event) => {
        const form = event.target.closest("form");
        if (!form || form.dataset.submitting === "true") {
            return;
        }

        if (form.classList.contains("reveal-again-form")) {
            event.preventDefault();
            submitForm(form);
        }
    });

    initializePackOpening();
})();
