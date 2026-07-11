# 大连油脂连续合约交易分析终端

面向大连商品交易所棕榈油 `P0` 与豆油 `Y0` 连续合约的静态分析网页。页面整合日线、1H/2H/4H、布林通道、ADX、RSI、关键价位、海外油脂市场、新闻快照与 DeepSeek 分析。

线上地址：<https://franksun0616.github.io/palm_dalian/>

## 交易决策层

- 交易许可：结合市场时段、数据可信度、多周期共振、均衡区和盈亏比，输出允许做多、允许做空、观望、暂停或休市。
- 双向计划：多头和空头同时给出触发区、止损、两个目标及对应盈亏比。
- 数据保护：AI 过期或落后于行情时自动降级为历史参考，由确定性规则接管策略。
- 仓位控制：推荐手数同时受单笔风险预算和最大保证金占用限制，并计入滑点。
- 数据口径：`P0/Y0` 是连续合约分析序列，不是可直接下单的具体月份合约。执行前必须核对主力月份、换月价差、流动性和交易所保证金。

## 数据更新

- 浏览器在交易时段内每 5 秒尝试读取新浪实时行情。
- 页面每 60 秒检查仓库中的日线、小时线、新闻、海外行情和 AI JSON。
- GitHub Actions 的数据任务配置为每 5 分钟触发，但 GitHub 可能延迟或节流，不能承诺分钟级后台落盘。
- DeepSeek 配置为每 3 小时自动运行一次，北京时间约为 08:00、11:00、14:00、17:00、20:00、23:00；GitHub 实际执行时间可能延后。

## 本地运行

直接使用 HTTP 服务打开，避免 `file://` 阻止 CSV/JSON 请求：

```bash
python3 -m http.server 8080
```

访问 <http://127.0.0.1:8080/>。

更新真实数据需要安装依赖：

```bash
python3 -m pip install -r requirements.txt
RUN_AI_ANALYSIS=false python3 update_data.py
```

## DeepSeek

在 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 中配置：

```text
DEEPSEEK_API_KEY
```

页面不会保存或发送 GitHub PAT，也不会把 DeepSeek key 放到浏览器。手动分析按钮只打开 GitHub Actions 页面，由已登录的仓库管理员运行 `Update palm oil data`，并保持 `Generate DeepSeek AI analysis = true`。

## 说明

本项目用于行情研究和交易纪律辅助，不构成投资建议。期货存在杠杆、跳空、流动性和保证金追加风险。
