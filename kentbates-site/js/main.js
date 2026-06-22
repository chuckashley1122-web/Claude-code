/* KENT BATES — site interactions
   Vanilla JS, no dependencies. Progressive enhancement only. */
(function () {
  "use strict";

  /* ---- Mobile nav toggle ---- */
  var toggle = document.querySelector(".nav-toggle");
  var links = document.querySelector(".nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    // Close menu after navigating
    links.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        links.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ---- Reveal on scroll ---- */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---- Gallery filtering ---- */
  var filterBar = document.querySelector(".filters");
  if (filterBar) {
    var pieces = document.querySelectorAll(".gallery-grid .piece");
    filterBar.addEventListener("click", function (ev) {
      var btn = ev.target.closest(".filter-pill");
      if (!btn) return;
      var cat = btn.dataset.filter;
      filterBar.querySelectorAll(".filter-pill").forEach(function (p) {
        p.setAttribute("aria-pressed", String(p === btn));
      });
      pieces.forEach(function (p) {
        var show = cat === "all" || p.dataset.cat === cat;
        p.classList.toggle("is-hidden", !show);
      });
    });
  }

  /* ---- Prefill contact form from ?item= (set by shop "Inquire to buy") ---- */
  var form = document.querySelector("[data-contact-form]");
  if (form) {
    var item = new URLSearchParams(window.location.search).get("item");
    if (item) {
      var subjSel = form.querySelector("#subject");
      var msg = form.querySelector("#message");
      if (subjSel) subjSel.value = "Buying a piece";
      if (msg && !msg.value) {
        msg.value = 'Hi Kent, I\'m interested in "' + item + '". Is it still available?';
      }
    }
  }

  /* ---- Contact form (front-end demo handling) ---- */
  if (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var status = form.querySelector(".form-status");
      var data = new FormData(form);
      var name = (data.get("name") || "there").toString().split(" ")[0];
      if (status) {
        status.hidden = false;
        status.textContent =
          "Thanks, " + name + "! Your message is ready — opening your email app to send it to Kent.";
      }
      // Fallback that works on a static host: open a prefilled email.
      var subject = encodeURIComponent("[kentbates.com] " + (data.get("subject") || "Inquiry"));
      var body = encodeURIComponent(
        "Name: " + (data.get("name") || "") + "\n" +
        "Email: " + (data.get("email") || "") + "\n\n" +
        (data.get("message") || "")
      );
      window.location.href = "mailto:KB@KENTBATES.com?subject=" + subject + "&body=" + body;
    });
  }

  /* ---- Checkout buttons (Stripe Payment Links) ----
     Each .buy-btn links to a Stripe Payment Link. Until a real link is pasted
     in (placeholders contain "REPLACE_"), clicking falls back to the inquiry
     form so the shop is never a dead end. Replace the href and it "just works". */
  document.querySelectorAll(".buy-btn").forEach(function (btn) {
    btn.addEventListener("click", function (ev) {
      var href = btn.getAttribute("href") || "";
      if (href.indexOf("REPLACE_") !== -1 || href === "#") {
        ev.preventDefault();
        var item = btn.dataset.item || "a piece";
        window.location.href = "contact.html?item=" + encodeURIComponent(item);
      }
      // Otherwise: let the browser follow the real Stripe link normally.
    });
  });

  /* ---- Gallery lightbox ----
     Works on any page with a .gallery-grid. Builds the overlay once, makes each
     .piece keyboard-accessible, and supports prev/next + Esc + backdrop close. */
  var grid = document.querySelector(".gallery-grid");
  if (grid) {
    var pieces = Array.prototype.slice.call(grid.querySelectorAll(".piece"));

    // Build overlay
    var lb = document.createElement("div");
    lb.className = "lightbox";
    lb.setAttribute("role", "dialog");
    lb.setAttribute("aria-modal", "true");
    lb.setAttribute("aria-label", "Artwork viewer");
    lb.innerHTML =
      '<div class="lightbox-stage">' +
        '<button class="lb-close" aria-label="Close">&times;</button>' +
        '<button class="lb-btn lb-prev" aria-label="Previous">&#8249;</button>' +
        '<div class="lightbox-art"></div>' +
        '<button class="lb-btn lb-next" aria-label="Next">&#8250;</button>' +
        '<div class="lightbox-cap"></div>' +
      '</div>';
    document.body.appendChild(lb);

    var lbArt = lb.querySelector(".lightbox-art");
    var lbCap = lb.querySelector(".lightbox-cap");
    var stage = lb.querySelector(".lightbox-stage");
    var current = -1;
    var lastFocus = null;

    function visiblePieces() {
      return pieces.filter(function (p) { return !p.classList.contains("is-hidden"); });
    }

    function show(piece) {
      var art = piece.querySelector(".art-fill");
      if (!art) return;
      var label = art.querySelector(".label");
      var title = label ? label.textContent : "Untitled";
      // Mirror the tile's collage class + aspect ratio
      lbArt.className = "lightbox-art " + (art.className.replace("art-fill", "").trim());
      var ar = art.style.getPropertyValue("--ar");
      stage.style.setProperty("--ar", ar || "3 / 4");
      lbCap.innerHTML = "<strong>" + title + "</strong>" +
        '<span>Surreal pop collage · <a href="contact.html?item=' +
        encodeURIComponent(title) + '">Inquire about this piece</a></span>';
    }

    function openAt(idx) {
      var vis = visiblePieces();
      if (!vis.length) return;
      current = (idx + vis.length) % vis.length;
      lastFocus = document.activeElement;
      show(vis[current]);
      lb.classList.add("open");
      document.body.style.overflow = "hidden";
      lb.querySelector(".lb-close").focus();
    }
    function close() {
      lb.classList.remove("open");
      document.body.style.overflow = "";
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    function step(dir) { openAt(current + dir); }

    pieces.forEach(function (p) {
      p.setAttribute("tabindex", "0");
      p.setAttribute("role", "button");
      var lbl = p.querySelector(".label");
      p.setAttribute("aria-label", "View " + (lbl ? lbl.textContent : "artwork"));
      p.addEventListener("click", function () {
        openAt(visiblePieces().indexOf(p));
      });
      p.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openAt(visiblePieces().indexOf(p)); }
      });
    });

    lb.querySelector(".lb-close").addEventListener("click", close);
    lb.querySelector(".lb-prev").addEventListener("click", function () { step(-1); });
    lb.querySelector(".lb-next").addEventListener("click", function () { step(1); });
    lb.addEventListener("click", function (e) { if (e.target === lb) close(); });
    document.addEventListener("keydown", function (e) {
      if (!lb.classList.contains("open")) return;
      if (e.key === "Escape") close();
      else if (e.key === "ArrowLeft") step(-1);
      else if (e.key === "ArrowRight") step(1);
    });
  }

  /* ---- Footer year ---- */
  var yr = document.querySelector("[data-year]");
  if (yr) yr.textContent = new Date().getFullYear();
})();
