import httpx
import re
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.event.filter import on_llm_response, after_message_sent
from astrbot.api.provider import LLMResponse
from astrbot import logger


@register("astrbot_plugin_llm_translator", "FlandreX", "LLM 回复翻译器", "1.0.0")
class LLMTranslatorPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        timeout = int(self.config.get("timeout", 30))
        self.client = httpx.AsyncClient(timeout=timeout)
        self._prompt = ""
        self._prompt_source = ""
        self._prompt_target = ""

    async def initialize(self):
        pass

    def _resolve_key(self):
        manual = self.config.get("api_key", "").strip()
        if manual:
            return manual
        try:
            provider = self.context.get_using_provider()
            if provider:
                keys = provider.get_keys()
                if keys:
                    logger.info("[llm_translator] 从 AstrBot Provider 自动获取 Key")
                    return keys[0]
        except Exception as e:
            logger.warning(f"[llm_translator] 获取 Key 失败: {e}")
        return ""

    def _get_prompt(self):
        source = self.config.get("source_lang", "") or "中文"
        target = self.config.get("target_lang", "") or "日语"
        if self._prompt_source != source or self._prompt_target != target:
            self._prompt = f"将以下{source}翻译成{target}，只输出译文，使用自然口语：\n\n"
            self._prompt_source = source
            self._prompt_target = target
        return self._prompt

    @on_llm_response()
    async def translate(self, event: AstrMessageEvent, response: LLMResponse):
        text = response.completion_text
        if not text or not text.strip():
            return

        original = text
        filter_re = self.config.get("text_filter_regex", "").strip()
        if filter_re:
            try:
                text = re.sub(filter_re, "", text)
            except re.error as e:
                logger.warning(f"[llm_translator] 正则过滤表达式错误: {e}")
                pass
            if not text:
                return

        key = self._resolve_key()
        if not key:
            logger.warning("[llm_translator] 未配置 API Key")
            return

        base = self.config.get("api_base", "").strip()
        model = self.config.get("api_model", "").strip()
        if base and "/chat/completions" not in base:
            base = base.rstrip("/") + "/v1/chat/completions"
        if not base or not model:
            try:
                provider = self.context.get_using_provider()
                if provider:
                    pconf = provider.provider_config
                    if not base:
                        base = pconf.get("api_base", "")
                        if base and "/chat/completions" not in base:
                            base = base.rstrip("/") + "/v1/chat/completions"
                    if not model:
                        model = provider.get_model()
            except Exception:
                pass
        if not base or not model:
            logger.warning("[llm_translator] 无法确定 API 端点或模型，请手动填写 api_base 和 api_model")
            return

        try:
            r = await self.client.post(
                base,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": self._get_prompt() + text}],
                    "max_tokens": int(self.config.get("max_tokens", 4096)),
                    "temperature": 0,
                },
            )
            if r.status_code == 200:
                choices = r.json().get("choices", [])
                if choices:
                    result = choices[0].get("message", {}).get("content", "").strip()
                    if result:
                        response.completion_text = result
                        logger.info(f"[llm_translator] 翻译成功: {len(text)}c -> {len(result)}c")
                        if self.config.get("send_original"):
                            event.set_extra("_llm_translator_original", original)
            else:
                logger.warning(f"[llm_translator] API {r.status_code}: {r.text[:300]}")
        except Exception as e:
            logger.error(f"[llm_translator] {type(e).__name__}: {e}")

    @after_message_sent()
    async def send_original(self, event: AstrMessageEvent):
        if not self.config.get("send_original"):
            return
        original = event.get_extra("_llm_translator_original")
        if not original:
            logger.warning("[llm_translator] 追发原文失败：未找到原文")
            return
        logger.info(f"[llm_translator] 追发原文: {len(original)}c")
        from astrbot.core.message.components import Plain
        from astrbot.core.message.message_event_result import MessageChain
        await event.send(MessageChain([Plain(original)]))

    async def terminate(self):
        await self.client.aclose()
