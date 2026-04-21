"""Adzuna API integration for job ingestion."""
import logging
import time
from typing import List, Dict, Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_session = requests.Session()


_REQUEST_DELAY_SECONDS = 1.5


def fetch_jobs(
    country: str = 'in',
    page: int = 1,
    results_per_page: int = 50,
    what: str = '',
) -> List[Dict[str, Any]]:
    """
    Fetch raw job results from Adzuna with automatic rate-limit handling.

    - Waits _REQUEST_DELAY_SECONDS before every call to avoid 429s.
    - If a 429 is returned, waits 60 seconds and retries once.
    - Returns [] on any other error.
    """
    cfg = settings.ADZUNA_CONFIG
    app_id = cfg.get('APP_ID')
    api_key = cfg.get('API_KEY')

    if not app_id or not api_key:
        logger.warning("Adzuna credentials not configured — skipping fetch")
        return []

    url = f"{cfg['BASE_URL']}/{country}/search/{page}"
    params: Dict[str, Any] = {
        'app_id':           app_id,
        'app_key':          api_key,
        'results_per_page': results_per_page,
        'content-type':     'application/json',
    }
    if what:
        params['what'] = what.lower()

    # Polite delay before every request
    time.sleep(_REQUEST_DELAY_SECONDS)

    for attempt in (1, 2):   # try once, retry once on 429
        try:
            resp = _session.get(url, params=params, timeout=30)

            if resp.status_code == 429:
                if attempt == 1:
                    wait = 60
                    logger.warning(
                        "Adzuna 429 rate limit (country=%s, what=%r) — "
                        "waiting %ds before retry", country, what, wait
                    )
                    time.sleep(wait)
                    continue   # retry
                else:
                    logger.warning(
                        "Adzuna 429 on retry (country=%s, what=%r) — skipping",
                        country, what,
                    )
                    return []

            resp.raise_for_status()
            return resp.json().get('results', [])

        except requests.HTTPError:
            return []
        except Exception as e:
            logger.warning(
                "Adzuna fetch failed (country=%s, page=%d): %s", country, page, e
            )
            return []