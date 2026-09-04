document.addEventListener("DOMContentLoaded", function () {
  var wicdBtn = document.getElementById("btn-wicd");
  var wicdWin = document.getElementById("wicd-window");
  var wicdClose = document.getElementById("wicd-close");
  var scrollBeforeWicd = null;

  function scrollPageTo(top) {
    var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: top, behavior: still ? "auto" : "smooth" });
  }

  function setWicd(open, moveFocus) {
    if (!wicdBtn || !wicdWin) return;
    wicdWin.hidden = !open;
    wicdBtn.hidden = open;
    wicdBtn.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      scrollBeforeWicd = window.scrollY;
      scrollPageTo(document.documentElement.scrollHeight);
    } else if (scrollBeforeWicd !== null) {
      scrollPageTo(scrollBeforeWicd);
      scrollBeforeWicd = null;
    }
    if (moveFocus !== false) {
      // preventScroll, or focusing undoes the scroll we just started
      (open ? wicdClose : wicdBtn).focus({ preventScroll: true });
    }
  }

  if (wicdBtn && wicdWin && wicdClose) {
    wicdBtn.addEventListener("click", function () { setWicd(true); });
    wicdClose.addEventListener("click", function () { setWicd(false); });
  }

  var aboutBtn = document.getElementById("btn-about");
  var aboutPanel = document.getElementById("about-panel");
  var aboutClose = document.getElementById("about-close");

  function aboutIsOpen() {
    return document.body.classList.contains("about-open");
  }

  function setAbout(open) {
    if (!aboutBtn || !aboutPanel) return;
    if (open && !wicdWin.hidden) setWicd(false, false);
    document.body.classList.toggle("about-open", open);
    aboutBtn.setAttribute("aria-expanded", open ? "true" : "false");
    aboutPanel.setAttribute("aria-hidden", open ? "false" : "true");
    window.setTimeout(function () {
      if (open === aboutIsOpen()) (open ? aboutClose : aboutBtn).focus({ preventScroll: true });
    }, open ? 1300 : 1200);
  }

  if (aboutBtn && aboutPanel && aboutClose) {
    aboutBtn.addEventListener("click", function (e) {
      e.preventDefault();
      setAbout(true);
    });
    aboutClose.addEventListener("click", function () { setAbout(false); });
  }

  function wireExit(linkId, extraClass) {
    var link = document.getElementById(linkId);
    if (!link) return;
    link.addEventListener("click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
      var href = link.getAttribute("href");
      if (!href || href === "#") return;
      e.preventDefault();
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        window.location.href = href;
        return;
      }
      scrollBeforeWicd = null;
      scrollPageTo(0);
      document.body.classList.add("page-exit");
      if (extraClass) document.body.classList.add(extraClass);
      window.setTimeout(function () { window.location.href = href; }, 900);
    });
  }
  wireExit("menu-social", "exit-social");
  wireExit("menu-marketing", null);

  // We leave with .page-exit on <body>, and the back/forward cache restores the
  // page exactly as it was left, so Back would land on a faded-out page. Reset
  // here instead: pageshow fires whether the page was restored or freshly
  // loaded, and on a fresh load this is a no-op.
  var freeze = document.createElement("style");
  freeze.textContent =
    "body.restoring, body.restoring * { transition: none !important; animation: none !important; }";

  window.addEventListener("pageshow", function () {
    document.head.appendChild(freeze);
    document.body.classList.add("restoring");
    document.body.classList.remove("page-exit", "exit-social");
    scrollBeforeWicd = null;
    setWicd(false, false);
    window.scrollTo(0, 0);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        document.body.classList.remove("restoring");
        if (freeze.parentNode) freeze.parentNode.removeChild(freeze);
      });
    });
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    if (aboutIsOpen()) setAbout(false);
    else if (wicdWin && !wicdWin.hidden) setWicd(false);
  });
});
