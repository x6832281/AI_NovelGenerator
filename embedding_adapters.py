# embedding_adapters.py
# -*- coding: utf-8 -*-
import logging
from typing import List
from langchain_openai import OpenAIEmbeddings

def ensure_openai_base_url_has_v1(url: str) -> str:
    """
    若用户输入的 url 不包含 '/v1'，则在末尾追加 '/v1'。
    """
    import re
    url = url.strip()
    if not url:
        return url
    if not re.search(r'/v\d+$', url):
        if '/v1' not in url:
            url = url.rstrip('/') + '/v1'
    return url

class BaseEmbeddingAdapter:
    """
    Embedding 接口统一基类
    """
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> List[float]:
        raise NotImplementedError

class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    基于 OpenAIEmbeddings（或兼容接口）的适配器
    兼容 DeepSeek 等 OpenAI 兼容 embedding 接口
    """
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self._embedding = OpenAIEmbeddings(
            openai_api_key=api_key,
            openai_api_base=ensure_openai_base_url_has_v1(base_url),
            model=model_name
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embedding.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        return self._embedding.embed_query(query)


class DashScopeEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    阿里云百炼 Embedding 适配器
    直接用 requests 调用兼容接口（避开 langchain_openai 的格式问题）
    """
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        # 使用 OpenAI 兼容接口
        self.url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _call_api(self, texts: List[str]) -> List[List[float]]:
        import requests
        embeddings = []
        for text in texts:
            payload = {
                "model": self.model_name,
                "input": text
            }
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=60)
            if response.status_code != 200:
                raise ValueError(
                    f"DashScope compatible API returned {response.status_code}: {response.text[:500]}"
                )
            result = response.json()
            if "data" not in result or not result["data"]:
                raise ValueError(f"Unexpected API response: {result}")
            embeddings.append(result["data"][0]["embedding"])
        return embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._call_api(texts)

    def embed_query(self, query: str) -> List[float]:
        results = self._call_api([query])
        return results[0] if results else []


def create_embedding_adapter(
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str
) -> BaseEmbeddingAdapter:
    """
    工厂函数：根据 interface_format 返回不同的 embedding 适配器实例
    """
    fmt = interface_format.strip().lower()
    if fmt == "openai":
        return OpenAIEmbeddingAdapter(api_key, base_url, model_name)
    elif fmt == "deepseek":
        return OpenAIEmbeddingAdapter(api_key, base_url, model_name)
    elif fmt == "阿里云百炼":
        return DashScopeEmbeddingAdapter(api_key, base_url, model_name)
    else:
        raise ValueError(f"Unknown embedding interface_format: {interface_format}")
