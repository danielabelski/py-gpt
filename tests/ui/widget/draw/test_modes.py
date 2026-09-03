#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2026.09.03 20:31:00                  #
# ================================================== #

from unittest.mock import MagicMock, patch

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor

from pygpt_net.ui.widget.draw.modes import (
    ArrowDrawMode,
    CircleDrawMode,
    DrawMode,
    FreeDrawMode,
    LineDrawMode,
    RectangleDrawMode,
    create_draw_mode_handlers,
)


def test_draw_mode_from_value():
    """Test stable IDs and fallback behavior."""
    assert DrawMode.from_value('free') == DrawMode.FREE
    assert DrawMode.from_value('ARROW') == DrawMode.ARROW
    assert DrawMode.from_value(DrawMode.LINE) == DrawMode.LINE
    assert DrawMode.from_value('invalid') == DrawMode.FREE
    assert DrawMode.from_value(None) == DrawMode.FREE


def test_create_draw_mode_handlers():
    """Test every drawing mode has its own reusable handler."""
    handlers = create_draw_mode_handlers()

    assert isinstance(handlers[DrawMode.FREE], FreeDrawMode)
    assert isinstance(handlers[DrawMode.ARROW], ArrowDrawMode)
    assert isinstance(handlers[DrawMode.RECTANGLE], RectangleDrawMode)
    assert isinstance(handlers[DrawMode.CIRCLE], CircleDrawMode)
    assert isinstance(handlers[DrawMode.LINE], LineDrawMode)
    assert set(handlers) == set(DrawMode)


def test_free_draw_lifecycle():
    """Test freehand gesture starts, updates and commits one transaction."""
    widget = MagicMock()
    widget._mode = 'brush'
    widget.brushSize = 5
    widget._pen = MagicMock()
    widget.drawingLayer = MagicMock()
    widget._dirty_canvas_rect_for_point.return_value = MagicMock()
    widget._dirty_canvas_rect_for_segment.return_value = MagicMock()
    widget._from_canvas_rect.side_effect = lambda value: value

    qt_painter = MagicMock()
    with patch('pygpt_net.ui.widget.draw.modes.free.QPainter', return_value=qt_painter):
        mode = FreeDrawMode()
        mode.begin(widget, QPoint(10, 10))
        mode.update(widget, QPoint(20, 20))
        mode.release(widget, QPoint(30, 30))

    widget._begin_draw_transaction.assert_called_once()
    qt_painter.drawPoint.assert_called_once_with(QPoint(10, 10))
    assert qt_painter.drawLine.call_count == 2
    widget._commit_draw_transaction.assert_called_once()
    assert mode.active is False


def test_shape_release_commits_only_after_mouse_release():
    """Test shape preview does not touch layer until release, then commits once."""
    widget = MagicMock()
    widget.drawingLayer = MagicMock()
    widget.brushSize = 3
    widget.brushColor = QColor('red')
    fake_painter = MagicMock()
    mode = LineDrawMode()

    mode.begin(widget, QPoint(10, 10))
    mode.update(widget, QPoint(50, 50))
    widget._commit_draw_transaction.assert_not_called()

    with patch('pygpt_net.ui.widget.draw.modes.shapes.QPainter', return_value=fake_painter):
        mode.release(widget, QPoint(60, 60))

    fake_painter.drawLine.assert_called_once()
    widget._mark_composite_dirty.assert_called_once()
    widget._commit_draw_transaction.assert_called_once()
    widget._cancel_draw_transaction.assert_not_called()
    assert mode.active is False


def test_shape_release_without_geometry_cancels_transaction():
    """Test zero-size shape is discarded instead of creating an undo entry."""
    widget = MagicMock()
    mode = RectangleDrawMode()

    mode.begin(widget, QPoint(10, 10))
    mode.release(widget, QPoint(10, 10))

    widget._cancel_draw_transaction.assert_called_once()
    widget._commit_draw_transaction.assert_not_called()


def test_shape_cancel_cancels_transaction():
    """Test ESC-style cancellation drops the active preview transaction."""
    widget = MagicMock()
    mode = CircleDrawMode()

    mode.begin(widget, QPoint(10, 10))
    mode.update(widget, QPoint(20, 20))
    mode.cancel(widget)

    widget._cancel_draw_transaction.assert_called_once()
    widget._commit_draw_transaction.assert_not_called()
    assert mode.active is False


def test_arrow_uses_filled_triangle_head():
    """Test arrow uses a shaft plus a filled three-point polygon head."""
    widget = MagicMock()
    widget.brushSize = 8
    widget.brushColor = QColor('red')
    painter = MagicMock()
    mode = ArrowDrawMode()
    mode.start = QPoint(10, 10)
    mode.current = QPoint(110, 10)

    mode.draw_shape(widget, painter)

    painter.drawLine.assert_called_once()
    painter.drawPolygon.assert_called_once()
    polygon = painter.drawPolygon.call_args.args[0]
    assert len(polygon) == 3
    painter.setBrush.assert_called()


def test_circle_is_drawn_from_center():
    """Test circle start point is treated as the center of the ellipse."""
    widget = MagicMock()
    widget.brushSize = 3
    widget.brushColor = QColor('red')
    painter = MagicMock()
    mode = CircleDrawMode()
    mode.start = QPoint(100, 100)
    mode.current = QPoint(130, 140)  # radius = 50

    mode.draw_shape(widget, painter)

    painter.drawEllipse.assert_called_once()
    rect = painter.drawEllipse.call_args.args[0]
    assert rect.center().x() == 100
    assert rect.center().y() == 100
    assert round(rect.width()) == 100
    assert round(rect.height()) == 100
