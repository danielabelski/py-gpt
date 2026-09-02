#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2026.09.02 20:55:00                  #
# ================================================== #

import os
from typing import Optional, List, Dict

# from langchain_community.chat_models import ChatOllama

from llama_index.core.llms.llm import BaseLLM as LlamaBaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding

from pygpt_net.core.types import (
    MODE_LLAMA_INDEX,
    MODE_CHAT,
)
from pygpt_net.provider.llms.base import BaseLLM
from pygpt_net.item.model import ModelItem
import nest_asyncio


class OllamaLLM(BaseLLM):
    def __init__(self, *args, **kwargs):
        super(OllamaLLM, self).__init__(*args, **kwargs)
        self.id = "ollama"
        self.name = "Ollama"
        self.type = [MODE_LLAMA_INDEX, "embeddings"]

    def completion(
            self,
            window,
            model: ModelItem,
            stream: bool = False
    ):
        """
        Return LLM provider instance for completion

        :param window: window instance
        :param model: model instance
        :param stream: stream mode
        :return: LLM provider instance
        """
        pass

    def chat(
            self,
            window,
            model: ModelItem,
            stream: bool = False
    ):
        """
        Return LLM provider instance for chat

        :param window: window instance
        :param model: model instance
        :param stream: stream mode
        :return: LLM provider instance

        args = self.parse_args(model.langchain)
        if "model" not in args:
            args["model"] = model.id
        return ChatOllama(**args)
        """
        pass

    def llama(
            self,
            window,
            model: ModelItem,
            stream: bool = False
    ) -> LlamaBaseLLM:
        """
        Return LLM provider instance for llama

        :param window: window instance
        :param model: model instance
        :param stream: stream mode
        :return: LLM provider instance
        """
        from llama_index.llms.openai_like import OpenAILike

        nest_asyncio.apply()
        args = self.parse_args(model.llama_index, window)

        model_id = (model.get_ollama_model() or model.id or "").strip()
        if not model_id:
            raise ValueError("Ollama model name is required")
        args["model"] = model_id

        # Reuse the exact endpoint/key resolution used by normal Chat,
        # including OLLAMA_API_BASE and per-model custom API overrides.
        client_args = window.core.models.prepare_client_args(MODE_CHAT, model)
        api_base = (client_args.get("base_url") or "").strip()
        if not api_base:
            api_base = window.core.models.ollama.get_base_url().rstrip("/") + "/v1"

        if not args.get("api_key"):
            args["api_key"] = client_args.get("api_key") or "ollama"
        if not args.get("api_base"):
            args["api_base"] = api_base
        if "is_chat_model" not in args:
            args["is_chat_model"] = True
        if "is_function_calling_model" not in args:
            args["is_function_calling_model"] = bool(model.tool_calls)

        # Keep PyGPT model limits in LlamaIndex metadata/request settings.
        ctx_size = window.core.models.get_num_ctx(model.id) if model.id else 0
        if ctx_size <= 0:
            ctx_size = window.core.config.get("max_total_tokens") or 0
        if ctx_size > 0 and "context_window" not in args:
            args["context_window"] = int(ctx_size)

        args = self.inject_llamaindex_http_clients(args, window.core.config)
        return OpenAILike(**args)

    def get_embeddings_model(
            self,
            window,
            config: Optional[List[Dict]] = None
    ) -> BaseEmbedding:
        """
        Return provider instance for embeddings

        :param window: window instance
        :param config: config keyword arguments list
        :return: Embedding provider instance
        """
        from llama_index.embeddings.ollama import OllamaEmbedding
        args = {}
        if config is not None:
            args = self.parse_args({
                "args": config,
            }, window)
        if 'OLLAMA_API_BASE' in os.environ:
            if "base_url" not in args:
                args["base_url"] = os.environ['OLLAMA_API_BASE']
        if "model" in args and "model_name" not in args:
            args["model_name"] = args.pop("model")
        return OllamaEmbedding(**args)

    def init_embeddings(
            self,
            window,
            env: Optional[List[Dict]] = None
    ):
        """
        Initialize embeddings provider

        :param window: window instance
        :param env: ENV configuration list
        """
        super(OllamaLLM, self).init_embeddings(window, env)

        # === FIX FOR LOCAL EMBEDDINGS ===
        # if there is no OpenAI api key then set fake key to prevent empty key Llama-index error
        if ('OPENAI_API_KEY' not in os.environ
                and (window.core.config.get('api_key') is None or window.core.config.get('api_key') == "")):
            os.environ['OPENAI_API_KEY'] = "_"
