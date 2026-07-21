(() => {
  const carousel = document.querySelector("[data-carousel]");
  if (!carousel) return;

  const slides = [...carousel.querySelectorAll("[data-carousel-slide]")];
  const previous = carousel.querySelector("[data-carousel-prev]");
  const next = carousel.querySelector("[data-carousel-next]");
  const dots = carousel.querySelector("[data-carousel-dots]");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (slides.length < 2 || !previous || !next || !dots) return;

  let current = 0;
  let timer;
  let manuallyStopped = false;
  const showLabel = dots.dataset.showLabel;

  const controls = slides.map((_, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "home-carousel__dot";
    button.setAttribute("aria-label", showLabel.replace("%d", String(index + 1)));
    button.addEventListener("click", () => select(index));
    dots.append(button);
    return button;
  });

  const show = (index) => {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, slideIndex) => {
      const active = slideIndex === current;
      slide.classList.toggle("is-active", active);
      slide.setAttribute("aria-hidden", String(!active));
      controls[slideIndex].classList.toggle("is-active", active);
      if (active) {
        controls[slideIndex].setAttribute("aria-current", "true");
      } else {
        controls[slideIndex].removeAttribute("aria-current");
      }
    });
  };

  const stopAutomatically = () => {
    manuallyStopped = true;
    window.clearInterval(timer);
  };

  const select = (index) => {
    show(index);
    stopAutomatically();
  };

  const start = () => {
    window.clearInterval(timer);
    if (manuallyStopped || reduceMotion.matches || document.hidden) return;
    timer = window.setInterval(() => show(current + 1), 6000);
  };

  previous.addEventListener("click", () => select(current - 1));
  next.addEventListener("click", () => select(current + 1));
  carousel.addEventListener("mouseenter", () => window.clearInterval(timer));
  carousel.addEventListener("mouseleave", start);
  carousel.addEventListener("focusin", () => window.clearInterval(timer));
  carousel.addEventListener("focusout", (event) => {
    if (!carousel.contains(event.relatedTarget)) start();
  });
  carousel.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") select(current - 1);
    if (event.key === "ArrowRight") select(current + 1);
  });
  document.addEventListener("visibilitychange", start);
  reduceMotion.addEventListener("change", start);

  show(0);
  start();
})();
