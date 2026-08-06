from datetime import date
from typing import Iterable

from services.naver_common import request_json

VALID_TIME_UNITS = {"date", "week", "month"}
VALID_DEVICES = {"pc", "mo"}
VALID_GENDERS = {"m", "f"}
VALID_AGES = {"10", "20", "30", "40", "50", "60"}


def _base_payload(start_date: date, end_date: date, time_unit: str, device: str | None,
                  gender: str | None, ages: Iterable[str] | None) -> dict:
    if start_date > end_date:
        raise ValueError("조회 시작일은 종료일보다 늦을 수 없습니다.")
    if time_unit not in VALID_TIME_UNITS:
        raise ValueError("조회 단위는 date, week, month 중 하나여야 합니다.")
    if device and device not in VALID_DEVICES:
        raise ValueError("기기는 pc 또는 mo만 사용할 수 있습니다.")
    if gender and gender not in VALID_GENDERS:
        raise ValueError("성별은 m 또는 f만 사용할 수 있습니다.")
    clean_ages = list(dict.fromkeys(str(age) for age in (ages or [])))
    if any(age not in VALID_AGES for age in clean_ages):
        raise ValueError("연령대는 10, 20, 30, 40, 50, 60만 사용할 수 있습니다.")
    payload = {"startDate": start_date.isoformat(), "endDate": end_date.isoformat(), "timeUnit": time_unit}
    if device:
        payload["device"] = device
    if gender:
        payload["gender"] = gender
    if clean_ages:
        payload["ages"] = clean_ages
    return payload


def category_trends(start_date: date, end_date: date, categories: Iterable[dict], *, time_unit: str = "date",
                    device: str | None = None, gender: str | None = None,
                    ages: Iterable[str] | None = None) -> list[dict]:
    clean_categories = list(categories)
    if not 1 <= len(clean_categories) <= 3:
        raise ValueError("쇼핑 분야는 1~3개를 지정해야 합니다.")
    for category in clean_categories:
        if not str(category.get("name", "")).strip() or not category.get("param"):
            raise ValueError("각 쇼핑 분야에는 이름과 분야 코드가 필요합니다.")
    payload = _base_payload(start_date, end_date, time_unit, device, gender, ages)
    payload["category"] = clean_categories
    return request_json("POST", "/v1/datalab/shopping/categories", payload=payload).get("results", [])


def keyword_trends(start_date: date, end_date: date, category: str, keywords: Iterable[dict], *,
                   time_unit: str = "date", device: str | None = None, gender: str | None = None,
                   ages: Iterable[str] | None = None) -> list[dict]:
    category = str(category).strip()
    clean_keywords = list(keywords)
    if not category:
        raise ValueError("쇼핑 분야 코드를 입력하세요.")
    if not 1 <= len(clean_keywords) <= 5:
        raise ValueError("쇼핑 키워드 그룹은 1~5개를 지정해야 합니다.")
    for group in clean_keywords:
        if not str(group.get("name", "")).strip() or not group.get("param"):
            raise ValueError("각 키워드 그룹에는 이름과 검색어가 필요합니다.")
    payload = _base_payload(start_date, end_date, time_unit, device, gender, ages)
    payload.update({"category": category, "keyword": clean_keywords})
    return request_json("POST", "/v1/datalab/shopping/category/keywords", payload=payload).get("results", [])
