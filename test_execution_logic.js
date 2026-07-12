"use strict";

const assert = require("node:assert/strict");
const {
  EXECUTION_ASSUMPTIONS,
  executionRoundTripCostPoints,
  decideTradeGate,
} = require("./execution_logic.js");

assert.equal(executionRoundTripCostPoints(10, 2, 3), 4.6);
assert.equal(EXECUTION_ASSUMPTIONS.minNetRr, 1.5);

const base = {
  status: "day-open",
  confidence: { quoteAge: 0.1, intradayAge: 5, score: 92 },
  inNoTradeZone: false,
  compositeSignal: 50,
  longSetup: { rr1: 1.8 },
  shortSetup: { rr1: 0.7 },
  contractBridge: {
    main: { symbol: "P2609" },
    mapping_verified: true,
    roll_state: "stable",
  },
  modelValidation: {
    strategy_version: "daily-trend-breakout-pullback-v1",
    status: "positive",
  },
};
const gate = (patch = {}) => decideTradeGate({ ...base, ...patch });

assert.equal(gate({
  contractBridge: { main: { symbol: "P2609" }, mapping_verified: false, roll_state: "stable" },
}).label, "暂停交易");
assert.match(gate({
  contractBridge: { main: { symbol: "P2609" }, mapping_verified: false, roll_state: "stable" },
}).reason, /主力月份尚未核对/);

assert.match(gate({
  contractBridge: { main: { symbol: "P2609" }, mapping_verified: true, roll_state: "urgent" },
}).reason, /紧急换月/);

assert.equal(gate().label, "多头候选");
assert.equal(gate().intradayValidated, false);

assert.equal(gate({
  modelValidation: { strategy_version: "intraday-mtf-v1", status: "positive" },
}).label, "允许做多");

assert.equal(gate({
  modelValidation: { strategy_version: "intraday-mtf-v1", status: "positive" },
  contractBridge: { main: { symbol: "P2609" }, mapping_verified: true, roll_state: "watch" },
}).label, "多头候选");

assert.equal(gate({
  modelValidation: { strategy_version: "intraday-mtf-v1", status: "rejected" },
}).label, "暂停交易");

assert.equal(gate({ longSetup: { rr1: 1.49 } }).label, "仅条件单");

assert.equal(gate({
  compositeSignal: -50,
  longSetup: { rr1: 0.7 },
  shortSetup: { rr1: 1.8 },
  modelValidation: { strategy_version: "intraday-mtf-v1", status: "positive" },
}).label, "允许做空");

console.log("execution logic: OK");
