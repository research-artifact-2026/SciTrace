const links = document.querySelectorAll('nav a[href^="#"]');

for (const link of links) {
  link.addEventListener("click", () => {
    for (const item of links) item.removeAttribute("aria-current");
    link.setAttribute("aria-current", "page");
  });
}

const zoomModal = document.querySelector("#zoom-modal");
const zoomImage = zoomModal?.querySelector("img");
const zoomClose = zoomModal?.querySelector(".zoom-close");

for (const trigger of document.querySelectorAll(".zoom-trigger")) {
  trigger.addEventListener("click", () => {
    if (!zoomModal || !zoomImage) return;
    zoomImage.src = trigger.dataset.zoomSrc || "";
    zoomImage.alt = trigger.dataset.zoomAlt || "";
    zoomModal.classList.add("open");
    zoomModal.setAttribute("aria-hidden", "false");
  });
}

function closeZoom() {
  if (!zoomModal || !zoomImage) return;
  zoomModal.classList.remove("open");
  zoomModal.setAttribute("aria-hidden", "true");
  zoomImage.src = "";
}

zoomClose?.addEventListener("click", closeZoom);
zoomModal?.addEventListener("click", (event) => {
  if (event.target === zoomModal) closeZoom();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeZoom();
});
