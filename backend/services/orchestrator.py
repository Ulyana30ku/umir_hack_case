from sqlalchemy.orm import Session
from models import Message
from services.log_service import LogService
from services.ml_agent_client import MLAgentClient
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class Orchestrator:
    """Orchestrator для обработки сообщений чата и генерации ответов."""

    @staticmethod
    def build_conversation_context(messages: list[Message]) -> str:
        """Собрать контекст разговора из истории сообщений."""
        if not messages:
            return ''

        context_parts = []
        for msg in messages:
            if msg.role == 'user':
                role_label = 'Пользователь'
            elif msg.role == 'assistant':
                role_label = 'Ассистент'
            else:
                role_label = 'Система'
            context_parts.append(f'{role_label}: {msg.content}')

        return '\n'.join(context_parts)

    @staticmethod
    def parse_user_intent(content: str) -> dict:
        """Упрощённый разбор интента пользователя."""
        intent = {
            'action': 'search',
            'target': None,
            'details': content,
        }

        content_lower = content.lower()

        if 'открой' in content_lower or 'go to' in content_lower:
            intent['action'] = 'open_url'
            intent['target'] = 'website'
        elif 'найди' in content_lower or 'find' in content_lower:
            intent['action'] = 'search'
            intent['target'] = 'product'
        elif 'новост' in content_lower or 'news' in content_lower:
            intent['action'] = 'search'
            intent['target'] = 'news'
        elif 'прочит' in content_lower or 'read' in content_lower:
            intent['action'] = 'read_page'
        elif 'click' in content_lower or 'нажм' in content_lower:
            intent['action'] = 'click'

        return intent

    @staticmethod
    def _extract_last_url_from_history(history: list[Message]) -> str | None:
        """Extract the most recent URL mentioned in assistant history."""
        url_pattern = re.compile(r'https?://[^\s)]+', re.IGNORECASE)

        for msg in reversed(history):
            if msg.role != 'assistant':
                continue

            match = url_pattern.search(msg.content or '')
            if match:
                return match.group(0)

        return None

    @staticmethod
    def _resolve_contextual_user_message(user_message: str, history: list[Message]) -> str:
        """Resolve pronoun-based references like 'там/здесь/тут' using recent history."""
        lowered = user_message.lower()
        last_url = Orchestrator._extract_last_url_from_history(history)
        if not last_url:
            return user_message

        if 'apple.com' in last_url:
            has_apple_pronoun_ref = bool(re.search(r'\b(?:у|й)\s+них\b', lowered))
            if has_apple_pronoun_ref:
                normalized = user_message.strip()
                normalized = re.sub(r'(?i)^а\s+', '', normalized).strip()
                normalized = re.sub(r'(?i)\b(?:у|й)\s+них\b', 'у apple', normalized).strip()
                normalized = re.sub(r'\s+', ' ', normalized).strip(' ,.-')
                return f'зайди на сайт apple.com и {normalized}'

        sort_keywords = ['сортир', 'по цене', 'дешев', 'дорог']
        if 'market.yandex.ru' in last_url and any(k in lowered for k in sort_keywords):
            parsed = urlparse(last_url)
            query = parse_qs(parsed.query)

            sort_value = 'aprice'
            if any(k in lowered for k in ['дорог', 'убыв', 'сначала дорог']):
                sort_value = 'dprice'

            query['how'] = [sort_value]

            rebuilt_query = urlencode(query, doseq=True)
            sorted_url = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    rebuilt_query,
                    parsed.fragment,
                ),
            )
            return f'открой {sorted_url}'

        has_reference = (
            any(token in lowered for token in [' там ', 'здесь', 'тут'])
            or bool(re.search(r'\b(?:у|й)\s+них\b', lowered))
        )
        if not has_reference:
            return user_message

        domain_hint = ''
        if 'market.yandex.ru' in last_url:
            domain_hint = 'на Яндекс Маркете'
        elif 'apple.com' in last_url:
            domain_hint = 'на сайте Apple'
        elif 'wikipedia.org' in last_url:
            domain_hint = 'в Википедии'
        elif 'bing.com/news' in last_url:
            domain_hint = 'в новостях Bing'
        elif 'bing.com/search' in last_url:
            domain_hint = 'в поиске Bing'

        if not domain_hint:
            return user_message

        normalized = user_message.strip()
        normalized = re.sub(r'(?i)^теперь\s+', '', normalized).strip()
        normalized = re.sub(r'(?i)\bтам\b', '', normalized).strip()
        normalized = re.sub(r'(?i)\b(здесь|тут)\b', '', normalized).strip()
        normalized = re.sub(r'\s+', ' ', normalized).strip(' ,.-')

        if not normalized:
            return f'Продолжи действие {domain_hint}'

        if domain_hint.lower() in normalized.lower():
            return normalized

        return f'{normalized} {domain_hint}'

    @staticmethod
    def handle_chat_message(
        db: Session,
        session_id: int,
        user_message: str,
        history: list[Message],
    ) -> tuple[str, list[dict], list[dict]]:
        """Обработать сообщение пользователя и вернуть ответ с логами."""

        logs = []
        step = 1

        LogService.add_log(
            db,
            session_id,
            step,
            'parse_intent',
            f'Parsing user message: {user_message[:100]}',
        )
        logs.append(
            {
                'step': step,
                'action': 'parse_intent',
                'details': f'Parsing user message: {user_message[:100]}',
            },
        )
        step += 1

        intent = Orchestrator.parse_user_intent(user_message)

        context = Orchestrator.build_conversation_context(history)
        LogService.add_log(
            db,
            session_id,
            step,
            'build_context',
            f'Built context from {len(history)} messages',
        )
        logs.append(
            {
                'step': step,
                'action': 'build_context',
                'details': f'Built context from {len(history)} messages',
            },
        )
        step += 1

        resolved_user_message = Orchestrator._resolve_contextual_user_message(user_message, history)
        if resolved_user_message != user_message:
            LogService.add_log(
                db,
                session_id,
                step,
                'resolve_context_refs',
                f'Resolved query: {resolved_user_message}',
            )
            logs.append(
                {
                    'step': step,
                    'action': 'resolve_context_refs',
                    'details': f'Resolved query: {resolved_user_message}',
                },
            )
            step += 1

        action = intent['action']
        LogService.add_log(
            db,
            session_id,
            step,
            f'route_{action}',
            f"Detected action: {action}, target: {intent.get('target')}",
        )
        logs.append(
            {
                'step': step,
                'action': f'route_{action}',
                'details': f"Detected action: {action}, target: {intent.get('target')}",
            },
        )
        step += 1

        assistant_response, actions = Orchestrator._execute_external_agent(
            db,
            session_id,
            resolved_user_message,
            '',
            step,
            logs,
        )

        if not assistant_response:
            response = Orchestrator._execute_action(
                db,
                session_id,
                action,
                intent,
                step,
                logs,
            )

            assistant_response = Orchestrator._generate_response(
                response,
                action,
                intent,
                history,
            )
            actions = []

        LogService.add_log(
            db,
            session_id,
            step,
            'generate_response',
            f'Generated assistant response ({len(assistant_response)} chars)',
        )
        logs.append(
            {
                'step': step,
                'action': 'generate_response',
                'details': f'Generated assistant response ({len(assistant_response)} chars)',
            },
        )

        return assistant_response, logs, actions

    @staticmethod
    def _execute_external_agent(
        db: Session,
        session_id: int,
        user_message: str,
        context: str,
        step: int,
        logs: list[dict],
    ) -> tuple[str, list[dict]]:
        """Выполнить запрос через внешний hack-parser-ml агент."""
        LogService.add_log(
            db,
            session_id,
            step,
            'execute_external_agent',
            'Calling hack-parser-ml /agent/run',
        )
        logs.append(
            {
                'step': step,
                'action': 'execute_external_agent',
                'details': 'Calling hack-parser-ml /agent/run',
            },
        )
        step += 1

        try:
            response = MLAgentClient.run_agent(query=user_message, context=context)

            outer_result = response.get('result') or {}
            inner_result = outer_result.get('result') or {}
            trace = inner_result.get('trace') or {}
            trace_steps = trace.get('steps') or []

            for trace_step in trace_steps[:10]:
                step_name = trace_step.get('step_name', 'unknown_step')
                status = trace_step.get('status', 'unknown')
                reasoning = trace_step.get('reasoning') or trace_step.get('error_message') or ''

                details = f'{step_name} [{status}]'
                if reasoning:
                    details = f'{details}: {reasoning[:220]}'

                LogService.add_log(
                    db,
                    session_id,
                    step,
                    f'external_{step_name}',
                    details,
                )
                logs.append(
                    {
                        'step': step,
                        'action': f'external_{step_name}',
                        'details': details,
                    },
                )
                step += 1

            summary = inner_result.get('summary')
            browser_result = inner_result.get('browser_result') or {}
            page_title = browser_result.get('page_title')
            final_url = browser_result.get('final_url')
            actions = Orchestrator._extract_extension_actions(trace)

            if summary:
                if page_title and final_url:
                    return f'{summary}\nСтраница: {page_title} ({final_url})', actions
                return summary, actions

            if response.get('error'):
                return f"Внешний агент вернул ошибку: {response.get('error')}", actions

            return 'Внешний агент выполнил запрос, но не вернул итоговое summary.', actions

        except Exception as exc:
            fallback_details = f'External agent unavailable, fallback to local logic: {str(exc)[:240]}'
            LogService.add_log(
                db,
                session_id,
                step,
                'external_agent_fallback',
                fallback_details,
            )
            logs.append(
                {
                    'step': step,
                    'action': 'external_agent_fallback',
                    'details': fallback_details,
                },
            )
            return '', []

    @staticmethod
    def _extract_extension_actions(trace: dict) -> list[dict]:
        """Преобразовать trace шаги в действия для browser extension."""
        actions: list[dict] = []

        for trace_step in trace.get('steps') or []:
            if trace_step.get('status') != 'completed':
                continue

            tool_name = trace_step.get('tool_name')
            input_payload = trace_step.get('input_payload') or {}

            if tool_name == 'browser.open_url' and input_payload.get('url'):
                actions.append({'type': 'open_url', 'url': input_payload.get('url')})
            elif tool_name == 'browser.type':
                text = input_payload.get('text')
                if text:
                    actions.append(
                        {
                            'type': 'input_text',
                            'selector': input_payload.get('selector'),
                            'value': text,
                        },
                    )
            elif tool_name == 'browser.scroll':
                direction = (input_payload.get('direction') or 'down').lower()
                if direction == 'down':
                    actions.append(
                        {
                            'type': 'scroll_down',
                            'amount': int(input_payload.get('amount') or 600),
                        },
                    )
            elif tool_name in {'browser.get_page_text', 'browser.extract_content'}:
                actions.append({'type': 'read_page'})

        return actions

    @staticmethod
    def _execute_action(
        db: Session,
        session_id: int,
        action: str,
        intent: dict,
        step: int,
        logs: list[dict],
    ) -> dict:
        """Mock выполнение действия."""

        result = {'success': True, 'data': {}}

        if action == 'open_url':
            LogService.add_log(
                db,
                session_id,
                step,
                'execute_open_url',
                'Opening URL (mock)',
            )
            logs.append(
                {
                    'step': step,
                    'action': 'execute_open_url',
                    'details': 'Opening URL (mock)',
                },
            )
            result['data'] = {'url': 'https://example.com', 'status': 'ok'}

        elif action == 'search':
            LogService.add_log(
                db,
                session_id,
                step,
                'execute_search',
                f"Searching for: {intent.get('details')}",
            )
            logs.append(
                {
                    'step': step,
                    'action': 'execute_search',
                    'details': f"Searching for: {intent.get('details')}",
                },
            )
            result['data'] = {'query': intent.get('details'), 'results': []}

        elif action == 'read_page':
            LogService.add_log(
                db,
                session_id,
                step,
                'execute_read_page',
                'Reading page content (mock)',
            )
            logs.append(
                {
                    'step': step,
                    'action': 'execute_read_page',
                    'details': 'Reading page content (mock)',
                },
            )
            result['data'] = {'content': 'Page content here...'}

        return result

    @staticmethod
    def _generate_response(
        result: dict,
        action: str,
        intent: dict,
        history: list[Message],
    ) -> str:
        """Генерировать осмысленный ответ ассистента."""

        if action == 'open_url':
            return (
                f"Я открыл сайт. Готов помощь с информацией. "
                f"Ваш запрос: {intent.get('details')}"
            )
        elif action == 'search':
            return (
                f"Я начал поиск по запросу: {intent.get('details')}. "
                f"Вот что я нашёл..."
            )
        elif action == 'read_page':
            return f"Я прочитал содержимое страницы. {intent.get('details')}"
        else:
            return (
                f"Я обработал ваш запрос: {intent.get('details')}. "
                f"Готов помочь дальше."
            )
