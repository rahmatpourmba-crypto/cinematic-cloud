/* قصه‌نگار — Prompt Studio client (GitHub Pages + Actions mode) */
(function () {
  "use strict";

  var OWNER = "rahmatpourmba-crypto";
  var REPO = "cinematic-cloud";
  var $ = function (id) { return document.getElementById(id); };
  var pollTimer = null;

  var faNum = function (n) {
    return String(n).replace(/\d/g, function (d) {
      return "۰۱۲۳۴۵۶۷۸۹"[d];
    });
  };

  var faDigits = function (n) { return faNum(n); };

  /* style picker */
  var styleEl = $("styles");
  styleEl.addEventListener("click", function (e) {
    var btn = e.target.closest(".style-btn");
    if (!btn) return;
    styleEl.querySelectorAll(".style-btn").forEach(function (b) { b.classList.remove("active"); });
    btn.classList.add("active");
  });

  $("engineTxt").textContent = "موتور رندر: GitHub Actions";

  function uuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID().replace(/-/g, "").slice(0, 12);
    return "s" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  }

  function jobUrl(id) { return "jobs/" + id + ".json"; }
  function videoUrl(id) { return "videos/" + id + "/video.mp4"; }

  function renderJob(job, id) {
    $("active").classList.remove("hidden");
    if (!job) {
      $("pstage").textContent = "در حال ساخت… (صفحه GitHub را باز نگه دار)";
      $("ppercent").textContent = "⏳";
      return false;
    }
    if (job.status === "done") {
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
      $("pstage").textContent = "آماده ✦";
      $("ppercent").textContent = "۱۰۰٪";
      var box = $("videoBox");
      box.classList.remove("hidden");
      $("player").src = job.video || videoUrl(id);
      $("player").poster = job.poster || "";
      $("dl").href = job.video || videoUrl(id);
      $("pstage").textContent = "آماده ✦";
      $("ppercent").textContent = "۱۰۰٪";
      return true;
    }
    if (job.status === "failed") {
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
      $("pstage").textContent = "خطا: " + (job.error || job.message || "نامشخص");
      $("ppercent").textContent = "—";
      return true;
    }
    $("pstage").textContent = job.message || "در حال ساخت… (معمولاً ۵ تا ۲۰ دقیقه)";
    $("ppercent").textContent = "⏳";
    return false;
  }

  function poll(id) {
    if (pollTimer) clearInterval(pollTimer);
    var watch = function () {
      fetch(jobUrl(id), { cache: "no-store" })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (renderJob(j, id)) { clearInterval(pollTimer); pollTimer = null; }
        })
        .catch(function () { renderJob(null, id); });
    };
    watch();
    pollTimer = setInterval(watch, 4000);
  }

  function listVideos() {
    fetch("videos/index.json", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (arr) {
        var ul = $("jobs");
        ul.innerHTML = "";
        (Array.isArray(arr) ? arr : []).slice(0, 12).forEach(function (v) {
          var li = document.createElement("li");
          var tag = document.createElement("span");
          tag.className = "tag " + (v.status === "done" ? "done" : "queued");
          tag.textContent = v.status === "done" ? "✔ آماده" : "⏳";
          var text = document.createElement("span");
          text.textContent = (v.prompt || "—").slice(0, 46) + "…";
          var ts = document.createElement("span");
          ts.className = "date";
          ts.textContent = v.created || "";
          var link = document.createElement("a");
          if (v.status === "done") {
            link.href = "videos/" + v.id + "/video.mp4";
            link.target = "_blank";
            link.textContent = "مشاهده";
          }
          li.appendChild(tag); li.appendChild(text); li.appendChild(link); li.appendChild(ts);
          ul.appendChild(li);
        });
      })
      .catch(function () {});
  }

  $("go").addEventListener("click", function () {
    var prompt = $("prompt").value.trim();
    if (prompt.length < 8) {
      $("prompt").focus();
      $("prompt").style.borderColor = "#f87171";
      return;
    }
    $("prompt").style.borderColor = "";
    var styleBtn = styleEl.querySelector(".style-btn.active");
    var payload = {
      prompt: prompt,
      style: styleBtn ? styleBtn.dataset.style : "cinematic",
      quality: $("quality").value
    };
    var id = uuid();
    payload.id = id;

    var title = prompt.split("\n")[0].slice(0, 70);
    var body = "<!-- studio-job -->\n" + JSON.stringify(payload);
    window.open(
      "https://github.com/" + OWNER + "/" + REPO + "/issues/new?title=" +
        encodeURIComponent(title) + "&body=" + encodeURIComponent(body),
      "_blank"
    );

    $("go").disabled = true;
    $("videoBox").classList.add("hidden");
    $("active").classList.remove("hidden");
    poll(id);
    setTimeout(function () { $("go").disabled = false; }, 3000);
  });

  $("again").addEventListener("click", function () {
    $("videoBox").classList.add("hidden");
    $("active").classList.add("hidden");
    $("prompt").focus();
  });

  /* reveal on scroll */
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  listVideos();
})();