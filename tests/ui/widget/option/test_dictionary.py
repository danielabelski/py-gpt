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

from PySide6.QtCore import Qt

from pygpt_net.ui.widget.option.dictionary import OptionDictModel


def test_header_labels_can_override_raw_dictionary_keys():
    model = OptionDictModel(
        items=[{"name": "Provider", "api_key": "SECRET"}],
        headers=["name", "api_key"],
        header_labels={"name": "Provider name", "api_key": "API key"},
    )

    assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "Provider name"
    assert model.headerData(1, Qt.Horizontal, Qt.DisplayRole) == "API key"


def test_secret_dictionary_field_is_masked_only_for_display():
    model = OptionDictModel(
        items=[{"name": "Provider", "api_key": "SECRET"}],
        headers=["name", "api_key"],
        secret_headers={"api_key"},
    )
    index = model.index(0, 1)

    assert model.data(index, Qt.DisplayRole) == "••••••••"
    assert model.data(index, Qt.EditRole) == "SECRET"


def test_empty_secret_dictionary_field_is_not_replaced_with_mask():
    model = OptionDictModel(
        items=[{"api_key": ""}],
        headers=["api_key"],
        secret_headers={"api_key"},
    )
    index = model.index(0, 0)

    assert model.data(index, Qt.DisplayRole) == ""
    assert model.data(index, Qt.EditRole) == ""
