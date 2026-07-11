// ── Dual-symbol config ─────────────────────────────────────
const SYMBOL_LABELS = {
  P0: { code: "P0", name: "棕榈油", emoji: "🌴", exchange: "DCE", sinaNode: "zly_qh" },
  Y0: { code: "Y0", name: "豆油",   emoji: "🌱", exchange: "DCE", sinaNode: "dy_qh" },
};
function activeLabel() { return SYMBOL_LABELS[state.activeSymbol] || SYMBOL_LABELS.P0; }
function siblingSymbol() { return state.activeSymbol === "P0" ? "Y0" : "P0"; }
function siblingLabel() { return SYMBOL_LABELS[siblingSymbol()]; }
function dataPath(filename) {
  return `data/${state.activeSymbol.toLowerCase()}/${filename}`;
}

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
  topbarTitle: document.getElementById("topbarTitle"),
  eyebrowText: document.getElementById("eyebrowText"),
  contractPill: document.getElementById("contractPill"),
  contractMapping: document.getElementById("contractMapping"),
  contractMappingStatus: document.getElementById("contractMappingStatus"),
  mappingEvidence: document.getElementById("mappingEvidence"),
  mappingMarketTime: document.getElementById("mappingMarketTime"),
  mainContractPrice: document.getElementById("mainContractPrice"),
  mainContractChange: document.getElementById("mainContractChange"),
  mainOpenInterest: document.getElementById("mainOpenInterest"),
  mainOpenInterestShare: document.getElementById("mainOpenInterestShare"),
  secondarySpread: document.getElementById("secondarySpread"),
  secondaryOpenInterest: document.getElementById("secondaryOpenInterest"),
  rollRisk: document.getElementById("rollRisk"),
  rollRiskReason: document.getElementById("rollRiskReason"),
  contractSpec: document.getElementById("contractSpec"),
  contractRuleRef: document.getElementById("contractRuleRef"),
  contractBridgeFreshness: document.getElementById("contractBridgeFreshness"),
  symBtns: document.querySelectorAll(".sym-btn"),
  siblingLink: document.getElementById("siblingLink"),
  siblingEmoji: document.getElementById("siblingEmoji"),
  siblingName: document.getElementById("siblingName"),
  siblingPrice: document.getElementById("siblingPrice"),
  siblingChange: document.getElementById("siblingChange"),
  siblingBias: document.getElementById("siblingBias"),
  boll1hStatus: document.getElementById("boll1hStatus"),
  boll1hDetail: document.getElementById("boll1hDetail"),
  boll2hStatus: document.getElementById("boll2hStatus"),
  boll2hDetail: document.getElementById("boll2hDetail"),
  boll4hStatus: document.getElementById("boll4hStatus"),
  boll4hDetail: document.getElementById("boll4hDetail"),
  boll2dStatus: document.getElementById("boll2dStatus"),
  boll2dDetail: document.getElementById("boll2dDetail"),
  multiStrategyCards: document.getElementById("multiStrategyCards"),
  intradayStrategyBias: document.getElementById("intradayStrategyBias"),
  intradayStrategyText: document.getElementById("intradayStrategyText"),
  newsRealtimeStatus: document.getElementById("newsRealtimeStatus"),
  newsRealtimeText: document.getElementById("newsRealtimeText"),
  newsTickerToggle: document.getElementById("newsTickerToggle"),
  newsTickerSection: document.getElementById("newsTickerSection"),
  newsTickerList: document.getElementById("newsTickerList"),
  newsTickerMeta: document.getElementById("newsTickerMeta"),
  lastPrice: document.getElementById("lastPrice"),
  lastChange: document.getElementById("lastChange"),
  lastDistance: document.getElementById("lastDistance"),
  themeToggleBtn: document.getElementById("themeToggleBtn"),
  marketBanner: document.getElementById("marketBanner"),
  sessionClock: document.getElementById("sessionClock"),
  tradeGate: document.getElementById("tradeGate"),
  tradeGateReason: document.getElementById("tradeGateReason"),
  tradeGateFactors: document.getElementById("tradeGateFactors"),
  marketRegime: document.getElementById("marketRegime"),
  regimeDetail: document.getElementById("regimeDetail"),
  nearestSupport: document.getElementById("nearestSupport"),
  nearestResistance: document.getElementById("nearestResistance"),
  levelContext: document.getElementById("levelContext"),
  dataConfidence: document.getElementById("dataConfidence"),
  dataConfidenceDetail: document.getElementById("dataConfidenceDetail"),
  planAsOf: document.getElementById("planAsOf"),
  longSetupStatus: document.getElementById("longSetupStatus"),
  longSetupEntry: document.getElementById("longSetupEntry"),
  longSetupTrigger: document.getElementById("longSetupTrigger"),
  longSetupStop: document.getElementById("longSetupStop"),
  longSetupTarget1: document.getElementById("longSetupTarget1"),
  longSetupTarget2: document.getElementById("longSetupTarget2"),
  longSetupRR: document.getElementById("longSetupRR"),
  shortSetupStatus: document.getElementById("shortSetupStatus"),
  shortSetupEntry: document.getElementById("shortSetupEntry"),
  shortSetupTrigger: document.getElementById("shortSetupTrigger"),
  shortSetupStop: document.getElementById("shortSetupStop"),
  shortSetupTarget1: document.getElementById("shortSetupTarget1"),
  shortSetupTarget2: document.getElementById("shortSetupTarget2"),
  shortSetupRR: document.getElementById("shortSetupRR"),
  noTradeStatus: document.getElementById("noTradeStatus"),
  noTradeZone: document.getElementById("noTradeZone"),
  noTradeReason: document.getElementById("noTradeReason"),
  planQuality: document.getElementById("planQuality"),
  planQualityDetail: document.getElementById("planQualityDetail"),
  modelMethod: document.getElementById("modelMethod"),
  modelStatus: document.getElementById("modelStatus"),
  modelTrades: document.getElementById("modelTrades"),
  modelSplitDate: document.getElementById("modelSplitDate"),
  modelExpectancy: document.getElementById("modelExpectancy"),
  modelProfitFactor: document.getElementById("modelProfitFactor"),
  modelDrawdown: document.getElementById("modelDrawdown"),
  modelWinRate: document.getElementById("modelWinRate"),
  modelDirectionCount: document.getElementById("modelDirectionCount"),
  modelVerdict: document.getElementById("modelVerdict"),
  modelLimitations: document.getElementById("modelLimitations"),
  aiNewsEmpty: document.getElementById("aiNewsEmpty"),
  aiStrategyEmpty: document.getElementById("aiStrategyEmpty"),
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
  aiFreshness: document.getElementById("aiFreshness"),
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
  aiRisk: document.getElementById("aiRisk"),
  aiAccuracy: document.getElementById("aiAccuracy"),
  alignScore: document.getElementById("alignScore"),
  alignScoreLabel: document.getElementById("alignScoreLabel"),
  overseasGrid: document.getElementById("overseasGrid"),
  overseasMeta: document.getElementById("overseasMeta"),
  askInput: document.getElementById("askInput"),
  askBtn: document.getElementById("askBtn"),
  askStatus: document.getElementById("askStatus"),
  askResponse: document.getElementById("askResponse"),
  askResponseMeta: document.getElementById("askResponseMeta"),
  askResponseText: document.getElementById("askResponseText"),
  posCapital: document.getElementById("posCapital"),
  posRisk: document.getElementById("posRisk"),
  posMaxMargin: document.getElementById("posMaxMargin"),
  posDirection: document.getElementById("posDirection"),
  posEntry: document.getElementById("posEntry"),
  posStop: document.getElementById("posStop"),
  posTarget: document.getElementById("posTarget"),
  posSlippage: document.getElementById("posSlippage"),
  posMult: document.getElementById("posMult"),
  posMargin: document.getElementById("posMargin"),
  posRiskBudget: document.getElementById("posRiskBudget"),
  posPerLotRisk: document.getElementById("posPerLotRisk"),
  posRiskLots: document.getElementById("posRiskLots"),
  posMarginLots: document.getElementById("posMarginLots"),
  posLotsRec: document.getElementById("posLotsRec"),
  posMarginUse: document.getElementById("posMarginUse"),
  posMarginUsePct: document.getElementById("posMarginUsePct"),
  posRR: document.getElementById("posRR"),
  posGap: document.getElementById("posGap"),
  posTargetPnl: document.getElementById("posTargetPnl"),
  posWarning: document.getElementById("posWarning")
};

function readColors() {
  const s = getComputedStyle(document.documentElement);
  return {
    up:   (s.getPropertyValue("--up").trim())   || "#cf3f35",
    down: (s.getPropertyValue("--down").trim()) || "#168f6a",
    grid: (s.getPropertyValue("--line").trim()) || "#e3e8df",
    text: (s.getPropertyValue("--muted").trim())|| "#66716a",
    ma: ["#c18c2d", "#326fb7", "#7657a8"]
  };
}

function initialActiveSymbol() {
  let saved = null;
  try { saved = localStorage.getItem("activeSymbol"); } catch (_) {}
  return (saved === "Y0" || saved === "P0") ? saved : "P0";
}

let state = {
  activeSymbol: initialActiveSymbol(),
  data: makeDemoData(),
  imported: false,
  autoLoaded: false,
  dataMeta: null,
  intradayMeta: null,
  newsSnapshot: null,
  hoverIndex: null,
  chartGeometry: null,
  visibleStart: null,
  visibleCount: null,
  sibling: null,
  contractBridge: null,
  modelValidation: null,
  isDragging: false,
  dragStartX: null,
  dragStartVisibleStart: null,
  decisionModel: null
};

// ── Theme (dark/light) ─────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  if (els.themeToggleBtn) {
    els.themeToggleBtn.textContent = theme === "dark" ? "☀️" : "🌙";
  }
}

function initTheme() {
  let saved = null;
  try { saved = localStorage.getItem("theme"); } catch (_) {}
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme = saved || (prefersDark ? "dark" : "light");
  applyTheme(theme);
}

function toggleTheme() {
  const cur = document.documentElement.dataset.theme || "light";
  const next = cur === "dark" ? "light" : "dark";
  applyTheme(next);
  try { localStorage.setItem("theme", next); } catch (_) {}
  draw();
}

// ── Market status ──────────────────────────────────────────
// Explicit Beijing time via Intl. No more UTC-offset math — one source of
// truth, correct regardless of the browser's local timezone (or DST changes
// anywhere in the world). Returns {weekday: 0-6 with 0=Sun, minutes: 0-1439}.
function bjParts() {
  const fmt = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Shanghai",
    weekday: "short",   // Sun/Mon/Tue/Wed/Thu/Fri/Sat
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  const parts = Object.fromEntries(
    fmt.formatToParts(new Date()).map(p => [p.type, p.value])
  );
  const wdMap = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  const hour24 = parts.hour === "24" ? 0 : parseInt(parts.hour, 10);
  return {
    weekday: wdMap[parts.weekday] ?? 0,
    hour: hour24,
    minute: parseInt(parts.minute, 10),
    minutes: hour24 * 60 + parseInt(parts.minute, 10),
  };
}

function bjWeekday()      { return bjParts().weekday; }
function bjMinutesOfDay() { return bjParts().minutes; }

// DCE palm oil (P0) + soybean oil (Y0) trading hours per user spec:
//   工作日早盘   09:00 – 11:30
//   工作日午盘   13:30 – 15:00
//   工作日夜盘   21:00 – 23:00
// Weekend = fully closed. Off-hours weekdays = 'closed'.
// Returns one of: 'day-open' | 'day-break' | 'night-open' | 'weekend' | 'closed'
function marketStatus() {
  const { weekday: wd, minutes: m } = bjParts();
  if (wd === 0 || wd === 6) return "weekend";
  const inMorning   = m >= 9 * 60 && m < 11 * 60 + 30;
  const inAfternoon = m >= 13 * 60 + 30 && m < 15 * 60;
  const inNight     = m >= 21 * 60 && m < 23 * 60;
  const inLunch     = m >= 11 * 60 + 30 && m < 13 * 60 + 30;
  if (inMorning || inAfternoon) return "day-open";
  if (inNight) return "night-open";
  if (inLunch) return "day-break";
  return "closed";
}

function updateMarketStatus() {
  const status = marketStatus();
  const statusLabels = {
    "day-open": "日盘交易中",
    "night-open": "夜盘交易中",
    "day-break": "午间休市",
    weekend: "周末休市",
    closed: "非交易时段",
  };
  if (els.sessionClock) {
    const clock = new Date().toLocaleTimeString("zh-CN", {
      timeZone: "Asia/Shanghai",
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    els.sessionClock.textContent = `北京时间 ${clock} · ${statusLabels[status]}`;
  }
  // Update the pulse indicator
  const liveInd = document.querySelector(".live-indicator");
  if (liveInd) {
    liveInd.classList.remove("market-closed", "market-weekend");
    const labelEl = liveInd.querySelector(".live-label");
    let label = "实时";
    if (status === "weekend") { liveInd.classList.add("market-weekend"); label = "休市"; }
    else if (status === "closed" || status === "day-break") { liveInd.classList.add("market-closed"); label = "非交易时段"; }
    if (labelEl) labelEl.textContent = label;
  }

  if (!els.marketBanner) return;
  if (status === "day-open" || status === "night-open") {
    els.marketBanner.hidden = true;
    els.marketBanner.classList.remove("weekend");
    return;
  }
  els.marketBanner.hidden = false;
  if (status === "weekend") {
    els.marketBanner.classList.add("weekend");
    els.marketBanner.textContent = "周末休市。周五夜盘会按下一个交易日归属，页面中的未来交易日标签不代表未来行情。";
  } else if (status === "day-break") {
    els.marketBanner.classList.remove("weekend");
    els.marketBanner.textContent = "午间休市（11:30-13:30），日盘 13:30 继续，夜盘 21:00-23:00。";
  } else {
    els.marketBanner.classList.remove("weekend");
    els.marketBanner.textContent = "非交易时段。日盘 09:00-11:30 / 13:30-15:00，夜盘 21:00-23:00。";
  }
}

function setLoadStatus(status, detail = "") {
  if (!els.dataStatus || !els.dataFreshness) return;
  els.dataStatus.textContent = status;
  els.dataStatus.className = status === "真实CSV" ? "quality-good" : status === "加载失败" ? "quality-bad" : "";
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
  if (state.visibleStart !== null && state.visibleCount !== null) {
    const start = Math.max(0, Math.min(state.data.length - 1, state.visibleStart));
    const end = Math.min(state.data.length, start + state.visibleCount);
    return state.data.slice(start, end);
  }
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

// Aggregate daily bars into 2-day bars. Skip any in-progress preliminary bar.
function aggregateTo2Day(daily) {
  const completed = daily.filter((r) => !r.preliminary);
  const result = [];
  // Walk from latest backwards so the most recent 2-day bar always ends at
  // the latest complete day (the leftover odd bar gets dropped at the start).
  for (let i = completed.length - 1; i > 0; i -= 2) {
    const second = completed[i];
    const first  = completed[i - 1];
    result.unshift({
      date: second.date,
      open: first.open,
      close: second.close,
      high: Math.max(first.high, second.high),
      low:  Math.min(first.low,  second.low),
      volume: (first.volume || 0) + (second.volume || 0),
    });
  }
  return result;
}

// Build a 2-day meta object with the same shape as one_hour/two_hour
// in intraday_meta.json so it can drive the same panels & fallback logic.
function compute2DayMeta(daily) {
  const bars = aggregateTo2Day(daily);
  if (bars.length < 20) return null;
  const closes = bars.map((b) => b.close);
  const last = bars[bars.length - 1];
  const period = 20;
  const window = closes.slice(-period);
  const mid = mean(window);
  const sd  = stddev(window);
  const upper = mid + 2 * sd;
  const lower = mid - 2 * sd;
  const prevClose = bars.length >= 2 ? bars[bars.length - 2].close : last.open;
  const change = (last.close - prevClose) / prevClose;
  return {
    label: "2日",
    latest_time: last.date,
    open: last.open,
    high: last.high,
    low: last.low,
    close: last.close,
    change_pct: `${change > 0 ? "+" : ""}${(change * 100).toFixed(2)}%`,
    volume: last.volume,
    rsi14: rsi(bars, 14),
    bollinger: { period, upper, mid, lower, bandWidth: mid ? (4 * sd) / mid : 0 },
  };
}

// Compute a bollinger-based meta for the daily timeframe straight from
// state.data so the multi-strategy panel has all 4 timeframes.
function computeDailyMeta(daily) {
  const bars = daily.filter((r) => !r.preliminary);
  if (bars.length < 20) return null;
  const closes = bars.map((b) => b.close);
  const period = 20;
  const window = closes.slice(-period);
  const mid = mean(window);
  const sd  = stddev(window);
  const last = bars[bars.length - 1];
  const prev = bars[bars.length - 2] || last;
  const change = (last.close - prev.close) / prev.close;
  return {
    label: "日线",
    latest_time: last.date,
    open: last.open, high: last.high, low: last.low, close: last.close,
    change_pct: `${change > 0 ? "+" : ""}${(change * 100).toFixed(2)}%`,
    volume: last.volume,
    rsi14: rsi(bars, 14),
    bollinger: { period, upper: mid + 2 * sd, mid, lower: mid - 2 * sd, bandWidth: mid ? (4 * sd) / mid : 0 },
  };
}

// Build a bias/entry/stop/take_profit/invalidation block for any timeframe
// that has a bollinger {upper, mid, lower} + a close price.
function strategyForTimeframe(meta, label) {
  if (!meta || !meta.bollinger) return null;
  const b = meta.bollinger;
  const close = meta.close;
  if (!Number.isFinite(b.upper) || !Number.isFinite(b.lower) || !Number.isFinite(b.mid)) return null;

  let bias, biasKind, entry, stop, takeProfit, invalidation;

  if (close > b.upper) {
    bias = "突破上轨"; biasKind = "up";
    entry  = `回踩中轨 ${b.mid.toFixed(0)} 不破再加多`;
    stop   = `跌破 ${b.mid.toFixed(0)}`;
    takeProfit = `观察上轨外延伸，目标 +1.5×带宽`;
    invalidation = `收盘回到中轨 ${b.mid.toFixed(0)} 下方`;
  } else if (close > b.mid) {
    bias = "中轨上方"; biasKind = "up";
    entry  = `回踩中轨 ${b.mid.toFixed(0)} 不破入场`;
    stop   = `跌破下轨 ${b.lower.toFixed(0)}`;
    takeProfit = `上轨 ${b.upper.toFixed(0)}`;
    invalidation = `跌破中轨 ${b.mid.toFixed(0)} 视为失败`;
  } else if (close > b.lower) {
    bias = "中轨下方"; biasKind = "down";
    entry  = `反弹至中轨 ${b.mid.toFixed(0)} 受阻空`;
    stop   = `突破上轨 ${b.upper.toFixed(0)}`;
    takeProfit = `下轨 ${b.lower.toFixed(0)}`;
    invalidation = `站稳中轨 ${b.mid.toFixed(0)} 视为失败`;
  } else {
    bias = "跌破下轨"; biasKind = "down";
    entry  = `反弹至 ${b.mid.toFixed(0)} 受阻空`;
    stop   = `突破 ${b.mid.toFixed(0)}`;
    takeProfit = `下轨外延伸，目标 -1.5×带宽`;
    invalidation = `收盘回到中轨 ${b.mid.toFixed(0)} 上方`;
  }

  // RSI overlay — soften bias if RSI contradicts
  const r = meta.rsi14;
  let rsiNote = "";
  if (Number.isFinite(r)) {
    if (biasKind === "up" && r > 72) rsiNote = ` · RSI ${r.toFixed(0)} 偏热`;
    else if (biasKind === "down" && r < 28) rsiNote = ` · RSI ${r.toFixed(0)} 偏冷`;
    else rsiNote = ` · RSI ${r.toFixed(0)}`;
  }

  return {
    label, bias, biasKind, entry, stop, take_profit: takeProfit, invalidation,
    rsiNote,
    price: close,
    changePct: meta.change_pct || "",
    upper: b.upper,
    mid: b.mid,
    lower: b.lower,
    bandWidth: Number(b.band_width ?? b.bandWidth ?? 0),
    rsi: Number(meta.rsi14),
  };
}

function renderMultiStrategyPanel() {
  if (!els.multiStrategyCards) return;
  const intraday = state.intradayMeta;
  const daily = computeDailyMeta(state.data || []);
  const tf2d = compute2DayMeta(state.data || []);

  const strategies = [
    intraday?.one_hour  ? strategyForTimeframe(intraday.one_hour,  "1 小时") : null,
    intraday?.two_hour  ? strategyForTimeframe(intraday.two_hour,  "2 小时") : null,
    intraday?.four_hour ? strategyForTimeframe(intraday.four_hour, "4 小时") : null,
    tf2d  ? strategyForTimeframe(tf2d,  "2 日")  : null,
    daily ? strategyForTimeframe(daily, "日线") : null,
  ].filter(Boolean);

  if (strategies.length === 0) {
    els.multiStrategyCards.innerHTML = `<div class="tf-card"><div class="tf-label">等待数据...</div></div>`;
    return;
  }

  els.multiStrategyCards.innerHTML = strategies.map((s) => `
    <div class="tf-card">
      <div class="tf-card-head">
        <span class="tf-label">${escapeHtml(s.label)}</span>
        <span class="tf-bias ${s.biasKind}">${escapeHtml(s.bias)}</span>
      </div>
      <div class="tf-price">${s.price.toFixed(0)} <span class="${/^\+/.test(s.changePct)?'up':/^-/.test(s.changePct)?'down':''}">${escapeHtml(s.changePct)}</span>${escapeHtml(s.rsiNote)}</div>
      <div class="tf-rows">
        <div class="row"><span>中轨</span><span>${s.mid.toFixed(0)}</span></div>
        <div class="row"><span>通道</span><span>${s.lower.toFixed(0)}-${s.upper.toFixed(0)}</span></div>
        <div class="row"><span>带宽</span><span>${formatPct(s.bandWidth)}</span></div>
        <div class="row"><span>纪律</span><span>${escapeHtml(s.invalidation)}</span></div>
      </div>
    </div>
  `).join("");
  renderAlignmentScore();
}

// ── Multi-timeframe alignment score (0-100) ────────────────
// Reads price position vs bollinger for daily / 2D / 2H / 1H,
// weights by timeframe importance, and normalizes to 0-100.
function computeAlignmentScore() {
  const daily  = computeDailyMeta(state.data || []);
  const twoD   = compute2DayMeta(state.data || []);
  const fourH  = state.intradayMeta ? state.intradayMeta.four_hour : null;
  const twoH   = state.intradayMeta ? state.intradayMeta.two_hour  : null;
  const oneH   = state.intradayMeta ? state.intradayMeta.one_hour  : null;

  // Given a meta with bollinger + close + rsi14, return the raw [-2, +2]
  // position score adjusted for RSI extremes.
  const rawFor = (m) => {
    if (!m || !m.bollinger) return null;
    const b = m.bollinger;
    const close = m.close;
    if (!Number.isFinite(close) || !Number.isFinite(b.upper) || !Number.isFinite(b.mid) || !Number.isFinite(b.lower)) {
      return null;
    }
    let raw;
    if (close > b.upper)      raw = 2;
    else if (close > b.mid)   raw = 1;
    else if (close < b.lower) raw = -2;
    else                       raw = -1;
    const r = m.rsi14;
    if (Number.isFinite(r)) {
      if (r > 70 && raw > 0) raw -= 0.5;
      if (r < 30 && raw < 0) raw += 0.5;
    }
    return raw;
  };

  const entries = [
    { m: daily, weight: 3 },
    { m: twoD,  weight: 2 },
    { m: fourH, weight: 1.75 },  // between 2D and 2H — swing horizon
    { m: twoH,  weight: 1.5 },
    { m: oneH,  weight: 1 },
  ].map((e) => ({ raw: rawFor(e.m), weight: e.weight }))
    .filter((e) => Number.isFinite(e.raw));

  if (entries.length === 0) return null;

  const wsum = entries.reduce((s, e) => s + e.weight, 0);
  const combined = entries.reduce((s, e) => s + e.raw * e.weight, 0) / wsum;
  const score = 50 + combined * 25;
  return Math.max(0, Math.min(100, score));
}

function renderAlignmentScore() {
  if (!els.alignScore || !els.alignScoreLabel) return;
  const score = computeAlignmentScore();
  if (score === null) {
    els.alignScore.textContent = "--";
    els.alignScore.className = "";
    els.alignScoreLabel.textContent = "--";
    return;
  }
  els.alignScore.textContent = Math.round(score);
  let label, cls;
  if (score > 75)      { label = "强烈偏多"; cls = "up"; }
  else if (score > 60) { label = "偏多";     cls = "up"; }
  else if (score >= 40) { label = "中性";     cls = ""; }
  else if (score >= 25) { label = "偏空";     cls = "down"; }
  else                  { label = "强烈偏空"; cls = "down"; }
  els.alignScore.className = cls;
  els.alignScoreLabel.textContent = label;
  els.alignScoreLabel.className = cls;
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
  const upCount = recent20.filter((item) => item > 0).length;
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
  const adx14 = adx(data, 14);
  const efficiency20 = efficiencyRatio(data, 20);
  const volPercentile = realizedVolPercentile(data, 20);

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
    winRate: upCount / Math.max(1, recent20.length),
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
    adx14,
    efficiency20,
    volPercentile,
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

function clamp(value, minValue, maxValue) {
  return Math.max(minValue, Math.min(maxValue, value));
}

function ageMinutes(value) {
  if (!value) return null;
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return null;
  return Math.max(0, (Date.now() - timestamp) / 60000);
}

function humanAge(minutes) {
  if (!Number.isFinite(minutes)) return "未知";
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${Math.round(minutes)} 分钟前`;
  if (minutes < 1440) return `${(minutes / 60).toFixed(minutes < 360 ? 1 : 0)} 小时前`;
  return `${(minutes / 1440).toFixed(1)} 天前`;
}

function efficiencyRatio(data, lookback = 20) {
  if (!Array.isArray(data) || data.length < 3) return null;
  const rows = data.slice(-(lookback + 1));
  if (rows.length < 3) return null;
  const net = Math.abs(rows.at(-1).close - rows[0].close);
  const path = rows.slice(1).reduce((sum, row, index) => {
    return sum + Math.abs(row.close - rows[index].close);
  }, 0);
  return path > 0 ? net / path : 0;
}

function adx(data, period = 14) {
  if (!Array.isArray(data) || data.length < period + 3) return null;
  const tr = [];
  const plusDm = [];
  const minusDm = [];
  for (let i = 1; i < data.length; i += 1) {
    const current = data[i];
    const previous = data[i - 1];
    const upMove = current.high - previous.high;
    const downMove = previous.low - current.low;
    plusDm.push(upMove > downMove && upMove > 0 ? upMove : 0);
    minusDm.push(downMove > upMove && downMove > 0 ? downMove : 0);
    tr.push(Math.max(
      current.high - current.low,
      Math.abs(current.high - previous.close),
      Math.abs(current.low - previous.close),
    ));
  }
  const dx = [];
  for (let end = period - 1; end < tr.length; end += 1) {
    const start = end - period + 1;
    const atrWindow = mean(tr.slice(start, end + 1));
    if (!(atrWindow > 0)) continue;
    const plusDi = 100 * mean(plusDm.slice(start, end + 1)) / atrWindow;
    const minusDi = 100 * mean(minusDm.slice(start, end + 1)) / atrWindow;
    const sumDi = plusDi + minusDi;
    if (sumDi > 0) dx.push(100 * Math.abs(plusDi - minusDi) / sumDi);
  }
  if (!dx.length) return null;
  return mean(dx.slice(-period));
}

function realizedVolPercentile(data, period = 20) {
  if (!Array.isArray(data) || data.length < period + 5) return null;
  const returns = data.slice(1).map((row, index) => {
    const previous = data[index].close;
    return previous > 0 ? Math.log(row.close / previous) : 0;
  });
  const samples = [];
  for (let end = period; end <= returns.length; end += 1) {
    samples.push(stddev(returns.slice(end - period, end)));
  }
  if (!samples.length) return null;
  const current = samples.at(-1);
  return samples.filter((value) => value <= current).length / samples.length * 100;
}

function rowsFromMeta(meta) {
  const rows = Array.isArray(meta?.last_30_bars) ? meta.last_30_bars : [];
  return rows.map((row) => ({
    open: Number(row.open),
    high: Number(row.high),
    low: Number(row.low),
    close: Number(row.close),
    volume: Number(row.volume || 0),
  })).filter((row) => [row.open, row.high, row.low, row.close].every(Number.isFinite));
}

function atrFromMeta(meta, fallback) {
  const value = atr(rowsFromMeta(meta), 14);
  if (Number.isFinite(value) && value > 0) return value;
  const boll = meta?.bollinger;
  if (boll && Number.isFinite(Number(boll.upper)) && Number.isFinite(Number(boll.lower))) {
    return Math.max(2, (Number(boll.upper) - Number(boll.lower)) / 4);
  }
  return fallback;
}

function signalForMeta(meta, currentPrice = null) {
  if (!meta?.bollinger) return null;
  const boll = meta.bollinger;
  const close = Number.isFinite(currentPrice) ? currentPrice : Number(meta.close);
  const halfBand = Math.max(1, (Number(boll.upper) - Number(boll.lower)) / 2);
  const position = clamp((close - Number(boll.mid)) / halfBand, -1.5, 1.5);
  const rsiValue = Number(meta.rsi14);
  const rsiComponent = Number.isFinite(rsiValue) ? clamp((rsiValue - 50) / 35, -1, 1) : 0;
  const rows = rowsFromMeta(meta);
  const tfAtr = atrFromMeta(meta, halfBand / 2);
  const slope = rows.length >= 6 && tfAtr > 0
    ? clamp((rows.at(-1).close - rows.at(-6).close) / (tfAtr * 2), -1, 1)
    : 0;
  return clamp((position * 0.55 + rsiComponent * 0.2 + slope * 0.25) * 70, -100, 100);
}

function assessAiFreshness(ai) {
  const generatedAge = ageMinutes(ai?.generated_at_utc);
  const generatedMs = Date.parse(ai?.generated_at_utc || "");
  const dataTimes = [state.dataMeta?.updated_at_utc, state.intradayMeta?.updated_at_utc]
    .map((value) => Date.parse(value || ""))
    .filter(Number.isFinite);
  const latestDataMs = dataTimes.length ? Math.max(...dataTimes) : null;
  const lagMinutes = Number.isFinite(generatedMs) && Number.isFinite(latestDataMs)
    ? Math.max(0, (latestDataMs - generatedMs) / 60000)
    : null;
  const status = marketStatus();
  const trading = status === "day-open" || status === "night-open";
  const maxAge = trading ? 240 : 1440;
  const maxLag = trading ? 90 : 720;
  const fresh = ai?.status === "ok"
    && Number.isFinite(generatedAge)
    && generatedAge <= maxAge
    && (!Number.isFinite(lagMinutes) || lagMinutes <= maxLag);
  let label = "AI 时间未知";
  if (Number.isFinite(generatedAge)) {
    if (fresh && trading) label = `AI 可执行 · ${humanAge(generatedAge)}`;
    else if (fresh) label = `休市参考 · ${humanAge(generatedAge)}`;
    else label = `AI 已过期 · ${humanAge(generatedAge)}`;
  }
  return { fresh, trading, generatedAge, lagMinutes, label };
}

function computeDataConfidence(analysis) {
  let score = 100;
  const reasons = [];
  const status = marketStatus();
  const trading = status === "day-open" || status === "night-open";
  const weekend = status === "weekend";
  const dailyAge = Math.max(0, Number(analysis.staleDays || 0));
  const intradayAge = ageMinutes(state.intradayMeta?.updated_at_utc);
  const newsAge = ageMinutes(state.newsSnapshot?.updated_at_utc);
  const bridgeAge = ageMinutes(state.contractBridge?.updated_at_utc);
  const quoteAge = lastQuote?.receivedAt ? Math.max(0, (Date.now() - lastQuote.receivedAt) / 60000) : null;
  const aiFreshness = assessAiFreshness(state.lastAi);

  if (!state.autoLoaded || !state.dataMeta) {
    score -= 40;
    reasons.push("当前不是自动真实数据");
  }
  if (dailyAge > (weekend ? 4 : 2)) {
    score -= 24;
    reasons.push(`日线距今 ${dailyAge} 天`);
  }
  if (trading) {
    if (!Number.isFinite(quoteAge)) {
      score -= 25;
      reasons.push("实时行情未接通");
    } else if (quoteAge > 1.5) {
      score -= 20;
      reasons.push(`实时报价 ${humanAge(quoteAge)}`);
    }
    if (!Number.isFinite(intradayAge) || intradayAge > 120) {
      score -= 18;
      reasons.push("小时线后台快照偏旧");
    }
    if (!state.contractBridge?.main) {
      score -= 20;
      reasons.push("可交易主力月份未确认");
    } else if (state.contractBridge.mapping_verified !== true) {
      score -= 15;
      reasons.push("连续与主力映射需复核");
    } else if (!Number.isFinite(bridgeAge) || bridgeAge > 15) {
      score -= 10;
      reasons.push("主力映射快照偏旧");
    }
  } else if (Number.isFinite(intradayAge) && intradayAge > 4320) {
    score -= 12;
    reasons.push("小时线超过 3 天未更新");
  }
  if (Number.isFinite(newsAge) && newsAge > (trading ? 720 : 1440)) {
    score -= 8;
    reasons.push("舆情快照偏旧");
  }
  if (state.lastAi && !aiFreshness.fresh) {
    score -= 5;
    reasons.push("AI 仅作历史参考");
  }

  score = clamp(Math.round(score), 0, 100);
  const label = score >= 85 ? "高" : score >= 65 ? "中" : "低";
  return {
    score,
    label,
    reasons,
    intradayAge,
    newsAge,
    quoteAge,
    bridgeAge,
    aiFreshness,
  };
}

function classifyRegime(analysis, compositeSignal) {
  const adxValue = Number(analysis.adx14);
  const efficiency = Number(analysis.efficiency20);
  const volPct = Number(analysis.volPercentile);
  const highVol = Number.isFinite(volPct) ? volPct >= 75 : analysis.atrPct >= 0.02;
  const trending = (Number.isFinite(adxValue) && adxValue >= 24)
    || (Number.isFinite(efficiency) && efficiency >= 0.34);
  const direction = compositeSignal >= 18 ? "上行" : compositeSignal <= -18 ? "下行" : "无方向";

  let label;
  let kind;
  if (trending && direction === "无方向") { label = "趋势强度高 · 周期冲突"; kind = "neutral"; }
  else if (trending && highVol) { label = `高波动${direction}趋势`; kind = compositeSignal >= 0 ? "up" : "down"; }
  else if (trending) { label = `${direction}趋势`; kind = compositeSignal >= 0 ? "up" : "down"; }
  else if (highVol) { label = "高波动震荡"; kind = "neutral"; }
  else { label = "均值回归震荡"; kind = "neutral"; }

  const adxText = Number.isFinite(adxValue) ? `ADX ${adxValue.toFixed(0)}` : "ADX --";
  const volText = Number.isFinite(volPct) ? `波动分位 ${volPct.toFixed(0)}%` : `ATR ${formatPct(analysis.atrPct)}`;
  return { label, kind, trending, highVol, detail: `${adxText} · ${volText} · 共振 ${compositeSignal.toFixed(0)}` };
}

function clusterLevels(candidates, tolerance) {
  const sorted = candidates
    .filter((item) => Number.isFinite(item.value) && item.value > 0)
    .sort((a, b) => a.value - b.value);
  const clusters = [];
  sorted.forEach((item) => {
    const last = clusters.at(-1);
    if (last && Math.abs(item.value - last.value) <= tolerance) {
      last.sum += item.value * item.weight;
      last.weight += item.weight;
      last.value = last.sum / last.weight;
      if (!last.labels.includes(item.label)) last.labels.push(item.label);
    } else {
      clusters.push({
        value: item.value,
        sum: item.value * item.weight,
        weight: item.weight,
        labels: [item.label],
      });
    }
  });
  return clusters;
}

function computeKeyLevels(analysis, price, tfAtr) {
  const candidates = [];
  const add = (value, label, weight = 1) => candidates.push({ value: Number(value), label, weight });
  const addBoll = (meta, label, weight) => {
    const boll = meta?.bollinger;
    if (!boll) return;
    add(boll.lower, `${label}下轨`, weight);
    add(boll.mid, `${label}中轨`, weight + 0.2);
    add(boll.upper, `${label}上轨`, weight);
    add(meta.low20, `${label}前低`, weight);
    add(meta.high20, `${label}前高`, weight);
  };
  addBoll(state.intradayMeta?.one_hour, "1H", 1.2);
  addBoll(state.intradayMeta?.two_hour, "2H", 1.0);
  addBoll(state.intradayMeta?.four_hour, "4H", 1.5);
  add(analysis.boll.lower, "日线下轨", 1.5);
  add(analysis.boll.mid, "日线中轨", 1.7);
  add(analysis.boll.upper, "日线上轨", 1.5);
  add(analysis.ma20, "MA20", 1.5);
  add(analysis.low20, "20日低点", 1.8);
  add(analysis.high20, "20日高点", 1.8);
  add(analysis.low60, "60日低点", 1.2);
  add(analysis.high60, "60日高点", 1.2);

  const aiFreshness = assessAiFreshness(state.lastAi);
  if (state.lastAi?.watch_levels && aiFreshness.fresh) {
    add(state.lastAi.watch_levels.support, "AI支撑", 0.8);
    add(state.lastAi.watch_levels.resistance, "AI压力", 0.8);
  }

  const clusters = clusterLevels(candidates, Math.max(6, tfAtr * 0.14));
  const supports = clusters.filter((item) => item.value < price - 1);
  const resistances = clusters.filter((item) => item.value > price + 1);
  const support = supports.at(-1) || { value: price - tfAtr, labels: ["ATR支撑"] };
  const nextSupport = supports.at(-2) || { value: support.value - tfAtr, labels: ["下一支撑"] };
  const resistance = resistances[0] || { value: price + tfAtr, labels: ["ATR压力"] };
  const nextResistance = resistances[1] || { value: resistance.value + tfAtr, labels: ["下一压力"] };
  return { support, nextSupport, resistance, nextResistance, clusters };
}

function roundToTick(value, tick = Number(activeContractSpecs().tick_size || 1)) {
  return Math.round(value / tick) * tick;
}

function buildDirectionalSetup(direction, context) {
  const { price, tfAtr, levels, compositeSignal, regime } = context;
  const isLong = direction === "long";
  const anchor = isLong ? levels.support.value : levels.resistance.value;
  const otherSide = isLong ? levels.resistance.value : levels.support.value;
  const nextOther = isLong ? levels.nextResistance.value : levels.nextSupport.value;
  const entryCenter = isLong ? anchor + tfAtr * 0.12 : anchor - tfAtr * 0.12;
  const entryLow = roundToTick(entryCenter - tfAtr * 0.08);
  const entryHigh = roundToTick(entryCenter + tfAtr * 0.08);
  const entry = (entryLow + entryHigh) / 2;
  let stop = isLong ? anchor - tfAtr * 0.32 : anchor + tfAtr * 0.32;
  const minRisk = tfAtr * 0.45;
  if (isLong && entry - stop < minRisk) stop = entry - minRisk;
  if (!isLong && stop - entry < minRisk) stop = entry + minRisk;
  stop = roundToTick(stop);
  const risk = Math.max(Number(activeContractSpecs().tick_size || 1) * 2, Math.abs(entry - stop));

  let target1 = otherSide;
  if (isLong && target1 <= entry + risk * 1.2) target1 = entry + risk * 1.2;
  if (!isLong && target1 >= entry - risk * 1.2) target1 = entry - risk * 1.2;
  let target2 = nextOther;
  if (isLong && target2 <= entry + risk * 2) target2 = entry + risk * 2;
  if (!isLong && target2 >= entry - risk * 2) target2 = entry - risk * 2;
  target1 = roundToTick(target1);
  target2 = roundToTick(target2);

  const reward1 = isLong ? target1 - entry : entry - target1;
  const reward2 = isLong ? target2 - entry : entry - target2;
  const rr1 = reward1 / risk;
  const rr2 = reward2 / risk;
  const aligned = isLong ? compositeSignal >= 20 : compositeSignal <= -20;
  const nearEntry = price >= entryLow - tfAtr * 0.12 && price <= entryHigh + tfAtr * 0.12;
  const status = aligned ? (nearEntry ? "接近触发" : "顺势等待") : "逆势备用";
  const statusClass = aligned ? (isLong ? "up" : "down") : "neutral";
  const trigger = regime.trending
    ? (isLong
      ? `${entryLow.toFixed(0)}-${entryHigh.toFixed(0)} 回踩后，15分钟重新收回并伴随量能确认`
      : `${entryLow.toFixed(0)}-${entryHigh.toFixed(0)} 反弹受阻后，15分钟重新跌回并伴随量能确认`)
    : (isLong
      ? `${entryLow.toFixed(0)}-${entryHigh.toFixed(0)} 出现止跌形态后再执行`
      : `${entryLow.toFixed(0)}-${entryHigh.toFixed(0)} 出现滞涨形态后再执行`);
  return {
    direction,
    entryLow,
    entryHigh,
    entry,
    stop,
    target1,
    target2,
    rr1,
    rr2,
    trigger,
    status,
    statusClass,
  };
}

function buildDecisionModel(analysis) {
  const price = Number.isFinite(lastQuote?.price)
    ? lastQuote.price
    : Number(state.intradayMeta?.one_hour?.close || analysis.last.close);
  const fallbackAtr = Math.max(12, Number(analysis.atr14 || 40) * 0.42);
  const tfAtr = Math.max(6, atrFromMeta(state.intradayMeta?.one_hour, fallbackAtr));
  const oneSignal = signalForMeta(state.intradayMeta?.one_hour, price);
  const twoSignal = signalForMeta(state.intradayMeta?.two_hour, price);
  const fourSignal = signalForMeta(state.intradayMeta?.four_hour, price);
  let dailySignal = (analysis.score - 50) * 1.35;
  if (analysis.last.close > analysis.ma20 && analysis.ma10 > analysis.ma20) dailySignal += 12;
  if (analysis.last.close < analysis.ma20 && analysis.ma10 < analysis.ma20) dailySignal -= 12;
  if (analysis.macdValue.hist > 0) dailySignal += 6;
  else dailySignal -= 6;
  dailySignal = clamp(dailySignal, -100, 100);

  const weighted = [
    [dailySignal, 0.35],
    [fourSignal, 0.30],
    [twoSignal, 0.15],
    [oneSignal, 0.20],
  ].filter(([value]) => Number.isFinite(value));
  const weightSum = weighted.reduce((sum, item) => sum + item[1], 0);
  const compositeSignal = weightSum
    ? weighted.reduce((sum, item) => sum + item[0] * item[1], 0) / weightSum
    : dailySignal;
  const regime = classifyRegime(analysis, compositeSignal);
  const confidence = computeDataConfidence(analysis);
  const levels = computeKeyLevels(analysis, price, tfAtr);

  const mids = [
    Number(state.intradayMeta?.one_hour?.bollinger?.mid),
    Number(state.intradayMeta?.two_hour?.bollinger?.mid),
    Number(state.intradayMeta?.four_hour?.bollinger?.mid),
    Number(analysis.boll.mid),
  ].filter(Number.isFinite);
  const center = mids.length ? mean(mids) : price;
  const halfZone = clamp(stddev(mids) + tfAtr * 0.12, tfAtr * 0.18, tfAtr * 0.55);
  const noTradeLow = roundToTick(center - halfZone);
  const noTradeHigh = roundToTick(center + halfZone);
  const inNoTradeZone = price >= noTradeLow && price <= noTradeHigh;

  const context = { price, tfAtr, levels, compositeSignal, regime };
  const longSetup = buildDirectionalSetup("long", context);
  const shortSetup = buildDirectionalSetup("short", context);
  const preferred = compositeSignal >= 0 ? longSetup : shortSetup;
  const preferredRr = Math.max(0, preferred.rr1);
  const qualityPenalty = (inNoTradeZone ? 15 : 0) + (preferredRr < 1.45 ? 8 : 0);
  const quality = clamp(Math.round(
    confidence.score * 0.45
      + (50 + Math.min(50, Math.abs(compositeSignal))) * 0.3
      + clamp(preferredRr / 2.5, 0, 1) * 25
      - qualityPenalty
  ), 0, 100);

  const status = marketStatus();
  let gate = { label: "仅条件单", kind: "neutral", reason: "等待价格离开均衡区并完成触发确认。" };
  if (status === "weekend") {
    gate = { label: "休市", kind: "neutral", reason: "市场关闭，当前计划只用于下个交易时段预案。" };
  } else if (status === "closed" || status === "day-break") {
    gate = { label: "等待开盘", kind: "neutral", reason: "非交易时段，不把静态报价当作可执行价格。" };
  } else if (!Number.isFinite(confidence.quoteAge) || confidence.quoteAge > 1.5) {
    gate = { label: "暂停交易", kind: "blocked", reason: "实时行情未接通或已经过期，不使用后台快照代替执行价格。" };
  } else if (!Number.isFinite(confidence.intradayAge) || confidence.intradayAge > 120) {
    gate = { label: "暂停交易", kind: "blocked", reason: "小时线后台快照超过两小时，等待刷新后再评估。" };
  } else if (confidence.score < 65) {
    gate = { label: "暂停交易", kind: "blocked", reason: "数据可信度不足，先恢复实时行情、主力映射或小时线快照。" };
  } else if (inNoTradeZone && Math.abs(compositeSignal) < 35) {
    gate = { label: "观望", kind: "neutral", reason: "价格处于多周期均衡区，方向优势不足。" };
  } else if (compositeSignal >= 25 && longSetup.rr1 >= 1.45) {
    gate = { label: "允许做多", kind: "up", reason: "多周期偏多且首目标盈亏比达到执行门槛，仍需触发确认。" };
  } else if (compositeSignal <= -25 && shortSetup.rr1 >= 1.45) {
    gate = { label: "允许做空", kind: "down", reason: "多周期偏空且首目标盈亏比达到执行门槛，仍需触发确认。" };
  }

  return {
    price,
    tfAtr,
    signals: { oneSignal, twoSignal, fourSignal, dailySignal, compositeSignal },
    regime,
    confidence,
    levels,
    noTradeLow,
    noTradeHigh,
    inNoTradeZone,
    longSetup,
    shortSetup,
    quality,
    gate,
  };
}

function renderSetup(setup, side) {
  const prefix = side === "long" ? "long" : "short";
  const statusEl = els[`${prefix}SetupStatus`];
  if (statusEl) {
    statusEl.textContent = setup.status;
    statusEl.className = `setup-status ${setup.statusClass}`;
  }
  els[`${prefix}SetupEntry`].textContent = `${setup.entryLow.toFixed(0)}-${setup.entryHigh.toFixed(0)}`;
  els[`${prefix}SetupTrigger`].textContent = setup.trigger;
  els[`${prefix}SetupStop`].textContent = setup.stop.toFixed(0);
  els[`${prefix}SetupTarget1`].textContent = setup.target1.toFixed(0);
  els[`${prefix}SetupTarget2`].textContent = setup.target2.toFixed(0);
  els[`${prefix}SetupRR`].textContent = `T1 ${setup.rr1.toFixed(1)}R · T2 ${setup.rr2.toFixed(1)}R`;
}

function renderDecisionCockpit(analysis) {
  if (!els.tradeGate) return;
  const model = buildDecisionModel(analysis);
  state.decisionModel = model;
  els.tradeGate.textContent = model.gate.label;
  els.tradeGate.className = `gate-pill ${model.gate.kind}`;
  els.tradeGateReason.textContent = model.gate.reason;
  const factorItems = [
    [`数据 ${model.confidence.score}`, model.confidence.score >= 85 ? "quality-good" : model.confidence.score < 65 ? "quality-bad" : ""],
    [`共振 ${model.signals.compositeSignal.toFixed(0)}`, model.signals.compositeSignal >= 20 ? "up" : model.signals.compositeSignal <= -20 ? "down" : ""],
    [`首目标 ${Math.max(model.longSetup.rr1, model.shortSetup.rr1).toFixed(1)}R`, ""],
    [model.inNoTradeZone ? "均衡区内" : "均衡区外", model.inNoTradeZone ? "" : "quality-good"],
  ];
  const baselineExpectancy = Number(state.modelValidation?.holdout?.expectancy_r);
  if (Number.isFinite(baselineExpectancy)) {
    const baselineKind = state.modelValidation?.status === "positive"
      ? "quality-good"
      : state.modelValidation?.status === "rejected" ? "quality-bad" : "";
    factorItems.push([`基准 ${baselineExpectancy >= 0 ? "+" : ""}${baselineExpectancy.toFixed(2)}R`, baselineKind]);
  }
  els.tradeGateFactors.innerHTML = factorItems.map(([text, kind]) => `<span class="${kind}">${escapeHtml(text)}</span>`).join("");

  els.marketRegime.textContent = model.regime.label;
  els.marketRegime.className = model.regime.kind;
  els.regimeDetail.textContent = model.regime.detail;
  els.nearestSupport.textContent = roundToTick(model.levels.support.value).toFixed(0);
  els.nearestResistance.textContent = roundToTick(model.levels.resistance.value).toFixed(0);
  els.levelContext.textContent = `距支撑 ${Math.max(0, model.price - model.levels.support.value).toFixed(0)} 点 · 距压力 ${Math.max(0, model.levels.resistance.value - model.price).toFixed(0)} 点`;
  els.dataConfidence.textContent = `${model.confidence.score} / 100 · ${model.confidence.label}`;
  els.dataConfidence.className = model.confidence.score >= 85 ? "quality-good" : model.confidence.score < 65 ? "quality-bad" : "";
  els.dataConfidenceDetail.textContent = model.confidence.reasons.length
    ? model.confidence.reasons.slice(0, 2).join(" · ")
    : "行情、小时线、AI 与舆情时间检查通过";

  renderSetup(model.longSetup, "long");
  renderSetup(model.shortSetup, "short");
  els.noTradeZone.textContent = `${model.noTradeLow.toFixed(0)}-${model.noTradeHigh.toFixed(0)}`;
  els.noTradeStatus.textContent = model.inNoTradeZone ? "区域内不追单" : "等待触发";
  els.noTradeReason.textContent = model.inNoTradeZone
    ? "当前位于多周期中轨密集区，先等价格离开后再判断方向。"
    : "不在计划入场区时不追价；止损失效后当日不在同方向立即重仓反手。";
  els.planQuality.textContent = `${model.quality} / 100`;
  els.planQuality.className = model.quality >= 75 ? "quality-good" : model.quality < 55 ? "quality-bad" : "";
  els.planQualityDetail.textContent = model.quality >= 75 ? "结构清晰" : model.quality >= 55 ? "等待确认" : "优势不足";
  const asOf = lastQuote?.tradedate && lastQuote?.ticktime
    ? formatMarketBarTime(`${lastQuote.tradedate} ${lastQuote.ticktime}`)
    : state.intradayMeta?.one_hour?.latest_time || analysis.last.date;
  els.planAsOf.textContent = `现价 ${model.price.toFixed(0)} · 行情标记 ${asOf}`;
}

function draw() {
  const data = visibleData();
  if (data.length < 5) return;

  const analysis = analyze(data);
  updateSummary(data, analysis);
  drawPriceChart(data);
  drawVolumeChart(data);
  if (lastQuote) applyRealtimeQuote(lastQuote);

  // Refresh the 2-day aggregated bollinger card (uses ALL of state.data,
  // not just the visible window) and let the intraday-strategy card pick
  // up the new 2D position.
  update2DayCard();
  if (state.intradayMeta) updateIntradayPanel();
  renderMultiStrategyPanel();
  renderAlignmentScore();
  renderDecisionCockpit(analysis);
  populatePosCalcDefaults();
}

function drawPriceChart(data) {
  const colors = readColors();
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
  const colors = readColors();
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
  const colors = readColors();
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
  const colors = readColors();
  els.legend.innerHTML = [
    `<span><i style="background:${colors.up}"></i>上涨</span>`,
    `<span><i style="background:${colors.down}"></i>下跌</span>`,
    ...maPeriods.map((period, index) => `<span><i style="background:${colors.ma[index]}"></i>MA${period}</span>`)
  ].join("");
}

function updateSummary(data, analysis) {
  const lbl = activeLabel();
  els.chartTitle.textContent = `${lbl.code} ${lbl.name}连续日线`;
  if (state.dataMeta) {
    els.chartSubhead.textContent = `${state.dataMeta.instrument_name || `${lbl.name}连续`} | 最新 ${state.dataMeta.latest_date} | 来源 ${state.dataMeta.source}`;
  } else {
    els.chartSubhead.textContent = state.imported || state.autoLoaded ? `已载入 ${lbl.code} 连续合约 CSV 数据` : "示例数据：未自动载入 CSV 时显示，日期不会超过今天";
  }
  const snapshotPrice = Number(state.intradayMeta?.one_hour?.close);
  const displayPrice = Number.isFinite(lastQuote?.price)
    ? lastQuote.price
    : Number.isFinite(snapshotPrice) ? snapshotPrice : analysis.last.close;
  const referencePrice = displayPrice !== analysis.last.close ? analysis.last.close : analysis.prev.close;
  const displayChange = displayPrice - referencePrice;
  const displayChangePct = referencePrice > 0 ? displayChange / referencePrice : 0;
  els.lastPrice.textContent = displayPrice.toFixed(0);
  els.lastChange.textContent = `${formatSigned(displayChange)} (${formatPct(displayChangePct)})`;
  els.lastChange.className = displayChange >= 0 ? "up" : "down";
  els.signalText.textContent = analysis.signal;
  els.signalText.className = analysis.signal === "偏强" ? "up" : analysis.signal === "偏弱" ? "down" : "";
  els.signalDetail.textContent = `综合评分 ${analysis.score.toFixed(0)} / 100`;
  els.upDays.textContent = `${analysis.upCount} / 20`;
  els.winRate.textContent = `最近 20 个交易日 ${formatPct(analysis.winRate)}`;
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

function bjDateIso() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function formatMarketBarTime(value) {
  const text = String(value || "");
  const datePart = text.slice(0, 10);
  if (/^\d{4}-\d{2}-\d{2}$/.test(datePart) && datePart > bjDateIso()) {
    return `${datePart}（交易日归属）`;
  }
  return text;
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

// ── Position size calculator ──────────────────────────────
// Tracks per-field "user_edited" flags so auto-populated defaults don't
// wipe values the user has typed. Cleared on symbol switch.
const POS_CALC_INPUT_IDS = [
  "posCapital", "posRisk", "posMaxMargin", "posDirection", "posEntry",
  "posStop", "posTarget", "posSlippage", "posMult", "posMargin",
];
let posCalcUserEdited = new Set();

function bindPosCalcInputs() {
  POS_CALC_INPUT_IDS.forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("input", () => {
      posCalcUserEdited.add(id);
      updatePosCalc();
    });
  });
}

function resetPosCalcUserEdited() {
  posCalcUserEdited = new Set();
}

// Fill entry from live price and stop from AI watch_levels — but only for
// fields the user has NOT touched.
function populatePosCalcDefaults() {
  if (!els.posEntry || !els.posStop) return;

  const model = state.decisionModel;
  const modelDirection = model?.signals?.compositeSignal < 0 ? "short" : "long";
  const modelSetup = modelDirection === "short" ? model?.shortSetup : model?.longSetup;

  if (!posCalcUserEdited.has("posDirection") && els.posDirection) {
    els.posDirection.value = modelDirection;
  }

  // Entry default: live price → last close
  if (!posCalcUserEdited.has("posEntry")) {
    let price = Number(modelSetup?.entry);
    if (!Number.isFinite(price) && lastQuote && Number.isFinite(lastQuote.price)) price = lastQuote.price;
    else if (state.data && state.data.length) {
      const last = state.data[state.data.length - 1];
      if (!Number.isFinite(price) && last) price = last.close;
    }
    if (Number.isFinite(price)) {
      els.posEntry.value = roundToTick(price);
    }
  }

  // Deterministic execution plan has priority. AI levels are only a fallback.
  if (!posCalcUserEdited.has("posStop")) {
    let stop = Number(modelSetup?.stop);
    if (!Number.isFinite(stop)) {
      const ai = state.lastAi;
      const wl = ai && typeof ai.watch_levels === "object" && ai.watch_levels !== null ? ai.watch_levels : null;
      const support = wl ? Number(wl.support || 0) : 0;
      const resistance = wl ? Number(wl.resistance || 0) : 0;
      stop = modelDirection === "short" ? resistance : support;
    }
    if (Number.isFinite(stop) && stop > 0) {
      els.posStop.value = roundToTick(stop);
    }
  }

  if (!posCalcUserEdited.has("posTarget") && els.posTarget) {
    const target = Number(modelSetup?.rr1 >= 1.5 ? modelSetup?.target1 : modelSetup?.target2);
    if (Number.isFinite(target) && target > 0) {
      els.posTarget.value = roundToTick(target);
    }
  }

  updatePosCalc();
}

function updatePosCalc() {
  if (!els.posPerLotRisk) return;
  const capital   = Number(els.posCapital?.value || 0);
  const riskPct   = Number(els.posRisk?.value    || 0);
  const maxMarginPct = Number(els.posMaxMargin?.value || 0);
  const direction = els.posDirection?.value || "long";
  const entry     = Number(els.posEntry?.value   || 0);
  const stop      = Number(els.posStop?.value    || 0);
  const target    = Number(els.posTarget?.value  || 0);
  const slippage  = Math.max(0, Number(els.posSlippage?.value || 0));
  const mult      = Number(els.posMult?.value    || 0);
  const marginPct = Number(els.posMargin?.value  || 0);

  const outputEls = [
    els.posRiskBudget, els.posPerLotRisk, els.posRiskLots, els.posMarginLots,
    els.posLotsRec, els.posMarginUse, els.posRR, els.posTargetPnl, els.posGap,
  ];
  if (!(capital > 0 && riskPct > 0 && maxMarginPct > 0 && entry > 0 && stop > 0 && target > 0 && mult > 0 && marginPct > 0)) {
    outputEls.forEach((el) => { if (el) el.textContent = "--"; });
    if (els.posMarginUsePct) els.posMarginUsePct.textContent = "--";
    if (els.posWarning) els.posWarning.textContent = "请补全资金、方向、入场、止损、目标和保证金参数。";
    return;
  }

  const directionValid = direction === "long"
    ? stop < entry && target > entry
    : stop > entry && target < entry;
  if (!directionValid) {
    outputEls.forEach((el) => { if (el) el.textContent = "--"; });
    if (els.posMarginUsePct) els.posMarginUsePct.textContent = "--";
    if (els.posWarning) {
      els.posWarning.textContent = direction === "long"
        ? "做多参数必须满足：止损价 < 入场价 < 目标价。"
        : "做空参数必须满足：目标价 < 入场价 < 止损价。";
      els.posWarning.className = "pos-warning error";
    }
    return;
  }

  const riskBudget = capital * riskPct / 100;
  const riskPoints = Math.abs(entry - stop) + slippage * 2;
  const rewardPoints = Math.max(0, Math.abs(target - entry) - slippage * 2);
  const perLotRisk = riskPoints * mult;
  const riskLots = perLotRisk > 0 ? Math.floor(riskBudget / perLotRisk) : 0;
  const marginPerLot = entry * mult * marginPct / 100;
  const marginBudget = capital * maxMarginPct / 100;
  const marginLots = marginPerLot > 0 ? Math.floor(marginBudget / marginPerLot) : 0;
  const lotsSafe = Math.max(0, Math.min(riskLots, marginLots));
  const marginUse = marginPerLot * lotsSafe;
  const marginUsePct = capital > 0 ? marginUse / capital * 100 : 0;
  const rr = riskPoints > 0 ? rewardPoints / riskPoints : 0;
  const targetPnl = rewardPoints * mult * lotsSafe;
  const gap = Math.abs(entry - stop);
  const gapPct = gap / entry * 100;

  els.posRiskBudget.textContent = Math.round(riskBudget).toLocaleString();
  els.posPerLotRisk.textContent = Math.round(perLotRisk).toLocaleString();
  els.posRiskLots.textContent = String(Math.max(0, riskLots));
  els.posMarginLots.textContent = String(Math.max(0, marginLots));
  els.posLotsRec.textContent = String(lotsSafe);
  els.posMarginUse.textContent = Math.round(marginUse).toLocaleString();
  els.posMarginUsePct.textContent = `${marginUsePct.toFixed(1)}% 账户资金`;
  els.posRR.textContent = `${rr.toFixed(2)}R`;
  els.posGap.textContent = `止损 ${gap.toFixed(0)} 点 / ${gapPct.toFixed(2)}%`;
  els.posTargetPnl.textContent = Math.round(targetPnl).toLocaleString();

  let warning = "参数通过风险预算与保证金双重约束。";
  let warningClass = "pos-warning success";
  if (lotsSafe === 0) {
    warning = "当前资金与风险参数不足以安全开 1 手，请缩小止损距离或降低合约暴露。";
    warningClass = "pos-warning error";
  } else if (rr < 1.5) {
    warning = `计划盈亏比只有 ${rr.toFixed(2)}R，低于 1.5R 执行门槛。`;
    warningClass = "pos-warning warn";
  } else if (marginLots < riskLots) {
    warning = "最终手数受最大保证金占用约束。";
  } else if (riskLots < marginLots) {
    warning = "最终手数受单笔风险预算约束。";
  }
  if (els.posWarning) {
    els.posWarning.textContent = warning;
    els.posWarning.className = warningClass;
  }
}

// ── Overseas markets ──────────────────────────────────────
// Loads a shared (non-symbol-scoped) data/overseas.json file. Cards show
// FCPO, CBOT soy oil, Brent (whatever the backend chose to publish).
async function autoLoadOverseas() {
  if (location.protocol === "file:") return;
  if (!els.overseasGrid) return;
  try {
    const r = await fetchWithRetry(`data/overseas.json?t=${Date.now()}`, { cache: "no-store" });
    if (!r.ok) {
      els.overseasGrid.innerHTML = `<div class="overseas-card"><span>暂无海外行情数据</span></div>`;
      if (els.overseasMeta) els.overseasMeta.textContent = `等待 data/overseas.json`;
      return;
    }
    const data = await r.json();
    // Backend writes { symbols: { FCPO:{...}, SOYBEAN_OIL:{...}, BRENT:{...} } }
    // Each value has: {name, price, change, change_pct: "+x.xx%" (string), source}
    const symbolsObj = (data && typeof data.symbols === "object") ? data.symbols : {};
    const items = Object.entries(symbolsObj).map(([sym, v]) => ({ symbol: sym, ...v }));
    if (els.overseasMeta) {
      const upd = data.updated_at_utc ? `更新 ${formatDateTime(data.updated_at_utc)}` : "";
      els.overseasMeta.textContent = items.length
        ? `页面每 60 秒检查 · ${items.length} 个市场${upd ? " · " + upd : ""}`
        : `页面每 60 秒检查 · 暂无数据${upd ? " · " + upd : ""}`;
    }
    if (!items.length) {
      els.overseasGrid.innerHTML = `<div class="overseas-card"><span>暂无海外行情数据</span></div>`;
      return;
    }
    els.overseasGrid.innerHTML = items.map((m) => {
      const priceRaw = Number(m.price);
      const price = Number.isFinite(priceRaw) ? priceRaw.toFixed(2) : "--";
      // change_pct arrives as a string like "+1.23%" — strip the % to compute
      // numeric direction, keep the string for display.
      const pctStr = typeof m.change_pct === "string" ? m.change_pct : "--";
      const pctRaw = Number(String(m.change_pct || "").replace("%", ""));
      const hasPct = Number.isFinite(pctRaw);
      const cls    = !hasPct ? "" : (pctRaw >= 0 ? "up" : "down");
      const name   = escapeHtml(m.name || m.symbol || "--");
      const symTxt = m.symbol && m.symbol !== m.name ? m.symbol : "";
      return `
        <div class="overseas-card">
          <div class="overseas-head">
            <strong>${name}</strong>
            ${symTxt ? `<small class="overseas-sym">${escapeHtml(symTxt)}</small>` : ""}
          </div>
          <div class="overseas-body">
            <span class="overseas-price">${price}</span>
            <span class="pct ${cls}">${escapeHtml(pctStr)}</span>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    els.overseasGrid.innerHTML = `<div class="overseas-card"><span>加载失败：${escapeHtml(err.message || "unknown")}</span></div>`;
  }
}

// ── AI accuracy line (below aiMeta, above aiSummary) ──────
async function autoLoadAccuracy() {
  if (location.protocol === "file:") return;
  if (!els.aiAccuracy) return;
  const _fetchSym = state.activeSymbol;
  try {
    const r = await fetchWithRetry(`${dataPath("ai_accuracy.json")}?t=${Date.now()}`, { cache: "no-store" });
    if (_fetchSym !== state.activeSymbol) return;
    if (!r.ok) {
      els.aiAccuracy.hidden = true;
      return;
    }
    const d = await r.json();
    // Backend writes `recent_hit_rate` as a fraction (0..1) or null when
    // there aren't enough graded entries yet.
    const rateRaw = Number(d.recent_hit_rate);
    const total   = Number(d.total_evaluated || 0);
    if (!Number.isFinite(rateRaw)) {
      els.aiAccuracy.hidden = true;
      return;
    }
    if (total < 10) {
      els.aiAccuracy.textContent = `AI 复盘样本 ${total} / 10 · 样本不足，暂不评价命中率`;
      els.aiAccuracy.hidden = false;
      els.aiAccuracy.classList.remove("warn");
      return;
    }
    // Defensive: accept fraction (0..1) or percent (0..100) in case an older
    // ai_accuracy.json format from an earlier run is still on disk.
    const pct  = rateRaw <= 1 ? rateRaw * 100 : rateRaw;
    const warn = Boolean(d.warning_low_accuracy);
    const prefix = warn ? "⚠️ " : "";
    els.aiAccuracy.textContent = `${prefix}近 20 次命中率: ${pct.toFixed(0)}% (总评估 ${total})`;
    els.aiAccuracy.hidden = false;
    els.aiAccuracy.classList.toggle("warn", warn);
  } catch (_) {
    els.aiAccuracy.hidden = true;
  }
}

// ── AI Q&A (ask.yml workflow + ask_response.json polling) ──
let askPollInterval = null;

function setAskStatus(text, type) {
  if (!els.askStatus) return;
  els.askStatus.textContent = text;
  els.askStatus.className = `ai-status${type ? ` ${type}` : ""}`;
}

function renderAskResponse(data, fresh) {
  if (!els.askResponse || !data) return;
  const q = data.question || "";
  const a = data.answer || "(无回复)";
  const time = data.asked_at_utc ? formatDateTime(data.asked_at_utc) : "";
  if (els.askResponseMeta) {
    els.askResponseMeta.textContent = fresh
      ? `问 ${time}：${q}`
      : `上次问题 ${time}（历史）：${q}`;
  }
  if (els.askResponseText) {
    els.askResponseText.textContent = a;
  }
  els.askResponse.hidden = false;
  els.askResponse.classList.toggle("stale", !fresh);
}

async function autoLoadAskResponse() {
  if (location.protocol === "file:") return;
  if (!els.askResponse) return;
  const _fetchSym = state.activeSymbol;
  try {
    const r = await fetchWithRetry(`${dataPath("ask_response.json")}?t=${Date.now()}`, { cache: "no-store" }, 2);
    if (_fetchSym !== state.activeSymbol) return;
    if (!r.ok) {
      state.lastAskResponse = null;
      els.askResponse.hidden = true;
      return;
    }
    const d = await r.json();
    state.lastAskResponse = d;
    renderAskResponse(d, /*fresh=*/false);
  } catch (_) {
    els.askResponse.hidden = true;
  }
}

const GH_ASK_WORKFLOW_URL = "https://github.com/FrankSun0616/palm_dalian/actions/workflows/ask.yml";

async function submitAskQuestion() {
  const question = (els.askInput?.value || "").trim();
  if (!question) {
    setAskStatus("请输入问题", "error");
    return;
  }
  const prevTime = state.lastAskResponse?.asked_at_utc || null;
  let copied = false;
  try {
    await navigator.clipboard.writeText(question);
    copied = true;
  } catch (_) {}
  window.open(GH_ASK_WORKFLOW_URL, "_blank", "noopener,noreferrer");
  setAskStatus(
    copied
      ? `问题已复制。请在 Actions 中选择 ${state.activeSymbol}，粘贴问题并运行；本页会检查回复。`
      : `已打开 Actions。请选择 ${state.activeSymbol} 并输入问题后运行；本页会检查回复。`,
    "loading",
  );
  const startTime = Date.now();
  const maxWait = 12 * 60 * 1000;
  if (askPollInterval) clearInterval(askPollInterval);
  askPollInterval = setInterval(async () => {
    if (Date.now() - startTime > maxWait) {
      clearInterval(askPollInterval);
      askPollInterval = null;
      setAskStatus("尚未检测到新回复，可再次打开 Actions 查看运行状态。", "error");
      return;
    }
    try {
      const r = await fetchWithRetry(`${dataPath("ask_response.json")}?t=${Date.now()}`, { cache: "no-store" }, 2);
      if (!r.ok) return;
      const d = await r.json();
      const newTime = d.asked_at_utc || null;
      if (newTime && newTime !== prevTime) {
        clearInterval(askPollInterval);
        askPollInterval = null;
        state.lastAskResponse = d;
        renderAskResponse(d, /*fresh=*/true);
        setAskStatus(`已回复 (${formatDateTime(newTime)})`, "success");
      }
    } catch (_) {}
  }, 20 * 1000);
}

if (els.askBtn) els.askBtn.addEventListener("click", submitAskQuestion);
bindPosCalcInputs();

els.periodSelect.addEventListener("change", () => {
  // Reset zoom/pan state so periodSelect controls the visible window again.
  state.visibleStart = null;
  state.visibleCount = null;
  draw();
});
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
const GH_WORKFLOW_DISPATCH_URL = `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/actions/workflows/${GH_WORKFLOW}/dispatches`;
const PUBLIC_ACTIONS_TOKEN = atob(
  "Z2l0aHViX3BhdF8xMUJIWlpDU1kwZDdKb050dVczVXU5X2dmMjd1c0V4aldwRHRMenU2ZXFNNHVKeF" +
  "VHM2Z6eDRYVW5ocE9WVGhlVjRPRzdGVEVaVU8yc3phbUEx"
);
let aiManualPollInterval = null;

function setAiStatus(text, type) {
  els.aiStatus.textContent = text;
  els.aiStatus.className = `ai-status${type ? ` ${type}` : ""}`;
}

async function generateAiAnalysis() {
  els.generateAiBtn.disabled = true;
  const pat = PUBLIC_ACTIONS_TOKEN;
  const requestedSymbol = state.activeSymbol;
  const resultPath = `data/${requestedSymbol.toLowerCase()}/ai_analysis.json`;
  let prevGenTime = state.lastAi?.generated_at_utc || null;
  setAiStatus("正在直接触发 GitHub Actions...", "loading");

  try {
    const previous = await fetchWithRetry(`${resultPath}?t=${Date.now()}`, { cache: "no-store" }, 2);
    if (previous.ok) prevGenTime = (await previous.json()).generated_at_utc || prevGenTime;
  } catch (_) {}

  try {
    const response = await fetch(GH_WORKFLOW_DISPATCH_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${pat}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({
        ref: "main",
        inputs: { run_ai_analysis: "true", symbols: "P0,Y0" },
      }),
    });
    if (!response.ok) {
      const body = await response.text().catch(() => "");
      setAiStatus(
        `触发失败 (${response.status})${body ? `：${body.slice(0, 120)}` : ""}`,
        "error",
      );
      els.generateAiBtn.disabled = false;
      return;
    }
  } catch (error) {
    setAiStatus(`触发网络错误：${error.message || "未知错误"}`, "error");
    els.generateAiBtn.disabled = false;
    return;
  }

  setAiStatus("Actions 已触发，P0/Y0 正在并行生成；本页会自动读取当前品种结果。", "loading");
  if (aiManualPollInterval) clearInterval(aiManualPollInterval);
  const startTime = Date.now();
  const maxWait = 12 * 60 * 1000;
  aiManualPollInterval = setInterval(async () => {
    if (Date.now() - startTime > maxWait) {
      clearInterval(aiManualPollInterval);
      aiManualPollInterval = null;
      setAiStatus("尚未检测到新结果，工作流可能仍在运行，可稍后重新加载。", "error");
      els.generateAiBtn.disabled = false;
      return;
    }
    try {
      const r = await fetchWithRetry(`${resultPath}?t=${Date.now()}`, { cache: "no-store" }, 2);
      if (!r.ok) return;
      const ai = await r.json();
      const newTime = ai.generated_at_utc || null;
      if (newTime && newTime !== prevGenTime) {
        clearInterval(aiManualPollInterval);
        aiManualPollInterval = null;
        if (state.activeSymbol === requestedSymbol) updateAiPanel(ai);
        setAiStatus(`分析完成 (${formatDateTime(newTime)})`, "success");
        els.generateAiBtn.disabled = false;
      }
    } catch (_) {}
  }, 10 * 1000);
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

els.priceCanvas.addEventListener("mousedown", (event) => {
  const geometry = state.chartGeometry;
  if (!geometry) return;
  state.isDragging = true;
  state.dragMoved = false;
  state.dragStartX = event.clientX;
  // Snapshot the current visible window so we can pan relative to it.
  const data = visibleData();
  const totalStart = state.data.length - data.length;
  state.dragStartVisibleStart = state.visibleStart !== null ? state.visibleStart : totalStart;
  state.dragStartVisibleCount = state.visibleCount !== null ? state.visibleCount : data.length;
  els.priceCanvas.style.cursor = "grabbing";
});

window.addEventListener("mouseup", () => {
  if (state.isDragging) {
    state.isDragging = false;
    els.priceCanvas.style.cursor = "";
  }
});

els.priceCanvas.addEventListener("mousemove", (event) => {
  const geometry = state.chartGeometry;
  if (!geometry) return;

  // Drag-to-pan takes priority over tooltip rendering
  if (state.isDragging && state.dragStartX !== null) {
    const deltaX = event.clientX - state.dragStartX;
    if (Math.abs(deltaX) > 2) state.dragMoved = true;
    const count = state.dragStartVisibleCount;
    const pxPerBar = geometry.innerW / Math.max(1, count - 1);
    const deltaBars = Math.round(-deltaX / pxPerBar);
    const maxStart = Math.max(0, state.data.length - count);
    const newStart = Math.max(0, Math.min(maxStart, state.dragStartVisibleStart + deltaBars));
    state.visibleStart = newStart;
    state.visibleCount = count;
    els.chartTooltip.hidden = true;
    state.hoverIndex = null;
    draw();
    return;
  }

  const data = visibleData();
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

  // MA at hover index — computed from same visible window so it matches lines on chart
  const maCfg = els.maSelect.value.split(",").map(Number);
  const maSeries = maCfg.map((p) => movingAverage(data, p));
  const maParts = maCfg.map((p, i) => {
    const v = maSeries[i][index];
    return v == null ? null : `MA${p} ${Math.round(v)}`;
  }).filter(Boolean);
  const maLine = maParts.length ? `<br>${maParts.join(" / ")}` : "";

  els.chartTooltip.innerHTML = `
    <strong>${row.date}${liveLabel}</strong>
    开 ${row.open.toFixed(0)} / 高 ${row.high.toFixed(0)}<br>
    低 ${row.low.toFixed(0)} / 收 ${row.close.toFixed(0)}<br>
    涨跌 ${formatSigned(change)} (${formatPct(change / previous.close)})<br>
    量 ${Math.round(row.volume / 10000)} 万手${maLine}${liveNote}
  `;
  draw();
});

els.priceCanvas.addEventListener("mouseleave", () => {
  state.hoverIndex = null;
  els.chartTooltip.hidden = true;
  draw();
});

// Wheel zoom — preserves the bar under the mouse as anchor
els.priceCanvas.addEventListener("wheel", (event) => {
  const geometry = state.chartGeometry;
  if (!geometry) return;
  event.preventDefault();

  const data = visibleData();
  const totalStart = state.data.length - data.length;
  const currentStart = state.visibleStart !== null ? state.visibleStart : totalStart;
  const currentCount = state.visibleCount !== null ? state.visibleCount : data.length;

  const rect = els.priceCanvas.getBoundingClientRect();
  const mouseX = event.clientX - rect.left;
  const anchorFrac = Math.max(0, Math.min(1,
    (mouseX - geometry.pad.left) / Math.max(1, geometry.innerW)
  ));
  const anchorIdx = currentStart + Math.round(anchorFrac * (currentCount - 1));

  // Wheel down → zoom out (more bars), wheel up → zoom in (fewer bars)
  const zoomFactor = event.deltaY > 0 ? 1.15 : 1 / 1.15;
  let newCount = Math.round(currentCount * zoomFactor);
  newCount = Math.max(30, Math.min(500, newCount));
  newCount = Math.min(newCount, state.data.length);
  if (newCount === currentCount) return;

  // Keep the anchor bar under the mouse
  const newAnchorOffset = Math.round(anchorFrac * (newCount - 1));
  let newStart = anchorIdx - newAnchorOffset;
  const maxStart = Math.max(0, state.data.length - newCount);
  newStart = Math.max(0, Math.min(maxStart, newStart));

  state.visibleStart = newStart;
  state.visibleCount = newCount;
  draw();
}, { passive: false });

async function fetchWithRetry(url, options = {}, attempts = 3) {
  let lastError = null;
  let lastResponse = null;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(url, options);
      lastResponse = response;
      if (response.ok || response.status < 500) return response;
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    if (attempt < attempts) {
      await new Promise((resolve) => setTimeout(resolve, attempt * 500));
    }
  }
  if (lastResponse) return lastResponse;
  throw lastError || new Error("网络请求失败");
}

function activeContractSpecs() {
  return state.contractBridge?.contract_specs || { multiplier: 10, tick_size: 1, tick_value: 10 };
}

function renderContractBridge(bridge) {
  if (!bridge?.main) {
    if (els.contractMapping) els.contractMapping.textContent = `${state.activeSymbol} → 等待主力月份`;
    if (els.contractMappingStatus) {
      els.contractMappingStatus.textContent = "等待盘口";
      els.contractMappingStatus.className = "bridge-status neutral";
    }
    if (els.mappingEvidence) els.mappingEvidence.textContent = "等待价格与持仓比对";
    if (els.mappingMarketTime) els.mappingMarketTime.textContent = "--";
    if (els.mainContractPrice) els.mainContractPrice.textContent = "--";
    if (els.mainContractChange) { els.mainContractChange.textContent = "--"; els.mainContractChange.className = ""; }
    if (els.mainOpenInterest) els.mainOpenInterest.textContent = "--";
    if (els.mainOpenInterestShare) els.mainOpenInterestShare.textContent = "--";
    if (els.secondarySpread) { els.secondarySpread.textContent = "--"; els.secondarySpread.className = ""; }
    if (els.secondaryOpenInterest) els.secondaryOpenInterest.textContent = "--";
    if (els.rollRisk) { els.rollRisk.textContent = "--"; els.rollRisk.className = ""; }
    if (els.rollRiskReason) els.rollRiskReason.textContent = "--";
    if (els.contractSpec) els.contractSpec.textContent = "--";
    if (els.contractRuleRef) els.contractRuleRef.textContent = "--";
    if (els.contractBridgeFreshness) els.contractBridgeFreshness.textContent = "后台每 5 分钟更新，交易时段浏览器同步核对实时盘口。";
    return;
  }
  const main = bridge.main;
  const secondary = bridge.secondary;
  const specs = bridge.contract_specs || activeContractSpecs();
  const mappingOk = bridge.mapping_verified === true;
  const rollState = bridge.roll_state || "stable";
  const statusKind = !mappingOk ? "mismatch" : rollState === "urgent" ? "urgent" : rollState === "watch" ? "watch" : "verified";
  const statusText = !mappingOk ? "映射需复核" : bridge.roll_label || "映射已核对";

  els.contractMapping.textContent = `${state.activeSymbol} → ${main.symbol} 主力`;
  els.contractMappingStatus.textContent = statusText;
  els.contractMappingStatus.className = `bridge-status ${statusKind}`;
  els.mappingEvidence.textContent = mappingOk
    ? `连续报价与 ${main.symbol} 的价格、持仓一致`
    : bridge.mapping_note || `未能确认 ${state.activeSymbol} 与 ${main.symbol} 完全一致`;
  els.mappingMarketTime.textContent = `${bridge.trading_day || "--"} ${bridge.market_time || ""} · ${bridge.source || "行情源未知"}`.trim();
  els.mainContractPrice.textContent = Number(main.price).toFixed(0);
  const changeRatio = Number(main.change_ratio);
  const change = Number(main.change);
  els.mainContractChange.textContent = Number.isFinite(changeRatio)
    ? `${formatSigned(change)} (${formatPct(changeRatio)}) · 对昨结算`
    : "涨跌基准待核对";
  els.mainContractChange.className = Number.isFinite(change) ? (change >= 0 ? "up" : "down") : "";
  els.mainOpenInterest.textContent = `${formatCompact(Number(main.open_interest || 0))} 手`;
  els.mainOpenInterestShare.textContent = Number.isFinite(Number(bridge.main_open_interest_share))
    ? `可见月份持仓占比 ${(Number(bridge.main_open_interest_share) * 100).toFixed(1)}%`
    : "持仓占比待计算";
  if (secondary) {
    const spread = Number(bridge.secondary_spread);
    els.secondarySpread.textContent = `${secondary.symbol} ${formatSigned(spread)} 点`;
    els.secondarySpread.className = spread > 0 ? "up" : spread < 0 ? "down" : "";
    els.secondaryOpenInterest.textContent = `持仓 ${formatCompact(Number(secondary.open_interest || 0))} 手 · 主力的 ${(Number(bridge.secondary_open_interest_ratio || 0) * 100).toFixed(1)}% · ${bridge.spread_structure || "--"}`;
  } else {
    els.secondarySpread.textContent = "无可用次主力";
    els.secondaryOpenInterest.textContent = "--";
  }
  els.rollRisk.textContent = `${bridge.roll_label || "--"} · ${Number(bridge.roll_score || 0)}/100`;
  els.rollRisk.className = rollState === "urgent" ? "up" : rollState === "watch" ? "" : "down";
  const monthText = Number.isFinite(Number(bridge.months_to_delivery_month))
    ? `距交割月份约 ${Number(bridge.months_to_delivery_month)} 个月。`
    : "";
  els.rollRiskReason.textContent = `${monthText}${bridge.roll_reason || ""}`;
  els.contractSpec.textContent = `${Number(specs.multiplier || 10)} 吨/手 · ${Number(specs.tick_size || 1)} 元/吨`;
  els.contractRuleRef.textContent = `每跳 ${Number(specs.tick_value || Number(specs.multiplier || 10) * Number(specs.tick_size || 1))} 元/手 · ${specs.rule_reference || "规则待核对"}`;
  const age = ageMinutes(bridge.updated_at_utc);
  const browserVerified = String(bridge.source || "").includes("浏览器");
  const closedNote = isTrading() ? "交易时段每 5 秒同步核对盘口。" : "当前休市，行情标记以盘口交易日和时间为准。";
  els.contractBridgeFreshness.textContent = Number.isFinite(age)
    ? `${browserVerified ? "浏览器" : "后台"}于 ${formatDateTime(bridge.updated_at_utc)}（${humanAge(age)}）${browserVerified ? "完成核对" : "更新映射"}；${closedNote}`
    : `映射更新时间未知；${closedNote}`;
  if (els.contractPill) els.contractPill.textContent = `${activeLabel().exchange} ${main.symbol} · ${state.activeSymbol} 连续 · 1H / 4H / 日线`;
  if (!posCalcUserEdited.has("posMult") && els.posMult) {
    els.posMult.value = Number(specs.multiplier || 10);
  }
}

function renderModelValidation(model) {
  if (!model?.holdout) {
    if (els.modelStatus) {
      els.modelStatus.textContent = "等待检验结果";
      els.modelStatus.className = "model-status neutral";
    }
    if (els.modelTrades) els.modelTrades.textContent = "--";
    if (els.modelSplitDate) els.modelSplitDate.textContent = "--";
    if (els.modelExpectancy) { els.modelExpectancy.textContent = "--"; els.modelExpectancy.className = ""; }
    if (els.modelProfitFactor) { els.modelProfitFactor.textContent = "--"; els.modelProfitFactor.className = ""; }
    if (els.modelDrawdown) els.modelDrawdown.textContent = "--";
    if (els.modelWinRate) els.modelWinRate.textContent = "--";
    if (els.modelDirectionCount) els.modelDirectionCount.textContent = "--";
    if (els.modelVerdict) els.modelVerdict.textContent = "正在读取固定参数基准模型的历史样本外表现。";
    if (els.modelLimitations) els.modelLimitations.textContent = "日线基准模型与 1H/4H 日内方案不同，结果不代表未来收益。";
    return;
  }
  const metrics = model.holdout;
  const status = ["positive", "unproven", "rejected"].includes(model.status) ? model.status : "neutral";
  els.modelStatus.textContent = model.status_label || "检验状态未知";
  els.modelStatus.className = `model-status ${status}`;
  els.modelTrades.textContent = String(metrics.trades ?? "--");
  els.modelSplitDate.textContent = model.sample_period?.holdout_start
    ? `${model.sample_period.holdout_start} 起 · 后 ${Math.round(Number(model.sample_period.holdout_fraction || 0) * 100)}%`
    : "时间切分未知";
  const expectancy = Number(metrics.expectancy_r);
  els.modelExpectancy.textContent = Number.isFinite(expectancy) ? `${expectancy >= 0 ? "+" : ""}${expectancy.toFixed(2)}R` : "--";
  els.modelExpectancy.className = Number.isFinite(expectancy) ? (expectancy > 0 ? "up" : "down") : "";
  const profitFactor = Number(metrics.profit_factor);
  els.modelProfitFactor.textContent = Number.isFinite(profitFactor) ? profitFactor.toFixed(2) : "--";
  els.modelProfitFactor.className = Number.isFinite(profitFactor) ? (profitFactor >= 1.2 ? "up" : profitFactor < 1 ? "down" : "") : "";
  const drawdown = Number(metrics.max_drawdown_r);
  els.modelDrawdown.textContent = Number.isFinite(drawdown) ? `${drawdown.toFixed(1)}R` : "--";
  els.modelWinRate.textContent = Number.isFinite(Number(metrics.win_rate)) ? `${(Number(metrics.win_rate) * 100).toFixed(1)}%` : "--";
  els.modelDirectionCount.textContent = `多 ${metrics.long_trades ?? 0} · 空 ${metrics.short_trades ?? 0}`;
  const costText = model.methodology?.cost_assumption || "成本假设未知";
  els.modelMethod.textContent = `下一开盘执行 · ${costText}`;

  if (model.status === "rejected") {
    els.modelVerdict.textContent = `样本外期望 ${expectancy.toFixed(2)}R、盈利因子 ${Number.isFinite(profitFactor) ? profitFactor.toFixed(2) : "--"}，该日线基准没有可用历史优势，不应据此开仓。`;
  } else if (model.status === "unproven") {
    els.modelVerdict.textContent = `样本外虽为正期望，但强度不足或稳定性不够，当前只能作为研究证据，不能视为已验证策略。`;
  } else if (model.status === "positive") {
    els.modelVerdict.textContent = `固定参数在样本外达到最低正优势门槛，但仍需具体月份合约与滚动窗口复验后才能用于执行。`;
  } else {
    els.modelVerdict.textContent = `样本数量不足，暂时不能判断该固定规则是否存在历史优势。`;
  }
  const limits = Array.isArray(model.limitations) ? model.limitations.slice(0, 2).join(" · ") : "";
  els.modelLimitations.textContent = limits || "日线基准模型与 1H/4H 日内方案不同，结果不代表未来收益。";
}

async function autoLoadContractBridge() {
  if (location.protocol === "file:") return;
  const fetchSymbol = state.activeSymbol;
  try {
    const response = await fetchWithRetry(`${dataPath("contract_bridge.json")}?t=${Date.now()}`, { cache: "no-store" });
    if (fetchSymbol !== state.activeSymbol) return;
    if (!response.ok) throw new Error(`合约映射 HTTP ${response.status}`);
    state.contractBridge = await response.json();
    renderContractBridge(state.contractBridge);
  } catch (error) {
    if (!state.contractBridge) renderContractBridge(null);
    if (els.contractBridgeFreshness) els.contractBridgeFreshness.textContent = `${error.message || "合约映射读取失败"}；执行前在交易软件人工确认。`;
  }
}

async function autoLoadModelValidation() {
  if (location.protocol === "file:") return;
  const fetchSymbol = state.activeSymbol;
  try {
    const response = await fetchWithRetry(`${dataPath("model_validation.json")}?t=${Date.now()}`, { cache: "no-store" });
    if (fetchSymbol !== state.activeSymbol) return;
    if (!response.ok) throw new Error(`模型检验 HTTP ${response.status}`);
    state.modelValidation = await response.json();
    renderModelValidation(state.modelValidation);
  } catch (error) {
    if (!state.modelValidation) renderModelValidation(null);
    if (els.modelVerdict) els.modelVerdict.textContent = error.message || "模型检验读取失败";
  }
}

async function autoLoadCsv() {
  if (location.protocol === "file:") {
    const message = "请通过 GitHub Pages 或本地 http server 打开，file:// 无法自动读取 CSV";
    setLoadStatus("加载失败", message);
    console.warn(message);
    return;
  }
  const lbl = activeLabel();
  const _fetchSym = state.activeSymbol;  // guard against symbol switch during fetch
  setLoadStatus("加载中", `正在读取真实 ${lbl.code} CSV...`);
  try {
    const cacheBust = `t=${Date.now()}`;
    const [response, metaResponse] = await Promise.all([
      fetchWithRetry(`${dataPath("daily.csv")}?${cacheBust}`, { cache: "no-store" }),
      fetchWithRetry(`${dataPath("source_meta.json")}?${cacheBust}`, { cache: "no-store" })
    ]);
    if (_fetchSym !== state.activeSymbol) return;  // user switched — drop stale response
    if (response.status === 404) {
      // Files not generated yet (e.g. fresh Y0 before first workflow run).
      // Keep demo data and show a helpful message rather than crashing.
      setLoadStatus("待生成", `${lbl.code} 数据尚未生成，等待后台生成`);
      state.autoLoaded = false;
      state.dataMeta = null;
      draw();
      return;
    }
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
  const _fetchSym = state.activeSymbol;
  try {
    const cacheBust = `t=${Date.now()}`;
    const response = await fetchWithRetry(`${dataPath("ai_analysis.json")}?${cacheBust}`, { cache: "no-store" });
    if (_fetchSym !== state.activeSymbol) return;
    if (response.status === 404) {
      // Fresh symbol without an AI run yet — show placeholder, don't crash.
      els.aiMeta.textContent = `${activeLabel().code} AI 分析尚未生成`;
      els.aiSummary.textContent = "等待后台生成 DeepSeek 短线分析。";
      els.aiBias.textContent = "--";
      els.aiBias.className = "bias-pill neutral";
      els.aiList.innerHTML = "";
      if (els.aiFreshness) {
        els.aiFreshness.textContent = "AI 尚未生成";
        els.aiFreshness.className = "ai-freshness stale";
      }
      state.lastAi = null;
      return;
    }
    if (!response.ok) throw new Error(`AI HTTP ${response.status}`);
    const ai = await response.json();
    updateAiPanel(ai);
  } catch (error) {
    els.aiMeta.textContent = "AI 分析读取失败";
    els.aiSummary.textContent = error.message || "未知错误";
    els.aiBias.textContent = "--";
    els.aiList.innerHTML = "";
    if (els.aiFreshness) {
      els.aiFreshness.textContent = "AI 读取失败";
      els.aiFreshness.className = "ai-freshness stale";
    }
  }
}

async function autoLoadIntradayMeta() {
  if (location.protocol === "file:") return;
  const _fetchSym = state.activeSymbol;
  try {
    const response = await fetchWithRetry(`${dataPath("intraday_meta.json")}?t=${Date.now()}`, { cache: "no-store" });
    if (_fetchSym !== state.activeSymbol) return;
    if (response.status === 404) {
      state.intradayMeta = null;
      els.boll1hStatus.textContent = "待生成";
      els.boll1hDetail.textContent = `${activeLabel().code} 1小时数据尚未生成`;
      els.boll2hStatus.textContent = "待生成";
      els.boll2hDetail.textContent = `${activeLabel().code} 2小时数据尚未生成`;
      if (els.boll4hStatus) {
        els.boll4hStatus.textContent = "待生成";
        els.boll4hStatus.className = "";
        els.boll4hDetail.textContent = `${activeLabel().code} 4小时数据尚未生成`;
      }
      renderMultiStrategyPanel();
      return;
    }
    if (!response.ok) throw new Error(`Intraday HTTP ${response.status}`);
    state.intradayMeta = await response.json();
    updateIntradayPanel();
    renderMultiStrategyPanel();
    // Re-run freshness and strategy selection against the newest market data.
    if (state.lastAi) updateAiPanel(state.lastAi);
    draw();
  } catch (error) {
    els.boll1hStatus.textContent = "加载失败";
    els.boll1hDetail.textContent = error.message || "无法读取1小时数据";
    els.boll2hStatus.textContent = "加载失败";
    els.boll2hDetail.textContent = error.message || "无法读取2小时数据";
  }
}

async function autoLoadNewsSnapshot() {
  if (location.protocol === "file:") return;
  const _fetchSym = state.activeSymbol;
  try {
    const response = await fetchWithRetry(`${dataPath("news_snapshot.json")}?t=${Date.now()}`, { cache: "no-store" });
    if (_fetchSym !== state.activeSymbol) return;
    if (response.status === 404) {
      state.newsSnapshot = null;
      els.newsRealtimeStatus.textContent = "待生成";
      els.newsRealtimeText.textContent = `${activeLabel().code} 舆情数据尚未生成`;
      if (els.newsTickerList) els.newsTickerList.innerHTML = "";
      if (els.newsTickerMeta) els.newsTickerMeta.textContent = "暂无新闻数据";
      return;
    }
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
    detail: `价 ${Number(price).toFixed(0)}｜上 ${Number(boll.upper).toFixed(0)} 中 ${Number(boll.mid).toFixed(0)} 下 ${Number(boll.lower).toFixed(0)}｜带宽 ${width}｜${read}｜${formatMarketBarTime(summary.latest_time)}`
  };
}

function update2DayCard() {
  if (!els.boll2dStatus) return;
  const twoDay = state.twoDay = compute2DayMeta(state.data || []);
  if (!twoDay) {
    els.boll2dStatus.textContent = "数据不足";
    els.boll2dStatus.className = "";
    els.boll2dDetail.textContent = "需要至少 40 个日线 bar";
    return;
  }
  const b = twoDay.bollinger;
  const status = twoDay.close > b.upper ? "突破上轨"
                : twoDay.close < b.lower ? "跌破下轨"
                : twoDay.close > b.mid   ? "中轨上方" : "中轨下方";
  els.boll2dStatus.textContent = status;
  els.boll2dStatus.className = /上轨|上方/.test(status) ? "up" : /下轨|下方/.test(status) ? "down" : "";
  els.boll2dDetail.textContent =
    `${twoDay.close.toFixed(0)} ${twoDay.change_pct} | 上 ${b.upper.toFixed(0)} / 中 ${b.mid.toFixed(0)} / 下 ${b.lower.toFixed(0)} | RSI ${(twoDay.rsi14 || 0).toFixed(1)}`;
}

function updateIntradayPanel() {
  const meta = state.intradayMeta;
  if (!meta) return;
  const price = lastQuote?.price || null;
  const one  = bandStatus(meta.one_hour,  price);
  const two  = bandStatus(meta.two_hour,  price);
  const four = bandStatus(meta.four_hour, price);
  els.boll1hStatus.textContent = one.title;
  els.boll1hStatus.className = /上轨|强势/.test(one.title) ? "up" : /下轨|弱势/.test(one.title) ? "down" : "";
  els.boll1hDetail.textContent = one.detail;
  els.boll2hStatus.textContent = two.title;
  els.boll2hStatus.className = /上轨|强势/.test(two.title) ? "up" : /下轨|弱势/.test(two.title) ? "down" : "";
  els.boll2hDetail.textContent = two.detail;
  if (els.boll4hStatus) {
    if (meta.four_hour) {
      els.boll4hStatus.textContent = four.title;
      els.boll4hStatus.className = /上轨|强势/.test(four.title) ? "up" : /下轨|弱势/.test(four.title) ? "down" : "";
      els.boll4hDetail.textContent = four.detail;
    } else {
      els.boll4hStatus.textContent = "待生成";
      els.boll4hStatus.className = "";
      els.boll4hDetail.textContent = "4小时数据尚未生成（首次运行后可见）";
    }
  }

  const onePos = meta.one_hour?.bollinger?.position || "";
  const fourPos = meta.four_hour?.bollinger?.position || "";
  const daily = computeDailyMeta(state.data || []);
  const dailyAbove = daily?.bollinger && daily.close > daily.bollinger.mid;
  const dailyBelow = daily?.bollinger && daily.close < daily.bollinger.mid;

  const alignedUp   = /上方|上轨/.test(onePos) && /上方|上轨/.test(fourPos);
  const alignedDown = /下方|下轨/.test(onePos) && /下方|下轨/.test(fourPos);

  let biasLabel, biasText, biasClass;
  if (alignedUp && dailyAbove) {
    biasLabel = "三周期共振偏多"; biasClass = "up";
    biasText = "1H/4H/日线同在中轨上方；只在计划回踩区确认后顺势，不追涨。";
  } else if (alignedDown && dailyBelow) {
    biasLabel = "三周期共振偏空"; biasClass = "down";
    biasText = "1H/4H/日线同在中轨下方；只在计划反弹区受阻后顺势，不追跌。";
  } else if (alignedUp) {
    biasLabel = "短线偏多"; biasClass = "up";
    biasText = "1H/4H 偏多但日线未确认，仓位和持有时间都应降低。";
  } else if (alignedDown) {
    biasLabel = "短线偏弱"; biasClass = "down";
    biasText = "1H/4H 偏弱但日线未确认，防止低位追空后快速反抽。";
  } else {
    biasLabel = "区间震荡"; biasClass = "";
    biasText = "1H/4H/日线信号不一致，均衡区内保持观望。";
  }
  els.intradayStrategyBias.textContent = biasLabel;
  els.intradayStrategyBias.className = biasClass;
  els.intradayStrategyText.textContent = biasText;
}

function updateNewsPanel() {
  const snap = state.newsSnapshot;
  const articles = Array.isArray(snap?.articles) ? snap.articles : [];
  const updated = snap?.updated_at_utc ? formatDateTime(snap.updated_at_utc) : "--";

  // Small board card summary
  els.newsRealtimeStatus.textContent = articles.length ? `${articles.length} 条` : "暂无";
  els.newsRealtimeText.textContent = articles.length
    ? `最新 ${updated}。${articles.slice(0, 2).map((item) => item.title).filter(Boolean).join("；")}`
    : `最新 ${updated}，没有抓到新舆情。`;

  // Full ticker list (clickable cards)
  if (els.newsTickerList && articles.length > 0) {
    els.newsTickerMeta.textContent = `${articles.length} 条 · 数据更新于 ${updated} · 页面每 60 秒检查`;
    els.newsTickerList.innerHTML = articles.map((a) => {
      const title  = escapeHtml(a.title || "(无标题)");
      const source = escapeHtml(a.source || "未知来源");
      const pub    = a.published_at_utc
        ? formatDateTime(a.published_at_utc).replace(/^\d{4}\//, "")
        : "";
      const url = a.url || "#";
      const tag = a.url ? "a" : "div";
      const linkAttrs = a.url ? `href="${escapeHtml(url)}" target="_blank" rel="noopener"` : "";
      return `
        <${tag} class="ticker-card" ${linkAttrs}>
          <div class="ticker-card-title">${title}</div>
          <div class="ticker-card-meta">
            <span class="source">📰 ${source}</span>
            ${pub ? `<span>${pub}</span>` : ""}
          </div>
        </${tag}>
      `;
    }).join("");
  } else if (els.newsTickerList) {
    els.newsTickerList.innerHTML = "";
    els.newsTickerMeta.textContent = "暂无新闻数据";
  }
}

// Click the small card to expand/collapse the full ticker section
if (els.newsTickerToggle && els.newsTickerSection) {
  els.newsTickerToggle.addEventListener("click", () => {
    const willShow = els.newsTickerSection.hidden;
    els.newsTickerSection.hidden = !willShow;
    if (willShow) {
      els.newsTickerSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  });
}

function biasClass(text) {
  if (/多|强/.test(text)) return "bullish";
  if (/空|弱/.test(text)) return "bearish";
  return "neutral";
}

// Rule-based strategy from 1H/4H plus daily context. It replaces an AI plan
// whenever that plan is missing or older than the current market snapshot.
function computeIntradayStrategyFromMeta(meta) {
  if (!meta || !meta.one_hour || !meta.four_hour) return null;
  const h1 = meta.one_hour;
  const h4 = meta.four_hour;
  const b1 = h1.bollinger || {};
  const b4 = h4.bollinger || {};
  if (!b1.mid || !b1.upper || !b1.lower || !b4.mid || !b4.upper || !b4.lower) return null;

  const pos = (close, b) =>
    close > b.upper ? "上轨上方" :
    close > b.mid   ? "中轨上方" :
    close > b.lower ? "中轨下方" : "下轨下方";

  const pos1 = pos(h1.close, b1);
  const pos4 = pos(h4.close, b4);
  const above1 = h1.close > b1.mid;
  const above4 = h4.close > b4.mid;

  let bias, entry, stop, takeProfit, invalidation;
  if (above1 && above4) {
    bias = "短线偏多";
    entry = `回踩 1H 中轨 ${b1.mid.toFixed(0)} 后重新收回，且 4H 保持中轨 ${b4.mid.toFixed(0)} 上方再考虑多单`;
    stop = `1H 收盘跌破 ${Math.min(b1.lower, b4.mid).toFixed(0)} 即退出`;
    takeProfit = `1H 上轨 ${b1.upper.toFixed(0)} 先减仓，4H 上轨 ${b4.upper.toFixed(0)} 为扩展目标`;
    invalidation = `4H 收盘跌破中轨 ${b4.mid.toFixed(0)}，多头逻辑失效`;
  } else if (!above1 && !above4) {
    bias = "短线偏空";
    entry = `反弹至 1H 中轨 ${b1.mid.toFixed(0)} 后再次转弱，且 4H 仍在中轨 ${b4.mid.toFixed(0)} 下方再考虑空单`;
    stop = `1H 收盘突破 ${Math.max(b1.upper, b4.mid).toFixed(0)} 即退出`;
    takeProfit = `1H 下轨 ${b1.lower.toFixed(0)} 先减仓，4H 下轨 ${b4.lower.toFixed(0)} 为扩展目标`;
    invalidation = `4H 收盘站上中轨 ${b4.mid.toFixed(0)}，空头逻辑失效`;
  } else {
    bias = "区间震荡";
    entry = `1H 与 4H 方向冲突，等待价格离开 ${Math.min(b1.mid, b4.mid).toFixed(0)}-${Math.max(b1.mid, b4.mid).toFixed(0)} 均衡区`;
    stop = "未形成方向优势前不建立主动仓位";
    takeProfit = `形成突破后先观察 1H 上下轨 ${b1.lower.toFixed(0)} / ${b1.upper.toFixed(0)}`;
    invalidation = `1H 与 4H 重新回到相反两侧时，取消原方向计划`;
  }

  const daily = computeDailyMeta(state.data || []);
  let dailyNote = "";
  if (daily?.bollinger) {
    const bd = daily.bollinger;
    const dayAbove = daily.close > bd.mid;
    const dayPosition = dayAbove ? "中轨上方" : "中轨下方";
    dailyNote = ` / 日线${dayPosition} (中 ${bd.mid.toFixed(0)})`;
    if (above1 && above4 && dayAbove) bias = "1H/4H/日线共振偏多";
    if (!above1 && !above4 && !dayAbove) bias = "1H/4H/日线共振偏空";
  }

  const rsiNote = `1H RSI ${(h1.rsi14 ?? 0).toFixed(1)} / 4H RSI ${(h4.rsi14 ?? 0).toFixed(1)}`;
  return {
    bias,
    entry,
    stop,
    take_profit: takeProfit,
    invalidation,
    notes: `确定性规则（1H ${pos1} / 4H ${pos4}${dailyNote} · ${rsiNote}）。只有时效检查通过的 DeepSeek 结果才会替换本策略。`,
    _fallback: true,
  };
}

function updateAiPanel(ai) {
  els.aiBias.textContent = ai.bias || "--";
  els.aiBias.className = `bias-pill ${biasClass(ai.bias || "")}`;
  const status = ai.status === "ok" ? "DeepSeek" : "规则备用";
  const generated = ai.generated_at_utc ? formatDateTime(ai.generated_at_utc) : "--";
  const realtimeTag = ai.realtime_price ? ` | 实时价 ${ai.realtime_price}` : "";
  els.aiMeta.textContent = `${status} | 日线 ${ai.latest_date || "--"}${realtimeTag} | 生成 ${generated}`;
  els.aiSummary.textContent = ai.summary || "暂无 AI 摘要。";

  // Remember the latest AI payload so we can re-render the strategy panel
  // whenever the live 1H/4H meta refreshes.
  state.lastAi = ai;
  const freshness = assessAiFreshness(ai);
  if (els.aiFreshness) {
    els.aiFreshness.textContent = freshness.label;
    els.aiFreshness.className = `ai-freshness ${freshness.fresh ? "fresh" : "stale"}`;
  }
  const aiPanel = els.aiMeta?.closest(".ai-panel");
  if (aiPanel) aiPanel.classList.toggle("ai-stale", !freshness.fresh);

  let strategy = ai.intraday_strategy && typeof ai.intraday_strategy === "object" ? ai.intraday_strategy : null;
  const hasAiStrategy = strategy && (strategy.entry || strategy.stop || strategy.take_profit);
  if (!hasAiStrategy || !freshness.fresh) {
    strategy = computeIntradayStrategyFromMeta(state.intradayMeta);
    if (strategy && hasAiStrategy && !freshness.fresh) strategy._staleAi = true;
  }

  if (strategy) {
    els.aiStrategy.hidden = false;
    const title = strategy._fallback
      ? `1H / 4H 日内策略 <small class="strategy-source-note">· ${strategy._staleAi ? "AI 过期，规则接管" : "实时规则"}</small>`
      : `1H / 4H 日内策略 <small class="strategy-source-note fresh">· AI 时效通过</small>`;
    const heading = els.aiStrategy.querySelector("h3");
    if (heading) heading.innerHTML = title;

    const frame = ai.decision_frame && typeof ai.decision_frame === "object" ? ai.decision_frame : null;
    const rows = [
      ...(frame ? [
        ["证据强度", `${Number(frame.confidence || 0).toFixed(0)} / 100`],
        ["市场状态", frame.regime || "--"],
        ["不交易条件", frame.no_trade_condition || "--"],
      ] : []),
      ["短线方向", strategy.bias],
      ["入场观察", strategy.entry],
      ["止损/风控", strategy.stop],
      ["止盈目标", strategy.take_profit],
      ["失效条件", strategy.invalidation],
      ["备注", strategy.notes],
    ];
    els.aiStrategyGrid.innerHTML = rows.map(([label, value]) => {
      const cls = biasClass(label === "短线方向" ? (value || "") : "");
      return `
        <div class="strategy-item">
          <span>${escapeHtml(label)}</span>
          <strong class="${cls === "neutral" ? "" : (cls === "bullish" ? "up" : "down")}">${escapeHtml(value || "--")}</strong>
        </div>
      `;
    }).join("");
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

  // News tab empty-state flip
  if (els.aiNewsEmpty) els.aiNewsEmpty.hidden = hasNews;
  // Strategy tab empty-state flip
  if (els.aiStrategyEmpty) els.aiStrategyEmpty.hidden = Boolean(strategy);

  updateDistanceLine();
  // AI bias just landed → refresh position-calc stop default (if user
  // hasn't edited it) and re-score alignment (label depends on AI too).
  populatePosCalcDefaults();
  renderAlignmentScore();
}

// ── Distance to AI support/resistance ──────────────────────
function updateDistanceLine() {
  if (!els.lastDistance) return;
  const ai = state.lastAi;
  const watchLevels = ai && typeof ai.watch_levels === "object" && ai.watch_levels !== null
    ? ai.watch_levels : null;
  if (!watchLevels) {
    els.lastDistance.textContent = "--";
    els.lastDistance.className = "";
    return;
  }
  const resistance = Number(watchLevels.resistance || 0);
  const support    = Number(watchLevels.support    || 0);

  // Prefer live quote; fall back to analysis last close from full data
  let price = null;
  if (lastQuote && Number.isFinite(lastQuote.price)) price = lastQuote.price;
  else {
    const intradayClose = Number(state.intradayMeta?.one_hour?.close);
    if (Number.isFinite(intradayClose)) price = intradayClose;
    else {
      const last = state.data && state.data.length ? state.data[state.data.length - 1] : null;
      if (last) price = last.close;
    }
  }
  if (!Number.isFinite(price)) {
    els.lastDistance.textContent = "--";
    els.lastDistance.className = "";
    return;
  }

  const parts = [];
  if (resistance > 0) {
    if (price < resistance) parts.push(`<span>离 AI 压力 ${Math.round(resistance - price)}</span>`);
    else parts.push(`<span class="up">破压力 +${Math.round(price - resistance)}</span>`);
  }
  if (support > 0) {
    if (price > support) parts.push(`<span>离 AI 支撑 ${Math.round(price - support)}</span>`);
    else parts.push(`<span class="down">破支撑 -${Math.round(support - price)}</span>`);
  }
  if (parts.length === 0) {
    els.lastDistance.textContent = "--";
  } else {
    els.lastDistance.innerHTML = parts.join(" · ");
  }
}

// ── AI panel tab switching ─────────────────────────────────
document.querySelectorAll(".ai-tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.tab;
    document.querySelectorAll(".ai-tab").forEach((b) => b.classList.toggle("active", b === btn));
    document.querySelectorAll(".ai-tab-content").forEach((c) => {
      c.hidden = c.dataset.tab !== target;
    });
  });
});

// ── Sibling widget ─────────────────────────────────────────
async function autoLoadSibling() {
  if (location.protocol === "file:") return;
  const sib = siblingSymbol();
  const sibLbl = siblingLabel();
  const dir = sib.toLowerCase();
  const cacheBust = `t=${Date.now()}`;

  // Reset displayed sibling identity (so a stale prior symbol doesn't linger)
  if (els.siblingEmoji) els.siblingEmoji.textContent = sibLbl.emoji;
  if (els.siblingName)  els.siblingName.textContent  = `${sibLbl.name} ${sibLbl.code}`;

  let sourceMeta = null;
  let ai = null;
  try {
    const [smResp, aiResp] = await Promise.all([
      fetchWithRetry(`data/${dir}/source_meta.json?${cacheBust}`, { cache: "no-store" }),
      fetchWithRetry(`data/${dir}/ai_analysis.json?${cacheBust}`, { cache: "no-store" }),
    ]);
    if (smResp.ok) sourceMeta = await smResp.json();
    if (aiResp.ok) ai = await aiResp.json();
  } catch (_) {}

  // Pick a price: prefer AI realtime_price, then source_meta.live_bar.close, then latest_close.
  let price = null;
  if (ai && Number.isFinite(Number(ai.realtime_price))) price = Number(ai.realtime_price);
  else if (sourceMeta && sourceMeta.live_bar && Number.isFinite(Number(sourceMeta.live_bar.close))) {
    price = Number(sourceMeta.live_bar.close);
  } else if (sourceMeta && Number.isFinite(Number(sourceMeta.latest_close))) {
    price = Number(sourceMeta.latest_close);
  }

  // Compute change_pct: prefer live_bar deltas, then AI-provided, else derive from open/close.
  let changePct = null;
  let changeAbs = null;
  if (sourceMeta && sourceMeta.live_bar) {
    const lb = sourceMeta.live_bar;
    const ref = Number(lb.prev_close ?? lb.open);
    if (Number.isFinite(ref) && ref > 0 && Number.isFinite(price)) {
      changeAbs = price - ref;
      changePct = changeAbs / ref;
    }
  }
  if (changePct === null && ai && ai.change_pct) {
    // Accept string "+1.23%" or number 0.0123
    const m = String(ai.change_pct).match(/^\s*([+-]?\d+(?:\.\d+)?)/);
    if (m) changePct = Number(m[1]) / (String(ai.change_pct).includes("%") ? 100 : 1);
  }

  state.sibling = { symbol: sib, sourceMeta, ai, price, changePct, changeAbs };

  // Populate DOM
  if (els.siblingPrice) {
    els.siblingPrice.textContent = Number.isFinite(price) ? price.toFixed(0) : "--";
  }
  if (els.siblingChange) {
    if (Number.isFinite(changePct)) {
      els.siblingChange.textContent = formatPct(changePct);
      els.siblingChange.className = `pct ${changePct >= 0 ? "up" : "down"}`;
    } else {
      els.siblingChange.textContent = "--";
      els.siblingChange.className = "pct";
    }
  }
  if (els.siblingBias) {
    const bias = ai && ai.bias ? String(ai.bias) : "";
    const summary = ai && ai.summary ? String(ai.summary) : "";
    if (bias) {
      const short = summary ? ` · ${summary.slice(0, 40)}${summary.length > 40 ? "…" : ""}` : "";
      els.siblingBias.textContent = `AI 观点：${bias}${short}`;
    } else if (sourceMeta && sourceMeta.latest_date) {
      els.siblingBias.textContent = `${sibLbl.code} 数据已就绪 · ${sourceMeta.latest_date}，AI 分析尚未生成`;
    } else {
      els.siblingBias.textContent = `${sibLbl.code} 数据尚未生成`;
    }
  }
}

// ── Real-time quote ──────────────────────────────────────────────────────────

let lastQuote = null;

// Session predicates delegate to marketStatus() so lunch and off-hours never
// masquerade as active trading.
function bjHour()         { return bjParts().hour; }
function isNightSession() { return marketStatus() === "night-open"; }
function isDaySession()   { return marketStatus() === "day-open"; }
function isTrading()      { return isDaySession() || isNightSession(); }

function sinaFuturesUrl(node) {
  return "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/" +
    `Market_Center.getHQFuturesData?page=1&num=100&sort=position&asc=0&node=${node}&base=futures`;
}

function normalizeLiveContract(item) {
  const price = Number(item?.trade);
  if (!(price > 0)) return null;
  const previousClose = Number(item.preclose || 0);
  const previousSettlement = Number(item.presettlement || 0) || Number(item.prevsettlement || 0);
  const reference = previousSettlement || previousClose;
  const change = reference > 0 ? price - reference : 0;
  return {
    symbol: String(item.symbol || "").toUpperCase(),
    name: String(item.name || ""),
    price,
    open: Number(item.open || 0),
    high: Number(item.high || 0),
    low: Number(item.low || 0),
    volume: Number(item.volume || 0),
    open_interest: Number(item.position || 0),
    prev_close: previousClose,
    prev_settlement: previousSettlement,
    reference_price: reference,
    reference_type: previousSettlement ? "previous_settlement" : "previous_close",
    change,
    change_ratio: reference > 0 ? change / reference : 0,
    tradedate: String(item.tradedate || ""),
    ticktime: String(item.ticktime || ""),
  };
}

function monthsToDelivery(contract, tradingDay) {
  const match = String(contract || "").toUpperCase().match(/^[A-Z]+(\d{2})(\d{2})$/);
  if (!match) return null;
  const year = 2000 + Number(match[1]);
  const month = Number(match[2]);
  const dayMatch = String(tradingDay || "").match(/^(\d{4})-(\d{2})/);
  if (!(month >= 1 && month <= 12) || !dayMatch) return null;
  return (year - Number(dayMatch[1])) * 12 + month - Number(dayMatch[2]);
}

function buildLiveContractBridge(board, symbol) {
  if (!Array.isArray(board)) return null;
  const prefix = symbol.replace(/0$/, "");
  const pattern = new RegExp(`^${prefix}\\d{4}$`);
  const continuous = normalizeLiveContract(board.find((item) => String(item.symbol || "").toUpperCase() === symbol));
  const candidates = board
    .filter((item) => pattern.test(String(item.symbol || "").toUpperCase()))
    .map(normalizeLiveContract)
    .filter((item) => item && item.open_interest > 0)
    .sort((a, b) => b.open_interest - a.open_interest || b.volume - a.volume);
  if (!candidates.length) return null;
  const main = candidates[0];
  const secondary = candidates[1] || null;
  const ratio = secondary && main.open_interest > 0 ? secondary.open_interest / main.open_interest : 0;
  const spread = secondary ? secondary.price - main.price : null;
  const totalOi = candidates.reduce((sum, item) => sum + item.open_interest, 0);
  const monthsLeft = monthsToDelivery(main.symbol, main.tradedate || continuous?.tradedate);
  let rollState = "stable";
  let rollLabel = "主力稳定";
  let rollReason = "主力持仓仍明显领先，暂未出现高强度换月信号。";
  if ((Number.isFinite(monthsLeft) && monthsLeft <= 1) || ratio >= 0.85) {
    rollState = "urgent";
    rollLabel = "临近换月";
    rollReason = "主力临近交割月或次主力持仓已接近主力，执行前必须复核流动性。";
  } else if ((Number.isFinite(monthsLeft) && monthsLeft <= 2) || ratio >= 0.50) {
    rollState = "watch";
    rollLabel = "监控移仓";
    rollReason = "主力进入交割月前约两个月或次主力持仓超过主力一半。";
  }
  const monthPressure = !Number.isFinite(monthsLeft) ? 10 : monthsLeft <= 0 ? 100 : monthsLeft === 1 ? 80 : monthsLeft === 2 ? 50 : monthsLeft === 3 ? 25 : 10;
  const specs = state.contractBridge?.contract_specs || { multiplier: 10, tick_size: 1, tick_value: 10, rule_reference: "大商所〔2026〕32号" };
  const mappingVerified = Boolean(continuous
    && Math.abs(continuous.price - main.price) <= Number(specs.tick_size || 1)
    && continuous.open_interest === main.open_interest);
  return {
    ...(state.contractBridge || {}),
    source: "Sina Market Center · 浏览器实时核对",
    symbol,
    updated_at_utc: new Date().toISOString(),
    trading_day: main.tradedate || continuous?.tradedate || "",
    market_time: main.ticktime || "",
    continuous,
    main,
    secondary,
    candidates: candidates.slice(0, 6),
    mapping_verified: mappingVerified,
    mapping_note: mappingVerified ? `${symbol} 当前行情与 ${main.symbol} 的价格及持仓一致。` : `${symbol} 与 ${main.symbol} 未完全一致。`,
    main_open_interest_share: totalOi ? main.open_interest / totalOi : 0,
    secondary_open_interest_ratio: ratio,
    secondary_spread: spread,
    secondary_spread_ratio: spread !== null && main.price ? spread / main.price : null,
    spread_structure: spread > 0 ? "远月升水" : spread < 0 ? "远月贴水" : "平水",
    months_to_delivery_month: monthsLeft,
    roll_state: rollState,
    roll_label: rollLabel,
    roll_score: Math.round(Math.max(monthPressure, ratio * 100)),
    roll_reason: rollReason,
    contract_specs: specs,
  };
}

async function fetchRealtimeQuote() {
  try {
    const node = activeLabel().sinaNode;
    const r = await fetch(`${sinaFuturesUrl(node)}&_=${Date.now()}`, { cache: "no-store" });
    if (!r.ok) return null;
    const data = await r.json();
    const sym = state.activeSymbol;
    const hit = Array.isArray(data) && data.find(item => item.symbol === sym);
    if (!hit || !+hit.trade) return null;
    const price     = +hit.trade;
    const prevClose = +hit.preclose;
    const prevSettlement = Number(hit.presettlement || 0) || Number(hit.prevsettlement || 0);
    const referencePrice = prevSettlement || prevClose;
    const bridge = buildLiveContractBridge(data, sym);
    return {
      price,
      high:      +hit.high,
      low:       +hit.low,
      open:      +hit.open,
      prevClose,
      prevSettlement,
      referencePrice,
      volume:    +hit.volume,
      change:    price - referencePrice,
      changePct: referencePrice > 0 ? (price - referencePrice) / referencePrice : 0,
      tradedate: hit.tradedate || "",
      ticktime:  hit.ticktime  || "",
      receivedAt: Date.now(),
      contractBridge: bridge,
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

  updateDistanceLine();
}

async function startRealtimeFeed() {
  if (location.protocol === "file:") return;
  const tick = async () => {
    const q = await fetchRealtimeQuote();
    if (q) {
      lastQuote = q;
      if (q.contractBridge) {
        state.contractBridge = q.contractBridge;
        renderContractBridge(state.contractBridge);
      }
    }
    updateLiveBar(lastQuote);
    updateIntradayPanel();
    draw(); // redraws chart with updated live bar; applyRealtimeQuote called at end of draw
  };
  await tick();
  setInterval(tick, 5000);
}

window.addEventListener("resize", draw);

// ── Active-symbol labels + switcher ────────────────────────
function applyActiveSymbolLabels() {
  const lbl = activeLabel();
  const title = `大连${lbl.name} ${lbl.code} 连续短线分析`;
  document.title = title;
  if (els.topbarTitle) els.topbarTitle.textContent = title;
  if (els.eyebrowText) {
    els.eyebrowText.textContent = lbl.code === "P0" ? "DCE Palm Oil Continuous" : "DCE Soybean Oil Continuous";
  }
  if (els.contractPill) {
    els.contractPill.textContent = `${lbl.exchange} ${lbl.code} 1H / 4H / 日线`;
  }
  // Toggle button active class
  if (els.symBtns) {
    els.symBtns.forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.sym === state.activeSymbol);
    });
  }
  // Sibling widget baseline (fill immediately; autoLoadSibling refreshes data)
  const sibLbl = siblingLabel();
  if (els.siblingEmoji) els.siblingEmoji.textContent = sibLbl.emoji;
  if (els.siblingName)  els.siblingName.textContent  = `${sibLbl.name} ${sibLbl.code}`;
  if (els.siblingPrice) els.siblingPrice.textContent = "--";
  if (els.siblingChange) {
    els.siblingChange.textContent = "--";
    els.siblingChange.className = "pct";
  }
  if (els.siblingBias) els.siblingBias.textContent = "加载中...";
}

function reloadAll() {
  // Reset symbol-specific state so the previous symbol's data does not linger
  state.data = makeDemoData();
  state.imported = false;
  state.autoLoaded = false;
  state.dataMeta = null;
  state.intradayMeta = null;
  state.newsSnapshot = null;
  state.contractBridge = null;
  state.modelValidation = null;
  state.lastAi = null;
  state.lastAskResponse = null;
  state.decisionModel = null;
  state.visibleStart = null;
  state.visibleCount = null;
  state.hoverIndex = null;
  state.twoDay = null;
  lastQuote = null;
  // Pos-calc: symbol-scoped defaults should re-populate on switch
  resetPosCalcUserEdited();
  // Kill any in-flight ask polling so it doesn't leak into the new symbol's
  // ask_response.json (dataPath uses the CURRENT activeSymbol on each tick).
  if (askPollInterval) {
    clearInterval(askPollInterval);
    askPollInterval = null;
    if (els.askBtn) els.askBtn.disabled = false;
  }
  // Hide previous symbol's ask history and clear input
  if (els.askResponse) els.askResponse.hidden = true;
  if (els.askInput) els.askInput.value = "";
  setAskStatus("", "");
  // Hide accuracy line while it reloads
  if (els.aiAccuracy) els.aiAccuracy.hidden = true;
  applyActiveSymbolLabels();
  renderContractBridge(null);
  renderModelValidation(null);
  draw();
  autoLoadContractBridge();
  autoLoadModelValidation();
  autoLoadCsv();
  autoLoadAiAnalysis();
  autoLoadIntradayMeta();
  autoLoadNewsSnapshot();
  autoLoadSibling();
  autoLoadAccuracy();
  autoLoadAskResponse();
  // Overseas is shared (not symbol-scoped) — still safe to refresh on switch
  autoLoadOverseas();
}

function setActiveSymbol(sym) {
  if (sym !== "P0" && sym !== "Y0") return;
  if (state.activeSymbol === sym) return;
  state.activeSymbol = sym;
  try { localStorage.setItem("activeSymbol", sym); } catch (_) {}
  reloadAll();
}

if (els.symBtns) {
  els.symBtns.forEach((btn) => {
    btn.addEventListener("click", () => setActiveSymbol(btn.dataset.sym));
  });
}
if (els.siblingLink) {
  els.siblingLink.addEventListener("click", (e) => {
    e.preventDefault();
    setActiveSymbol(siblingSymbol());
  });
}

// Theme
initTheme();
if (els.themeToggleBtn) els.themeToggleBtn.addEventListener("click", toggleTheme);

// Market status
updateMarketStatus();
setInterval(updateMarketStatus, 30 * 1000);

applyActiveSymbolLabels();
renderContractBridge(null);
renderModelValidation(null);
draw();
autoLoadContractBridge();
autoLoadModelValidation();
autoLoadCsv();
autoLoadAiAnalysis();
autoLoadIntradayMeta();
autoLoadNewsSnapshot();
autoLoadSibling();
autoLoadAccuracy();
autoLoadAskResponse();
autoLoadOverseas();
startRealtimeFeed();
setInterval(autoLoadCsv, 60 * 1000);
setInterval(autoLoadContractBridge, 60 * 1000);
setInterval(autoLoadModelValidation, 5 * 60 * 1000);
setInterval(autoLoadAiAnalysis, 60 * 1000);
setInterval(autoLoadIntradayMeta, 60 * 1000);
setInterval(autoLoadNewsSnapshot, 60 * 1000);
setInterval(autoLoadSibling, 60 * 1000);
setInterval(autoLoadAccuracy, 60 * 1000);
setInterval(autoLoadOverseas, 60 * 1000);
