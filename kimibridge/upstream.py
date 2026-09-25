from contextlib import contextmanager
from dataclasses import dataclass
import json
from typing import Any, Generator, Iterator
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class UpstreamResponse:
    body: bytes
    status: int
    headers: dict[str, str]


@dataclass
class UpstreamStreamResponse:
    status: int
    headers: dict[str, str]
    response: Any

    def iter_chunks(self, chunk_size: int = 4096) -> Iterator[bytes]:
        read_fn = getattr(self.response, "read1", self.response.read)
        while True:
            chunk = read_fn(chunk_size)
            if not chunk:
                break
            yield chunk


class UpstreamUnavailable(Exception):
    def __init__(self, reason: object) -> None:
        super().__init__(str(reason))
        self.reason = reason


class UpstreamHttpError(Exception):
    def __init__(self, status: int, body: bytes) -> None:
        super().__init__(f"Upstream returned HTTP {status}")
        self.status = status
        self.body = body


class KimiUpstreamClient:
    def __init__(self, base_url: str, timeout: int = 60) -> None:
        clean_url = base_url.rstrip("/")
        if clean_url.endswith("/v1"):
            clean_url = clean_url[:-3]
        self.base_url = clean_url
        self.timeout = timeout

    def chat_completions(
        self,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> UpstreamResponse:
        return self.post_json("/v1/chat/completions", headers, payload)

    def stream_chat_completions(
        self,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> Generator[UpstreamStreamResponse, None, None]:  # type: ignore[type-arg]
        return self.stream_post_json("/v1/chat/completions", headers, payload)  # type: ignore[return-value]

    def list_models(self, headers: dict[str, str]) -> UpstreamResponse:
        return self.get_json("/v1/models", headers)

    def get_json(
        self,
        path: str,
        headers: dict[str, str],
    ) -> UpstreamResponse:
        request = Request(
            f"{self.base_url}{path}",
            headers=headers,
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return UpstreamResponse(
                    body=response.read(),
                    status=response.status,
                    headers=dict(response.headers.items()),
                )
        except HTTPError as exc:
            raise UpstreamHttpError(exc.code, exc.read()) from exc
        except URLError as exc:
            raise UpstreamUnavailable(exc.reason) from exc

    def post_json(
        self,
        path: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> UpstreamResponse:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return UpstreamResponse(
                    body=response.read(),
                    status=response.status,
                    headers=dict(response.headers.items()),
                )
        except HTTPError as exc:
            raise UpstreamHttpError(exc.code, exc.read()) from exc
        except URLError as exc:
            raise UpstreamUnavailable(exc.reason) from exc

    @contextmanager
    def stream_post_json(
        self,
        path: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> Generator[UpstreamStreamResponse, None, None]:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            response = urlopen(request, timeout=self.timeout)
        except HTTPError as exc:
            raise UpstreamHttpError(exc.code, exc.read()) from exc
        except URLError as exc:
            raise UpstreamUnavailable(exc.reason) from exc

        try:
            yield UpstreamStreamResponse(
                status=response.status,
                headers=dict(response.headers.items()),
                response=response,
            )
        finally:
            response.close()

