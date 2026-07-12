# GitHub Pages Deployment

## Repository settings

1. Open `Settings -> Pages`.
2. Set the source to `GitHub Actions`.
3. Add the Actions secret `DEEPSEEK_API_KEY`.
4. Run `Update palm oil data` once, then open <https://franksun0616.github.io/palm_dalian/>.

## Workflows

- `.github/workflows/update-data.yml`
  - Data schedule: `*/5 * * * *`.
  - DeepSeek schedule: `0 */3 * * *`.
  - Manual dispatch keeps the `run_ai_analysis` toggle.
  - Updates both `P0` and `Y0`, commits generated files, uploads the Pages artifact and deploys it.
  - Uses `deepseek-v4-pro` with thinking enabled and high reasoning effort for both symbols in parallel.
- `.github/workflows/ask.yml`
  - Manual DeepSeek question with symbol and question inputs.
  - Commits the answer JSON; the resulting push triggers the normal Pages workflow.
- `.github/workflows/notify.yml`
  - Evaluates configured notification rules.

GitHub scheduled workflows are best-effort. The five-minute cron is not a guarantee that a new commit or deployment will occur every five minutes. The webpage distinguishes browser polling time from backend data time.

## Credential model

- `DEEPSEEK_API_KEY` remains an Actions Secret and is never sent to the browser.
- The repository owner explicitly chose a one-click public workflow dispatch, so `app.js` contains a Base64-encoded GitHub PAT. This is public exposure, not encryption; anyone who can inspect the page can recover it.
- The exposed PAT should be limited to this repository and only the permissions required to dispatch Actions. Rotating or revoking it disables the one-click button until `app.js` is updated.

## Contract scope

`P0` and `Y0` are continuous analysis series. They are useful for trend continuity but do not replace the actual tradable delivery-month contract. Before execution, confirm the main contract, spread around rollover, liquidity, tick size and current margin requirements.
