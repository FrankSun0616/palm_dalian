# 大连棕榈油连续行情 K 线分析

这是一个纯静态网页，用于查看大连棕榈油 `P0` 连续合约日线的 K 线、规则技术分析和 DeepSeek 日线分析。

## 使用方法

直接打开 `index.html` 可以看内置示例数据。

当前已验证的数据口径是大连商品交易所棕榈油 `P0` 连续合约，即 `棕榈油连续`。

如果要自动加载最新 CSV，请先更新数据，然后用本地服务器打开：

```bash
.venv/bin/python update_data.py
python3 -m http.server 8080
```

然后访问 `http://localhost:8080`。

页面也支持手动导入 CSV 替换行情。

线上部署和自动更新见 `DEPLOY.md`。

DeepSeek AI 分析需要在 GitHub repo 的 `Settings -> Secrets and variables -> Actions` 中添加 secret：

```text
DEEPSEEK_API_KEY
```

AI 分析现在只会在 GitHub Actions 手动运行时生成：

```text
Actions -> Update palm oil data -> Run workflow -> Generate DeepSeek AI analysis = true
```

自动定时任务只更新日线 CSV，不自动调用 DeepSeek。

网页里的 `触发 DeepSeek 分析` 按钮会打开 GitHub Actions 手动运行页面；为了保护 GitHub token 和 DeepSeek key，静态网页不会直接从浏览器调用 workflow。

GitHub Pages 目标地址：

```text
https://franksun0616.github.io/palm_dalian/
```

## CSV 字段

```csv
date,open,high,low,close,volume
2026-05-06,7800,7890,7750,7860,523000
```

## 说明

页面中的趋势信号基于均线、涨跌、支撑压力和波动率做技术分析演示，不构成投资建议。
