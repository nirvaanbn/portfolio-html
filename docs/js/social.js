// Social Media page. The grid is a wall of poster images so every thumbnail
// fills its white border exactly; clicking one plays it in a lightbox, which
// is the only way a TikTok card gets the width it needs to render properly.
document.addEventListener("DOMContentLoaded", function () {
  var box = document.getElementById("soc-lightbox");
  var media = document.getElementById("soc-lb-media");
  var closeBtn = document.getElementById("soc-lb-close");
  if (!box || !media || !closeBtn) return;

  var lastFocus = null;

  function clearPlayer() {
    Array.prototype.slice.call(media.querySelectorAll("iframe, video"))
      .forEach(function (el) { el.remove(); });   // stops playback
  }

  function open(btn) {
    var kind = btn.getAttribute("data-kind");
    var src = btn.getAttribute("data-src");
    if (!src) return;
    clearPlayer();
    media.setAttribute("data-aspect", btn.getAttribute("data-aspect") || "portrait");

    var player;
    if (kind === "video") {
      player = document.createElement("video");
      player.src = src;
      player.controls = true;
      player.autoplay = true;
      player.setAttribute("playsinline", "");
    } else {
      player = document.createElement("iframe");
      player.src = src;
      player.setAttribute("allow", "autoplay; encrypted-media; picture-in-picture; fullscreen");
      player.setAttribute("allowfullscreen", "");
    }
    player.title = btn.getAttribute("aria-label") || "video";
    media.appendChild(player);

    lastFocus = btn;
    box.hidden = false;
    // let the browser paint the hidden state first so the fade actually runs
    requestAnimationFrame(function () { box.classList.add("is-open"); });
    document.body.classList.add("soc-lb-open");
    closeBtn.focus();
  }

  function close() {
    box.classList.remove("is-open");
    document.body.classList.remove("soc-lb-open");
    clearPlayer();
    box.hidden = true;
    if (lastFocus) lastFocus.focus();
  }

  // Local clips play right where they are, inside their white border.
  function playInline(btn) {
    var v = document.createElement("video");
    v.src = btn.getAttribute("data-src");
    v.controls = true;
    v.autoplay = true;
    v.setAttribute("playsinline", "");
    v.className = "soc-inline-video";
    v.title = btn.getAttribute("aria-label") || "video";
    btn.replaceWith(v);
    v.focus();
  }

  document.querySelectorAll(".soc-play").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (btn.getAttribute("data-kind") === "inline") playInline(btn);
      else open(btn);
    });
  });
  closeBtn.addEventListener("click", close);
  box.addEventListener("click", function (e) { if (e.target === box) close(); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !box.hidden) close();
  });
});
