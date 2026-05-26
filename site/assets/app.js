const paperLink = document.querySelector('.topbar nav a[href="#paper"]');
const benchmarkLink = document.querySelector('.topbar nav a[href="#benchmark"]');
const brandLink = document.querySelector('.brand[href="#paper"]');
const paperView = document.querySelector("#paper");
const benchmarkView = document.querySelector("#benchmark");
const primaryLinks = [paperLink, benchmarkLink, brandLink].filter(Boolean);
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let activeView = null;
let transitionTimer = null;

function setPrimaryNav(isBenchmark) {
  paperLink?.toggleAttribute("aria-current", !isBenchmark);
  benchmarkLink?.toggleAttribute("aria-current", isBenchmark);
}

function getRequestedView() {
  return window.location.hash === "#benchmark" ? "benchmark" : "paper";
}

function applyView(viewName, animate = false) {
  const nextView = viewName === "benchmark" ? benchmarkView : paperView;
  const currentView = activeView === "benchmark" ? benchmarkView : paperView;
  const isBenchmark = viewName === "benchmark";

  setPrimaryNav(isBenchmark);
  window.clearTimeout(transitionTimer);

  if (!nextView || !currentView || !animate || activeView === null || activeView === viewName || prefersReducedMotion) {
    paperView?.classList.toggle("is-visible", !isBenchmark);
    benchmarkView?.classList.toggle("is-visible", isBenchmark);
    if (paperView) paperView.hidden = isBenchmark;
    if (benchmarkView) benchmarkView.hidden = !isBenchmark;
    activeView = viewName;
    window.scrollTo(0, 0);
    return;
  }

  currentView.classList.add("is-exiting");
  currentView.classList.remove("is-visible");

  transitionTimer = window.setTimeout(() => {
    currentView.hidden = true;
    currentView.classList.remove("is-exiting");
    nextView.hidden = false;
    nextView.classList.add("is-visible");
    activeView = viewName;
    window.scrollTo(0, 0);
  }, 180);
}

for (const link of primaryLinks) {
  link.addEventListener("click", (event) => {
    const targetHash = link.getAttribute("href");
    const viewName = targetHash === "#benchmark" ? "benchmark" : "paper";
    if (activeView === viewName) return;
    event.preventDefault();
    history.pushState(null, "", targetHash);
    applyView(viewName, true);
  });
}

window.addEventListener("popstate", () => applyView(getRequestedView(), true));
applyView(getRequestedView(), false);

for (const button of document.querySelectorAll("[data-copy-target]")) {
  button.addEventListener("click", async () => {
    const target = document.querySelector(button.dataset.copyTarget);
    const text = target?.innerText || "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      const original = button.textContent;
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.textContent = original;
      }, 1200);
    } catch {
      button.textContent = "Select BibTeX";
    }
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
