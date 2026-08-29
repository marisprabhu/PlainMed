/* PlainMed mobile client.
 *
 * Holds the document only in a module-scoped variable: no localStorage, no
 * IndexedDB, no service-worker caching of report data. Closing the tab or
 * pressing Clear ends the session, which is what "never stored" has to mean
 * on the client as well as the server.
 */
(function () {
  "use strict";

  // Bump when this file changes. Printed to the console and shown in the
  // footer, so "the browser is running an old copy" is a visible fact
  // rather than something to be guessed at.
  var CLIENT_BUILD = "2026-08-29d";
  var API = "/api/v1";
  var state = {
    doc: null, result: null, session: null,
    consentVersion: null, notice: null, lang: "en"
  };

  var $ = function (id) { return document.getElementById(id); };

  /* --------------------------------------------------------- utilities */

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function show(view) {
    // Leaving the camera view must always release the device, or the
    // recording indicator stays on after the user has moved on.
    if (view !== "view-camera") stopCamera();
    ["view-consent", "view-capture", "view-camera", "view-review", "view-results"]
      .forEach(function (id) { $(id).hidden = id !== view; });
    $("restart").hidden = (view === "view-capture" || view === "view-consent");
    window.scrollTo(0, 0);
  }

  function busy(on, text) {
    $("busy").hidden = !on;
    if (text) $("busy-text").textContent = text;
  }

  /* Send a fault to the server so it lands in the log the operator reads.
     Asking a user to open devtools is a poor ask, and impossible on a
     phone. Best effort: never let reporting an error cause another one. */
  function report(where, error) {
    try {
      var body = {
        build: CLIENT_BUILD,
        ua: navigator.userAgent,
        where: String(where || "unknown"),
        message: (error && error.message) || String(error),
        stack: (error && error.stack) || ""
      };
      fetch(API + "/client-error", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        keepalive: true
      }).catch(function () {});
    } catch (e) { /* reporting must never throw */ }
  }

  // Anything that escapes a handler still gets reported.
  window.addEventListener("error", function (e) {
    report("window.onerror", e.error || e.message);
  });
  window.addEventListener("unhandledrejection", function (e) {
    report("unhandledrejection", e.reason);
  });

  function fail(error) {
    busy(false);
    // A blank error box is the worst possible outcome: the user sees a dead
    // page with no way to act. Anything unexpected still produces a message.
    var message =
      (typeof error === "string" && error) ||
      (error && error.message) ||
      "Something went wrong. Reloading the page usually fixes it.";
    $("error-text").textContent = message;
    $("build-tag").textContent = "build " + CLIENT_BUILD;
    // The real object goes to the console so a defect can be diagnosed
    // instead of inferred from a screenshot.
    if (error && error.stack) {
      console.error("[PlainMed " + CLIENT_BUILD + "]", error);
    } else {
      console.error("[PlainMed " + CLIENT_BUILD + "] " + message);
    }
    report("fail", error);
    $("error").hidden = false;
  }

  /* Consent gate. DPDP requires the notice to be shown and consent given
     before any processing, so a session is never minted implicitly - it is
     minted only by the user pressing the button on the notice screen.
     The token is anonymous and lives in memory only. */
  async function loadNotice(lang) {
    var r = await fetch(API + "/notice?lang=" + encodeURIComponent(lang));
    if (!r.ok) {
      throw new Error("PlainMed is temporarily unavailable. Please try later.");
    }
    var n = await r.json();
    state.notice = n;
    state.lang = n.language;
    state.consentVersion = n.consent_version;
    renderNotice(n);
    return n;
  }

  function renderNotice(n) {
    $("nt-title").textContent = n.title;
    $("nt-intro").textContent = n.intro;
    $("nt-retention").textContent = n.retention;
    $("nt-sharing").textContent = n.sharing;
    $("nt-withdraw").textContent = n.withdraw;
    $("nt-grievance").textContent = n.grievance;
    $("nt-board").textContent = n.board;
    $("nt-advice").textContent = n.not_medical_advice;
    $("nt-age").textContent = n.age;

    $("nt-items").innerHTML = n.items.map(function (i) {
      return "<tr><td>" + esc(i.data) + "</td><td>" + esc(i.purpose) + "</td></tr>";
    }).join("");
    $("nt-rights").innerHTML = n.rights.map(function (r) {
      return "<li>" + esc(r) + "</li>";
    }).join("");

    var c = n.contact || {};
    $("nt-contact").textContent = (c.name || c.email)
      ? [c.name, c.email].filter(Boolean).join(" · ")
      : "";
  }

  async function grantConsent() {
    var r = await fetch(API + "/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        accepted: true,
        consent_version: state.consentVersion,
        age_confirmed: true
      })
    });
    if (!r.ok) {
      var b = null;
      try { b = await r.json(); } catch (e) {}
      throw new Error((b && b.detail) || "Could not record your consent.");
    }
    state.session = (await r.json()).session;
    return state.session;
  }

  async function ensureSession() {
    if (state.session) return state.session;
    // No silent re-consent: send the user back to the notice.
    show("view-consent");
    throw new Error("Please read the notice and give your consent to continue.");
  }

  async function call(path, options) {
    options = options || {};
    var token = await ensureSession();
    options.headers = Object.assign({}, options.headers, {
      "x-plainmed-session": token
    });

    var response;
    try {
      response = await fetch(API + path, options);
    } catch (e) {
      throw new Error("Could not reach PlainMed. Check your connection and try again.");
    }
    if (response.status === 401) {
      // Session expired mid-flow. Consent cannot be renewed silently, so
      // return the user to the notice rather than re-consenting for them.
      state.session = null;
      show("view-consent");
      throw new Error("Your session expired. Please review the notice again.");
    }
    if (response.status === 429) {
      throw new Error("Too many requests. Please wait a moment and try again.");
    }
    var body = null;
    try { body = await response.json(); } catch (e) { /* non-JSON error page */ }
    if (!response.ok) {
      throw new Error((body && (body.detail || body.error)) ||
        "Something went wrong reading your report.");
    }
    return body;
  }

  /* ----------------------------------------------------------- camera */

  /* `capture="environment"` on a file input opens the camera on phones but
     is ignored on desktop, where it degrades to a file picker. getUserMedia
     gives a real viewfinder on both — and localhost counts as a secure
     context, so it works for a local demo without certificates.
     Anything that fails here falls back to the file input. */
  var camStream = null;

  function stopCamera() {
    if (!camStream) return;
    camStream.getTracks().forEach(function (t) { t.stop(); });
    camStream = null;
    $("cam-video").srcObject = null;
  }

  async function openCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      $("camera").click();          // no live camera available
      return;
    }
    // The browser shows its own permission prompt here. Say so, rather than
    // leaving a spinner over a prompt the user needs to see and answer.
    busy(true, "Allow camera access when your browser asks…");
    try {
      var request = navigator.mediaDevices.getUserMedia({
        video: {
          // Rear camera on a phone; ignored where there is only one.
          facingMode: { ideal: "environment" },
          // Small print on a lab report needs resolution.
          width: { ideal: 1920 },
          height: { ideal: 1440 }
        },
        audio: false
      });

      // A dismissed prompt never settles, so a request that has not been
      // answered must not leave the user on a spinner forever.
      camStream = await Promise.race([
        request,
        new Promise(function (_, reject) {
          setTimeout(function () {
            reject(new Error("camera-permission-timeout"));
          }, 20000);
        })
      ]);
      var video = $("cam-video");
      video.srcObject = camStream;
      await video.play();
      busy(false);
      show("view-camera");
    } catch (e) {
      busy(false);
      stopCamera();
      report("openCamera", e);

      // Denied, dismissed, in use, or unavailable. Say which, then fall back
      // to the file input - on a phone that still opens the native camera.
      if (e && (e.name === "NotAllowedError" || e.message === "camera-permission-timeout")) {
        fail("PlainMed needs camera permission to take a photo. Allow it in " +
             "your browser, or use “Choose an existing photo” instead.");
        return;
      }
      if (e && e.name === "NotReadableError") {
        fail("Your camera is being used by another app. Close it and try again.");
        return;
      }
      $("camera").click();
    }
  }

  function captureFrame() {
    var video = $("cam-video");
    var w = video.videoWidth, h = video.videoHeight;
    if (!w || !h) { fail("The camera is not ready yet. Try again."); return; }

    var canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    canvas.getContext("2d").drawImage(video, 0, 0, w, h);

    canvas.toBlob(function (blob) {
      stopCamera();
      if (!blob) { fail("Could not capture the photo. Try again."); return; }
      sendPhoto(new File([blob], "scan.jpg", { type: "image/jpeg" }));
    }, "image/jpeg", 0.92);
  }

  /* ------------------------------------------------------------- scan */

  async function sendPhoto(file) {
    busy(true, "Reading your report…");
    var form = new FormData();
    form.append("image", file, file.name || "scan.jpg");
    try {
      var data = await call("/scan/photo", { method: "POST", body: form });
      onScanned(data);
    } catch (e) { fail(e); }
  }

  async function sendPdf(file) {
    busy(true, "Reading your PDF…");
    var form = new FormData();
    form.append("file", file, file.name || "report.pdf");
    try {
      var data = await call("/scan/pdf", { method: "POST", body: form });
      onScanned(data);
    } catch (e) { fail(e); }
  }

  async function sendText(text) {
    busy(true, "Reading your report…");
    try {
      var data = await call("/scan/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
      });
      onScanned(data);
    } catch (e) { fail(e); }
  }

  function onScanned(data) {
    busy(false);
    state.doc = data.document;
    renderReview(data);
    show("view-review");
  }

  /* ----------------------------------------------------------- review */

  function renderReview(data) {
    var doc = data.document;
    var unsure = data.low_confidence_span_ids || [];
    var n = doc.values.length;

    $("review-lede").textContent = n
      ? "We read " + n + " result" + (n === 1 ? "" : "s") +
        ". Tap any value to correct it before we explain anything."
      : "We could not read any test results from this. Try a clearer photo.";

    var warn = $("review-warn");
    if (unsure.length) {
      warn.hidden = false;
      warn.textContent = "We were unsure about " + unsure.length + " line" +
        (unsure.length === 1 ? "" : "s") + ", highlighted below. " +
        "Please check " + (unsure.length === 1 ? "it" : "them") +
        " against your report carefully.";
    } else {
      warn.hidden = true;
    }

    var html = doc.values.map(function (v) {
      // Trust the server's judgement: confidence scales differ per OCR
      // engine, so the threshold lives with the engine, not here.
      var flagged = v.needs_review === true;
      var meta = [];
      if (v.ref_raw) meta.push("Reference range " + esc(v.ref_raw));
      else meta.push("No reference range listed");
      if (v.flag) meta.push('<span class="row-flag">Report flag: ' + esc(v.flag) + "</span>");

      return '' +
        '<div class="row' + (flagged ? " review" : "") + '" data-span="' + esc(v.span_id) + '">' +
          '<div class="row-top">' +
            '<input class="row-name f-name" value="' + esc(v.analyte) + '" ' +
                   'aria-label="Test name" style="border:none;background:none;padding:0;font-weight:600;flex:1 1 auto;">' +
            '<span class="row-src">' + esc(v.span_id) + '</span>' +
          '</div>' +
          '<div class="row-fields">' +
            '<input class="f-value" value="' + esc(v.raw_value) + '" aria-label="Value" inputmode="decimal">' +
            '<input class="f-unit" value="' + esc(v.unit || "") + '" aria-label="Unit" placeholder="unit">' +
          '</div>' +
          '<div class="row-meta">' + meta.join(" &middot; ") + "</div>" +
          (flagged ? '<span class="row-unsure">⚠ Unclear in the photo — please confirm</span>' : "") +
        "</div>";
    }).join("");

    $("review-list").innerHTML = html;
    $("explain").disabled = n === 0;
  }

  function collectCorrections() {
    var out = [];
    var rows = $("review-list").querySelectorAll(".row");
    var byId = {};
    state.doc.values.forEach(function (v) { byId[v.span_id] = v; });

    Array.prototype.forEach.call(rows, function (row) {
      var id = row.getAttribute("data-span");
      var original = byId[id];
      if (!original) return;
      var name = row.querySelector(".f-name").value.trim();
      var value = row.querySelector(".f-value").value.trim();
      var unit = row.querySelector(".f-unit").value.trim();
      var changed =
        name !== original.analyte ||
        value !== original.raw_value ||
        unit !== (original.unit || "");
      // A line the user looked at and confirmed is also worth sending, so the
      // server can clear its low-confidence marking.
      if (changed || (original.ocr_confidence != null)) {
        out.push({ span_id: id, analyte: name, raw_value: value, unit: unit });
      }
    });
    return out;
  }

  /* ---------------------------------------------------------- explain */

  async function explain() {
    busy(true, "Explaining your report…");
    try {
      var data = await call("/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document: state.doc,
          corrections: collectCorrections()
        })
      });
      busy(false);
      state.result = data.result;
      renderResults(data);
      show("view-results");
    } catch (e) { fail(e); }
  }

  /* ---------------------------------------------------------- results */

  var STATUS_LABELS = {
    flagged_high: "Marked high in your report",
    flagged_low: "Marked low in your report",
    flagged_abnormal: "Marked abnormal in your report",
    above_range: "Above the reference range listed in your report",
    below_range: "Below the reference range listed in your report",
    within_range: "Within the reference range listed in your report",
    no_range: "No reference range listed in your report"
  };
  var ATTENTION = {
    flagged_high: 1, flagged_low: 1, flagged_abnormal: 1,
    above_range: 1, below_range: 1
  };

  function renderResults(data) {
    var r = data.result;

    $("issues").innerHTML = (r.issues || []).map(function (i) {
      return '<div class="issue ' + esc(i.severity) + '">' + esc(i.message) + "</div>";
    }).join("");

    var parts = [];
    if (r.narrative && r.narrative.items.length) {
      parts.push(r.narrative.items.map(function (item) {
        return '<div class="card summary"><p>' + esc(item.text) + "</p>" +
          '<p class="src">Sources: ' + esc(item.span_ids.join(", ")) + "</p></div>";
      }).join(""));
    }

    parts.push((r.cards || []).map(function (c) {
      var badge = c.status
        ? '<span class="badge' + (ATTENTION[c.status] ? " attention" : "") + '">' +
          esc(STATUS_LABELS[c.status] || c.status) + "</span>"
        : "";
      var src;
      if (c.kind === "glossary") src = "Source: PlainMed local glossary";
      else if (c.span_ids && c.span_ids.length) src = "Sources: " + esc(c.span_ids.join(", "));
      else src = "Not specified in your report";
      return '<div class="card ' + esc(c.kind) + '">' +
        "<h3>" + esc(c.title) + badge + "</h3>" +
        "<p>" + esc(c.body).replace(/\n\n/g, "</p><p>") + "</p>" +
        '<p class="src">' + src + "</p></div>";
    }).join(""));
    $("panel-cards").innerHTML = parts.join("");

    var parsed = {};
    state.doc.values.forEach(function (v) { parsed[v.span_id] = 1; });
    var unparsed = {};
    (state.doc.unparsed_span_ids || []).forEach(function (id) { unparsed[id] = 1; });

    $("panel-source").innerHTML =
      '<p class="lede">Green lines were read as results. Yellow lines were not ' +
      "interpreted &mdash; check them yourself.</p>" +
      state.doc.spans.map(function (s) {
        var cls = parsed[s.id] ? "parsed" : (unparsed[s.id] ? "unparsed" : "");
        return '<div class="srcline ' + cls + '"><span class="id">' + esc(s.id) +
          "</span><span>" + esc(s.text) + "</span></div>";
      }).join("");

    var ask = "";
    if ((r.comprehension_questions || []).length) {
      ask += "<h3>Check your understanding</h3>";
      ask += r.comprehension_questions.map(function (q, qi) {
        return '<div class="qcard" data-q="' + qi + '"><p>' + esc(q.question) + "</p>" +
          q.options.map(function (o, oi) {
            return '<button class="opt" data-q="' + qi + '" data-o="' + oi + '">' +
              esc(o) + "</button>";
          }).join("") +
          '<p class="qfeed" hidden></p></div>';
      }).join("");
    }
    ask += "<h3>Questions to take to your clinician</h3>";
    ask += (r.clinician_questions || []).map(function (q) {
      return '<div class="ask">' + esc(q.text) +
        '<p class="src">Sources: ' + esc(q.span_ids.join(", ")) + "</p></div>";
    }).join("");
    $("panel-ask").innerHTML = ask;

    $("panel-ask").addEventListener("click", function (e) {
      var btn = e.target.closest(".opt");
      if (!btn) return;
      var qi = +btn.getAttribute("data-q");
      var oi = +btn.getAttribute("data-o");
      var q = r.comprehension_questions[qi];
      var card = btn.closest(".qcard");
      var feed = card.querySelector(".qfeed");
      Array.prototype.forEach.call(card.querySelectorAll(".opt"), function (b) {
        b.classList.remove("right", "wrong");
      });
      if (oi === q.answer_index) {
        btn.classList.add("right");
        feed.textContent = "That matches your report.";
      } else {
        btn.classList.add("wrong");
        feed.textContent = "That does not match your report. " + q.explanation;
      }
      feed.hidden = false;
    });

    $("foot-status").textContent =
      "Explained by: " + data.backend + " · processed, never stored";
  }

  /* -------------------------------------------------------------- wire */

  function withdrawConsent() {
    // Withdrawal must be as easy as giving consent (DPDP s.6(4)). Dropping
    // the token stops all further processing immediately; nothing is stored
    // server-side, so there is nothing left to erase.
    state.session = null;
    // Clear the affirmations too. Leaving them ticked would let someone
    // click straight back through without re-reading, which is not a
    // withdrawal in any meaningful sense.
    $("agree-age").checked = false;
    $("agree-consent").checked = false;
    refreshConsentButton();
    reset();
    show("view-consent");
  }

  /* Where to land after clearing. Never assume the capture screen is safe:
     without a session the user would sit on a camera button that cannot
     work, which reads as the app being broken. */
  function landingView() {
    return state.session ? "view-capture" : "view-consent";
  }

  function reset() {
    state.doc = null;
    state.result = null;
    // The session is deliberately kept: it identifies nobody, and dropping
    // it on every clear would force a needless round trip.
    ["camera", "gallery", "pdf"].forEach(function (id) { $(id).value = ""; });
    $("paste").value = "";
    $("review-list").innerHTML = "";
    $("panel-cards").innerHTML = "";
    $("panel-source").innerHTML = "";
    $("panel-ask").innerHTML = "";
    $("issues").innerHTML = "";
    $("foot-status").textContent = "Processed, never stored.";
    show(landingView());
  }

  $("open-camera").addEventListener("click", openCamera);
  $("cam-shoot").addEventListener("click", captureFrame);
  $("cam-cancel").addEventListener("click", function () { show("view-capture"); });

  $("camera").addEventListener("change", function (e) {
    if (e.target.files && e.target.files[0]) sendPhoto(e.target.files[0]);
  });
  $("gallery").addEventListener("change", function (e) {
    if (e.target.files && e.target.files[0]) sendPhoto(e.target.files[0]);
  });
  $("pdf").addEventListener("change", function (e) {
    if (e.target.files && e.target.files[0]) sendPdf(e.target.files[0]);
  });
  $("paste-go").addEventListener("click", function () {
    var text = $("paste").value.trim();
    if (text) sendText(text);
  });

  $("explain").addEventListener("click", explain);
  $("back").addEventListener("click", reset);
  $("done").addEventListener("click", reset);
  $("restart").addEventListener("click", reset);
  $("error-close").addEventListener("click", async function () {
    $("error").hidden = true;
    reset();
    // The consent screen behind this overlay may be blank - that is what a
    // failed notice load leaves behind, and every button on it is inert.
    // Restore it from state if we have it, re-fetch if we do not, so "Try
    // again" always returns to a working page rather than a dead one.
    if (state.notice) {
      renderNotice(state.notice);
      return;
    }
    busy(true, "Reconnecting…");
    try {
      await loadNotice(state.lang || navigator.language || "en");
      busy(false);
      show("view-consent");
    } catch (e) {
      fail(e);
    }
  });

  document.querySelector(".tabs").addEventListener("click", function (e) {
    var tab = e.target.closest(".tab");
    if (!tab) return;
    Array.prototype.forEach.call(document.querySelectorAll(".tab"), function (t) {
      t.classList.toggle("active", t === tab);
    });
    ["panel-cards", "panel-source", "panel-ask"].forEach(function (id) {
      $(id).hidden = id !== tab.getAttribute("data-panel");
    });
  });

  /* ------------------------------------------------------ consent wire */

  function refreshConsentButton() {
    $("consent-go").disabled =
      !($("agree-age").checked && $("agree-consent").checked);
  }
  $("agree-age").addEventListener("change", refreshConsentButton);
  $("agree-consent").addEventListener("change", refreshConsentButton);

  $("lang").addEventListener("change", function (e) {
    loadNotice(e.target.value).catch(function (err) { fail(err); });
  });

  $("consent-go").addEventListener("click", async function () {
    busy(true, "Starting…");
    try {
      await grantConsent();
      busy(false);
      show("view-capture");
    } catch (e) { fail(e); }
  });

  $("error-reload").addEventListener("click", function () { location.reload(); });
  $("review-notice").addEventListener("click", function () { show("view-consent"); });
  $("withdraw").addEventListener("click", withdrawConsent);

  // Releasing the device on unload matters as much as on navigation.
  window.addEventListener("pagehide", stopCamera);

  console.info("[PlainMed] client build " + CLIENT_BUILD);
  // Tell the server the page loaded, so its log shows whether the browser
  // is even running current code.
  report("startup", { message: "client loaded ok", stack: "" });

  // Show the notice first. Nothing else runs until consent is given.
  loadNotice(navigator.language || "en").catch(fail);

  fetch(API + "/health").then(function (r) { return r.json(); }).then(function (h) {
    if (h && h.ocr_backend) {
      $("foot-status").textContent =
        "Processed, never stored · " + h.ocr_backend + " + " + h.llm_backend;
    }
  }).catch(function () { /* offline: the page still works once loaded */ });
})();
