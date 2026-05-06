const els = {
  priceCanvas: document.getElementById("priceCanvas"),
  volumeCanvas: document.getElementById("volumeCanvas"),
  chartTooltip: document.getElementById("chartTooltip"),
  periodSelect: document.getElementById("periodSelect"),
  maSelect: document.getElementById("maSelect"),
  csvInput: document.getElementById("csvInput"),
  resetBtn: document.getElementById("resetBtn"),
  modeButtons: Array.from(document.querySelectorAll(".market-switch button")),
  lastPrice: document.getElementById("lastPrice"),
  lastChange: document.getElementById("lastChange"),
  signalText: document.getElementById("signalText"),
  signalDetail: document.getElementById("signalDetail"),
  upDays: document.getElementById("upDays"),
  winRate: document.getElementById("winRate"),
  volatility: document.getElementById("volatility"),
  chartTitle: document.getElementById("chartTitle"),
  chartSubhead: document.getElementById("chartSubhead"),
  legend: document.getElementById("legend"),
  analysisText: document.getElementById("analysisText"),
  resistance: document.getElementById("resistance"),
  support: document.getElementById("support"),
  observationList: document.getElementById("observationList")
};

const colors = {
  up: "#cf3f35",
  down: "#168f6a",
  grid: "#e3e8df",
  text: "#66716a",
  ma: ["#c18c2d", "#326fb7", "#7657a8"]
};

let state = {
  mode: "weighted",
  data: makeDemoData("weighted"),
  imported: false,
  autoLoaded: false,
  dataMeta: null,
  hoverIndex: null,
  chartGeometry: null
};

function makeDemoData(mode) {
  const rows = [];
  const end = new Date();
  end.setHours(0, 0, 0, 0);
  let close = mode === "weighted" ? 7810 : 7740;
  let drift = mode === "weighted" ? 3.6 : 2.3;

  for (let i = 279; i >= 0; i -= 1) {
    const date = new Date(end);
    date.setDate(end.getDate() - i);
    if (date.getDay() === 0 || date.getDay() === 6) continue;

    const wave = Math.sin(i / 13) * 48 + Math.cos(i / 31) * 82;
    const shock = Math.sin(i / 5) * 27 + (i % 37 === 0 ? 95 : 0) - (i % 53 === 0 ? 110 : 0);
    const open = close + Math.sin(i / 7) * 22;
    close = Math.max(5900, close + drift + wave * 0.03 + shock * 0.18 + (Math.random() - 0.48) * 58);
    const high = Math.max(open, close) + 34 + Math.abs(Math.sin(i / 6) * 42);
    const low = Math.min(open, close) - 32 - Math.abs(Math.cos(i / 8) * 38);
    const volume = Math.round(410000 + Math.abs(close - open) * 1100 + Math.abs(Math.sin(i / 9)) * 230000);

    rows.push({
      date: date.toISOString().slice(0, 10),
      open: round(open),
      high: round(high),
      low: round(low),
      close: round(close),
      volume
    });
  }

  return rows;
}

function round(value) {
  return Math.round(value * 100) / 100;
}

function visibleData() {
  const count = Number(els.periodSelect.value);
  return state.data.slice(-count);
}

function movingAverage(data, period) {
  return data.map((row, index) => {
    if (index < period - 1) return null;
    const window = data.slice(index - period + 1, index + 1);
    return window.reduce((sum, item) => sum + item.close, 0) / period;
  });
}

function analyze(data) {
  const last = data[data.length - 1];
  const prev = data[data.length - 2] || last;
  const ma10 = movingAverage(data, 10).at(-1);
  const ma20 = movingAverage(data, 20).at(-1);
  const ma60 = movingAverage(data, Math.min(60, data.length)).at(-1);
  const changes = data.slice(1).map((row, index) => (row.close - data[index].close) / data[index].close);
  const recent20 = changes.slice(-20);
  const mean = recent20.reduce((sum, item) => sum + item, 0) / Math.max(1, recent20.length);
  const variance = recent20.reduce((sum, item) => sum + (item - mean) ** 2, 0) / Math.max(1, recent20.length);
  const vol = Math.sqrt(variance) * Math.sqrt(252);
  const upCount = changes.filter((item) => item > 0).length;
  const high20 = Math.max(...data.slice(-20).map((row) => row.high));
  const low20 = Math.min(...data.slice(-20).map((row) => row.low));
  const change = last.close - prev.close;
  const changePct = change / prev.close;

  let score = 0;
  if (last.close > ma20) score += 1;
  if (ma10 > ma20) score += 1;
  if (ma20 > ma60) score += 1;
  if (changePct > 0) score += 1;
  if (last.close < ma20) score -= 1;
  if (ma10 < ma20) score -= 1;

  const signal = score >= 3 ? "偏强" : score <= -1 ? "偏弱" : "震荡";
  const distanceToResistance = (high20 - last.close) / last.close;
  const distanceToSupport = (last.close - low20) / last.close;

  return {
    last,
    prev,
    change,
    changePct,
    vol,
    upCount,
    winRate: upCount / Math.max(1, changes.length),
    high20,
    low20,
    ma10,
    ma20,
    ma60,
    signal,
    score,
    observations: [
      `收盘价位于 MA20 ${last.close >= ma20 ? "上方" : "下方"}，短线结构${last.close >= ma20 ? "较稳" : "承压"}。`,
      `MA10 ${ma10 >= ma20 ? "上穿或高于" : "低于"} MA20，动量信号${ma10 >= ma20 ? "改善" : "偏谨慎"}。`,
      `距离 20 日压力约 ${(distanceToResistance * 100).toFixed(2)}%，距离 20 日支撑约 ${(distanceToSupport * 100).toFixed(2)}%。`
    ]
  };
}

function draw() {
  const data = visibleData();
  if (data.length < 5) return;

  const analysis = analyze(data);
  updateSummary(data, analysis);
  drawPriceChart(data);
  drawVolumeChart(data);
}

function drawPriceChart(data) {
  const canvas = els.priceCanvas;
  const ctx = setupCanvas(canvas);
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const pad = { top: 18, right: 58, bottom: 28, left: 12 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const highs = data.map((row) => row.high);
  const lows = data.map((row) => row.low);
  const maPeriods = els.maSelect.value.split(",").map(Number);
  const maValues = maPeriods.flatMap((period) => movingAverage(data, period).filter(Boolean));
  const maxPrice = Math.max(...highs, ...maValues);
  const minPrice = Math.min(...lows, ...maValues);
  const spread = maxPrice - minPrice || 1;
  const y = (price) => pad.top + (maxPrice - price) / spread * innerH;
  const x = (index) => pad.left + index / Math.max(1, data.length - 1) * innerW;
  const candleW = Math.max(3, Math.min(12, innerW / data.length * 0.62));
  state.chartGeometry = { pad, innerW, innerH, width, height, minPrice, maxPrice };

  ctx.clearRect(0, 0, width, height);
  drawGrid(ctx, width, height, pad, minPrice, maxPrice);

  data.forEach((row, index) => {
    const cx = x(index);
    const rising = row.close >= row.open;
    ctx.strokeStyle = rising ? colors.up : colors.down;
    ctx.fillStyle = rising ? colors.up : colors.down;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(cx, y(row.high));
    ctx.lineTo(cx, y(row.low));
    ctx.stroke();

    const top = y(Math.max(row.open, row.close));
    const bottom = y(Math.min(row.open, row.close));
    const bodyH = Math.max(2, bottom - top);
    if (rising) {
      ctx.fillRect(cx - candleW / 2, top, candleW, bodyH);
    } else {
      ctx.strokeRect(cx - candleW / 2, top, candleW, bodyH);
    }
  });

  maPeriods.forEach((period, maIndex) => {
    const values = movingAverage(data, period);
    ctx.strokeStyle = colors.ma[maIndex % colors.ma.length];
    ctx.lineWidth = 2;
    ctx.beginPath();
    values.forEach((value, index) => {
      if (!value) return;
      if (index === period - 1) ctx.moveTo(x(index), y(value));
      else ctx.lineTo(x(index), y(value));
    });
    ctx.stroke();
  });

  drawHover(ctx, data, x, y, pad, height);
  updateLegend(maPeriods);
}

function drawHover(ctx, data, x, y, pad, height) {
  if (state.hoverIndex === null || !data[state.hoverIndex]) return;
  const row = data[state.hoverIndex];
  const cx = x(state.hoverIndex);
  const cy = y(row.close);

  ctx.save();
  ctx.strokeStyle = "rgba(30, 42, 36, 0.35)";
  ctx.setLineDash([4, 4]);
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(cx, pad.top);
  ctx.lineTo(cx, height - pad.bottom);
  ctx.moveTo(pad.left, cy);
  ctx.lineTo(ctx.canvas.clientWidth - pad.right, cy);
  ctx.stroke();
  ctx.restore();
}

function drawGrid(ctx, width, height, pad, minPrice, maxPrice) {
  ctx.strokeStyle = colors.grid;
  ctx.fillStyle = colors.text;
  ctx.lineWidth = 1;
  ctx.font = "12px Arial";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";

  for (let i = 0; i <= 5; i += 1) {
    const y = pad.top + (height - pad.top - pad.bottom) * i / 5;
    const price = maxPrice - (maxPrice - minPrice) * i / 5;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(width - pad.right, y);
    ctx.stroke();
    ctx.fillText(price.toFixed(0), width - 8, y);
  }
}

function drawVolumeChart(data) {
  const canvas = els.volumeCanvas;
  const ctx = setupCanvas(canvas);
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const pad = { top: 10, right: 58, bottom: 22, left: 12 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const maxVolume = Math.max(...data.map((row) => row.volume));
  const barW = Math.max(2, innerW / data.length * 0.62);

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = colors.grid;
  ctx.beginPath();
  ctx.moveTo(pad.left, height - pad.bottom);
  ctx.lineTo(width - pad.right, height - pad.bottom);
  ctx.stroke();

  data.forEach((row, index) => {
    const x = pad.left + index / Math.max(1, data.length - 1) * innerW;
    const h = row.volume / maxVolume * innerH;
    ctx.fillStyle = row.close >= row.open ? "rgba(207, 63, 53, 0.5)" : "rgba(22, 143, 106, 0.5)";
    ctx.fillRect(x - barW / 2, height - pad.bottom - h, barW, h);
  });

  ctx.fillStyle = colors.text;
  ctx.font = "12px Arial";
  ctx.textAlign = "right";
  ctx.fillText(`${Math.round(maxVolume / 10000)} 万手`, width - 8, pad.top + 8);
}

function setupCanvas(canvas) {
  const ratio = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.round(rect.width * ratio);
  canvas.height = Math.round(rect.height * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return ctx;
}

function updateLegend(maPeriods) {
  els.legend.innerHTML = [
    `<span><i style="background:${colors.up}"></i>上涨</span>`,
    `<span><i style="background:${colors.down}"></i>下跌</span>`,
    ...maPeriods.map((period, index) => `<span><i style="background:${colors.ma[index]}"></i>MA${period}</span>`)
  ].join("");
}

function updateSummary(data, analysis) {
  const modeName = state.mode === "weighted" ? "加权" : "连续";
  els.chartTitle.textContent = `P ${modeName}日线`;
  if (state.dataMeta) {
    els.chartSubhead.textContent = `${state.dataMeta.instrument_name || "棕榈油连续"} | 最新 ${state.dataMeta.latest_date} | 来源 ${state.dataMeta.source}`;
  } else {
    els.chartSubhead.textContent = state.imported || state.autoLoaded ? "已载入 P0 连续合约 CSV 数据" : "示例数据：未自动载入 CSV 时显示，日期不会超过今天";
  }
  els.lastPrice.textContent = analysis.last.close.toFixed(0);
  els.lastChange.textContent = `${formatSigned(analysis.change)} (${formatPct(analysis.changePct)})`;
  els.lastChange.className = analysis.change >= 0 ? "up" : "down";
  els.signalText.textContent = analysis.signal;
  els.signalText.className = analysis.signal === "偏强" ? "up" : analysis.signal === "偏弱" ? "down" : "";
  els.signalDetail.textContent = `趋势评分 ${analysis.score} / 4`;
  els.upDays.textContent = `${analysis.upCount} 天`;
  els.winRate.textContent = `样本上涨率 ${formatPct(analysis.winRate)}`;
  els.volatility.textContent = formatPct(analysis.vol);
  els.resistance.textContent = analysis.high20.toFixed(0);
  els.support.textContent = analysis.low20.toFixed(0);
  els.analysisText.textContent = makeAnalysisText(analysis);
  els.observationList.innerHTML = analysis.observations.map((item) => `<li>${item}</li>`).join("");
}

function makeAnalysisText(a) {
  if (a.signal === "偏强") {
    return "价格站上关键均线且短期均线排列改善，短线多头占优。若放量突破压力位，趋势可能继续延伸；若回落跌破 MA20，需要降低追涨预期。";
  }
  if (a.signal === "偏弱") {
    return "价格低于中短期均线，反弹持续性需要成交量确认。若跌破近 20 日支撑，弱势结构可能加深；重新站回 MA20 前宜以震荡偏弱看待。";
  }
  return "当前信号偏震荡，价格与均线没有形成一致方向。更适合观察压力/支撑区间内的放量突破或缩量回踩，而不是提前押单边。";
}

function formatSigned(value) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(0)}`;
}

function formatPct(value) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(2)}%`;
}

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) throw new Error("CSV 至少需要表头和一行数据");
  const headers = lines[0].split(",").map((item) => item.trim().toLowerCase());
  const required = ["date", "open", "high", "low", "close", "volume"];
  const missing = required.filter((key) => !headers.includes(key));
  if (missing.length) throw new Error(`缺少字段：${missing.join(", ")}`);

  return lines.slice(1).map((line) => {
    const cells = line.split(",").map((item) => item.trim());
    const row = Object.fromEntries(headers.map((key, index) => [key, cells[index]]));
    return {
      date: row.date.replaceAll("/", "-"),
      open: Number(row.open),
      high: Number(row.high),
      low: Number(row.low),
      close: Number(row.close),
      volume: Number(row.volume)
    };
  }).filter((row) => row.date && [row.open, row.high, row.low, row.close, row.volume].every(Number.isFinite))
    .sort((a, b) => a.date.localeCompare(b.date));
}

els.modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    els.modeButtons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    state.mode = button.dataset.mode;
    state.data = makeDemoData(state.mode);
    state.imported = false;
    draw();
  });
});

els.periodSelect.addEventListener("change", draw);
els.maSelect.addEventListener("change", draw);
els.resetBtn.addEventListener("click", () => {
  state.data = makeDemoData(state.mode);
  state.imported = false;
  state.autoLoaded = false;
  state.dataMeta = null;
  els.csvInput.value = "";
  draw();
});

els.csvInput.addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    const text = await file.text();
    const rows = parseCsv(text);
    if (rows.length < 20) throw new Error("有效数据少于 20 行");
    state.data = rows;
    state.imported = true;
    state.autoLoaded = false;
    state.dataMeta = null;
    draw();
  } catch (error) {
    alert(error.message);
  }
});

els.priceCanvas.addEventListener("mousemove", (event) => {
  const data = visibleData();
  const geometry = state.chartGeometry;
  if (!geometry) return;
  const rect = els.priceCanvas.getBoundingClientRect();
  const mouseX = event.clientX - rect.left;
  const raw = (mouseX - geometry.pad.left) / geometry.innerW * (data.length - 1);
  const index = Math.max(0, Math.min(data.length - 1, Math.round(raw)));
  state.hoverIndex = index;
  const row = data[index];
  const previous = data[index - 1] || row;
  const change = row.close - previous.close;
  const chartPanelRect = els.priceCanvas.parentElement.getBoundingClientRect();
  const left = Math.min(rect.left - chartPanelRect.left + mouseX + 14, chartPanelRect.width - 190);
  const top = Math.max(72, event.clientY - chartPanelRect.top - 18);

  els.chartTooltip.hidden = false;
  els.chartTooltip.style.left = `${left}px`;
  els.chartTooltip.style.top = `${top}px`;
  els.chartTooltip.innerHTML = `
    <strong>${row.date}</strong>
    开 ${row.open.toFixed(0)} / 高 ${row.high.toFixed(0)}<br>
    低 ${row.low.toFixed(0)} / 收 ${row.close.toFixed(0)}<br>
    涨跌 ${formatSigned(change)} (${formatPct(change / previous.close)})<br>
    量 ${Math.round(row.volume / 10000)} 万手
  `;
  draw();
});

els.priceCanvas.addEventListener("mouseleave", () => {
  state.hoverIndex = null;
  els.chartTooltip.hidden = true;
  draw();
});

async function autoLoadCsv() {
  if (location.protocol === "file:") {
    console.warn("CSV auto-load needs http:// or https://. Open through a local server or GitHub Pages.");
    return;
  }
  try {
    const [response, metaResponse] = await Promise.all([
      fetch("data/palm_oil_p0_daily.csv", { cache: "no-store" }),
      fetch("data/source_meta.json", { cache: "no-store" })
    ]);
    if (!response.ok) return;
    const text = await response.text();
    const rows = parseCsv(text);
    if (rows.length < 20) return;
    state.dataMeta = metaResponse.ok ? await metaResponse.json() : null;
    state.data = rows;
    state.mode = "continuous";
    state.imported = false;
    state.autoLoaded = true;
    els.modeButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.mode === "continuous");
    });
    draw();
  } catch (error) {
    console.warn("CSV auto-load skipped:", error);
  }
}

window.addEventListener("resize", draw);
draw();
autoLoadCsv();
setInterval(autoLoadCsv, 60 * 1000);
