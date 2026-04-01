"""Email notification sender using smtplib."""
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_rain_alert(
    smtp_host: str,
    smtp_port: int,
    sender: str,
    password: str,
    recipient: str,
    location_name: str,
    max_probability: int,
    hours_ahead: int,
    forecast: list[dict],
    dry_run: bool = False,
) -> None:
    """Send a rain alert email. If dry_run=True, print instead of sending."""
    subject = f"☂ 雨の予報 — {location_name} (確率 {max_probability}%)"

    lines = [
        f"{location_name}で雨が降る可能性があります。",
        "",
        f"最高降水確率: {max_probability}% (今後{hours_ahead}時間以内)",
        f"チェック時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "時間帯別予報:",
    ]
    for entry in forecast:
        time_str = entry["time"].strftime("%H:%M")
        prob = entry["precipitation_probability"]
        lines.append(f"  {time_str} — {prob}%")

    lines += ["", "傘をお忘れなく！"]
    body = "\n".join(lines)

    if dry_run:
        print("[DRY RUN] メール送信をスキップします")
        print(f"  宛先: {recipient}")
        print(f"  件名: {subject}")
        print("--- 本文 ---")
        print(body)
        print("------------")
        return

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
