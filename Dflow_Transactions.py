#!/usr/bin/env python3
# api_watchdog.py

import os, time, json, pathlib, requests

# ========= CONFIG (edit these) =========
TG_BOT_TOKEN = "bot8443866055:AAHwfJYhU9rAkNo_sIhfD46x7sFvi4WhJrE"        # <-- rotate your token in @BotFather and paste here
TG_CHAT_ID   = "-1003269167073"

API_BASE = "https://dflow.topledger.xyz/transactions"
API_PARAMS = {
    "wallet": "8fdkaKYrnpfdyZ2gQkWF5vZxuhy1E2co8CibRiYuQhfm"
}

# Exact JSON to match (order-insensitive for dict keys)
EXPECTED_JSON_STR = r"""
{
  "transaction_count": 1,
  "transactions": [
    {
      "app_id": 120,
      "block_slot": 375046669,
      "block_time": "2025-10-22T11:57:31+00:00",
      "input_amount": 23.2,
      "input_mint": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
      "instruction_index": 2,
      "instruction_type": "Swap2",
      "output_amount": 0.044169412,
      "output_mint": "So11111111111111111111111111111111111111112",
      "platform_fee_bps": "85",
      "positive_slippage_fee_limit_pct": "5",
      "quoted_out_amount": 0.043810488,
      "signer": "8fdkaKYrnpfdyZ2gQkWF5vZxuhy1E2co8CibRiYuQhfm",
      "slippage_bps": "50",
      "tx_id": "2DzozusxmJh61pvXL38QTcLjn2PRy9qbmyZVT75NnC5x7XTervqJPCQw3ARL6QmPWs93AmmSFJSGWR6xbQ7rwidY"
    }
  ],
  "wallet": "8fdkaKYrnpfdyZ2gQkWF5vZxuhy1E2co8CibRiYuQhfm"
}
"""
EXPECTED_JSON = json.loads(EXPECTED_JSON_STR)
RELAX_FLOATS = False  # set True if you see tiny float noise

def _normalize(obj):
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_normalize(v) for v in obj]
    if RELAX_FLOATS and isinstance(obj, float):
        return round(obj, 12)
    return obj

def json_equal(a, b):
    return _normalize(a) == _normalize(b)

API_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "api-watchdog/1.0"
}

TIMEOUT_SEC     = 5
EXPECT_STATUS   = 200
MAX_LATENCY_MS  = 200
HEARTBEAT_MIN   = 0

STATE_FILE      = pathlib.Path("./.api_watchdog_state")
HEARTBEAT_FILE  = pathlib.Path("./.api_watchdog_heartbeat")

# --- ENV overrides (optional) ---
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", TG_BOT_TOKEN)
TG_CHAT_ID   = os.getenv("TG_CHAT_ID", TG_CHAT_ID)
TIMEOUT_SEC  = float(os.getenv("TIMEOUT_SEC", TIMEOUT_SEC))
EXPECT_STATUS= int(os.getenv("EXPECT_STATUS", EXPECT_STATUS))
MAX_LATENCY_MS = int(os.getenv("MAX_LATENCY_MS", MAX_LATENCY_MS))
HEARTBEAT_MIN   = int(os.getenv("HEARTBEAT_MIN", HEARTBEAT_MIN))

def send_telegram(msg: str):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("Telegram not configured (missing TG_BOT_TOKEN/TG_CHAT_ID)")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print("Telegram error:", r.status_code, r.text)
        else:
            print("Telegram ok")
    except Exception as e:
        print("Telegram exception:", e)

def read_state() -> str:
    try:
        return STATE_FILE.read_text().strip()
    except FileNotFoundError:
        return ""

def write_state(s: str):
    try:
        STATE_FILE.write_text(s)
    except Exception as e:
        print("State write error:", e)

def should_heartbeat() -> bool:
    if HEARTBEAT_MIN <= 0: return False
    now = time.time()
    try:
        last = float(HEARTBEAT_FILE.read_text())
    except Exception:
        last = 0.0
    if now - last > HEARTBEAT_MIN * 60:
        try:
            HEARTBEAT_FILE.write_text(str(now))
        except Exception as e:
            print("Heartbeat write error:", e)
        return True
    return False

def classify(result_ok: bool, latency_ms: int, payload_ok: bool) -> str:
    if not result_ok: return "DOWN"
    if not payload_ok: return "BAD_PAYLOAD"
    if latency_ms > MAX_LATENCY_MS: return "SLOW"
    return "UP"

def main():
    t0 = time.perf_counter()
    err = None
    status = None
    text = ""
    payload_ok = True
    final_url = f"{API_BASE}?wallet={API_PARAMS.get('wallet','')}"  # default

    try:
        r = requests.get(API_BASE, params=API_PARAMS, headers=API_HEADERS, timeout=TIMEOUT_SEC)
        status = r.status_code
        text = r.text
        final_url = r.url  # actual URL used
        print("DBG URL:", final_url)
        print("DBG STATUS:", status)
    except Exception as e:
        err = str(e)
        print("DBG EXC:", err)

    latency_ms = int((time.perf_counter() - t0) * 1000)
    result_ok = (err is None) and (status == EXPECT_STATUS)

    if result_ok:
        try:
            j = r.json()
            payload_ok = json_equal(j, EXPECTED_JSON)
        except Exception as e:
            payload_ok = False
            print("DBG JSON error:", e)

    state = classify(result_ok, latency_ms, payload_ok)
    last = read_state()

    base = f"API Watchdog\nURL: {final_url}\nStatus: {status}\nLatency: {latency_ms} ms"
    if err:
        base += f"\nError: {err}"

    if state != last:
        if state == "UP":
            send_telegram(f"✅ <b>RECOVERY</b>\n{base}")
        elif state == "SLOW":
            send_telegram(f"⚠️ <b>SLOW</b>\n{base}\nLimit: {MAX_LATENCY_MS} ms")
        elif state == "BAD_PAYLOAD":
            send_telegram(f"⚠️ <b>BAD PAYLOAD</b>\n{base}\nReason: Response JSON != EXPECTED_JSON")
        else:
            send_telegram(f"🚨 <b>DOWN</b>\n{base}")
        write_state(state)
    else:
        if state != "UP":
            send_telegram(f"ℹ️ <b>{state}</b>\n{base}")
        elif should_heartbeat():
            send_telegram(f"✅ <b>HEARTBEAT</b> API OK\nURL: {final_url}")

if __name__ == "__main__":
    main()
