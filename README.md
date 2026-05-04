# Tamil Nadu Election Results Live Tracker

A lightweight live dashboard for Tamil Nadu election trends using the Election Commission of India JSON feed.

Source feed:
https://results.eci.gov.in/ResultAcGenMay2026/election-json-S22-live.json

Trends are provisional. Final official data is published by ECI in Form-20.

## Files

- `scraper.py` fetches the ECI JSON and writes the Tamil Nadu S22 snapshot to `data.json`.
- `index.html` is the responsive GitHub Pages dashboard.
- `scriptable-widget.js` is a medium iPhone Scriptable widget.
- `.github/workflows/update.yml` refreshes `data.json` every 5 minutes.
- `.nojekyll` makes GitHub Pages serve files directly.

## Run Locally

```bash
python scraper.py
python -m http.server 8000
```

Open:

```text
http://localhost:8000
```

## Create GitHub Repo and Push

```bash
git init
git add .
git commit -m "Initial TN election tracker"
git branch -M main
git remote add origin <repo-url>
git push -u origin main
```

## Enable GitHub Pages

1. Go to repository `Settings`.
2. Go to `Pages`.
3. Select `Deploy from branch`.
4. Choose branch `main`.
5. Choose folder `root`.
6. Save.

Your dashboard will be available at:

```text
https://<username>.github.io/<repo-name>/
```

Your data URL will be:

```text
https://<username>.github.io/<repo-name>/data.json
```

## Run GitHub Action Manually

1. Go to `Actions`.
2. Select `Update TN Election Results`.
3. Click `Run workflow`.

The workflow also runs every 5 minutes and commits `data.json` only when it changes.

## Install Scriptable Widget

1. Install Scriptable on iPhone.
2. Open `scriptable-widget.js`.
3. Replace `DATA_URL` with:

```js
https://<username>.github.io/<repo-name>/data.json
```

4. Copy the code into Scriptable.
5. Add a Scriptable medium widget to the Home Screen.
6. Edit the widget and select the script.

iOS controls widget refresh frequency, so the widget may not update every minute even though the script requests periodic refreshes.
