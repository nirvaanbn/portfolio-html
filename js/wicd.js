// Landing-page interactions: the "WHAT I CAN DO" window and the
// About Me slide-over. All animation lives in css/style.css; this
// file only toggles classes/attributes and manages focus.
document.addEventListener("DOMContentLoaded", function () {
  // ----- WHAT I CAN DO window -----
  var wicdBtn = document.getElementById("btn-wicd");
  var wicdWin = document.getElementById("wicd-window");
  var wicdClose = document.getElementById("wicd-close");
  var scrollBeforeWicd = null;

  // Most browser windows are wider than 16:9, so the stage's bottom -- and
  // with it the menu's third button -- sits below the fold. Opening the menu
  // scrolls down to reveal it; closing returns you where you were.
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
    // preventScroll: focusing would otherwise yank the page back up and
    // fight the smooth scroll we just started
    if (moveFocus !== false) {
      (open ? wicdClose : wicdBtn).focus({ preventScroll: true });
    }
  }

  if (wicdBtn && wicdWin && wicdClose) {
    wicdBtn.addEventListener("click", function () { setWicd(true); });
    wicdClose.addEventListener("click", function () { setWicd(false); });
  }

  // ----- About Me slide-over -----
  var aboutBtn = document.getElementById("btn-about");
  var aboutPanel = document.getElementById("about-panel");
  var aboutClose = document.getElementById("about-close");

  function aboutIsOpen() {
    return document.body.classList.contains("about-open");
  }

  function setAbout(open) {
    if (!aboutBtn || !aboutPanel) return;
    if (open && !wicdWin.hidden) setWicd(false, false); // tidy up first
    document.body.classList.toggle("about-open", open);
    aboutBtn.setAttribute("aria-expanded", open ? "true" : "false");
    aboutPanel.setAttribute("aria-hidden", open ? "false" : "true");
    // focus targets only become focusable once their fade finishes
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

  // ----- Menu pages: play the exit beat, then navigate -----
  // The stars are drawn at identical coordinates on the next page, so once
  // the artwork has faded and the planet has slid away, swapping documents
  // is invisible. Scrolling back to the top matters: opening the menu
  // scrolled us down, and the next page starts at the top.
  function wireExit(linkId, extraClass) {
    var link = document.getElementById(linkId);
    if (!link) return;
    link.addEventListener("click", function (e) {
      // let ctrl/cmd/middle-click open a new tab the normal way
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
      var href = link.getAttribute("href");
      if (!href || href === "#") return;
      e.preventDefault();
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        window.location.href = href;
        return;
      }
      scrollBeforeWicd = null;               // don't let the close handler fight it
      scrollPageTo(0);
      document.body.classList.add("page-exit");
      if (extraClass) document.body.classList.add(extraClass);
      window.setTimeout(function () { window.location.href = href; }, 900);
    });
  }
  wireExit("menu-social", "exit-social");   // also fades the star its title covers
  wireExit("menu-marketing", null);

  // ----- Escape backs out of whatever is open -----
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    if (aboutIsOpen()) setAbout(false);
    else if (wicdWin && !wicdWin.hidden) setWicd(false);
  });
});
