#!/usr/bin/env python3
"""rainAlert — sends an email when rain is forecast within the configured window."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from weather import get_rain_forecast
from notifier import send_rain_alert

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
STATE_PATH = BASE_DIR / "state.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"ERROR: 設定ファイルが見つかりません: {CONFIG_PATH}", file=sys.stderr)
        print("config.example.yaml をコピーして config.yaml を作成してください。", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f)


def is_in_cooldown(state: dict, cooldown_hours: float) -> bool:
    last_sent = state.get("last_sent")
    if not last_sent:
        return False
    last_dt = datetime.fromisoformat(last_sent)
    now = datetime.now(timezone.utc).astimezone()
    elapsed_hours = (now - last_dt).total_seconds() / 3600
    return elapsed_hours < cooldown_hours


def main() -> None:
    parser = argparse.ArgumentParser(description="雨アラート")
    parser.add_argument("--dry-run", action="store_true", help="メールを送らずに動作確認")
    parser.add_argument("--force", action="store_true", help="クールダウンを無視して実行")
    args = parser.parse_args()

    config = load_config()
    alert = config["alert"]

    threshold = alert["rain_probability_threshold"]
    hours_ahead = alert["check_hours_ahead"]
    cooldown_hours = alert["cooldown_hours"]

    # 環境変数が設定されていればそちらを優先（GitHub Actions Secrets 対応）
    import os
    loc_cfg = config.get("location", {})
    loc = {
        "name":      os.environ.get("RAIN_LOCATION_NAME",      loc_cfg.get("name", "")),
        "latitude":  float(os.environ.get("RAIN_LOCATION_LAT", loc_cfg.get("latitude", 0))),
        "longitude": float(os.environ.get("RAIN_LOCATION_LON", loc_cfg.get("longitude", 0))),
    }
    if not loc["name"]:
        print("ERROR: 場所の設定が不足しています。config.yaml または環境変数を確認してください。", file=sys.stderr)
        sys.exit(1)

    email_cfg = config.get("email", {})
    email = {
        "smtp_host": os.environ.get("RAIN_SMTP_HOST", email_cfg.get("smtp_host", "smtp.gmail.com")),
        "smtp_port": int(os.environ.get("RAIN_SMTP_PORT", email_cfg.get("smtp_port", 587))),
        "sender":    os.environ.get("RAIN_EMAIL_SENDER",   email_cfg.get("sender", "")),
        "password":  os.environ.get("RAIN_EMAIL_PASSWORD", email_cfg.get("password", "")),
        "recipient": os.environ.get("RAIN_EMAIL_RECIPIENT", email_cfg.get("recipient", "")),
    }
    if not email["sender"] or not email["password"] or not email["recipient"]:
        print("ERROR: メール設定が不足しています。config.yaml または環境変数を確認してください。", file=sys.stderr)
        sys.exit(1)

    state = load_state()

    if not args.force and not args.dry_run and is_in_cooldown(state, cooldown_hours):
        last_sent = state.get("last_sent", "")
        print(f"クールダウン中のためスキップします (前回通知: {last_sent})")
        return

    print(f"{loc['name']} の天気予報を取得中...")
    forecast = get_rain_forecast(loc["latitude"], loc["longitude"], hours_ahead)

    if not forecast:
        print("予報データが取得できませんでした。")
        return

    max_prob = max(e["precipitation_probability"] for e in forecast)
    print(f"今後{hours_ahead}時間の最高降水確率: {max_prob}% (閾値: {threshold}%)")

    if max_prob < threshold:
        print("雨の予報なし。通知しません。")
        return

    print(f"降水確率が閾値を超えました ({max_prob}% >= {threshold}%)。通知を送信します。")
    send_rain_alert(
        smtp_host=email["smtp_host"],
        smtp_port=email["smtp_port"],
        sender=email["sender"],
        password=email["password"],
        recipient=email["recipient"],
        location_name=loc["name"],
        max_probability=max_prob,
        hours_ahead=hours_ahead,
        forecast=forecast,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        save_state({"last_sent": datetime.now(timezone.utc).astimezone().isoformat()})
        print("通知を送信しました。")
    else:
        print("[DRY RUN] 完了。")


if __name__ == "__main__":
    main()
