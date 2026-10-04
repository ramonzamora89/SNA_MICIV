/**
 * Narrative Controller (Intersection Observer Interface)
 * Generic scroll controller -- hint text comes from each .step's
 * `data-hint` attribute (authored directly in index.html by render-site),
 * not a parallel hardcoded JS dictionary.
 */

document.addEventListener("DOMContentLoaded", () => {
    const steps = document.querySelectorAll(".step");

    const observerOptions = {
        root: null,
        rootMargin: "-25% 0px -35% 0px",
        threshold: 0.15
    };

    let lastActiveStepIndex = -1;

    const stepObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const targetStep = entry.target;
                const stepIndex = parseInt(targetStep.getAttribute("data-step"), 10);

                if (stepIndex !== lastActiveStepIndex) {
                    lastActiveStepIndex = stepIndex;

                    steps.forEach(s => s.classList.remove("active"));
                    targetStep.classList.add("active");

                    if (typeof setVisualState === "function") {
                        setVisualState(stepIndex);
                    }

                    const zoomHint = document.querySelector("#zoom-hint");
                    const hint = targetStep.getAttribute("data-hint");
                    if (zoomHint && hint) {
                        zoomHint.innerText = hint;
                    }
                }
            }
        });
    }, observerOptions);

    steps.forEach(step => stepObserver.observe(step));
});
