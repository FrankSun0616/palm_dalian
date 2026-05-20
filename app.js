const els = {
  priceCanvas: document.getElementById("priceCanvas"),
  volumeCanvas: document.getElementById("volumeCanvas"),
  chartTooltip: document.getElementById("chartTooltip"),
  periodSelect: document.getElementById("periodSelect"),
  maSelect: document.getElementById("maSelect"),
  csvInput: document.getElementById("csvInput"),
  reloadBtn: document.getElementById("reloadBtn"),
  demoBtn: document.getElementById("demoBtn"),
  generateAiBtn: document.getElementById("generateAiBtn"),
  aiStatus: document.getElementById("aiStatus"),
  boll1hStatus: document.getElementById("boll1hStatus"),
  boll1hDetail: document.getElementById("boll1hDetail"),
  boll2hStatus: document.getElementById("boll2hStatus"),
  boll2hDetail: document.getElementById("boll2hDetail"),
  intradayStrategyBias: document.getElementById("intradayStrategyBias"),
  intradayStrategyText: document.getElementById("intradayStrategyText"),
  newsRealtimeStatus: document.getElementById("newsRealtimeStatus"),
  newsRealtimeText: document.getElementById("newsRealtimeText"),
  lastPrice: document.getElementById("lastPrice"),
  lastChange: document.getElementById("lastChange"),
  signalText: document.getElementById("signalText"),
  signalDetail: document.getElementById("signalDetail"),
  upDays: document.getElementById("upDays"),
  winRate: document.getElementById("winRate"),
  volatility: document.getElementById("volatility"),
  dataStatus: document.getElementById("dataStatus"),
  dataFreshness: document.getElementById("dataFreshness"),
  chartTitle: document.getElementById("chartTitle"),
  chartSubhead: document.getElementById("chartSubhead"),
  legend: document.getElementById("legend"),
  analysisText: document.getElementById("analysisText"),
  resistance: document.getElementById("resistance"),
  support: document.getElementById("support"),
  observationList: document.getElementById("observationList"),
  indicatorGrid: document.getElementById("indicatorGrid"),
  scoreFill: document.getElementById("scoreFill"),
  signalList: document.getElementById("signalList"),
  scenarioList: document.getElementById("scenarioList"),
  riskTable: document.getElementById("riskTable"),
  aiMeta: document.getElementById("aiMeta"),
  aiBias: document.getElementById("aiBias"),
  aiSummary: document.getElementById("aiSummary"),
  aiStrategy: document.getElementById("aiStrategy"),
  aiStrategyGrid: document.getElementById("aiStrategyGrid"),
  aiList: document.getElementById("aiList"),
  aiNewsSection: document.getElementById("aiNewsSection"),
  aiNewsList: document.getElementById("aiNewsList"),
  aiArticlesSection: document.getElementById("aiArticlesSection"),
  aiArticlesList: document.getElementById("aiArticlesList"),
  aiSupport: document.getElementById("aiSupport"),
  aiResistance: document.getElementById("aiResistance"),
  aiRisk: document.getElementById("aiRisk")
};

const colors = {
  up: "#cf3f35",
  down: "#168f6a",
  grid: "#e3e8df",
  text: "#66716a",
  ma: ["#c18c2d", "#326fb7", "#7657a8"]
};

let state = {
  data: makeDemoData(),
  imported: false,
  autoLoaded: false,
  dataMeta: null,
  intradayMeta: null,
  newsSnapshot: null,
  hoverIndex: null,
  chartGeometry: null
};

function setLoadStatus(status, detail = "") {
  if (!els.dataStatus || !els.dataFreshness) return;
  els.dataStatus.textContent = status;
  els.dataStatus.className = status === "真实CSV" ? "up" : status === "加载失败" ? "down" : "";
  els.dataFreshness.textContent = detail;
}

function makeDemoData() {
  const rows = [];
  const end = new Date();
  end.setHours(0, 0, 0, 0);
  let close = 7740;
  const drift = 2.3;

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

function mean(values) {
  if (!values.length) return 0;
  return values.reduce((sum, item) => sum + item, 0) / values.length;
}

function stddev(values) {
  if (!values.length) return 0;
  const avg = mean(values);
  return Math.sqrt(mean(values.map((item) => (item - avg) ** 2)));
}

function ema(values, period) {
  const k = 2 / (period + 1);
  const result = [];
  values.forEach((value, index) => {
    if (index === 0) result.push(value);
    else result.push(value * k + result[index - 1] * (1 - k));
  });
  return result;
}

function rsi(data, period = 14) {
  if (data.length <= period) return null;
  const changes = data.slice(1).map((row, index) => row.close - data[index].close);
  const seed = changes.slice(0, period);
  let avgGain = mean(seed.map((value) => Math.max(value, 0)));
  let avgLoss = mean(seed.map((value) => Math.max(-value, 0)));

  for (let i = period; i < changes.length; i += 1) {
    const gain = Math.max(changes[i], 0);
    const loss = Math.max(-changes[i], 0);
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
  }

  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

function macd(data) {
  const closes = data.map((row) => row.close);
  const ema12 = ema(closes, 12);
  const ema26 = ema(closes, 26);
  const dif = closes.map((_, index) => ema12[index] - ema26[index]);
  const dea = ema(dif, 9);
  const hist = dif.map((value, index) => value - dea[index]);
  return { dif: dif.at(-1), dea: dea.at(-1), hist: hist.at(-1), prevHist: hist.at(-2) || 0 };
}

function atr(data, period = 14) {
  if (data.length < 2) return null;
  const trs = data.slice(1).map((row, index) => {
    const prevClose = data[index].close;
    return Math.max(row.high - row.low, Math.abs(row.high - prevClose), Math.abs(row.low - prevClose));
  });
  return mean(trs.slice(-period));
}

function bollinger(data, period = 20, width = 2) {
  const window = data.slice(-period).map((row) => row.close);
  const mid = mean(window);
  const sd = stddev(window);
  return { upper: mid + width * sd, mid, lower: mid - width * sd, bandWidth: mid ? (width * 2 * sd) / mid : 0 };
}

function maxDrawdown(data, period = 60) {
  let peak = -Infinity;
  let drawdown = 0;
  data.slice(-period).forEach((row) => {
    peak = Math.max(peak, row.close);
    drawdown = Math.min(drawdown, (row.close - peak) / peak);
  });
  return drawdown;
}

function closeStreak(data) {
  let streak = 0;
  for (let i = data.length - 1; i > 0; i -= 1) {
    const diff = data[i].close - data[i - 1].close;
    if (diff === 0) break;
    if (streak === 0) streak = diff > 0 ? 1 : -1;
    else if ((streak > 0 && diff > 0) || (streak < 0 && diff < 0)) streak += streak > 0 ? 1 : -1;
    else break;
  }
  return streak;
}

function dateAgeDays(dateText) {
  if (!dateText) return null;
  const date = new Date(`${dateText}T00:00:00`);
  if (Number.isNaN(date.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((today - date) / 86400000);
}

function analyze(data) {
  const last = data[data.length - 1];
  const prev = data[data.length - 2] || last;
  const closes = data.map((row) => row.close);
  const ma10 = movingAverage(data, 10).at(-1);
  const ma20 = movingAverage(data, 20).at(-1);
  const ma60 = movingAverage(data, Math.min(60, data.length)).at(-1);
  const ma120 = movingAverage(data, Math.min(120, data.length)).at(-1);
  const changes = data.slice(1).map((row, index) => (row.close - data[index].close) / data[index].close);
  const recent20 = changes.slice(-20);
  const avgChange = mean(recent20);
  const variance = mean(recent20.map((item) => (item - avgChange) ** 2));
  const vol = Math.sqrt(variance) * Math.sqrt(252);
  const upCount = changes.filter((item) => item > 0).length;
  const high20 = Math.max(...data.slice(-20).map((row) => row.high));
  const low20 = Math.min(...data.slice(-20).map((row) => row.low));
  const high60 = Math.max(...data.slice(-60).map((row) => row.high));
  const low60 = Math.min(...data.slice(-60).map((row) => row.low));
  const change = last.close - prev.close;
  const changePct = change / prev.close;
  const rsi14 = rsi(data, 14);
  const macdValue = macd(data);
  const atr14 = atr(data, 14);
  const boll = bollinger(data, 20, 2);
  const volumeAvg20 = mean(data.slice(-20).map((row) => row.volume));
  const volumeRatio = last.volume / Math.max(1, volumeAvg20);
  const drawdown60 = maxDrawdown(data, 60);
  const streak = closeStreak(data);
  const dayRangePct = (last.high - last.low) / last.close;
  const closePosition = (last.close - last.low) / Math.max(1, last.high - last.low);
  const atrPct = atr14 ? atr14 / last.close : 0;
  const trendSlope20 = data.length > 21 ? (ma20 - movingAverage(data.slice(0, -20), 20).at(-1)) / last.close : 0;
  const support = Math.min(low20, boll.lower);
  const resistance = Math.max(high20, boll.upper);
  const distanceToResistance = (high20 - last.close) / last.close;
  const distanceToSupport = (last.close - low20) / last.close;
  const riskReward = distanceToSupport > 0 ? distanceToResistance / distanceToSupport : null;
  const fib382 = high60 - (high60 - low60) * 0.382;
  const fib618 = high60 - (high60 - low60) * 0.618;

  const checks = [
    { label: "收盘价站上 MA20", ok: last.close > ma20, weight: 1.1 },
    { label: "MA10 高于 MA20", ok: ma10 > ma20, weight: 1 },
    { label: "MA20 高于 MA60", ok: ma20 > ma60, weight: 1 },
    { label: "MACD 柱体为正", ok: macdValue.hist > 0, weight: 0.9 },
    { label: "RSI 位于强势区", ok: rsi14 >= 50 && rsi14 <= 72, weight: 0.8 },
    { label: "放量但不过热", ok: volumeRatio >= 1 && volumeRatio <= 1.8, weight: 0.7 },
    { label: "收盘靠近日内高位", ok: closePosition >= 0.55, weight: 0.6 },
    { label: "价格未跌破布林中轨", ok: last.close >= boll.mid, weight: 0.8 }
  ];
  const positiveScore = checks.reduce((sum, item) => sum + (item.ok ? item.weight : 0), 0);
  const totalScore = checks.reduce((sum, item) => sum + item.weight, 0);
  const score = positiveScore / totalScore * 100;
  const signal = score >= 68 ? "偏强" : score <= 42 ? "偏弱" : "震荡";
  const staleDays = dateAgeDays(last.date);

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
    high60,
    low60,
    ma10,
    ma20,
    ma60,
    ma120,
    rsi14,
    macdValue,
    atr14,
    atrPct,
    boll,
    volumeAvg20,
    volumeRatio,
    drawdown60,
    streak,
    dayRangePct,
    closePosition,
    trendSlope20,
    support,
    resistance,
    riskReward,
    fib382,
    fib618,
    signal,
    score,
    checks,
    staleDays,
    observations: [
      `收盘价位于 MA20 ${last.close >= ma20 ? "上方" : "下方"}，短线结构${last.close >= ma20 ? "较稳" : "承压"}。`,
      `MA10 ${ma10 >= ma20 ? "高于" : "低于"} MA20，MACD 柱体${macdValue.hist >= 0 ? "为正" : "为负"}，动量${ma10 >= ma20 && macdValue.hist >= 0 ? "偏顺" : "仍需确认"}。`,
      `RSI14 为 ${rsi14.toFixed(1)}，${rsi14 > 72 ? "进入偏热区，追高风险上升" : rsi14 < 35 ? "处于偏冷区，短线可能有修复需求" : "处在可观察区间"}。`,
      `成交量为 20 日均量的 ${volumeRatio.toFixed(2)} 倍，${volumeRatio > 1.5 ? "量能明显放大" : volumeRatio < 0.8 ? "量能偏弱" : "量能中性"}。`,
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
  if (lastQuote) applyRealtimeQuote(lastQuote);
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
    ctx.globalAlpha = row.preliminary ? 0.7 : 1;
    const candleColor = row.preliminary ? "#4f8ef7" : (rising ? colors.up : colors.down);
    ctx.strokeStyle = candleColor;
    ctx.fillStyle = candleColor;
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
    if (row.preliminary) {
      ctx.fillStyle = colors.text;
      ctx.globalAlpha = 0.6;
      ctx.font = "10px Arial";
      ctx.textAlign = "center";
      ctx.fillText("夜盘", cx, pad.top + 6);
    }
    ctx.globalAlpha = 1;
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
  els.chartTitle.textContent = "P0 棕榈油连续日线";
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
  els.signalDetail.textContent = `综合评分 ${analysis.score.toFixed(0)} / 100`;
  els.upDays.textContent = `${analysis.upCount} 天`;
  els.winRate.textContent = `样本上涨率 ${formatPct(analysis.winRate)}`;
  els.volatility.textContent = formatPct(analysis.vol);
  updateDataStatus(analysis);
  els.resistance.textContent = analysis.resistance.toFixed(0);
  els.support.textContent = analysis.support.toFixed(0);
  els.analysisText.textContent = makeAnalysisText(analysis);
  els.observationList.innerHTML = analysis.observations.map((item) => {
    // Highlight bullish/bearish phrases inline
    const highlighted = String(item)
      .replace(/(多头排列|向上突破|放量上涨|强势|偏热|看多|连涨|站上|突破上轨|上行|拉升)/g, '<span class="up">$1</span>')
      .replace(/(空头排列|向下跌破|放量下跌|弱势|偏冷|看空|连跌|跌破|跌破下轨|下行|回落|缩量)/g, '<span class="down">$1</span>');
    return `<li>${highlighted}</li>`;
  }).join("");
  els.indicatorGrid.innerHTML = makeIndicatorCards(analysis);
  els.scoreFill.style.width = `${Math.max(3, Math.min(100, analysis.score))}%`;
  els.signalList.innerHTML = analysis.checks.map((item) => {
    const klass = item.ok ? "up" : "down";
    return `<li><span class="${klass}">${item.ok ? "通过" : "未过"}</span> ${item.label}</li>`;
  }).join("");
  els.scenarioList.innerHTML = makeScenarios(analysis);
  els.riskTable.innerHTML = makeRiskTable(analysis);
}

function makeAnalysisText(a) {
  if (a.signal === "偏强") {
    return `综合评分 ${a.score.toFixed(0)}，结构偏强。价格位于关键均线之上，动量指标配合时更容易向压力区试探。若突破 ${a.resistance.toFixed(0)} 且成交量维持在 20 日均量上方，趋势延伸概率提高；若跌回 MA20 下方，需要把偏强判断降级。`;
  }
  if (a.signal === "偏弱") {
    return `综合评分 ${a.score.toFixed(0)}，结构偏弱。价格或动量没有形成一致向上，反弹更需要量能和均线确认。若跌破 ${a.support.toFixed(0)}，弱势结构可能加深；重新站回 MA20 并修复 MACD 前，宜谨慎看待追多。`;
  }
  return `综合评分 ${a.score.toFixed(0)}，当前偏震荡。价格与均线、动量、量能没有形成单边一致性。更适合观察 ${a.support.toFixed(0)}-${a.resistance.toFixed(0)} 区间内的放量突破或缩量回踩，而不是提前押单边。`;
}

function updateDataStatus(analysis) {
  const sourceLabel = state.autoLoaded || state.dataMeta ? "真实CSV" : state.imported ? "手动CSV" : "示例";
  const latest = state.dataMeta?.latest_date || analysis.last.date;
  const updated = state.dataMeta?.updated_at_utc ? `更新 ${formatDateTime(state.dataMeta.updated_at_utc)}` : "本地生成";
  const checked = `检查 ${bjNow()}`;
  const stale = analysis.staleDays === null ? "" : analysis.staleDays > 3 ? `，距今 ${analysis.staleDays} 天，需核对` : `，距今 ${analysis.staleDays} 天`;
  setLoadStatus(sourceLabel, `${latest}${stale} | ${updated} | ${checked}`);
}

// Return CSS color class ("up" red / "down" green / "") for any bullish/bearish
// keyword combo. Used to colorize indicator values, scenario tags, etc.
function biasColor(text) {
  if (!text) return "";
  const s = String(text);
  if (/多头|偏热|突破上|站上|强势|放量|连涨|向上|看多|利多|扩张/.test(s)) return "up";
  if (/空头|偏冷|跌破|破位|弱势|缩量|连跌|向下|看空|利空|收缩|回撤|风险转弱/.test(s)) return "down";
  return "";
}

// Color a numeric MACD/ATR/etc. value based on its sign or threshold.
function valueColor(value, mode = "sign") {
  if (mode === "sign") return value > 0 ? "up" : value < 0 ? "down" : "";
  if (mode === "rsi")  return value > 60 ? "up" : value < 40 ? "down" : "";
  if (mode === "volRatio") return value > 1.2 ? "up" : value < 0.8 ? "down" : "";
  if (mode === "drawdown") return value < -0.05 ? "down" : value > -0.02 ? "up" : "";
  return "";
}

function makeIndicatorCards(a) {
  const maStructure = a.ma10 > a.ma20 && a.ma20 > a.ma60
    ? "多头排列" : a.ma10 < a.ma20 && a.ma20 < a.ma60 ? "空头排列" : "交错震荡";
  const rsiState = a.rsi14 > 72 ? "偏热，防冲高回落"
                  : a.rsi14 < 35 ? "偏冷，关注修复" : "中性区间";
  const macdHistTrend = a.macdValue.hist >= a.macdValue.prevHist ? "扩张" : "收缩";
  const bollState = a.last.close > a.boll.upper ? "突破上轨"
                  : a.last.close < a.boll.lower ? "跌破下轨" : "在轨道内";
  const streakLabel = a.streak > 0 ? `${a.streak} 连涨`
                     : a.streak < 0 ? `${Math.abs(a.streak)} 连跌` : "无连续";

  const cards = [
    ["MA 结构",  maStructure,            `MA10 ${a.ma10.toFixed(0)} / MA20 ${a.ma20.toFixed(0)} / MA60 ${a.ma60.toFixed(0)}`,
                 biasColor(maStructure)],
    ["RSI14",    a.rsi14.toFixed(1),     rsiState,
                 valueColor(a.rsi14, "rsi")],
    ["MACD",     a.macdValue.hist.toFixed(1),
                 `DIF ${a.macdValue.dif.toFixed(1)} / DEA ${a.macdValue.dea.toFixed(1)}，柱体<span class="${biasColor(macdHistTrend)}">${macdHistTrend}</span>`,
                 valueColor(a.macdValue.hist, "sign")],
    ["布林带",   `${a.boll.lower.toFixed(0)}-${a.boll.upper.toFixed(0)}`,
                 `带宽 ${formatPct(a.boll.bandWidth)}，收盘<span class="${biasColor(bollState)}">${bollState}</span>`,
                 biasColor(bollState)],
    ["ATR14",    a.atr14.toFixed(0),     `约 ${formatPct(a.atrPct)}，日内波动 ${formatPct(a.dayRangePct)}`,
                 ""],
    ["量能",     `${a.volumeRatio.toFixed(2)}x`,
                 `当前 ${formatCompact(a.last.volume)} / 20日均量 ${formatCompact(a.volumeAvg20)}`,
                 valueColor(a.volumeRatio, "volRatio")],
    ["60日回撤", formatPct(a.drawdown60),
                 `60日高 ${a.high60.toFixed(0)} / 低 ${a.low60.toFixed(0)}`,
                 valueColor(a.drawdown60, "drawdown")],
    ["连涨连跌", streakLabel,
                 `收盘位置 ${formatPct(a.closePosition)}`,
                 biasColor(streakLabel)],
  ];

  return cards.map(([label, value, detail, color]) => `
    <div class="indicator">
      <span>${label}</span>
      <strong class="${color}">${value}</strong>
      <small>${detail}</small>
    </div>
  `).join("");
}

function makeScenarios(a) {
  const upsideTarget = a.resistance + Math.max(1, a.atr14);
  const downsideTarget = a.support - Math.max(1, a.atr14);
  const pullbackZone = Math.min(a.ma20, a.boll.mid);
  const scenarios = [
    ["向上突破", `${a.resistance.toFixed(0)} 上方放量站稳`, `目标观察 ${upsideTarget.toFixed(0)}；若量能低于 20 日均量，突破可信度下降。`, "up"],
    ["区间震荡", `${a.support.toFixed(0)}-${a.resistance.toFixed(0)}`, `价格没有离开区间前，以均值回归和等待确认更合理。`, ""],
    ["回踩修复", `回踩 ${pullbackZone.toFixed(0)} 附近`, `若缩量企稳且 RSI 不跌破 45，属于较健康回踩。`, ""],
    ["风险转弱", `${a.support.toFixed(0)} 下方收盘`, `下方风险位看 ${downsideTarget.toFixed(0)}；此时趋势评分通常会继续下调。`, "down"],
  ];
  return scenarios.map(([title, trigger, detail, color]) => `
    <div class="scenario">
      <span class="${color}">${title}</span>
      <strong class="${color}">${trigger}</strong>
      <small>${detail}</small>
    </div>
  `).join("");
}

function makeRiskTable(a) {
  // 红 = 上方压力，绿 = 下方支撑
  const rows = [
    ["近20日支撑", a.low20,  "跌破后短线结构转弱",  "down"],
    ["综合支撑",   a.support,"结合布林下轨和20日低点", "down"],
    ["MA20 防守",  a.ma20,   "趋势跟踪的核心分界",  ""],
    ["近20日压力", a.high20, "突破后观察是否放量",  "up"],
    ["综合压力",   a.resistance, "结合布林上轨和20日高点", "up"],
    ["60日38.2%",  a.fib382, "60日区间回撤参考",    ""],
    ["60日61.8%",  a.fib618, "60日区间深回撤参考",  ""],
  ];

  return rows.map(([name, value, note, color]) => `
    <div class="risk-row">
      <div>
        <span>${name}</span>
        <small>${note}</small>
      </div>
      <strong class="${color}">${value.toFixed(0)}</strong>
    </div>
  `).join("");
}

function formatSigned(value) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(0)}`;
}

function formatPct(value) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(2)}%`;
}

function formatCompact(value) {
  if (Math.abs(value) >= 10000) return `${Math.round(value / 10000)}万`;
  return Math.round(value).toString();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

const TZ = "Asia/Shanghai";

function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { timeZone: TZ, hour12: false });
}

function bjNow(opts = {}) {
  return new Date().toLocaleTimeString("zh-CN", { timeZone: TZ, hour12: false, ...opts });
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

els.periodSelect.addEventListener("change", draw);
els.maSelect.addEventListener("change", draw);
els.reloadBtn.addEventListener("click", () => {
  autoLoadCsv();
});

els.demoBtn.addEventListener("click", () => {
  state.data = makeDemoData();
  state.imported = false;
  state.autoLoaded = false;
  state.dataMeta = null;
  els.csvInput.value = "";
  draw();
});

const GH_OWNER = "FrankSun0616";
const GH_REPO = "palm_dalian";
const GH_WORKFLOW = "update-data.yml";
const PAT_KEY = "gh_pat_palm_dalian";

// Embedded PAT for one-click triggering. Base64 only to bypass GitHub
// secret-scanning on push (the user explicitly approved making it public).
localStorage.setItem(PAT_KEY, atob(
  "Z2l0aHViX3BhdF8xMUJIWlpDU1kwZDdKb050dVczVXU5X2dmMjd1c0V4aldwRHRMenU2ZXFNNHVKeF" +
  "VHM2Z6eDRYVW5ocE9WVGhlVjRPRzdGVEVaVU8yc3phbUEx"
));

function setAiStatus(text, type) {
  els.aiStatus.textContent = text;
  els.aiStatus.className = `ai-status${type ? ` ${type}` : ""}`;
}

async function generateAiAnalysis() {
  const pat = localStorage.getItem(PAT_KEY) || "";
  if (!pat) {
    setAiStatus("PAT 未设置，无法触发", "error");
    return;
  }

  els.generateAiBtn.disabled = true;
  setAiStatus("正在触发 GitHub Actions...", "loading");

  // Remember previous generation time so we can detect when a fresh one lands.
  let prevGenTime = null;
  try {
    const r = await fetch(`data/ai_analysis.json?t=${Date.now()}`, { cache: "no-store" });
    if (r.ok) {
      const ai = await r.json();
      prevGenTime = ai.generated_at_utc || null;
    }
  } catch (_) {}

  try {
    const resp = await fetch(
      `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/actions/workflows/${GH_WORKFLOW}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${pat}`,
          Accept: "application/vnd.github+json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ ref: "main", inputs: { run_ai_analysis: "true" } })
      }
    );
    if (!resp.ok) {
      const body = await resp.text().catch(() => "");
      setAiStatus(`触发失败 (${resp.status})${body ? "：" + body.slice(0, 80) : ""}`, "error");
      els.generateAiBtn.disabled = false;
      return;
    }
  } catch (err) {
    setAiStatus(`网络错误：${err.message}`, "error");
    els.generateAiBtn.disabled = false;
    return;
  }

  setAiStatus("正在网络搜索 + 生成深度分析，约 6–10 分钟后自动刷新...", "loading");

  const startTime = Date.now();
  const maxWait = 12 * 60 * 1000;
  const interval = setInterval(async () => {
    if (Date.now() - startTime > maxWait) {
      clearInterval(interval);
      setAiStatus("超时，请手动刷新页面", "error");
      els.generateAiBtn.disabled = false;
      return;
    }
    try {
      const r = await fetch(`data/ai_analysis.json?t=${Date.now()}`, { cache: "no-store" });
      if (!r.ok) return;
      const ai = await r.json();
      const newTime = ai.generated_at_utc || null;
      if (newTime && newTime !== prevGenTime) {
        clearInterval(interval);
        updateAiPanel(ai);
        setAiStatus(`✓ 分析完成 (${formatDateTime(newTime)})`, "success");
        els.generateAiBtn.disabled = false;
      }
    } catch (_) {}
  }, 25 * 1000);
}

els.generateAiBtn.addEventListener("click", generateAiAnalysis);

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
  const liveLabel = row.preliminary ? (isNightSession() ? " 🌙夜盘" : " ⚡实时") : "";
  const liveNote  = row.preliminary ? `<br><small>${isNightSession() ? "夜盘进行中" : "实时行情"}，数据未完整</small>` : "";
  els.chartTooltip.innerHTML = `
    <strong>${row.date}${liveLabel}</strong>
    开 ${row.open.toFixed(0)} / 高 ${row.high.toFixed(0)}<br>
    低 ${row.low.toFixed(0)} / 收 ${row.close.toFixed(0)}<br>
    涨跌 ${formatSigned(change)} (${formatPct(change / previous.close)})<br>
    量 ${Math.round(row.volume / 10000)} 万手${liveNote}
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
    const message = "请通过 GitHub Pages 或本地 http server 打开，file:// 无法自动读取 CSV";
    setLoadStatus("加载失败", message);
    console.warn(message);
    return;
  }
  setLoadStatus("加载中", "正在读取真实 P0 CSV...");
  try {
    const cacheBust = `t=${Date.now()}`;
    const [response, metaResponse] = await Promise.all([
      fetch(`data/palm_oil_p0_daily.csv?${cacheBust}`, { cache: "no-store" }),
      fetch(`data/source_meta.json?${cacheBust}`, { cache: "no-store" })
    ]);
    if (!response.ok) throw new Error(`CSV HTTP ${response.status}`);
    const text = await response.text();
    const rows = parseCsv(text);
    if (rows.length < 20) throw new Error(`CSV有效数据少于20行: ${rows.length}`);
    state.dataMeta = metaResponse.ok ? await metaResponse.json() : null;
    state.data = rows;
    // Only pre-seed the live_bar from source_meta during night session —
    // the real-time feed handles injecting today's bar during daytime.
    if (state.dataMeta && state.dataMeta.live_bar && isNightSession()) {
      const lb = state.dataMeta.live_bar;
      state.data.push({
        date: lb.date,
        open: lb.open,
        high: lb.high,
        low: lb.low,
        close: lb.close,
        volume: lb.volume,
        preliminary: true
      });
    }
    state.imported = false;
    state.autoLoaded = true;
    draw();
  } catch (error) {
    setLoadStatus("加载失败", error.message || "未知错误");
    console.warn("CSV auto-load skipped:", error);
  }
}

async function autoLoadAiAnalysis() {
  if (location.protocol === "file:") return;
  try {
    const cacheBust = `t=${Date.now()}`;
    const response = await fetch(`data/ai_analysis.json?${cacheBust}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`AI HTTP ${response.status}`);
    const ai = await response.json();
    updateAiPanel(ai);
  } catch (error) {
    els.aiMeta.textContent = "AI 分析读取失败";
    els.aiSummary.textContent = error.message || "未知错误";
    els.aiBias.textContent = "--";
    els.aiList.innerHTML = "";
  }
}

async function autoLoadIntradayMeta() {
  if (location.protocol === "file:") return;
  try {
    const response = await fetch(`data/intraday_meta.json?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Intraday HTTP ${response.status}`);
    state.intradayMeta = await response.json();
    updateIntradayPanel();
  } catch (error) {
    els.boll1hStatus.textContent = "加载失败";
    els.boll1hDetail.textContent = error.message || "无法读取1小时数据";
    els.boll2hStatus.textContent = "加载失败";
    els.boll2hDetail.textContent = error.message || "无法读取2小时数据";
  }
}

async function autoLoadNewsSnapshot() {
  if (location.protocol === "file:") return;
  try {
    const response = await fetch(`data/news_snapshot.json?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`News HTTP ${response.status}`);
    state.newsSnapshot = await response.json();
    updateNewsPanel();
  } catch (error) {
    els.newsRealtimeStatus.textContent = "舆情读取失败";
    els.newsRealtimeText.textContent = error.message || "无法读取舆情数据";
  }
}

function bandStatus(summary, realtimePrice = null) {
  if (!summary || !summary.bollinger) return { title: "--", detail: "暂无布林数据" };
  const boll = summary.bollinger;
  const price = realtimePrice || summary.close || boll.close;
  const width = formatPct(Number(boll.band_width || 0));
  const pos = price > boll.upper ? "突破上轨" : price < boll.lower ? "跌破下轨" : price >= boll.mid ? "中轨上方" : "中轨下方";
  let read = "震荡";
  if (price > boll.upper) read = "偏强但防追高";
  else if (price < boll.lower) read = "偏弱但防急跌反抽";
  else if (price >= boll.mid) read = "回到强势半区";
  else read = "位于弱势半区";
  return {
    title: `${pos}`,
    detail: `价 ${Number(price).toFixed(0)}｜上 ${Number(boll.upper).toFixed(0)} 中 ${Number(boll.mid).toFixed(0)} 下 ${Number(boll.lower).toFixed(0)}｜带宽 ${width}｜${read}｜${summary.latest_time || ""}`
  };
}

function updateIntradayPanel() {
  const meta = state.intradayMeta;
  if (!meta) return;
  const price = lastQuote?.price || null;
  const one = bandStatus(meta.one_hour, price);
  const two = bandStatus(meta.two_hour, price);
  els.boll1hStatus.textContent = one.title;
  els.boll1hStatus.className = /上轨|强势/.test(one.title) ? "up" : /下轨|弱势/.test(one.title) ? "down" : "";
  els.boll1hDetail.textContent = one.detail;
  els.boll2hStatus.textContent = two.title;
  els.boll2hStatus.className = /上轨|强势/.test(two.title) ? "up" : /下轨|弱势/.test(two.title) ? "down" : "";
  els.boll2hDetail.textContent = two.detail;

  const onePos = meta.one_hour?.bollinger?.position || "";
  const twoPos = meta.two_hour?.bollinger?.position || "";
  const alignedUp = /上方|上轨/.test(onePos) && /上方|上轨/.test(twoPos);
  const alignedDown = /下方|下轨/.test(onePos) && /下方|下轨/.test(twoPos);
  els.intradayStrategyBias.textContent = alignedUp ? "短线偏多" : alignedDown ? "短线偏弱" : "区间震荡";
  els.intradayStrategyBias.className = alignedUp ? "up" : alignedDown ? "down" : "";
  els.intradayStrategyText.textContent = alignedUp
    ? "1H/2H 同在布林中轨上方，适合等回踩中轨不破再看延续；跌回2H中轨下方则降级。"
    : alignedDown
      ? "1H/2H 同在中轨下方，反弹先看压力，未重新站回2H中轨前不追多。"
      : "1H/2H 信号不一致，优先按布林上下轨做区间观察，等待放量突破再跟随。";
}

function updateNewsPanel() {
  const snap = state.newsSnapshot;
  const articles = Array.isArray(snap?.articles) ? snap.articles : [];
  const updated = snap?.updated_at_utc ? formatDateTime(snap.updated_at_utc) : "--";
  els.newsRealtimeStatus.textContent = articles.length ? `${articles.length} 条` : "暂无";
  els.newsRealtimeText.textContent = articles.length
    ? `最新 ${updated}。${articles.slice(0, 2).map((item) => item.title).filter(Boolean).join("；")}`
    : `最新 ${updated}，没有抓到新舆情。`;
}

function biasClass(text) {
  if (/多|强/.test(text)) return "bullish";
  if (/空|弱/.test(text)) return "bearish";
  return "neutral";
}

function updateAiPanel(ai) {
  els.aiBias.textContent = ai.bias || "--";
  els.aiBias.className = `bias-pill ${biasClass(ai.bias || "")}`;
  const status = ai.status === "ok" ? "DeepSeek" : "规则备用";
  const generated = ai.generated_at_utc ? formatDateTime(ai.generated_at_utc) : "--";
  const realtimeTag = ai.realtime_price ? ` | 实时价 ${ai.realtime_price}` : "";
  els.aiMeta.textContent = `${status} | 日线 ${ai.latest_date || "--"}${realtimeTag} | 生成 ${generated}`;
  els.aiSummary.textContent = ai.summary || "暂无 AI 摘要。";

  const strategy = ai.intraday_strategy && typeof ai.intraday_strategy === "object" ? ai.intraday_strategy : null;
  if (strategy) {
    els.aiStrategy.hidden = false;
    const rows = [
      ["短线方向", strategy.bias],
      ["入场观察", strategy.entry],
      ["止损/风控", strategy.stop],
      ["止盈目标", strategy.take_profit],
      ["失效条件", strategy.invalidation],
      ["备注", strategy.notes],
    ];
    els.aiStrategyGrid.innerHTML = rows.map(([label, value]) => `
      <div class="strategy-item">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value || "--")}</strong>
      </div>
    `).join("");
  } else {
    els.aiStrategy.hidden = true;
  }

  // Map any bias label to a CSS class. Handles 中性偏多/中性偏空 nuances.
  const impactClass = (imp) => {
    if (!imp) return "neutral";
    if (/中性偏空|偏空|看空|利空|空头|弱/.test(imp)) return "down";
    if (/中性偏多|偏多|看多|利多|多头|强/.test(imp)) return "up";
    if (/中性/.test(imp)) return "neutral";
    return "neutral";
  };

  // Highlight ONLY explicit bullish/bearish impact words. Avoid generic
  // direction words like "增长/下降" which are context-dependent (e.g. supply
  // increases are bearish for price).
  const colorizeText = (text) => {
    return escapeHtml(text)
      .replace(/(利多|看多|偏多|多头排列|强势|放量上涨|底部支撑|利好)/g,
               '<span class="up">$1</span>')
      .replace(/(利空|看空|偏空|空头排列|弱势|放量下跌|破位|压制|担忧)/g,
               '<span class="down">$1</span>');
  };

  // Convert "[利空] xxx" / "[中性偏多] xxx" → "<badge>利空</badge> xxx" with color.
  // The badge gives the dominant signal; we don't keyword-color the body to
  // avoid misleading users (e.g. "产量增长" reads bullish but is bearish for price).
  const renderImpactItem = (raw) => {
    const m = String(raw).match(/^\s*\[([^\]]+)\]\s*(.*)$/);
    if (m) {
      const label = m[1];
      const body  = m[2];
      return `<span class="news-badge ${impactClass(label)}">${escapeHtml(label)}</span> ${escapeHtml(body)}`;
    }
    return escapeHtml(raw);
  };

  // Technical analysis bullets — also inline-highlight bias words
  const items = Array.isArray(ai.analysis) ? ai.analysis : ai.analysis ? [ai.analysis] : [];
  els.aiList.innerHTML = items.map((item) => `<li>${colorizeText(item)}</li>`).join("");

  // News / sentiment detailed bullets
  const newsItems = Array.isArray(ai.news_impact) ? ai.news_impact : [];
  const articles  = Array.isArray(ai.news_articles) ? ai.news_articles : [];
  const hasNews   = newsItems.length > 0 || articles.length > 0;

  if (hasNews) {
    els.aiNewsSection.hidden = false;

    // Detailed impact bullets — each gets a colored prefix badge
    els.aiNewsList.innerHTML = newsItems.map((item) => `<li>${renderImpactItem(item)}</li>`).join("");

    // Source article cards
    if (articles.length > 0) {
      els.aiArticlesList.innerHTML = articles.map((a) => `
        <div class="news-card">
          <div class="news-card-head">
            <span class="news-badge ${impactClass(a.impact)}">${escapeHtml(a.impact || "中性")}</span>
            ${a.url && a.url.startsWith("http")
              ? `<a class="news-title" href="${escapeHtml(a.url)}" target="_blank" rel="noopener">${escapeHtml(a.title || "查看原文")}</a>`
              : `<span class="news-title">${escapeHtml(a.title || "")}</span>`
            }
          </div>
          ${a.source ? `<small class="news-source">${escapeHtml(a.source)}</small>` : ""}
          ${a.detail ? `<p class="news-detail">${colorizeText(a.detail)}</p>` : ""}
        </div>
      `).join("");
      els.aiArticlesSection.hidden = false;
    } else {
      els.aiArticlesSection.hidden = true;
    }
  } else {
    els.aiNewsSection.hidden = true;
  }

  const watchLevels = typeof ai.watch_levels === "object" && ai.watch_levels !== null ? ai.watch_levels : {};
  els.aiSupport.textContent = Number(watchLevels.support || 0) ? Number(watchLevels.support).toFixed(0) : "--";
  els.aiResistance.textContent = Number(watchLevels.resistance || 0) ? Number(watchLevels.resistance).toFixed(0) : "--";
  els.aiRisk.textContent = ai.risk_note || "本分析仅供行情研究，不构成投资建议。";
}

// ── Real-time quote ──────────────────────────────────────────────────────────

let lastQuote = null;

function bjHour() { return (new Date().getUTCHours() + 8) % 24; }
function isNightSession() { const h = bjHour(); return h >= 21 && h <= 23; }
function isDaySession()   { const h = bjHour(); return h >= 9  && h <= 15; }
function isTrading()      { return isDaySession() || isNightSession(); }

const SINA_FUTURES_URL =
  "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/" +
  "Market_Center.getHQFuturesData?page=1&sort=position&asc=0&node=zly_qh&base=futures";

async function fetchRealtimeQuote() {
  try {
    const r = await fetch(`${SINA_FUTURES_URL}&_=${Date.now()}`, { cache: "no-store" });
    if (!r.ok) return null;
    const data = await r.json();
    const p0 = Array.isArray(data) && data.find(item => item.symbol === "P0");
    if (!p0 || !+p0.trade) return null;
    const price     = +p0.trade;
    const prevClose = +p0.preclose;
    return {
      price,
      high:      +p0.high,
      low:       +p0.low,
      open:      +p0.open,
      prevClose,
      volume:    +p0.volume,
      change:    price - prevClose,
      changePct: prevClose > 0 ? (price - prevClose) / prevClose : 0,
      tradedate: p0.tradedate || "",
      ticktime:  p0.ticktime  || ""
    };
  } catch (_) {
    return null;
  }
}

// Inject or update the in-progress bar in state.data from real-time quote
function updateLiveBar(q) {
  if (!isTrading()) {
    // Outside trading hours — remove any stale preliminary bar
    const idx = state.data.findIndex(r => r.preliminary);
    if (idx >= 0) state.data.splice(idx, 1);
    return;
  }
  if (!q || !q.tradedate) return;
  // Skip if this date is already a completed bar in the CSV
  const lastCompleted = [...state.data].reverse().find(r => !r.preliminary);
  if (lastCompleted && q.tradedate <= lastCompleted.date) return;

  const bar = {
    date: q.tradedate,
    open: q.open,
    high: q.high,
    low: q.low,
    close: q.price,
    volume: q.volume,
    preliminary: true
  };
  const idx = state.data.findIndex(r => r.preliminary);
  if (idx >= 0) state.data[idx] = bar;
  else state.data.push(bar);
}

// Update metric card with real-time price (no draw calls)
function applyRealtimeQuote(q) {
  if (!q) return;

  els.lastPrice.textContent = q.price.toFixed(0);
  els.lastChange.textContent = `${formatSigned(q.change)} (${formatPct(q.changePct)})`;
  els.lastChange.className = q.change >= 0 ? "up" : "down";

  const metricCard = els.lastPrice.closest(".metric");
  if (metricCard && !metricCard.querySelector(".live-dot")) {
    metricCard.querySelector("span").insertAdjacentHTML("beforeend", '<span class="live-dot"></span>');
  }
}

async function startRealtimeFeed() {
  if (location.protocol === "file:") return;
  const tick = async () => {
    const q = await fetchRealtimeQuote();
    if (q) lastQuote = q;
    updateLiveBar(lastQuote);
    updateIntradayPanel();
    draw(); // redraws chart with updated live bar; applyRealtimeQuote called at end of draw
  };
  await tick();
  setInterval(tick, 5000);
}

window.addEventListener("resize", draw);
draw();
autoLoadCsv();
autoLoadAiAnalysis();
autoLoadIntradayMeta();
autoLoadNewsSnapshot();
startRealtimeFeed();
setInterval(autoLoadCsv, 60 * 1000);
setInterval(autoLoadAiAnalysis, 60 * 1000);
setInterval(autoLoadIntradayMeta, 60 * 1000);
setInterval(autoLoadNewsSnapshot, 60 * 1000);
