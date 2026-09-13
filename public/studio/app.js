/* قصه‌نگار — Prompt Studio client */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var pollTimer = null;

  var faNum = function (n) {
    return String(n).replace(/\d/g, function (d) {
      return "۰۱۲۳۴۵۶۷۸۹"[d];
    });
  };

  var tagOf = function (st) {
    if (st === "done") return "✔ آماده";
    if (st === "failed") return "✖ ناموفق";
    if (st === "running") return "⏳ در حال ساخت";
    return "⏳ در صف";
  };

  /* style picker */
  var styleEl = $("styles");
  styleEl.addEventListener("click", function (e) {
    var btn = e.target.closest(".style-btn");
    if (!btn) return;
    styleEl.querySelectorAll(".style-btn").forEach(function (b) { b.classList.remove("active"); });
    btn.classList.add("active");
  });

  /* engine status */
  fetch("/health")
    .then(function (r) { return r.json(); })
    .then(function (h) {
      var on = h.google_available;
      $("engineTxt").textContent = on ? "موتور گوگل فعال" : "حالت رایگان";
      $("engine").querySelector(".dot").classList.toggle("off", !on);
    })
    .catch(function () {
      $("engineTxt").textContent = "آفلاین";
    });

  function poll(id) {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(function () {
      fetch("/api/jobs/" + id)
        .then(function (r) { return r.json(); })
        .then(renderJob)
        .catch(function () {});
    }, 2000);
  }

  function renderJob(job) {
    if (!job) return;
    $("active").classList.remove("hidden");
    $("pstage").textContent = job.stage || job.status;
    $("ppercent").textContent = faNum(job.progress) + "٪";
    $("pfill").style.width = job.progress + "%";

    if (job.status === "done") {
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
      var box = $("videoBox");
      box.classList.remove("hidden");
      $("player").src = job.video;
      $("dl").href = job.video;
      $("pstage").textContent = "آماده ✦";
      $("ppercent").textContent = "۱۰۰٪";
    } else if (job.status === "failed") {
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
      $("pstage").textContent = "خطا: " + job.message;
      $("ppercent").textContent = "—";
    }
    refreshList();
  }

  function refreshList() {
    fetch("/api/jobs")
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var ul = $("jobs");
        ul.innerHTML = "";
        (j.jobs || []).forEach(function (jb) {
          var li = document.createElement("li");
          var tag = document.createElement("span");
          tag.className = "tag " + jb.status;
          tag.textContent = tagOf(jb.status);
          var text = document.createElement("span");
          text.textContent = jb.prompt ? jb.prompt.slice(0, 46) + "…" : "—";
          var ts = document.createElement("span");
          ts.className = "date";
          ts.textContent = jb.created_at;
          var link = document.createElement("a");
          if (jb.status === "done") {
            link.href = jb.video;
            link.target = "_blank";
            link.textContent = "مشاهده";
          } else {
            link.textContent = "";
          }
          li.appendChild(tag);
          li.appendChild(text);
          li.appendChild(link);
          li.appendChild(ts);
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
    var styleBtn = styleEl.querySelector(".style-btn.active");
    var body = {
      prompt: prompt,
      style: styleBtn ? styleBtn.dataset.style : "cinematic",
      quality: $("quality").value
    };
    $("go").disabled = true;
    $("videoBox").classList.add("hidden");

    fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        $("go").disabled = false;
        if (res.job_id) {
          fetch("/api/jobs/" + res.job_id).then(function (r) { return r.json(); }).then(renderJob);
          poll(res.job_id);
        }
      })
      .catch(function () { $("go").disabled = false; });
  });

  $("again").addEventListener("click", function () {
    $("videoBox").classList.add("hidden");
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

  refreshList();
})();