#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2026.09.05 12:30:00                  #
# ================================================== #

from pygpt_net.item.model import ModelItem


def test_integrity():
    """Test ModeItem integrity"""
    item = ModelItem()

    assert item.id is None
    assert item.name is None
    assert item.mode == ["chat"]
    assert item.langchain == {}
    assert item.ctx == 0
    assert item.tokens == 0
    assert item.default is False
    assert item.is_hidden is False


def test_runtime_custom_provider_is_openai_compatible():
    item = ModelItem("custom-model")
    item.provider = "custom_my_api_12345678"
    item.mode = ["chat", "llama_index"]

    assert item.is_openai_supported() is True
    assert item.is_supported("chat") is True


def test_non_compatible_unknown_provider_is_not_supported_in_chat():
    item = ModelItem("unknown-model")
    item.provider = "unknown_provider"
    item.mode = ["chat"]

    assert item.is_openai_supported() is False
    assert item.is_supported("chat") is False
