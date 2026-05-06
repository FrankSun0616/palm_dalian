# Deploy Online

The current validated data source is DCE palm oil continuous contract `P0` through AKShare/Sina.

## What Can Auto-Update

- The webpage is static HTML/CSS/JS.
- The Python script `update_data.py` fetches the newest `P0` daily K-line and writes:
  - `data/palm_oil_p0_daily.csv`
  - `data/source_meta.json`
- The page auto-loads this CSV when served over HTTP.
- The page also checks for a refreshed CSV every 1 minute.

## GitHub Pages Setup

1. Create or use the GitHub repository named `palm_dalian`.
2. Upload this folder's files to the repository root, or push this local git repository.
3. In GitHub, open `Settings -> Pages`.
4. Set source to `GitHub Actions`.
5. Run the workflow `Update palm oil data`, or push a new commit.
6. Open the generated GitHub Pages URL.

Expected project URL after Pages is enabled:

```text
https://franksun0616.github.io/palm_dalian/
```

The workflow `.github/workflows/update-data.yml` is set to run every 5 minutes, which is the shortest interval supported by GitHub Actions scheduled workflows.

GitHub can throttle scheduled workflows, so exact execution time is not guaranteed.

The same workflow updates the CSV and deploys the static site to GitHub Pages.

## DeepSeek AI Analysis

To enable AI analysis, add this GitHub Actions secret:

```text
DEEPSEEK_API_KEY
```

The key must not be committed to the repository. When configured, `update_data.py` writes `data/ai_analysis.json`; the webpage refreshes that file every minute.

You can also run it manually from GitHub Actions with `Run workflow`.

## Important Limitation

This validates the `P0` continuous contract for 大连棕榈油.
