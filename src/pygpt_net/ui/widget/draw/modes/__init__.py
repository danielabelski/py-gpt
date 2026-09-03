#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .base import DrawMode, DRAW_MODE_ORDER, DRAW_MODE_NAMES, DRAW_MODE_TRANSLATION_KEYS
from .free import FreeDrawMode
from .shapes import ArrowDrawMode, RectangleDrawMode, CircleDrawMode, LineDrawMode


def create_draw_mode_handlers():
    """Create one reusable handler instance per Painter drawing mode."""
    return {
        DrawMode.FREE: FreeDrawMode(),
        DrawMode.ARROW: ArrowDrawMode(),
        DrawMode.RECTANGLE: RectangleDrawMode(),
        DrawMode.CIRCLE: CircleDrawMode(),
        DrawMode.LINE: LineDrawMode(),
    }


__all__ = [
    "DrawMode",
    "DRAW_MODE_ORDER",
    "DRAW_MODE_NAMES",
    "DRAW_MODE_TRANSLATION_KEYS",
    "create_draw_mode_handlers",
]
