/* ─────────────────────────────────────────────────────────────────────
   Civic — consumer app
   Minimal interactivity: drag-drop photos, voice recording, results render.
   ───────────────────────────────────────────────────────────────────── */

(function () {
  "use strict";

  /* ─────────────────────────────────────────────────────────────────
     Utilities
     ───────────────────────────────────────────────────────────────── */

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function esc(s) {
    if (s == null) return "";
    const d = document.createElement("div");
    d.textContent = String(s);
    return d.innerHTML;
  }

  function severityBucket(score) {
    if (score == null) return { cls: "", label: "Unknown" };
    if (score >= 8) return { cls: "high", label: "High" };
    if (score >= 5) return { cls: "mid",  label: "Medium" };
    return                 { cls: "low",  label: "Low" };
  }

  function statusBadge(status) {
    const map = {
      submitted:    "status-submitted",
      routed:       "status-routed",
      "in progress":"status-in-progress",
      acknowledged: "status-in-progress",
      escalated:    "status-escalated",
      fixed:        "status-resolved",
      resolved:     "status-resolved",
    };
    const norm = (status || "submitted").toLowerCase();
    return map[norm] || "status-default";
  }

  function timeAgo(iso) {
    if (!iso) return "Just now";
    const then = new Date(iso);
    if (isNaN(then.getTime())) return "Recently";
    const sec = Math.max(0, (Date.now() - then.getTime()) / 1000);
    if (sec < 60) return "Just now";
    if (sec < 3600) return Math.floor(sec / 60) + "m ago";
    if (sec < 86400) return Math.floor(sec / 3600) + "h ago";
    if (sec < 86400 * 7) return Math.floor(sec / 86400) + "d ago";
    return then.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  /* Category icon picker — returns one of the inline SVGs from the page */
  function categoryGlyph(category) {
    const c = (category || "").toLowerCase();
    if (c.indexOf("road") >= 0 || c.indexOf("pothole") >= 0) return "glyph-road";
    if (c.indexOf("waste") >= 0 || c.indexOf("tipping") >= 0) return "glyph-bin";
    if (c.indexOf("light") >= 0 || c.indexOf("traffic") >= 0) return "glyph-lamp";
    if (c.indexOf("tree") >= 0 || c.indexOf("vegetation") >= 0 || c.indexOf("parks") >= 0) return "glyph-tree";
    if (c.indexOf("noise") >= 0) return "glyph-noise";
    if (c.indexOf("graffiti") >= 0 || c.indexOf("cleanliness") >= 0) return "glyph-clean";
    return "glyph-generic";
  }

  function glyphSVG(name) {
    const glyphs = {
      "glyph-road":
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21l3-18M19 21l-3-18M12 5v2M12 11v2M12 17v2"/></svg>',
      "glyph-bin":
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M9 7V4h6v3M6 7l1 13a1 1 0 001 1h8a1 1 0 001-1l1-13M10 11v6M14 11v6"/></svg>',
      "glyph-lamp":
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v3M7 9h10l-2 6H9zM12 15v6M9 21h6"/></svg>',
      "glyph-tree":
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3c2.5 1.5 4 3.5 4 6s-1 4-3 5h-2c-2-1-3-2.5-3-5s1.5-4.5 4-6zM12 14v7M9 21h6"/></svg>',
      "glyph-noise":
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5L6 9H3v6h3l5 4zM15.5 8.5a5 5 0 010 7M18.5 5.5a9 9 0 010 13"/></svg>',
      "glyph-clean":
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21l4-4M6 19l3-9 10-4-4 10-9 3M16 8l-3-3"/></svg>',
      "glyph-generic":
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16v.5"/></svg>',
    };
    return glyphs[name] || glyphs["glyph-generic"];
  }

  /* ─────────────────────────────────────────────────────────────────
     Results renderer — shared between camera + mic flows
     ───────────────────────────────────────────────────────────────── */

  function renderResult(data, mountId) {
    const root = $("#" + mountId);
    if (!root) return;

    const sev = data.severity_score || 0;
    const bucket = severityBucket(sev);
    const status = data.status || "submitted";
    const badge = statusBadge(status);

    root.innerHTML = "" +
      '<div class="result-banner">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>' +
        '<span>Report received. Forwarded to the right team.</span>' +
      '</div>' +

      '<div class="card">' +
        '<div class="card-row">' +
          '<div class="card-cell"><span class="k">Category</span><span class="v">' + esc(data.category || "Uncategorised") + '</span></div>' +
          (data.subcategory ? '<div class="card-cell"><span class="k">Type</span><span class="v">' + esc(data.subcategory) + '</span></div>' : '') +
          '<div class="card-cell">' +
            '<span class="k">Severity</span>' +
            '<span class="v severity-pill"><span class="severity-dot ' + bucket.cls + '"></span>' + bucket.label + ' &middot; ' + sev + '/10</span>' +
          '</div>' +
          '<div class="card-cell">' +
            '<span class="k">Status</span>' +
            '<span class="v"><span class="status-badge ' + badge + '"><span class="dot"></span>' + esc(status) + '</span></span>' +
          '</div>' +
        '</div>' +
      '</div>' +

      (data.council || data.department || data.borough || data.address
        ? '<div class="card">' +
            '<div class="card-row">' +
              (data.council ? '<div class="card-cell"><span class="k">Council</span><span class="v">' + esc(data.council) + '</span></div>' : '') +
              (data.department ? '<div class="card-cell"><span class="k">Department</span><span class="v">' + esc(data.department) + '</span></div>' : '') +
              (data.borough ? '<div class="card-cell"><span class="k">Borough</span><span class="v">' + esc(data.borough) + '</span></div>' : '') +
              (data.address ? '<div class="card-cell"><span class="k">Location</span><span class="v">' + esc(data.address) + '</span></div>' : '') +
            '</div>' +
          '</div>'
        : '') +

      (data.submission_text
        ? '<div class="card">' +
            '<div class="submission-title">Formal submission</div>' +
            '<div class="submission-block">' + esc(data.submission_text) + '</div>' +
          '</div>'
        : '') +

      '<div class="result-actions">' +
        '<a class="link" href="/processed">View on dashboard &rarr;</a>' +
        '<a class="primary-btn" href="/app/home">See your reports</a>' +
      '</div>';

    root.classList.add("is-visible");
  }

  function showError(noticeId, message) {
    const el = $("#" + noticeId);
    if (!el) return;
    el.textContent = message;
    el.classList.add("is-visible");
  }

  function hideError(noticeId) {
    const el = $("#" + noticeId);
    if (el) el.classList.remove("is-visible");
  }

  function showLoading(loadingId) {
    const el = $("#" + loadingId);
    if (el) el.classList.add("is-visible");
  }

  function hideLoading(loadingId) {
    const el = $("#" + loadingId);
    if (el) el.classList.remove("is-visible");
  }

  /* ─────────────────────────────────────────────────────────────────
     Camera flow
     ───────────────────────────────────────────────────────────────── */

  function initCamera() {
    const form = $("#cameraForm");
    if (!form) return;

    const dropZone = $("#dropZone");
    const fileInput = $("#photoInput");
    const previewWrap = $("#preview");
    const previewImg = $("#previewImg");
    const clearBtn = $("#clearPhoto");
    const description = $("#description");
    const submitBtn = $("#submitBtn");
    const intakeView = $("#intakeView");
    const loadingView = $("#loadingView");
    const resultView = $("#resultView");

    let currentFile = null;

    function setFile(file) {
      if (!file || !file.type || file.type.indexOf("image/") !== 0) {
        showError("notice", "Please choose an image file.");
        return;
      }
      hideError("notice");
      currentFile = file;
      const reader = new FileReader();
      reader.onload = function (e) {
        previewImg.src = e.target.result;
        previewWrap.hidden = false;
        dropZone.hidden = true;
        submitBtn.disabled = false;
      };
      reader.readAsDataURL(file);
    }

    function clearFile() {
      currentFile = null;
      fileInput.value = "";
      previewImg.src = "";
      previewWrap.hidden = true;
      dropZone.hidden = false;
      submitBtn.disabled = true;
    }

    // File input change
    fileInput.addEventListener("change", function (e) {
      const file = e.target.files && e.target.files[0];
      if (file) setFile(file);
    });

    // Drag and drop
    ["dragenter", "dragover"].forEach(function (evt) {
      dropZone.addEventListener(evt, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add("is-drag");
      });
    });

    ["dragleave", "drop"].forEach(function (evt) {
      dropZone.addEventListener(evt, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("is-drag");
      });
    });

    dropZone.addEventListener("drop", function (e) {
      const file = e.dataTransfer.files && e.dataTransfer.files[0];
      if (file) setFile(file);
    });

    if (clearBtn) clearBtn.addEventListener("click", clearFile);

    // Submit
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      if (!currentFile) return;

      hideError("notice");
      intakeView.hidden = true;
      showLoading("loadingView");

      const fd = new FormData();
      fd.append("photo", currentFile);
      if (description.value.trim()) fd.append("text", description.value.trim());

      try {
        const resp = await fetch("/api/intake-photo", {
          method: "POST",
          body: fd,
        });
        if (!resp.ok) {
          const data = await resp.json().catch(function () { return {}; });
          throw new Error(data.error || "Unable to submit (" + resp.status + ")");
        }
        const data = await resp.json();
        hideLoading("loadingView");
        renderResult(data, "resultView");
      } catch (err) {
        hideLoading("loadingView");
        intakeView.hidden = false;
        showError("notice", err.message || "Something went wrong.");
      }
    });
  }

  /* ─────────────────────────────────────────────────────────────────
     Mic flow — Web Speech API for browser-native transcription
     ───────────────────────────────────────────────────────────────── */

  function initMic() {
    const micBtn = $("#micBtn");
    if (!micBtn) return;

    const status = $("#micStatus");
    const meta = $("#micMeta");
    const transcriptEl = $("#transcript");
    const submitBtn = $("#submitBtn");
    const intakeView = $("#intakeView");
    const loadingView = $("#loadingView");
    const resultView = $("#resultView");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let recording = false;
    let startedAt = 0;
    let timerInterval = null;
    let finalTranscript = "";

    if (!SpeechRecognition) {
      // Fallback — let user type directly.
      status.textContent = "Voice not supported here";
      meta.textContent = "Type your report below instead.";
      micBtn.disabled = true;
      transcriptEl.setAttribute("contenteditable", "true");
      transcriptEl.classList.remove("empty");
      transcriptEl.textContent = "";
      transcriptEl.addEventListener("input", function () {
        submitBtn.disabled = transcriptEl.textContent.trim().length === 0;
      });
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-GB";

    recognition.addEventListener("result", function (e) {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        if (res.isFinal) {
          finalTranscript += res[0].transcript + " ";
        } else {
          interim += res[0].transcript;
        }
      }
      const combined = (finalTranscript + interim).trim();
      if (combined.length) {
        transcriptEl.classList.remove("empty");
        transcriptEl.textContent = combined;
        submitBtn.disabled = false;
      }
    });

    recognition.addEventListener("end", function () {
      // If user just hit stop, this is expected.
      if (recording) stopRecording();
    });

    recognition.addEventListener("error", function (e) {
      stopRecording();
      const err = e.error || "unknown";
      if (err === "no-speech") {
        meta.textContent = "Didn't catch that. Try again.";
      } else if (err === "not-allowed" || err === "service-not-allowed") {
        showError("notice", "Microphone access denied. Enable it in your browser settings.");
      } else {
        showError("notice", "Voice error: " + err);
      }
    });

    function formatDuration(secs) {
      const m = Math.floor(secs / 60);
      const s = Math.floor(secs % 60);
      return m + ":" + (s < 10 ? "0" + s : s);
    }

    function startRecording() {
      finalTranscript = "";
      transcriptEl.textContent = "";
      transcriptEl.classList.add("empty");
      transcriptEl.removeAttribute("contenteditable");
      submitBtn.disabled = true;
      hideError("notice");

      try {
        recognition.start();
      } catch (e) {
        // Already started; ignore.
      }
      recording = true;
      startedAt = Date.now();
      micBtn.classList.add("is-recording");
      status.textContent = "Listening";
      meta.textContent = "0:00 — tap to stop";

      timerInterval = setInterval(function () {
        const elapsed = (Date.now() - startedAt) / 1000;
        meta.textContent = formatDuration(elapsed) + " — tap to stop";
      }, 200);
    }

    function stopRecording() {
      recording = false;
      micBtn.classList.remove("is-recording");
      try {
        recognition.stop();
      } catch (e) { /* ignore */ }
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }

      const text = transcriptEl.textContent.trim();
      if (text.length) {
        status.textContent = "Got it";
        meta.textContent = "Edit if needed, then submit";
        transcriptEl.setAttribute("contenteditable", "true");
      } else {
        status.textContent = "Tap to record";
        meta.textContent = "Speak naturally — we'll transcribe.";
      }
    }

    micBtn.addEventListener("click", function () {
      if (recording) stopRecording();
      else startRecording();
    });

    // Allow editing transcript directly
    transcriptEl.addEventListener("input", function () {
      const text = transcriptEl.textContent.trim();
      finalTranscript = text + " ";
      submitBtn.disabled = text.length === 0;
    });

    // Submit
    submitBtn.addEventListener("click", async function () {
      const transcript = transcriptEl.textContent.trim();
      if (!transcript) return;

      if (recording) stopRecording();

      hideError("notice");
      intakeView.hidden = true;
      showLoading("loadingView");

      try {
        const resp = await fetch("/api/intake-voice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcript: transcript }),
        });
        if (!resp.ok) {
          const data = await resp.json().catch(function () { return {}; });
          throw new Error(data.error || "Unable to submit (" + resp.status + ")");
        }
        const data = await resp.json();
        hideLoading("loadingView");
        renderResult(data, "resultView");
      } catch (err) {
        hideLoading("loadingView");
        intakeView.hidden = false;
        showError("notice", err.message || "Something went wrong.");
      }
    });
  }

  /* ─────────────────────────────────────────────────────────────────
     Home — list of reports
     ───────────────────────────────────────────────────────────────── */

  function initHome() {
    const list = $("#reportList");
    const empty = $("#emptyState");
    if (!list) return;

    fetch("/api/processed")
      .then(function (r) { return r.json(); })
      .then(function (items) {
        if (!Array.isArray(items) || items.length === 0) {
          if (empty) empty.hidden = false;
          return;
        }
        // Newest first
        items.sort(function (a, b) {
          const ta = a.reported_at ? new Date(a.reported_at).getTime() : 0;
          const tb = b.reported_at ? new Date(b.reported_at).getTime() : 0;
          return tb - ta;
        });
        renderList(items);
      })
      .catch(function () {
        if (empty) empty.hidden = false;
      });

    function renderList(items) {
      list.innerHTML = items.map(function (issue, idx) {
        const sev = issue.severity_score || 0;
        const bucket = severityBucket(sev);
        const badge = statusBadge(issue.status);
        const glyph = categoryGlyph(issue.category);
        const reported = issue.reported_at || "";

        return '' +
          '<div class="report-card" data-idx="' + idx + '">' +
            '<div class="report-icon">' + glyphSVG(glyph) + '</div>' +
            '<div class="report-body">' +
              '<div class="report-title">' +
                '<span>' + esc(issue.title || "Untitled report") + '</span>' +
                '<span class="status-badge ' + badge + '"><span class="dot"></span>' + esc(issue.status || "submitted") + '</span>' +
              '</div>' +
              '<div class="report-meta">' +
                '<span class="severity-pill"><span class="severity-dot ' + bucket.cls + '"></span>' + bucket.label + '</span>' +
                '<span class="sep"></span>' +
                '<span>' + esc(issue.category || "Uncategorised") + '</span>' +
                (issue.borough ? '<span class="sep"></span><span>' + esc(issue.borough) + '</span>' : '') +
                '<span class="sep"></span>' +
                '<span>' + timeAgo(reported) + '</span>' +
              '</div>' +
              '<div class="report-detail">' +
                '<div class="report-detail-row">' +
                  '<div><span class="k">Severity</span><span class="v">' + sev + '/10</span></div>' +
                  (issue.subcategory ? '<div><span class="k">Type</span><span class="v">' + esc(issue.subcategory) + '</span></div>' : '') +
                  (issue.council ? '<div><span class="k">Council</span><span class="v">' + esc(issue.council) + '</span></div>' : '') +
                  (issue.department ? '<div><span class="k">Department</span><span class="v">' + esc(issue.department) + '</span></div>' : '') +
                  (issue.address ? '<div><span class="k">Location</span><span class="v">' + esc(issue.address) + '</span></div>' : '') +
                '</div>' +
                (issue.description
                  ? '<h4>Your description</h4><div class="body-text">' + esc(issue.description) + '</div>'
                  : '') +
                (issue.submission_text
                  ? '<h4>Formal submission</h4><div class="body-text">' + esc(issue.submission_text) + '</div>'
                  : '') +
              '</div>' +
            '</div>' +
          '</div>';
      }).join("");

      // Tap to expand
      $$(".report-card", list).forEach(function (card) {
        card.addEventListener("click", function () {
          card.classList.toggle("is-open");
        });
      });
    }
  }

  /* ─────────────────────────────────────────────────────────────────
     Boot
     ───────────────────────────────────────────────────────────────── */

  document.addEventListener("DOMContentLoaded", function () {
    initCamera();
    initMic();
    initHome();
  });
})();
