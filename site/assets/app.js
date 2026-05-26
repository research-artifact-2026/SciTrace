const links = document.querySelectorAll('nav a[href^="#"]');
const paperView = document.querySelector("#paper");
const benchmarkView = document.querySelector("#benchmark");
const paperAnchors = new Set(["", "#paper", "#abstract", "#method", "#experiments"]);

function setActiveLink(hash) {
  const activeHash = hash === "" ? "#paper" : hash;
  for (const item of links) {
    item.toggleAttribute("aria-current", item.getAttribute("href") === activeHash);
  }
}

function showViewFromHash() {
  const hash = window.location.hash || "#paper";
  const isBenchmark = hash === "#benchmark";

  if (paperView && benchmarkView) {
    paperView.hidden = isBenchmark;
    benchmarkView.hidden = !isBenchmark;
  }

  setActiveLink(hash);

  if (paperAnchors.has(hash) && hash !== "#paper" && hash !== "") {
    document.querySelector(hash)?.scrollIntoView({ block: "start" });
  } else {
    window.scrollTo(0, 0);
  }
}

window.addEventListener("hashchange", showViewFromHash);
showViewFromHash();

for (const link of links) {
  link.addEventListener("click", () => {
    window.setTimeout(showViewFromHash, 0);
  });
}

for (const zoomArea of document.querySelectorAll("[data-wheel-zoom]")) {
  const image = zoomArea.querySelector("img");
  const reset = zoomArea.parentElement?.querySelector("[data-zoom-reset]");
  let scale = 1;
  let panX = 0;
  let panY = 0;
  let pointerId = null;
  let startX = 0;
  let startY = 0;
  let startPanX = 0;
  let startPanY = 0;

  function render() {
    if (!image) return;
    image.style.setProperty("--zoom", scale.toFixed(3));
    image.style.setProperty("--pan-x", `${panX}px`);
    image.style.setProperty("--pan-y", `${panY}px`);
  }

  zoomArea.addEventListener("wheel", (event) => {
    event.preventDefault();
    const previousScale = scale;
    const delta = event.deltaY > 0 ? 0.9 : 1.1;
    scale = Math.min(4, Math.max(0.75, scale * delta));

    const rect = zoomArea.getBoundingClientRect();
    const offsetX = event.clientX - rect.left - rect.width / 2;
    const offsetY = event.clientY - rect.top - rect.height / 2;
    const ratio = scale / previousScale;
    panX = offsetX - (offsetX - panX) * ratio;
    panY = offsetY - (offsetY - panY) * ratio;
    render();
  }, { passive: false });

  zoomArea.addEventListener("pointerdown", (event) => {
    pointerId = event.pointerId;
    startX = event.clientX;
    startY = event.clientY;
    startPanX = panX;
    startPanY = panY;
    zoomArea.classList.add("dragging");
    zoomArea.setPointerCapture(pointerId);
  });

  zoomArea.addEventListener("pointermove", (event) => {
    if (pointerId !== event.pointerId) return;
    panX = startPanX + event.clientX - startX;
    panY = startPanY + event.clientY - startY;
    render();
  });

  function endDrag(event) {
    if (pointerId !== event.pointerId) return;
    zoomArea.classList.remove("dragging");
    zoomArea.releasePointerCapture(pointerId);
    pointerId = null;
  }

  zoomArea.addEventListener("pointerup", endDrag);
  zoomArea.addEventListener("pointercancel", endDrag);

  reset?.addEventListener("click", () => {
    scale = 1;
    panX = 0;
    panY = 0;
    render();
  });

  render();
}
