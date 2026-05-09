# llm_adapters.py
# -*- coding: utf-8 -*-
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from openai import OpenAI
import requests


def check_base_url(url: str) -> str:
    """
    处理base_url的规则：
    1. 如果url以#结尾，则移除#并直接使用用户提供的url
    2. 否则检查是否需要添加/v1后缀
    """
    import re
    url = url.strip()
    if not url:
        return url
        
    if url.endswith('#'):
        return url.rstrip('#')
        
    if not re.search(r'/v\d+$', url):
        if '/v1' not in url:
            url = url.rstrip('/') + '/v1'
    return url


class BaseLLMAdapter:
    """
    统一适配器基类
    约定：
      子类可以通过重写 _build_request 来使用不同的请求格式
      外部调用 call(prompt) 会经过预处理、重试、日志、后处理等公共逻辑
    """
    def call(self, user_prompt: str, system_prompt: str = "", stop_sequences=None) -> str:
        raise NotImplementedError
    
    def call_with_messages(self, messages: list, stop_sequences=None) -> str:
        raise NotImplementedError


class DeepSeekAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float, timeout: int):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def call(self, user_prompt: str, system_prompt: str = "", stop_sequences=None) -> str:
        messages = [
            {"role": "system", "content": system_prompt if system_prompt else "你是DeepSeek，是一个 AI 人工智能助手"},
            {"role": "user", "content": user_prompt}
        ]
        return self.call_with_messages(messages, stop_sequences)

    def call_with_messages(self, messages: list, stop_sequences=None) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stop=stop_sequences,
                timeout=self.timeout
            )
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or ""
            return ""
        except Exception as e:
            logging.error(f"DeepSeek API 调用失败: {e}")
            return ""


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float, timeout: int):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.client = ChatOpenAI(
            openai_api_key=api_key,
            openai_api_base=base_url,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            request_timeout=timeout
        )

    def call(self, user_prompt: str, system_prompt: str = "", stop_sequences=None) -> str:
        messages = [
            {"role": "system", "content": system_prompt if system_prompt else "You are a helpful AI assistant."},
            {"role": "user", "content": user_prompt}
        ]
        return self.call_with_messages(messages, stop_sequences)

    def call_with_messages(self, messages: list, stop_sequences=None) -> str:
        try:
            response = self.client.invoke(messages, stop=stop_sequences)
            return response.content if response and hasattr(response, 'content') else str(response)
        except Exception as e:
            logging.error(f"OpenAI API 调用失败: {e}")
            return ""


class ClaudeAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float, timeout: int):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.api_key = api_key
        self.base_url = base_url

    def call(self, user_prompt: str, system_prompt: str = "", stop_sequences=None) -> str:
        messages = [
            {"role": "system", "content": system_prompt if system_prompt else "You are Claude, a helpful AI assistant."},
            {"role": "user", "content": user_prompt}
        ]
        return self.call_with_messages(messages, stop_sequences)

    def call_with_messages(self, messages: list, stop_sequences=None) -> str:
        try:
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stop=stop_sequences,
                timeout=self.timeout
            )
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or ""
            return ""
        except Exception as e:
            logging.error(f"Claude API 调用失败: {e}")
            return ""


def create_llm_adapter(
    interface_format: str,
    base_url: str,
    model_name: str,
    api_key: str,
    temperature: float,
    max_tokens: int,
    timeout: int
) -> BaseLLMAdapter:
    """
    工厂函数：根据 interface_format 返回不同的适配器实例。
    """
    fmt = interface_format.strip().lower()
    if fmt == "deepseek":
        return DeepSeekAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "openai":
        return OpenAIAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "claude":
        return ClaudeAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    else:
        raise ValueError(f"Unknown interface_format: {interface_format}")
