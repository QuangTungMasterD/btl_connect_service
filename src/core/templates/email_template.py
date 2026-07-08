def build_email_content(event_id: str, user_id: str, username: str, user_role: str, severity: str, title: str, message: str, timestamp: str):
    """
    Trả về (subject, html_content) cho email.
    Layout: header, send_to, Event ID, Time, Message.
    """
    severity_upper = severity.upper()
    if severity_upper == "CRITICAL":
        subject = "🚨 CRITICAL SYSTEM ALERT"
        color = "#dc3545"
    elif severity_upper == "HIGH":
        subject = "⚠️ HIGH PRIORITY SYSTEM ALERT"
        color = "#fd7e14"
    elif severity_upper == "MEDIUM":
        subject = "📢 SYSTEM NOTIFICATION"
        color = "#ffc107"
    else:
        subject = "ℹ️ SYSTEM INFORMATION"
        color = "#28a745"

    send_to_line = f"Send to: {user_role} - {username} - {user_id}"

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .alert {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 15px;
                border-radius: 5px;
                max-width: 600px;
            }}
            .header {{
                font-size: 22px;
                font-weight: bold;
                color: {color};
                border-bottom: 2px solid {color};
                padding-bottom: 8px;
                margin-bottom: 15px;
            }}
            .send-to {{
                font-weight: bold;
                background: #e9ecef;
                padding: 6px 12px;
                border-radius: 4px;
                border-left: 4px solid {color};
            }}
            .field {{
                margin: 8px 0;
            }}
            .field strong {{
                color: #333;
            }}
            .event-id {{
                font-family: monospace;
                background: #e9ecef;
                padding: 2px 6px;
                border-radius: 3px;
            }}
            .time {{
                font-style: italic;
                color: #6c757d;
            }}
            .message-box {{
                background: #f1f3f5;
                padding: 8px 12px;
                border-left: 4px solid {color};
                border-radius: 4px;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <div class="alert">
            <div class="header">🚨 SYSTEM ALERT - {severity}</div>
            <p><strong class="send-to">📨 {send_to_line}</strong></p>
            <p class="field"><strong>Event ID:</strong> <span class="event-id">{event_id}</span></p>
            <p class="field"><strong>Time:</strong> <span class="time">{timestamp}</span></p>
            <p class="field"><strong>Message:</strong></p>
            <div class="message-box">{message}</div>
        </div>
    </body>
    </html>
    """
    return subject, html