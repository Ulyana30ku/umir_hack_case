import json
import os
from typing import Any
from urllib import error, request


class MLAgentClient:
    """Клиент для вызова внешнего hack-parser-ml API."""

    @staticmethod
    def _base_url() -> str:
        return os.getenv('ML_AGENT_BASE_URL', 'http://127.0.0.1:8000/ml').rstrip('/')

    @staticmethod
    def _timeout_seconds() -> float:
        raw_timeout = os.getenv('ML_AGENT_TIMEOUT_SECONDS', '180')
        try:
            return float(raw_timeout)
        except ValueError:
            return 180.0

    @staticmethod
    def run_agent(
        query: str,
        run_id: str | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Запустить внешний агент и вернуть JSON-ответ."""
        payload: dict[str, Any] = {'query': query}
        if run_id:
            payload['run_id'] = run_id
        if context:
            payload['context'] = context

        req = request.Request(
            url=f'{MLAgentClient._base_url()}/agent/run',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )

        try:
            with request.urlopen(req, timeout=MLAgentClient._timeout_seconds()) as resp:
                body = resp.read().decode('utf-8')
                return json.loads(body)
        except error.HTTPError as exc:
            body = exc.read().decode('utf-8', errors='ignore')
            raise RuntimeError(
                f'ML agent HTTP error {exc.code}: {body[:300]}' if body else f'ML agent HTTP error {exc.code}',
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(f'ML agent unavailable: {exc.reason}') from exc
        except TimeoutError as exc:
            raise RuntimeError('ML agent request timed out') from exc
