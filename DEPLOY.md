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
- `.github/workflows/ask.yml`
  - Manual DeepSeek question with symbol and question inputs.
  - Commits the answer JSON; the resulting push triggers the normal Pages workflow.
- `.github/workflows/notify.yml`
  - Evaluates configured notification rules.

GitHub scheduled workflows are best-effort. The five-minute cron is not a guarantee that a new commit or deployment will occur every five minutes. The webpage distinguishes browser polling time from backend data time.

## Security invariants

- Never commit `DEEPSEEK_API_KEY`, a GitHub PAT, or any other credential.
- Never embed a token in `app.js`, HTML, Base64 text, URL parameters or browser storage.
- Static GitHub Pages cannot securely perform authenticated workflow dispatches. Manual buttons must open the GitHub Actions page and rely on the user's authenticated GitHub session.

## Contract scope

`P0` and `Y0` are continuous analysis series. They are useful for trend continuity but do not replace the actual tradable delivery-month contract. Before execution, confirm the main contract, spread around rollover, liquidity, tick size and current margin requirements.
