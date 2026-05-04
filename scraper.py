import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


ECI_JSON_URL = "https://results.eci.gov.in/ResultAcGenMay2026/election-json-S22-live.json"
OUTPUT_PATH = Path("data.json")
STATE_CODE = "S22"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://results.eci.gov.in/ResultAcGenMay2026/partywiseresult-S22.htm",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}

RETRY_STATUS_CODES = {403, 408, 429, 500, 502, 503, 504}


def log(message):
    print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {message}", flush=True)


def load_previous_data():
    if not OUTPUT_PATH.exists():
        return None

    try:
        with OUTPUT_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        log(f"Could not read existing {OUTPUT_PATH}: {exc}")
        return None


def fetch_eci_json(max_attempts=5):
    last_error = None

    with requests.Session() as session:
        session.headers.update(HEADERS)

        for attempt in range(1, max_attempts + 1):
            try:
                log(f"Fetching ECI JSON, attempt {attempt}/{max_attempts}")
                response = session.get(ECI_JSON_URL, timeout=25)
                log(f"ECI response status: {response.status_code}")

                if response.status_code == 200:
                    return response.json()

                preview = response.text[:240].replace("\n", " ")
                last_error = RuntimeError(
                    f"unexpected status {response.status_code}; body preview: {preview}"
                )

                if response.status_code not in RETRY_STATUS_CODES:
                    break
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = exc
                log(f"Network retryable error: {exc}")
            except requests.RequestException as exc:
                last_error = exc
                log(f"Request failed: {exc}")
                break
            except json.JSONDecodeError as exc:
                last_error = exc
                log(f"Response was not valid JSON: {exc}")
                break

            if attempt < max_attempts:
                delay = min(45, (2 ** (attempt - 1)) + random.uniform(0.5, 2.5))
                log(f"Waiting {delay:.1f}s before retry")
                time.sleep(delay)

    raise RuntimeError(f"Failed to fetch ECI JSON after retries: {last_error}")


def extract_tamil_nadu(raw_data):
    state_data = raw_data.get(STATE_CODE)
    if not isinstance(state_data, dict):
        raise ValueError(f"ECI JSON did not contain expected {STATE_CODE} object")

    chart_data = state_data.get("chartData", [])
    if not isinstance(chart_data, list):
        raise ValueError(f"{STATE_CODE}.chartData was missing or not a list")

    filtered_rows = [
        row
        for row in chart_data
        if isinstance(row, list) and len(row) >= 5 and row[1] == STATE_CODE
    ]

    trimmed_state = dict(state_data)
    trimmed_state["chartData"] = filtered_rows

    if len(filtered_rows) != len(chart_data):
        log(f"Filtered chartData from {len(chart_data)} rows to {len(filtered_rows)} {STATE_CODE} rows")
    else:
        log(f"Found {len(filtered_rows)} {STATE_CODE} chartData rows")

    return {STATE_CODE: trimmed_state}


def build_payload(raw_data):
    return {
        "source": ECI_JSON_URL,
        "state_code": STATE_CODE,
        "updated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data": extract_tamil_nadu(raw_data),
    }


def save_payload(payload):
    temp_path = OUTPUT_PATH.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    temp_path.replace(OUTPUT_PATH)
    log(f"Saved {OUTPUT_PATH} with {len(payload['data'][STATE_CODE].get('chartData', []))} rows")


def write_empty_fallback(error):
    payload = {
        "source": ECI_JSON_URL,
        "state_code": STATE_CODE,
        "updated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fetch_error": str(error),
        "data": {STATE_CODE: {"chartData": [], "tableData": []}},
    }
    save_payload(payload)


def main():
    try:
        raw_data = fetch_eci_json()
        save_payload(build_payload(raw_data))
    except Exception as exc:
        log(f"Fetch/update failed: {exc}")
        previous = load_previous_data()

        if previous is not None:
            log(f"Keeping existing {OUTPUT_PATH}; exiting successfully for GitHub Actions")
            return 0

        log(f"No existing {OUTPUT_PATH}; writing empty fallback payload")
        write_empty_fallback(exc)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
