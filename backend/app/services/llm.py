import httpx

from app.core.config import settings


class LocalProvider:
    async def generate(self, system_prompt: str, input_data: dict) -> dict:
        return {
            "text": f"Local provider response for: {input_data.get('message', input_data)}",
            "provider": "local",
            "model": "deterministic",
        }


class OpenAICompatibleProvider:
    async def generate(self, system_prompt: str, input_data: dict) -> dict:
        if not settings.llm_base_url or not settings.llm_api_key or not settings.llm_model:
            raise RuntimeError("LLM provider is not configured")
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                settings.llm_base_url.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": str(input_data)},
                    ],
                },
            )
            r.raise_for_status()
            return r.json()


def provider():
    return (
        OpenAICompatibleProvider()
        if settings.llm_provider.lower() in ("openai", "openai-compatible")
        else LocalProvider()
    )
