const coverImage = document.getElementById("book-cover-image");
const coverButtons = document.querySelectorAll("[data-cover-src]");

for (const button of coverButtons) {
    button.addEventListener("click", () => {
        coverImage.src = button.dataset.coverSrc;
        coverImage.alt = button.dataset.coverAlt;
        for (const other of coverButtons) {
            const selected = other === button;
            other.classList.toggle("active", selected);
            other.setAttribute("aria-pressed", String(selected));
        }
    });
}
