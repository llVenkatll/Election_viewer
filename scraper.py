import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


ECI_JSON_URL = "https://results.eci.gov.in/ResultAcGenMay2026/election-json-S22-live.json"
ECI_PAGE_URL = "https://results.eci.gov.in/ResultAcGenMay2026/partywiseresult-S22.htm"
OUTPUT_PATH = Path("data.json")
STATE_CODE = "S22"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": ECI_PAGE_URL,
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


def fetch_with_requests(max_attempts=5):
    last_error = None

    with requests.Session() as session:
        for attempt in range(1, max_attempts + 1):
            try:
                log(f"Fetching ECI JSON with requests, attempt {attempt}/{max_attempts}")
                response = session.get(ECI_JSON_URL, headers=headers, timeout=20)
                print(f"Requests status code: {response.status_code}", flush=True)

                if response.status_code == 200:
                    print("Success: fetched ECI JSON with requests", flush=True)
                    return response.json()

                preview = response.text[:240].replace("\n", " ")
                last_error = RuntimeError(
                    f"unexpected status {response.status_code}; body preview: {preview}"
                )

                if response.status_code not in RETRY_STATUS_CODES:
                    break
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = exc
                log(f"Retryable request error: {exc}")
            except requests.RequestException as exc:
                last_error = exc
                log(f"Request failed: {exc}")
                break
            except json.JSONDecodeError as exc:
                last_error = exc
                log(f"Response was not valid JSON: {exc}")
                break

            if attempt < max_attempts:
                log("Waiting 2s before retry")
                time.sleep(2)

    raise RuntimeError(f"Failed to fetch ECI JSON after retries: {last_error}")


def fetch_with_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed") from exc

    log("Fetching ECI JSON with Playwright Chromium fallback")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        try:
            context = browser.new_context(
                user_agent=headers["User-Agent"],
                extra_http_headers={
                    "Accept-Language": headers["Accept-Language"],
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
                viewport={"width": 1365, "height": 900},
            )
            page = context.new_page()

            log(f"Opening ECI page: {ECI_PAGE_URL}")
            page_response = page.goto(ECI_PAGE_URL, wait_until="domcontentloaded", timeout=45000)
            if page_response is not None:
                print(f"Playwright page status code: {page_response.status}", flush=True)
            page.wait_for_timeout(3000)

            log("Fetching ECI JSON through Playwright browser context")
            response = context.request.get(
                ECI_JSON_URL,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Referer": ECI_PAGE_URL,
                },
                timeout=45000,
            )
            print(f"Playwright status code: {response.status}", flush=True)

            if response.status == 200:
                print("Success: fetched ECI JSON with Playwright context request", flush=True)
                return response.json()

            context_preview = response.text()[:240].replace("\n", " ")
            log(
                "Playwright context request failed; trying same-origin page fetch "
                f"(status {response.status})"
            )

            page_fetch = page.evaluate(
                """
                async (url) => {
                  const response = await fetch(url, {
                    cache: "no-store",
                    credentials: "include",
                    headers: { "Accept": "application/json, text/plain, */*" }
                  });
                  return {
                    status: response.status,
                    text: await response.text()
                  };
                }
                """,
                ECI_JSON_URL,
            )
            print(f"Playwright page fetch status code: {page_fetch['status']}", flush=True)

            if page_fetch["status"] != 200:
                page_preview = page_fetch["text"][:240].replace("\n", " ")
                raise RuntimeError(
                    f"Playwright context request returned status {response.status}; "
                    f"body preview: {context_preview}. "
                    f"Page fetch returned status {page_fetch['status']}; body preview: {page_preview}"
                )

            print("Success: fetched ECI JSON with Playwright page fetch", flush=True)
            return json.loads(page_fetch["text"])
        finally:
            browser.close()


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
        print(f"Number of rows parsed: {len(filtered_rows)}", flush=True)
        log(f"Filtered chartData from {len(chart_data)} rows to {len(filtered_rows)} {STATE_CODE} rows")
    else:
        print(f"Number of rows parsed: {len(filtered_rows)}", flush=True)
        log(f"Found {len(filtered_rows)} {STATE_CODE} chartData rows")

    return {STATE_CODE: trimmed_state}


def build_payload(raw_data):
    return {
        "source": ECI_JSON_URL,
        "state_code": STATE_CODE,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "data": extract_tamil_nadu(raw_data),
    }


def save_payload(payload):
    temp_path = OUTPUT_PATH.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    temp_path.replace(OUTPUT_PATH)
    log(f"Saved {OUTPUT_PATH} with {len(payload['data'][STATE_CODE].get('chartData', []))} rows")


def main():
    try:
        try:
            raw_data = fetch_with_requests()
            print("Data source method: requests", flush=True)
        except Exception as requests_exc:
            log(f"Requests fetch failed; trying Playwright fallback: {requests_exc}")
            raw_data = fetch_with_playwright()
            print("Data source method: Playwright", flush=True)

        save_payload(build_payload(raw_data))
        print("Success: data.json updated", flush=True)
    except Exception as exc:
        log(f"Both fetch methods failed or update could not be saved: {exc}")
        print("FAILED FETCH – keeping old data", flush=True)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
