const API = "/api";

/* 数字人文配色 */
const DH_COLORS = {
  ink: "#2a2218",
  inkFaint: "#7a6e5c",
  cinnabar: "#a83f39",
  cinnabarLight: "rgba(168, 63, 57, 0.75)",
  indigo: "#3d5a80",
  indigoLight: "rgba(61, 90, 128, 0.7)",
  gold: "#8b6914",
  tea: "#5c7a5a",
  clay: "#9a7b5a",
  mist: "#6a8cad",
  parchment: "#c4b59a",
  chartPalette: [
    "#a83f39", "#3d5a80", "#8b6914", "#5c7a5a",
    "#9a7b5a", "#6a8cad", "#7a5c8a", "#c45c48",
    "#4a6fa5", "#b8860b",
  ],
};

const chartDefaults = {
  color: DH_COLORS.inkFaint,
  font: { family: '"Noto Serif SC", "Songti SC", serif' },
};

Chart.defaults.color = chartDefaults.color;
Chart.defaults.font.family = chartDefaults.font.family;

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

function setDbStatus(text, connected) {
  const el = document.getElementById("db-status");
  el.textContent = text;
  el.classList.toggle("connected", connected);
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
        {
          label: "景点总数",
          data: totals,
          backgroundColor: DH_COLORS.indigoLight,
          borderColor: DH_COLORS.indigo,
          borderWidth: 1,
        },
        {
          label: "徐霞客足迹",
          data: xuxiake,
          backgroundColor: DH_COLORS.cinnabarLight,
          borderColor: DH_COLORS.cinnabar,
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: DH_COLORS.ink, padding: 16, usePointStyle: true },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: DH_COLORS.inkFaint, maxRotation: 45 },
        },
        y: {
          grid: { color: "rgba(196, 181, 154, 0.5)" },
          ticks: { color: DH_COLORS.inkFaint },
          beginAtZero: true,
        },
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
          backgroundColor: DH_COLORS.chartPalette,
          borderColor: "#faf6ee",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: {
            color: DH_COLORS.ink,
            boxWidth: 10,
            padding: 10,
            font: { size: 11 },
          },
        },
      },
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
      <td>${r.IsXuXiake ? '<span class="tag">霞客足迹</span>' : '<span class="tag normal">—</span>'}</td>
      <td><a class="link lit-link" data-id="${r.LocationID}">阅典籍</a></td>
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
    opt.textContent = `${d.Province}（${d.total}）`;
    sel.appendChild(opt);
  });
}

async function openTravelog(id) {
  const data = await fetchJson(`/travelogs/${id}`);
  const modal = document.getElementById("modal");
  document.getElementById("modal-title").textContent = data.Title;
  document.getElementById("modal-meta").textContent =
    `${data.Username} · ${data.PublishTime} · ${formatNum(data.Likes)} 赞 · ${data.checkins.length} 处打卡`;
  document.getElementById("modal-body").textContent = data.Content;
  const list = document.getElementById("modal-checkins");
  list.innerHTML = data.checkins
    .map(
      (c) =>
        `<li>${escapeHtml(c.LocName)}（${escapeHtml(c.Province)}）${c.IsXuXiake ? " · 霞客足迹" : ""} — ${c.CheckInTime}</li>`
    )
    .join("");
  modal.classList.add("open");
  document.body.style.overflow = "hidden";
}

async function openLiterature(locationId) {
  const data = await fetchJson(`/locations/${locationId}/literature`);
  const modal = document.getElementById("modal");
  document.getElementById("modal-title").textContent = `${data.location.LocName} · 典籍`;
  document.getElementById("modal-meta").textContent = data.location.Province;
  document.getElementById("modal-body").innerHTML =
    data.literature.length === 0
      ? '<p class="lit-translate">此地暂无著录文献。</p>'
      : data.literature
          .map(
            (l) => `
          <div class="lit-block">
            <p class="lit-date">${escapeHtml(l.WriteDate || "年代不详")}</p>
            <p class="lit-original">${escapeHtml(l.OriginalText)}</p>
            ${l.TranslateInfo ? `<p class="lit-translate">${escapeHtml(l.TranslateInfo)}</p>` : ""}
          </div>`
          )
          .join("");
  document.getElementById("modal-checkins").innerHTML = "";
  modal.classList.add("open");
  document.body.style.overflow = "hidden";
}

function escapeHtml(s) {
  if (!s) return "";
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function closeModal() {
  document.getElementById("modal").classList.remove("open");
  document.body.style.overflow = "";
}

document.getElementById("modal-close").addEventListener("click", closeModal);
document.querySelector(".modal-backdrop")?.addEventListener("click", closeModal);

document.getElementById("btn-filter").addEventListener("click", () => loadLocations());

async function init() {
  try {
    const health = await fetchJson("/health");
    setDbStatus(`已接通 · ${health.database}`, true);
    await loadStats();
    await fillProvinceFilter();
    await loadProvinceChart();
    await loadTopCheckinsChart();
    await loadLatestTravelogs();
    await loadLocations();
  } catch (e) {
    setDbStatus("未连接", false);
    showError("无法加载数据：" + e.message + "。请确认后端服务与 MySQL 已启动。");
    console.error(e);
  }
}

init();
