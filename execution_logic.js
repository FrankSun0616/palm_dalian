(function initPalmExecutionLogic(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.PalmExecutionLogic = api;
}(typeof globalThis !== "undefined" ? globalThis : this, () => {
  const EXECUTION_ASSUMPTIONS = Object.freeze({
    slippagePointsPerSide: 2,
    feeYuanPerLotPerSide: 3,
    minNetRr: 1.5,
  });

  function executionRoundTripCostPoints(
    multiplier = 10,
    slippagePerSide = EXECUTION_ASSUMPTIONS.slippagePointsPerSide,
    feePerSide = EXECUTION_ASSUMPTIONS.feeYuanPerLotPerSide,
  ) {
    const safeMultiplier = Number.isFinite(multiplier) && multiplier > 0 ? multiplier : 10;
    const slippage = Math.max(0, Number(slippagePerSide) || 0);
    const fee = Math.max(0, Number(feePerSide) || 0);
    return slippage * 2 + (fee * 2) / safeMultiplier;
  }

  function decideTradeGate({
    status,
    confidence,
    inNoTradeZone,
    compositeSignal,
    longSetup,
    shortSetup,
    contractBridge,
    modelValidation,
  }) {
    const preferredDirection = compositeSignal >= 0 ? "long" : "short";
    const preferredSetup = preferredDirection === "long" ? longSetup : shortSetup;
    const preferredRr = Math.max(0, Number(preferredSetup?.rr1) || 0);
    const mappingVerified = Boolean(contractBridge?.main?.symbol && contractBridge.mapping_verified === true);
    const rollState = String(contractBridge?.roll_state || "unknown");
    const strategyVersion = String(modelValidation?.strategy_version || "");
    const validationSameScope = /^intraday(?:[-_]|$)/i.test(strategyVersion);
    const intradayValidationStatus = validationSameScope
      ? String(modelValidation?.status || "missing")
      : "missing";
    const intradayValidated = intradayValidationStatus === "positive";
    const context = {
      preferredDirection,
      preferredRr,
      mappingVerified,
      rollState,
      validationSameScope,
      intradayValidationStatus,
      intradayValidated,
    };
    const result = (label, kind, reason) => ({ label, kind, reason, ...context });

    if (status === "weekend") {
      return result("休市", "neutral", "市场关闭，当前计划只用于下个交易时段预案。");
    }
    if (status === "closed" || status === "day-break") {
      return result("等待开盘", "neutral", "非交易时段，不把静态报价当作可执行价格。");
    }
    if (!Number.isFinite(confidence?.quoteAge) || confidence.quoteAge > 1.5) {
      return result("暂停交易", "blocked", "实时行情未接通或已经过期，不使用后台快照代替执行价格。");
    }
    if (!Number.isFinite(confidence?.intradayAge) || confidence.intradayAge > 120) {
      return result("暂停交易", "blocked", "小时线后台快照超过两小时，等待刷新后再评估。");
    }
    if (!mappingVerified) {
      return result("暂停交易", "blocked", "连续合约与可交易主力月份尚未核对，先在交易软件确认具体合约。");
    }
    if (rollState === "urgent") {
      return result("暂停交易", "blocked", "主力合约处于紧急换月状态，先完成移仓并核对价差与流动性。");
    }
    if (rollState === "unknown") {
      return result("暂停交易", "blocked", "换月状态未知，不能把连续合约信号直接用于具体月份下单。");
    }
    if (confidence.score < 65) {
      return result("暂停交易", "blocked", "数据可信度不足，先恢复实时行情、主力映射或小时线快照。");
    }
    if (inNoTradeZone && Math.abs(compositeSignal) < 35) {
      return result("观望", "neutral", "价格处于多周期均衡区，方向优势不足。");
    }

    const longReady = compositeSignal >= 25 && longSetup.rr1 >= EXECUTION_ASSUMPTIONS.minNetRr;
    const shortReady = compositeSignal <= -25 && shortSetup.rr1 >= EXECUTION_ASSUMPTIONS.minNetRr;
    if (!longReady && !shortReady) {
      return result("仅条件单", "neutral", `方向共振或净首目标盈亏比尚未达到 ${EXECUTION_ASSUMPTIONS.minNetRr.toFixed(1)}R 门槛。`);
    }

    const sideLabel = longReady ? "多头" : "空头";
    const sideKind = longReady ? "up" : "down";
    if (validationSameScope && intradayValidationStatus === "rejected") {
      return result("暂停交易", "blocked", `同口径 1H/4H ${sideLabel}规则样本外无优势，不进入实盘许可。`);
    }
    if (!intradayValidated) {
      const evidence = validationSameScope
        ? "同口径日内优势尚未证实"
        : "尚无同口径 1H/4H 日内样本外验证";
      return result(`${sideLabel}候选`, sideKind, `${sideLabel}共振且净首目标达到门槛，但${evidence}；只用于触发观察或模拟盘。`);
    }
    if (rollState === "watch") {
      return result(`${sideLabel}候选`, sideKind, "日内验证与净盈亏比通过，但当前处于移仓监控；须在交易软件确认具体月份、价差与流动性。");
    }
    return result(`允许做${longReady ? "多" : "空"}`, sideKind, `${sideLabel}共振、净盈亏比和同口径样本外验证均达到门槛，仍须等待触发确认。`);
  }

  return Object.freeze({
    EXECUTION_ASSUMPTIONS,
    executionRoundTripCostPoints,
    decideTradeGate,
  });
}));
