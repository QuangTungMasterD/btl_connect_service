def build_telegram_content(event_id: str, user_id: str, username: str, user_role: str, severity: str, title: str, message: str, timestamp: str) -> str:
    """
    Trả về nội dung HTML cho Telegram (parse_mode='HTML').
    Layout: header, send_to, Event ID, Time, Message.
    """
    severity_upper = severity.upper()
    if severity_upper == "CRITICAL":
        header = "🚨 CRITICAL SYSTEM ALERT"
    elif severity_upper == "HIGH":
        header = "⚠️ HIGH PRIORITY SYSTEM ALERT"
    elif severity_upper == "MEDIUM":
        header = "📢 SYSTEM NOTIFICATION"
    else:  # LOW
        header = "ℹ️ SYSTEM INFORMATION"

    send_to_line = f"Send to: {user_role} - {username} - {user_id}"

    text = f"""
<b>{header}</b>

<b>📨 {send_to_line}</b>

<b>Event ID:</b> <code>{event_id}</code>
<b>Time:</b> <i>{timestamp}</i>
<b>Message:</b> <i>{message}</i>
    """
    return text.strip()