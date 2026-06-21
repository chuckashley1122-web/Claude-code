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

  /* ---- Footer year ---- */
  var yr = document.querySelector("[data-year]");
  if (yr) yr.textContent = new Date().getFullYear();
})();
