/* AMUZI SPORTS — SITE INTERACTIONS
   Progressive enhancement: all content is usable without JS.
   Handles: sticky header, mobile nav, scroll reveal, counters,
   radar chart draw-in, accordion, pathway stage focus, audience switch. */

(function () {
  "use strict";

  var doc = document;

  /* ---------- Sticky header ---------- */
  var header = doc.querySelector(".site-header");
  if (header && !header.classList.contains("is-solid")) {
    var onScroll = function () {
      if (window.scrollY > 24) header.classList.add("is-scrolled");
      else header.classList.remove("is-scrolled");
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------- Mobile nav ---------- */
  var toggle = doc.querySelector("[data-nav-toggle]");
  var mobileNav = doc.querySelector("[data-mobile-nav]");
  if (toggle && mobileNav) {
    var closeNav = function () {
      toggle.setAttribute("aria-expanded", "false");
      mobileNav.classList.remove("is-open");
      doc.body.style.overflow = "";
    };
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      mobileNav.classList.toggle("is-open", !open);
      doc.body.style.overflow = !open ? "hidden" : "";
    });
    mobileNav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", closeNav);
    });
    doc.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeNav();
    });
  }

  /* ---------- Scroll reveal ---------- */
  var revealEls = doc.querySelectorAll("[data-reveal]");
  if (revealEls.length) {
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              io.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
      );
      revealEls.forEach(function (el) { io.observe(el); });
    } else {
      revealEls.forEach(function (el) { el.classList.add("is-visible"); });
    }
  }

  /* ---------- Animated counters ---------- */
  var counters = doc.querySelectorAll("[data-counter]");
  if (counters.length && "IntersectionObserver" in window) {
    var runCounter = function (el) {
      var target = parseFloat(el.getAttribute("data-counter"));
      var suffix = el.getAttribute("data-suffix") || "";
      var duration = 1400;
      var start = null;
      var from = 0;
      function step(ts) {
        if (!start) start = ts;
        var progress = Math.min((ts - start) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        var value = from + (target - from) * eased;
        el.textContent = (Number.isInteger(target) ? Math.round(value) : value.toFixed(1)) + suffix;
        if (progress < 1) window.requestAnimationFrame(step);
      }
      window.requestAnimationFrame(step);
    };
    var cio = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            runCounter(entry.target);
            cio.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.6 }
    );
    counters.forEach(function (el) { cio.observe(el); });
  }

  /* ---------- Metric bars (performance section) ---------- */
  var bars = doc.querySelectorAll("[data-bar]");
  if (bars.length && "IntersectionObserver" in window) {
    var bio = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var val = entry.target.getAttribute("data-bar");
            entry.target.style.width = val + "%";
            bio.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );
    bars.forEach(function (el) { bio.observe(el); });
  }

  /* ---------- Accordion ---------- */
  doc.querySelectorAll(".accordion-item").forEach(function (item) {
    var trigger = item.querySelector(".accordion-trigger");
    var panel = item.querySelector(".accordion-panel");
    if (!trigger || !panel) return;
    trigger.addEventListener("click", function () {
      var isOpen = item.classList.contains("is-open");
      item.parentElement.querySelectorAll(".accordion-item.is-open").forEach(function (other) {
        if (other !== item) {
          other.classList.remove("is-open");
          other.querySelector(".accordion-panel").style.maxHeight = null;
          other.querySelector(".accordion-trigger").setAttribute("aria-expanded", "false");
        }
      });
      item.classList.toggle("is-open", !isOpen);
      trigger.setAttribute("aria-expanded", String(!isOpen));
      panel.style.maxHeight = !isOpen ? panel.scrollHeight + "px" : null;
    });
  });

  /* ---------- Audience switch (contact page) ---------- */
  var switchBtns = doc.querySelectorAll("[data-audience-btn]");
  var audiencePanels = doc.querySelectorAll("[data-audience-panel]");
  if (switchBtns.length) {
    switchBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var target = btn.getAttribute("data-audience-btn");
        switchBtns.forEach(function (b) { b.classList.toggle("is-active", b === btn); });
        audiencePanels.forEach(function (p) {
          p.hidden = p.getAttribute("data-audience-panel") !== target;
        });
        var typeField = doc.querySelector("#enquiry-type");
        if (typeField) typeField.value = target;
      });
    });
  }

  /* ---------- Back to top ---------- */
  var backToTop = doc.querySelector("[data-back-to-top]");
  if (backToTop) {
    window.addEventListener(
      "scroll",
      function () {
        backToTop.classList.toggle("is-visible", window.scrollY > 900);
      },
      { passive: true }
    );
    backToTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ---------- Current year in footer ---------- */
  var yearEl = doc.querySelector("[data-year]");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- Enquiry form (no backend wired — structured for future API/CMS) ---------- */
  var forms = doc.querySelectorAll("[data-enquiry-form]");
  forms.forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var confirmation = form.parentElement.querySelector("[data-form-confirmation]");
      form.hidden = true;
      if (confirmation) confirmation.hidden = false;
      /* TODO: wire to enquiry API / CRM endpoint before go-live. */
    });
  });
})();
