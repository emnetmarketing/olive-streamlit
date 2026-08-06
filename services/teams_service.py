from typing import Any
from urllib.parse import urlparse

import httpx

from components.config import secret

TIMEOUT_SECONDS = 15


def build_alert_payload(metrics: dict[str, Any], *, title: str = "Olive 트렌드 분석 알림") -> dict:
    facts = [
        {"title": "분석 키워드", "value": f"{int(metrics.get('keywords', 0)):,}"},
        {"title": "급상승 감지", "value": f"{int(metrics.get('surges', 0)):,}"},
        {"title": "네이버 매칭", "value": f"{int(metrics.get('matched', 0)):,}"},
        {"title": "오늘 언급량", "value": f"{int(metrics.get('total_today', 0)):,}"},
    ]
    return {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "contentUrl": None,
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.2",
                "body": [
                    {"type": "TextBlock", "text": title, "weight": "Bolder", "size": "Medium"},
                    {"type": "FactSet", "facts": facts},
                ],
            },
        }],
    }


def send_teams_alert(metrics: dict[str, Any], *, webhook_url: str | None = None,
                     title: str = "Olive 트렌드 분석 알림") -> None:
    url = str(webhook_url or secret("TEAMS_WEBHOOK_URL", required=True)).strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Teams Webhook URL은 유효한 HTTPS 주소여야 합니다.")
    try:
        response = httpx.post(url, json=build_alert_payload(metrics, title=title), timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise RuntimeError("Teams 알림 요청 시간이 초과되었습니다.") from exc
    except httpx.HTTPError as exc:
        status = getattr(exc.response, "status_code", None)
        suffix = f" (HTTP {status})" if status else ""
        raise RuntimeError(f"Teams 알림 전송에 실패했습니다{suffix}.") from exc
