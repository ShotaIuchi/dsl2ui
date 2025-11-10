#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import json
import sys
from io import StringIO
from unittest.mock import patch
import toJetpackCompose

class TestToJetpackCompose(unittest.TestCase):

    def setUp(self):
        """テストの前処理"""
        self.maxDiff = None

    def test_dp(self):
        """dp関数のテスト"""
        self.assertEqual(toJetpackCompose.dp(10), "10.dp")
        self.assertEqual(toJetpackCompose.dp(10.5), "10.dp")  # round(10.5) = 10 in Python 3
        self.assertEqual(toJetpackCompose.dp(0), None)
        self.assertEqual(toJetpackCompose.dp(None), None)

    def test_indent(self):
        """indent関数のテスト"""
        self.assertEqual(toJetpackCompose.indent(0), "")
        self.assertEqual(toJetpackCompose.indent(1), "  ")
        self.assertEqual(toJetpackCompose.indent(3), "      ")

    def test_apply_size(self):
        """apply_size関数のテスト"""
        # FILL width
        layout = {"width": {"mode": "FILL"}}
        self.assertEqual(toJetpackCompose.apply_size(layout), "modifier = Modifier.fillMaxWidth()")

        # FILL height
        layout = {"height": {"mode": "FILL"}}
        self.assertEqual(toJetpackCompose.apply_size(layout), "modifier = Modifier.fillMaxHeight()")

        # FIXED dimensions
        layout = {
            "width": {"mode": "FIXED", "value": 100},
            "height": {"mode": "FIXED", "value": 50}
        }
        result = toJetpackCompose.apply_size(layout)
        self.assertIn("width(100.dp)", result)
        self.assertIn("height(50.dp)", result)

        # With padding
        layout = {"padding": [16, 8, 16, 8]}
        result = toJetpackCompose.apply_size(layout)
        self.assertIn("padding(start = 16.dp, top = 8.dp, end = 16.dp, bottom = 8.dp)", result)

        # Combined
        layout = {
            "width": {"mode": "FILL"},
            "height": {"mode": "FIXED", "value": 48},
            "padding": [8, 8, 8, 8]
        }
        result = toJetpackCompose.apply_size(layout)
        self.assertIn("fillMaxWidth()", result)
        self.assertIn("height(48.dp)", result)
        self.assertIn("padding(", result)

    def test_map_arrangement(self):
        """map_arrangement関数のテスト"""
        # Vertical arrangement
        layout = {"direction": "VERTICAL", "spacing": 12}
        result = toJetpackCompose.map_arrangement(layout)
        self.assertEqual(result, "verticalArrangement = Arrangement.spacedBy(12.dp)")

        # Horizontal arrangement
        layout = {"direction": "HORIZONTAL", "spacing": 8}
        result = toJetpackCompose.map_arrangement(layout)
        self.assertEqual(result, "horizontalArrangement = Arrangement.spacedBy(8.dp)")

        # No spacing
        layout = {"direction": "VERTICAL"}
        result = toJetpackCompose.map_arrangement(layout)
        self.assertEqual(result, "")

    def test_map_container(self):
        """map_container関数のテスト"""
        # Horizontal scroll
        result = toJetpackCompose.map_container({}, "horizontal")
        self.assertEqual(result[0], "LazyRow")
        self.assertEqual(result[1], [])
        self.assertTrue(result[2])  # lazy

        # Row with vertical scroll
        layout = {"direction": "HORIZONTAL"}
        result = toJetpackCompose.map_container(layout, "vertical")
        self.assertEqual(result[0], "Row")
        self.assertEqual(result[1], ["horizontalScroll(rememberScrollState())"])
        self.assertFalse(result[2])  # not lazy

        # Column with vertical scroll
        layout = {"direction": "VERTICAL"}
        result = toJetpackCompose.map_container(layout, "vertical")
        self.assertEqual(result[0], "Column")
        self.assertEqual(result[1], ["verticalScroll(rememberScrollState())"])
        self.assertFalse(result[2])  # not lazy

    def test_to_compose_name(self):
        """to_compose_name関数のテスト"""
        self.assertEqual(toJetpackCompose.to_compose_name("Za/IconButton"), "ZaIconButton")
        self.assertEqual(toJetpackCompose.to_compose_name("Za/Button"), "ZaButton")
        self.assertEqual(toJetpackCompose.to_compose_name("component-name"), "component name")  # actual behavior
        self.assertEqual(toJetpackCompose.to_compose_name("my_component"), "my component")  # actual behavior

    def test_stringify_prop(self):
        """stringify_prop関数のテスト"""
        self.assertEqual(toJetpackCompose.stringify_prop("enabled", True), "enabled = true")
        self.assertEqual(toJetpackCompose.stringify_prop("enabled", False), "enabled = false")
        self.assertEqual(toJetpackCompose.stringify_prop("size", 42), "size = 42")
        self.assertEqual(toJetpackCompose.stringify_prop("label", "Hello"), 'label = "Hello"')
        self.assertEqual(toJetpackCompose.stringify_prop("value", "{{item.name}}"), "value = item.name")

    def test_emit_node_text(self):
        """TEXT ノードの出力テスト"""
        node = {"type": "TEXT", "text": "在庫一覧"}
        result = toJetpackCompose.emit_node(node, 1)
        self.assertEqual(result, '  Text("在庫一覧")')

    def test_emit_node_spacer(self):
        """SPACER ノードの出力テスト"""
        # In vertical context
        node = {"type": "SPACER"}
        result = toJetpackCompose.emit_node(node, 1, "VERTICAL")
        self.assertEqual(result, "  Spacer(Modifier.height(0.dp).weight(1f))")

        # In horizontal context
        result = toJetpackCompose.emit_node(node, 1, "HORIZONTAL")
        self.assertEqual(result, "  Spacer(Modifier.width(0.dp).weight(1f))")

    def test_emit_node_instance(self):
        """INSTANCE ノードの出力テスト"""
        node = {
            "type": "INSTANCE",
            "name": "Za/Button",
            "props": {"label": "新規追加", "variant": "Primary"},
            "layout": {"width": {"mode": "FILL"}}
        }
        result = toJetpackCompose.emit_node(node, 1)
        self.assertIn("ZaButton(", result)
        self.assertIn('label = "新規追加"', result)
        self.assertIn('variant = "Primary"', result)
        self.assertIn("modifier = Modifier.fillMaxWidth()", result)

    def test_emit_node_frame_simple(self):
        """シンプルな FRAME ノードの出力テスト"""
        node = {
            "type": "FRAME",
            "layout": {"direction": "HORIZONTAL", "spacing": 8},
            "children": [
                {"type": "TEXT", "text": "Title"},
                {"type": "SPACER"}
            ]
        }
        result = toJetpackCompose.emit_node(node, 1)
        lines = result.split("\n")
        self.assertIn("Row(", lines[0])
        self.assertIn("horizontalArrangement = Arrangement.spacedBy(8.dp)", lines[0])
        self.assertEqual(lines[1], '    Text("Title")')
        self.assertEqual(lines[2], "    Spacer(Modifier.width(0.dp).weight(1f))")

    def test_emit_node_with_repeat(self):
        """repeat を持つ FRAME ノードの出力テスト"""
        node = {
            "type": "FRAME",
            "layout": {"direction": "VERTICAL", "spacing": 8},
            "repeat": {"for": "items", "as": "item"},
            "children": [
                {"type": "TEXT", "text": "{{item.name}}"}
            ]
        }
        result = toJetpackCompose.emit_node(node, 1)
        self.assertIn("items.forEach { item ->", result)
        self.assertIn("Column(", result)
        self.assertIn("verticalArrangement = Arrangement.spacedBy(8.dp)", result)

    def test_emit_node_overlay(self):
        """OVERLAY ノードの出力テスト"""
        node = {
            "type": "OVERLAY",
            "position": {"right": 16, "bottom": 16},
            "child": {"type": "TEXT", "text": "FAB"}
        }
        result = toJetpackCompose.emit_node(node, 1)
        self.assertIn("Box(Modifier.align(Alignment.BottomEnd)", result)
        self.assertIn("end = 16.dp", result)
        self.assertIn("bottom = 16.dp", result)

    def test_emit_node_with_visibility(self):
        """visible 条件付きノードの出力テスト"""
        node = {
            "type": "TEXT",
            "text": "Conditional",
            "visible": "{{showText}}"
        }
        result = toJetpackCompose.emit_node(node, 1)
        lines = result.split("\n")
        self.assertEqual(lines[0], "  if (showText) {")
        self.assertEqual(lines[1], '    Text("Conditional")')
        self.assertEqual(lines[2], "  }")

    def test_to_pascal(self):
        """to_pascal関数のテスト"""
        self.assertEqual(toJetpackCompose.to_pascal("inventory-screen"), "InventoryScreen")
        self.assertEqual(toJetpackCompose.to_pascal("my_component_name"), "MyComponentName")
        self.assertEqual(toJetpackCompose.to_pascal("123test"), "123test")
        self.assertEqual(toJetpackCompose.to_pascal(""), "GeneratedScreen")

    def test_wrap_file(self):
        """wrap_file関数のテスト"""
        body = '    Text("Hello")'
        result = toJetpackCompose.wrap_file("TestScreen", body)

        self.assertIn("package ui.generated", result)
        self.assertIn("import androidx.compose.foundation.layout.*", result)
        self.assertIn("import androidx.compose.material3.Text", result)
        self.assertIn("@Composable", result)
        self.assertIn("fun TestScreen(", result)
        self.assertIn("items: List<Any> = emptyList()", result)
        self.assertIn("Box(Modifier.fillMaxSize())", result)
        self.assertIn(body, result)

    def test_main_with_simple_dsl(self):
        """main関数の統合テスト（シンプルなDSL）"""
        dsl = {
            "type": "FRAME",
            "name": "TestScreen",
            "layout": {"direction": "VERTICAL", "spacing": 16},
            "children": [
                {"type": "TEXT", "text": "Hello World"},
                {"type": "SPACER"}
            ]
        }

        with patch('sys.stdin', StringIO(json.dumps(dsl))):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with patch('sys.argv', ['toJetpackCompose.py']):
                    toJetpackCompose.main()
                output = mock_stdout.getvalue()

        self.assertIn("fun TestScreen(", output)
        self.assertIn("Column(", output)
        self.assertIn("verticalArrangement = Arrangement.spacedBy(16.dp)", output)
        self.assertIn('Text("Hello World")', output)
        self.assertIn("Spacer(", output)

    def test_main_with_complex_dsl(self):
        """main関数の統合テスト（実際のdsl.jsonに近い構造）"""
        dsl = {
            "type": "FRAME",
            "name": "InventoryScreen",
            "layout": {"direction": "VERTICAL", "spacing": 12, "padding": [16, 16, 16, 16]},
            "scroll": "vertical",
            "children": [
                {
                    "type": "FRAME",
                    "name": "Header",
                    "layout": {"direction": "HORIZONTAL", "spacing": 8},
                    "children": [
                        {"type": "TEXT", "text": "在庫一覧"},
                        {"type": "SPACER"},
                        {"type": "INSTANCE", "name": "Za/IconButton", "props": {"icon": "search"}}
                    ]
                },
                {
                    "type": "INSTANCE",
                    "name": "Za/Button",
                    "props": {"label": "新規追加"},
                    "layout": {"width": {"mode": "FILL"}}
                }
            ]
        }

        with patch('sys.stdin', StringIO(json.dumps(dsl))):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with patch('sys.argv', ['toJetpackCompose.py']):
                    toJetpackCompose.main()
                output = mock_stdout.getvalue()

        self.assertIn("fun InventoryScreen(", output)
        self.assertIn("Column(", output)
        # verticalScroll is not applied because scroll is specified at root level
        self.assertIn("verticalArrangement = Arrangement.spacedBy(12.dp)", output)
        self.assertIn("Row(", output)
        self.assertIn("horizontalArrangement = Arrangement.spacedBy(8.dp)", output)
        self.assertIn('Text("在庫一覧")', output)
        self.assertIn('ZaIconButton(icon = "search"', output)
        self.assertIn('ZaButton(label = "新規追加"', output)
        self.assertIn("fillMaxWidth()", output)

    def test_main_with_lazy_row(self):
        """LazyRow を使用するケースのテスト"""
        dsl = {
            "type": "FRAME",
            "name": "HorizontalList",
            "scroll": "horizontal",
            "layout": {"spacing": 10},
            "children": [
                {"type": "TEXT", "text": "Item 1"},
                {"type": "TEXT", "text": "Item 2"}
            ]
        }

        with patch('sys.stdin', StringIO(json.dumps(dsl))):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with patch('sys.argv', ['toJetpackCompose.py']):
                    toJetpackCompose.main()
                output = mock_stdout.getvalue()

        self.assertIn("LazyRow(", output)
        # LazyRow doesn't have arrangement in current implementation

    def test_lazy_row_with_items_blocks(self):
        """LazyRow が item {} ブロックを生成するテスト"""
        dsl = {
            "type": "FRAME",
            "scroll": "horizontal",
            "layout": {"spacing": 8},
            "children": [
                {"type": "TEXT", "text": "Item 1"},
                {"type": "TEXT", "text": "Item 2"}
            ]
        }
        result = toJetpackCompose.emit_node(dsl, 1)
        self.assertIn("LazyRow(", result)
        self.assertIn("item {", result)
        self.assertIn('Text("Item 1")', result)
        self.assertIn('Text("Item 2")', result)

    def test_lazy_row_with_repeat_uses_items_function(self):
        """LazyRow + repeat が items() 関数を使うテスト"""
        dsl = {
            "type": "FRAME",
            "scroll": "horizontal",
            "layout": {"spacing": 8},
            "repeat": {"for": "items", "as": "item"},
            "children": [
                {"type": "TEXT", "text": "{{item.name}}"}
            ]
        }
        result = toJetpackCompose.emit_node(dsl, 1)
        self.assertIn("LazyRow(", result)
        self.assertIn("items(items) { item ->", result)
        self.assertNotIn("forEach", result)

    def test_vertical_scroll_modifier_applied(self):
        """verticalScroll Modifier が適用されるテスト"""
        dsl = {
            "type": "FRAME",
            "scroll": "vertical",
            "layout": {"direction": "VERTICAL", "spacing": 12},
            "children": [
                {"type": "TEXT", "text": "Item 1"}
            ]
        }
        result = toJetpackCompose.emit_node(dsl, 1)
        self.assertIn("Column(", result)
        self.assertIn("verticalScroll(rememberScrollState())", result)

    def test_horizontal_scroll_modifier_applied(self):
        """横スクロール時に Row + horizontalScroll が適用されるテスト"""
        dsl = {
            "type": "FRAME",
            "scroll": "vertical",
            "layout": {"direction": "HORIZONTAL", "spacing": 8},
            "children": [
                {"type": "TEXT", "text": "Item 1"}
            ]
        }
        result = toJetpackCompose.emit_node(dsl, 1)
        self.assertIn("Row(", result)
        self.assertIn("horizontalScroll(rememberScrollState())", result)

    def test_overlay_alignment_bottom_end(self):
        """OVERLAY の alignment が BottomEnd になるテスト"""
        node = {
            "type": "OVERLAY",
            "position": {"right": 16, "bottom": 16},
            "child": {"type": "TEXT", "text": "FAB"}
        }
        result = toJetpackCompose.emit_node(node, 1)
        self.assertIn("Alignment.BottomEnd", result)

    def test_overlay_alignment_top_start(self):
        """OVERLAY の alignment が TopStart になるテスト"""
        node = {
            "type": "OVERLAY",
            "position": {"left": 8, "top": 8},
            "child": {"type": "TEXT", "text": "Badge"}
        }
        result = toJetpackCompose.emit_node(node, 1)
        self.assertIn("Alignment.TopStart", result)

    def test_overlay_alignment_center(self):
        """OVERLAY の alignment が Center になるテスト"""
        node = {
            "type": "OVERLAY",
            "position": {"left": 8, "right": 8, "top": 8, "bottom": 8},
            "child": {"type": "TEXT", "text": "Center"}
        }
        result = toJetpackCompose.emit_node(node, 1)
        self.assertIn("Alignment.Center", result)

    def test_text_with_expression(self):
        """TEXT ノードが {{}} 式を展開するテスト"""
        node = {"type": "TEXT", "text": "{{item.name}}"}
        result = toJetpackCompose.emit_node(node, 1)
        self.assertEqual(result, "  Text(item.name)")

    def test_text_with_string_literal(self):
        """TEXT ノードが通常の文字列をそのまま出力するテスト"""
        node = {"type": "TEXT", "text": "Hello World"}
        result = toJetpackCompose.emit_node(node, 1)
        self.assertEqual(result, '  Text("Hello World")')

    def test_calculate_alignment(self):
        """calculate_alignment 関数のテスト"""
        # TopStart
        self.assertEqual(toJetpackCompose.calculate_alignment({"left": 8, "top": 8}), "Alignment.TopStart")
        # TopEnd
        self.assertEqual(toJetpackCompose.calculate_alignment({"right": 8, "top": 8}), "Alignment.TopEnd")
        # BottomStart
        self.assertEqual(toJetpackCompose.calculate_alignment({"left": 8, "bottom": 8}), "Alignment.BottomStart")
        # BottomEnd
        self.assertEqual(toJetpackCompose.calculate_alignment({"right": 8, "bottom": 8}), "Alignment.BottomEnd")
        # Center
        self.assertEqual(toJetpackCompose.calculate_alignment({}), "Alignment.Center")

if __name__ == "__main__":
    unittest.main()