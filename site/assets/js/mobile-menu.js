(() => {
  const menu = document.querySelector(".mobile-menu");
  const toggle = menu?.querySelector(".mobile-menu-toggle");
  const backdrop = menu?.querySelector(".mobile-menu-backdrop");
  const media = window.matchMedia("(max-width: 860px)");
  const background = () => document.querySelectorAll(".skip-link, .masthead-inner, main, .site-footer");
  if (!menu || !toggle || !backdrop) return;

  const close = () => {
    menu.open = false;
    toggle.focus();
  };
  const sync = () => {
    if (!media.matches && menu.open) menu.open = false;
    toggle.setAttribute("aria-expanded", String(menu.open));
    background().forEach((element) => { element.toggleAttribute("inert", menu.open); });
  };

  menu.addEventListener("toggle", sync);
  media.addEventListener("change", sync);
  backdrop.addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && menu.open) close();
  });
  sync();
})();
