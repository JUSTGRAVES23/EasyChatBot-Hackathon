from __future__ import annotations

from html import escape

from ..domain.academy_notification import AcademyNotification


class AcademyEmailFormatter:
    """Render the one-week notification as email HTML/text."""

    def render(self, notification: AcademyNotification) -> dict[str, str]:
        username = escape(notification.username, quote=True)
        portal_url = escape(notification.portal_url, quote=True)

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>One Week at EasyChatBot</title>
</head>
<body style="margin:0;padding:0;background:#f7f7f7;font-family:Arial,sans-serif;">
<div style="max-width:620px;margin:0 auto;padding:32px 20px;">
<div style="background:#ffffff;border-radius:16px;padding:32px;">
<div style="text-align:center;margin-bottom:24px;">
<img src="cid:easychatbot-logo" alt="EasyChatBot"
     style="max-width:220px;height:auto;">
</div>
<h1>🎓 Congratulations, @{username}!</h1>
<p>It has been one week since you joined the EasyChatBot Academy.</p>
<p>What a great start! Every lesson you complete, every question you ask,
and every conversation you have is another step forward in your journey.</p>
<p>Keep exploring, keep practising, and keep building your confidence.
Your Academy journey is only just beginning. 🚀</p>
<div style="text-align:center;margin:30px 0;">
<a href="{portal_url}"
   style="display:inline-block;padding:14px 24px;border-radius:10px;
          text-decoration:none;font-weight:bold;">
🚀 Continue Learning
</a>
</div>
<p>Keep going, @{username}. We are growing with you.</p>
<hr>
<p style="font-size:12px;color:#666;">
This is an automated message from EasyChatBot.
</p>
<p style="font-size:12px;color:#666;">
<a href="{portal_url}">Open EasyChatBot</a>
</p>
<p style="font-size:12px;color:#666;text-align:center;">
EasyChatBot — Growing With You.
</p>
</div>
</div>
</body>
</html>
"""

        text = f"""🎓 Congratulations, @{notification.username}!

It has been one week since you joined the EasyChatBot Academy.

What a great start! Every lesson you complete, every question you ask,
and every conversation you have is another step forward in your journey.

Keep exploring, keep practising, and keep building your confidence.
Your Academy journey is only just beginning. 🚀

Continue Learning:
{notification.portal_url}

This is an automated message from EasyChatBot.

EasyChatBot — Growing With You.
"""
        return {"html": html, "body": text}


class AcademyTelegramFormatter:
    """Render the same notification as Telegram-friendly text."""

    def render(self, notification: AcademyNotification) -> str:
        return (
            f"🎓 *Congratulations, @{notification.username}!*\n\n"
            "It has been one week since you joined the EasyChatBot Academy.\n\n"
            "What a great start! Every lesson you complete, every question "
            "you ask, and every conversation you have is another step forward "
            "in your journey.\n\n"
            "Keep exploring, keep practising, and keep building your confidence. "
            "Your Academy journey is only just beginning. 🚀\n\n"
            f"Keep going, @{notification.username}. We are growing with you."
        )
