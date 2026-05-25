const links = document.querySelectorAll('nav a[href^="#"]');

for (const link of links) {
  link.addEventListener("click", () => {
    for (const item of links) item.removeAttribute("aria-current");
    link.setAttribute("aria-current", "page");
  });
}
