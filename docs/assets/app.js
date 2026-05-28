if (window.location.hostname.includes("anonymous.4open.science")) {
  document.documentElement.classList.add("anonymous-host");
}

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

const benchmarkDomains = [
  { name: "Physics", color: "#f8dc78" },
  { name: "Medicine", color: "#ffe997" },
  { name: "Chemistry", color: "#d3efbf" },
  { name: "Material", color: "#aee9dc" },
  { name: "Biology", color: "#bdd7fb" },
  { name: "Information Science", color: "#c9d2ff" },
];

function polarToCartesian(cx, cy, radius, angleDegrees) {
  const angleRadians = (angleDegrees - 90) * Math.PI / 180;
  return {
    x: cx + radius * Math.cos(angleRadians),
    y: cy + radius * Math.sin(angleRadians),
  };
}

function describeArc(cx, cy, outerRadius, innerRadius, startAngle, endAngle) {
  const outerStart = polarToCartesian(cx, cy, outerRadius, endAngle);
  const outerEnd = polarToCartesian(cx, cy, outerRadius, startAngle);
  const innerStart = polarToCartesian(cx, cy, innerRadius, startAngle);
  const innerEnd = polarToCartesian(cx, cy, innerRadius, endAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";

  return [
    "M", outerStart.x, outerStart.y,
    "A", outerRadius, outerRadius, 0, largeArcFlag, 0, outerEnd.x, outerEnd.y,
    "L", innerStart.x, innerStart.y,
    "A", innerRadius, innerRadius, 0, largeArcFlag, 1, innerEnd.x, innerEnd.y,
    "Z",
  ].join(" ");
}

for (const chart of document.querySelectorAll("[data-domain-chart]")) {
  const slices = chart.querySelector(".domain-slices");
  const domainLabel = chart.querySelector("[data-chart-domain]");
  const copy = chart.querySelector("[data-chart-copy]");
  const total = chart.querySelector("[data-chart-total]");
  if (!slices || !domainLabel || !copy || !total) continue;

  function setActiveDomain(domainName, slice) {
    for (const item of slices.querySelectorAll(".domain-slice")) {
      item.classList.toggle("active", item === slice);
    }
    domainLabel.textContent = domainName;
    total.textContent = "60";
    copy.textContent = `${domainName} contributes 40 high-risk research tasks and 20 tool-related risk tasks.`;
  }

  benchmarkDomains.forEach((domain, index) => {
    const start = index * 60;
    const end = start + 58;
    const mid = start + 30;
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", describeArc(210, 210, 158, 86, start, end));
    path.setAttribute("fill", domain.color);
    path.setAttribute("class", "domain-slice");
    path.setAttribute("tabindex", "0");
    path.style.animationDelay = `${index * 70}ms`;

    const labelPoint = polarToCartesian(210, 210, 124, mid);
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", labelPoint.x);
    label.setAttribute("y", labelPoint.y);
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("dominant-baseline", "middle");
    label.setAttribute("class", "domain-label");
    label.textContent = domain.name.replace("Information Science", "Info Sci.");

    path.addEventListener("mouseenter", () => setActiveDomain(domain.name, path));
    path.addEventListener("focus", () => setActiveDomain(domain.name, path));
    path.addEventListener("click", () => setActiveDomain(domain.name, path));

    slices.append(path, label);
    if (index === 0) setActiveDomain(domain.name, path);
  });
}

for (const zoomArea of document.querySelectorAll("[data-wheel-zoom]")) {
  const zoomTarget = zoomArea.querySelector("svg, img");
  let scale = 1;
  let panX = 0;
  let panY = 0;
  let pointerId = null;
  let startX = 0;
  let startY = 0;
  let startPanX = 0;
  let startPanY = 0;

  function renderZoom() {
    if (!zoomTarget) return;
    zoomTarget.style.setProperty("--zoom", scale.toFixed(3));
    zoomTarget.style.setProperty("--pan-x", `${panX}px`);
    zoomTarget.style.setProperty("--pan-y", `${panY}px`);
  }

  zoomArea.addEventListener("wheel", (event) => {
    event.preventDefault();
    const previousScale = scale;
    const delta = event.deltaY > 0 ? 0.9 : 1.1;
    scale = Math.min(3.2, Math.max(0.82, scale * delta));

    const rect = zoomArea.getBoundingClientRect();
    const offsetX = event.clientX - rect.left - rect.width / 2;
    const offsetY = event.clientY - rect.top - rect.height / 2;
    const ratio = scale / previousScale;
    panX = offsetX - (offsetX - panX) * ratio;
    panY = offsetY - (offsetY - panY) * ratio;
    renderZoom();
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
    renderZoom();
  });

  function endDrag(event) {
    if (pointerId !== event.pointerId) return;
    zoomArea.classList.remove("dragging");
    zoomArea.releasePointerCapture(pointerId);
    pointerId = null;
  }

  zoomArea.addEventListener("pointerup", endDrag);
  zoomArea.addEventListener("pointercancel", endDrag);

  renderZoom();
}
