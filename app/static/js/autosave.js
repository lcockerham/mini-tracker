const TYPING_DELAY_MS = 800;

function setupAutosave(form) {
    const status = document.createElement("p");
    status.className = "autosave-status";
    status.setAttribute("role", "status");
    form.append(status);

    let typingTimer;
    let pending = Promise.resolve();

    function showStatus(text, isError = false) {
        status.textContent = text;
        status.classList.toggle("error", isError);
    }

    async function send(body) {
        try {
            // The edit routes answer with a redirect back to the detail page;
            // stopping at the redirect avoids re-rendering it on every save.
            const response = await fetch(form.action, {
                method: "POST",
                body,
                redirect: "manual",
                keepalive: true,
            });
            if (response.type === "opaqueredirect" || response.ok) {
                showStatus("Saved");
            } else {
                showStatus("Save failed", true);
            }
        } catch {
            showStatus("Save failed", true);
        }
    }

    function save() {
        clearTimeout(typingTimer);
        if (!form.checkValidity()) {
            showStatus("Not saved: fix the highlighted field", true);
            form.reportValidity();
            return;
        }
        // Capture the form now, but send one request at a time so a slow
        // earlier save can't overwrite a newer one.
        const body = new FormData(form);
        showStatus("Saving…");
        pending = pending.then(() => send(body));
    }

    form.addEventListener("change", save);
    form.addEventListener("input", (event) => {
        if (event.target.matches("input[type=text], input[type=url], input[type=number], textarea")) {
            clearTimeout(typingTimer);
            typingTimer = setTimeout(save, TYPING_DELAY_MS);
        }
    });
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        save();
    });
}

for (const form of document.querySelectorAll("form[data-autosave]")) {
    setupAutosave(form);
}
