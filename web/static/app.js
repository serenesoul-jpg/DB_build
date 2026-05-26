const API = "/api";

async function fetchJson(path) {
  const res = await fetch(API + path);
  if (!res.ok) throw new Error(`请求失败: ${path} (${res.status})`);
  return res.json();
}

function showError(msg) {
  const el = document.getElementById("error");
  el.textContent = msg;
  el.classList.add("show");
}

function formatNum(n) {
  return Number(n).toLocaleString("zh-CN");
}

async function loadStats() {
  const s = await fetchJson("/stats");
  document.getElementById("stat-users").textContent = formatNum(s.users);
  document.getElementById("stat-locations").textContent = formatNum(s.locations);
  document.getElementById("stat-xuxiake").textContent = formatNum(s.xuxiake_locations);
  document.getElementById("stat-travelogs").textContent = formatNum(s.travelogs);
  document.getElementById("stat-checkins").textContent = formatNum(s.checkins);
  document.getElementById("stat-literature").textContent = formatNum(s.literature);
  document.getElementById("stat-likes").textContent = formatNum(s.total_likes);
}

async function loadProvinceChart() {
  const data = await fetchJson("/locations/provinces");
  const labels = data.slice(0, 12).map((d) => d.Province.replace(/省|市|自治区/g, ""));
  const totals = data.slice(0, 12).map((d) => d.total);
  const xuxiake = data.slice(0, 12).map((d) => d.xuxiake_count);

  new Chart(document.getElementById("chart-provinces"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "景点总数", data: totals, backgroundColor: "rgba(74, 158, 255, 0.7)" },
        { label: "徐霞客足迹", data: xuxiake, backgroundColor: "rgba(201, 162, 39, 0.85)" },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#8b9cb3" } } },
      scales: {
        x: { ticks: { color: "#8b9cb3", maxRotation: 45 } },
        y: { ticks: { color: "#8b9cb3" }, beginAtZero: true },
      },
    },
  });
}

async function loadTopCheckinsChart() {
  const data = await fetchJson("/locations/top-checkins?limit=10");
  new Chart(document.getElementById("chart-checkins"), {
    type: "doughnut",
    data: {
      labels: data.map((d) => d.LocName),
      datasets: [
        {
          data: data.map((d) => d.checkin_count),
          backgroundColor: [
            "#c9a227", "#4a9eff", "#3dd68c", "#e8784a", "#9b7ede",
            "#5ec8e8", "#e85d8a", "#7eb86a", "#d4a574", "#6a8cad",
          ],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "right", labels: { color: "#8b9cb3", boxWidth: 12 } } },
    },
  });
}

async function loadLatestTravelogs() {
  const rows = await fetchJson("/travelogs/latest?limit=15");
  const tbody = document.querySelector("#travelog-table tbody");
  tbody.innerHTML = rows
    .map(
      (r) => `
    <tr>
      <td><a class="link" data-id="${r.TravelogID}">${escapeHtml(r.Title)}</a></td>
      <td>${escapeHtml(r.Username)}</td>
      <td>${r.spot_count}</td>
      <td>${formatNum(r.Likes)}</td>
      <td>${r.PublishTime || ""}</td>
    </tr>`
    )
    .join("");

  tbody.querySelectorAll("a.link").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      openTravelog(Number(a.dataset.id));
    });
  });
}

async function loadLocations() {
  const province = document.getElementById("filter-province").value;
  const isXx = document.getElementById("filter-xuxiake").value;
  let url = "/locations?limit=30";
  if (province) url += `&province=${encodeURIComponent(province)}`;
  if (isXx !== "") url += `&is_xuxiake=${isXx}`;

  const rows = await fetchJson(url);
  const tbody = document.querySelector("#location-table tbody");
  tbody.innerHTML = rows
    .map(
      (r) => `
    <tr>
      <td>${escapeHtml(r.LocName)}</td>
      <td>${escapeHtml(r.Province)}</td>
      <td>${r.IsXuXiake ? '<span class="tag">徐霞客足迹</span>' : '<span class="tag normal">—</span>'}</td>
      <td><a class="link lit-link" data-id="${r.LocationID}">文献</a></td>
    </tr>`
    )
    .join("");

  tbody.querySelectorAll(".lit-link").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      openLiterature(Number(a.dataset.id));
    });
  });
}

async function fillProvinceFilter() {
  const data = await fetchJson("/locations/provinces");
  const sel = document.getElementById("filter-province");
  data.forEach((d) => {
    const opt = document.createElement("option");
    opt.value = d.Province;
    opt.textContent = `${d.Province} (${d.total})`;
    sel.appendChild(opt);
  });
}

async function openTravelog(id) {
  const data = await fetchJson(`/travelogs/${id}`);
  const modal = document.getElementById("modal");
  document.getElementById("modal-title").textContent = data.Title;
  document.getElementById("modal-meta").textContent =
    `作者 ${data.Username} · ${data.PublishTime} · ${formatNum(data.Likes)} 赞 · ${data.checkins.length} 处打卡`;
  document.getElementById("modal-body").textContent = data.Content;
  const list = document.getElementById("modal-checkins");
  list.innerHTML = data.checkins
    .map(
      (c) =>
        `<li>${escapeHtml(c.LocName)}（${escapeHtml(c.Province)}）${c.IsXuXiake ? " ★" : ""} — ${c.CheckInTime}</li>`
    )
    .join("");
  modal.classList.add("open");
}

async function openLiterature(locationId) {
  const data = await fetchJson(`/locations/${locationId}/literature`);
  const modal = document.getElementById("modal");
  document.getElementById("modal-title").textContent = data.location.LocName + " · 关联文献";
  document.getElementById("modal-meta").textContent = data.location.Province;
  document.getElementById("modal-body").innerHTML =
    data.literature.length === 0
      ? "<p>暂无文献记录</p>"
      : data.literature
          .map(
            (l) =>
              `<p><strong>${escapeHtml(l.WriteDate || "年代不详")}</strong></p>
           <p>${escapeHtml(l.OriginalText)}</p>
           <p style="color:#8b9cb3;margin-top:0.5rem">${escapeHtml(l.TranslateInfo || "")}</p><hr style="border-color:#2d3d52;margin:1rem 0">`
          )
          .join("");
  document.getElementById("modal-checkins").innerHTML = "";
  modal.classList.add("open");
}

function escapeHtml(s) {
  if (!s) return "";
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

document.getElementById("modal-close").addEventListener("click", () => {
  document.getElementById("modal").classList.remove("open");
});

document.getElementById("btn-filter").addEventListener("click", () => loadLocations());

async function init() {
  try {
    const health = await fetchJson("/health");
    document.getElementById("db-status").textContent = `已连接 · ${health.database}`;
    await loadStats();
    await fillProvinceFilter();
    await loadProvinceChart();
    await loadTopCheckinsChart();
    await loadLatestTravelogs();
    await loadLocations();
  } catch (e) {
    showError("无法加载数据：" + e.message + "。请确认后端服务与 MySQL 已启动。");
    console.error(e);
  }
}

init();
