#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2025.08.02 20:00:00                  #
# ================================================== #

import hashlib
import re
from typing import Optional, List, Dict


class LLM:
    def __init__(self, window=None):
        """
        LLMs manager

        :param window: Window instance
        """
        self.window = window
        self.llms = {}
        self._runtime_custom_ids = set()
        self._runtime_custom_signature = None


    @staticmethod
    def is_custom_provider(id: str) -> bool:
        """Return True for a runtime custom provider ID."""
        return isinstance(id, str) and id.startswith("custom_")

    @staticmethod
    def make_custom_provider_id(name: str) -> str:
        """Build a deterministic internal provider ID from its display name."""
        raw = (name or "").strip()
        normalized = raw.casefold()
        slug = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_") or "provider"
        slug = slug[:40]
        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:8]
        return f"custom_{slug}_{digest}"

    def sync_custom(self, force: bool = False):
        """Synchronize runtime custom providers from ``api_custom_providers`` config."""
        if self.window is None or not hasattr(self.window, "core"):
            return
        config = getattr(self.window.core, "config", None)
        if config is None:
            return

        rows = config.get("api_custom_providers", []) or []
        if not isinstance(rows, list):
            rows = []
        signature = repr([
            (
                str(item.get("name", "") or "").strip(),
                str(item.get("api_base", "") or "").strip(),
                str(item.get("api_key", "") or ""),
            )
            for item in rows if isinstance(item, dict)
        ])
        if not force and signature == self._runtime_custom_signature:
            return

        # Remove only providers previously created from runtime config. Providers
        # registered through a custom launcher remain untouched.
        for provider_id in list(self._runtime_custom_ids):
            self.llms.pop(provider_id, None)
        self._runtime_custom_ids.clear()

        from pygpt_net.provider.llms.custom import CustomLLM

        for item in rows:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "") or "").strip()
            api_base = str(item.get("api_base", "") or "").strip()
            api_key = str(item.get("api_key", "") or "")
            if not name or not api_base:
                continue

            provider_id = self.make_custom_provider_id(name)
            # Do not overwrite a provider registered by code with the same ID.
            if provider_id in self.llms and provider_id not in self._runtime_custom_ids:
                continue
            self.llms[provider_id] = CustomLLM(
                provider_id=provider_id,
                name=name,
                api_base=api_base,
                api_key=api_key,
            )
            self._runtime_custom_ids.add(provider_id)

        self._runtime_custom_signature = signature

    def get_ids(
            self,
            type: Optional[str] = None
    ) -> List[str]:
        """
        Get providers ids

        :param type: provider type
        :return: providers ids
        """
        self.sync_custom()
        if type is not None:
            return [id for id in self.llms.keys() if type in self.llms[id].type]
        return list(self.llms.keys())  # get all

    def get_choices(
            self,
            type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get providers choices

        :param type: provider type
        :return: providers choices
        """
        self.sync_custom()
        choices = {}
        if type is not None:
            for id in list(self.llms.keys()):
                if type in self.llms[id].type:
                    choices[id] = self.llms[id].name
        else:
            for id in list(self.llms.keys()):
                choices[id] = self.llms[id].name

        # sorted by name
        return dict(sorted(choices.items(), key=lambda item: item[1].lower()))

    def get_provider_name(self, id: str) -> str:
        """
        Get provider name by id

        :param id: LLM id
        :return: provider name
        """
        self.sync_custom()
        return self.llms[id].name if id in self.llms else id

    def get(self, id: str):
        """
        Get LLM provider by id

        :param id: LLM id
        :return: LLM provider instance
        """
        self.sync_custom()
        return self.llms[id] if id in self.llms else None

    def register(
            self,
            id: str,
            llm
    ):
        """
        Register LLM provider

        :param id: LLM id
        :param llm: LLM object
        """
        self.llms[id] = llm
