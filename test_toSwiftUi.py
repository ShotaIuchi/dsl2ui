#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import json
import sys
from io import StringIO
from unittest.mock import patch
import toSwiftUi

class TestToSwiftUi(unittest.TestCase):

    def setUp(self):
        """テストの前処理"""
        self.maxDiff = None

    def test_px(self):
        """px関数のテスト"""
        self.assertEqual(toSwiftUi.px(10), "10")
        self.assertEqual(toSwiftUi.px(10.5), "10")  # round(10.5) = 10 in Python 3
        self.assertEqual(toSwiftUi.px(None), None)
        self.assertEqual(toSwiftUi.px("invalid"), None)

    def test_indent(self):
        """indent関数のテスト"""
        self.assertEqual(toSwiftUi.indent(0), "")
        self.assertEqual(toSwiftUi.indent(1), "  ")
        self.assertEqual(toSwiftUi.indent(3), "      ")

    def test_to_pascal(self):
        """to_pascal関数のテスト"""
        self.assertEqual(toSwiftUi.to_pascal("inventory-screen"), "InventoryScreen")
        self.assertEqual(toSwiftUi.to_pascal("my_component_name"), "MyComponentName")
        self.assertEqual(toSwiftUi.to_pascal("123test"), "123test")
        self.assertEqual(toSwiftUi.to_pascal(""), "GeneratedScreen")

    def test_to_swift_name(self):
        """to_swift_name関数のテスト"""
        self.assertEqual(toSwiftUi.to_swift_name("Za/IconButton"), "ZaIconButton")
        self.assertEqual(toSwiftUi.to_swift_name("Za/Button"), "ZaButton")
        self.assertEqual(toSwiftUi.to_swift_name("component-name"), "componentname")  # actual behavior
        self.assertEqual(toSwiftUi.to_swift_name("123name"), "_123name")

    def test_edge_insets(self):
        """edge_insets関数のテスト"""
        self.assertEqual(
            toSwiftUi.edge_insets([16, 8, 16, 8]),
            "EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16)"
        )
        self.assertEqual(toSwiftUi.edge_insets([0, 0, 0, 0]),
            "EdgeInsets(top: 0, leading: 0, bottom: 0, trailing: 0)")
        self.assertEqual(toSwiftUi.edge_insets(None), None)
        self.assertEqual(toSwiftUi.edge_insets([1, 2]), None)

    def test_apply_frame(self):
        """apply_frame関数のテスト"""
        # FILL width
        layout = {"width": {"mode": "FILL"}}
        self.assertEqual(toSwiftUi.apply_frame(layout), ".frame(maxWidth: .infinity)")

        # FIXED height
        layout = {"height": {"mode": "FIXED", "value": 56}}
        self.assertEqual(toSwiftUi.apply_frame(layout), ".frame(height: 56)")

        # With padding
        layout = {"padding": [16, 16, 16, 16]}
        self.assertEqual(toSwiftUi.apply_frame(layout),
            ".padding(EdgeInsets(top: 16, leading: 16, bottom: 16, trailing: 16))")

        # Combined
        layout = {
            "width": {"mode": "FILL"},
            "height": {"mode": "FIXED", "value": 48},
            "padding": [8, 8, 8, 8]
        }
        self.assertIn("maxWidth: .infinity", toSwiftUi.apply_frame(layout))
        self.assertIn("height: 48", toSwiftUi.apply_frame(layout))

    def test_stack_head(self):
        """stack_head関数のテスト"""
        # Horizontal stack
        layout = {"direction": "HORIZONTAL", "spacing": 8}
        result = toSwiftUi.stack_head(layout, None)
        self.assertEqual(result[0], "HStack(spacing: 8)")
        self.assertIsNone(result[1])

        # Vertical scroll
        layout = {"direction": "VERTICAL", "spacing": 12}
        result = toSwiftUi.stack_head(layout, "vertical")
        self.assertEqual(result[0], "ScrollView(.vertical, showsIndicators: true)")
        self.assertEqual(result[1], "VStack(spacing: 12)")

        # Horizontal scroll
        layout = {"spacing": 10}
        result = toSwiftUi.stack_head(layout, "horizontal")
        self.assertEqual(result[0], "ScrollView(.horizontal, showsIndicators: false)")
        self.assertEqual(result[1], "HStack(spacing: 10)")

    def test_stringify_prop(self):
        """stringify_prop関数のテスト"""
        self.assertEqual(toSwiftUi.stringify_prop("enabled", True), "enabled: true")
        self.assertEqual(toSwiftUi.stringify_prop("enabled", False), "enabled: false")
        self.assertEqual(toSwiftUi.stringify_prop("size", 42), "size: 42")
        self.assertEqual(toSwiftUi.stringify_prop("label", "Hello"), 'label: "Hello"')
        self.assertEqual(toSwiftUi.stringify_prop("value", "{{item.name}}"), "value: item.name")

    def test_emit_node_text(self):
        """TEXT ノードの出力テスト"""
        node = {"type": "TEXT", "text": "在庫一覧"}
        result = toSwiftUi.emit_node(node, 1)
        self.assertEqual(result, '  Text("在庫一覧")')

    def test_emit_node_spacer(self):
        """SPACER ノードの出力テスト"""
        node = {"type": "SPACER"}
        result = toSwiftUi.emit_node(node, 2)
        self.assertEqual(result, "    Spacer()")

    def test_emit_node_instance(self):
        """INSTANCE ノードの出力テスト"""
        node = {
            "type": "INSTANCE",
            "name": "Za/Button",
            "props": {"label": "新規追加", "variant": "Primary"},
            "layout": {"width": {"mode": "FILL"}}
        }
        result = toSwiftUi.emit_node(node, 1)
        self.assertIn("ZaButton(", result)
        self.assertIn('label: "新規追加"', result)
        self.assertIn("variant: \"Primary\"", result)
        self.assertIn(".frame(maxWidth: .infinity)", result)

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
        result = toSwiftUi.emit_node(node, 1)
        lines = result.split("\n")
        self.assertEqual(lines[0], "  HStack(spacing: 8) {")
        self.assertEqual(lines[1], '    Text("Title")')
        self.assertEqual(lines[2], "    Spacer()")
        self.assertEqual(lines[3], "  }")

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
        result = toSwiftUi.emit_node(node, 1)
        self.assertIn("ForEach(items.indices", result)
        self.assertIn("let item = items[idx]", result)

    def test_emit_node_overlay(self):
        """OVERLAY ノードの出力テスト"""
        node = {
            "type": "OVERLAY",
            "position": {"right": 16, "bottom": 16},
            "child": {"type": "TEXT", "text": "FAB"}
        }
        result = toSwiftUi.emit_node(node, 1)
        self.assertIn("ZStack(alignment: .bottomTrailing)", result)
        self.assertIn(".padding(.trailing, 16)", result)
        self.assertIn(".padding(.bottom, 16)", result)

    def test_emit_node_with_visibility(self):
        """visible 条件付きノードの出力テスト"""
        node = {
            "type": "TEXT",
            "text": "Conditional",
            "visible": "{{showText}}"
        }
        result = toSwiftUi.emit_node(node, 1)
        lines = result.split("\n")
        self.assertEqual(lines[0], "  if showText {")
        self.assertEqual(lines[1], '    Text("Conditional")')
        self.assertEqual(lines[2], "  }")

    def test_wrap_file(self):
        """wrap_file関数のテスト"""
        body = '    Text("Hello")'
        result = toSwiftUi.wrap_file("TestScreen", body)

        self.assertIn("import SwiftUI", result)
        self.assertIn("struct TestScreen: View", result)
        self.assertIn("var items: [Any] = []", result)
        self.assertIn("var body: some View", result)
        self.assertIn(body, result)
        self.assertIn("#Preview", result)

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
                with patch('sys.argv', ['toSwiftUi.py']):
                    toSwiftUi.main()
                output = mock_stdout.getvalue()

        self.assertIn("struct TestScreen: View", output)
        self.assertIn("VStack(spacing: 16)", output)
        self.assertIn('Text("Hello World")', output)
        self.assertIn("Spacer()", output)

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
                with patch('sys.argv', ['toSwiftUi.py']):
                    toSwiftUi.main()
                output = mock_stdout.getvalue()

        self.assertIn("struct InventoryScreen: View", output)
        self.assertIn("ScrollView(.vertical", output)
        self.assertIn("VStack(spacing: 12)", output)
        self.assertIn("HStack(spacing: 8)", output)
        self.assertIn('Text("在庫一覧")', output)
        self.assertIn("ZaIconButton(icon: \"search\")", output)
        self.assertIn("ZaButton(label: \"新規追加\")", output)
        self.assertIn("maxWidth: .infinity", output)

    def test_text_with_expression(self):
        """TEXT ノードが {{}} 式を展開するテスト"""
        node = {"type": "TEXT", "text": "{{item.name}}"}
        result = toSwiftUi.emit_node(node, 1)
        self.assertEqual(result, "  Text(item.name)")

    def test_text_with_string_literal(self):
        """TEXT ノードが通常の文字列をそのまま出力するテスト"""
        node = {"type": "TEXT", "text": "Hello World"}
        result = toSwiftUi.emit_node(node, 1)
        self.assertEqual(result, '  Text("Hello World")')

    def test_overlay_alignment_bottom_trailing(self):
        """OVERLAY の alignment が .bottomTrailing になるテスト"""
        node = {
            "type": "OVERLAY",
            "position": {"right": 16, "bottom": 16},
            "child": {"type": "TEXT", "text": "FAB"}
        }
        result = toSwiftUi.emit_node(node, 1)
        self.assertIn("ZStack(alignment: .bottomTrailing)", result)

    def test_overlay_alignment_top_leading(self):
        """OVERLAY の alignment が .topLeading になるテスト"""
        node = {
            "type": "OVERLAY",
            "position": {"left": 8, "top": 8},
            "child": {"type": "TEXT", "text": "Badge"}
        }
        result = toSwiftUi.emit_node(node, 1)
        self.assertIn("ZStack(alignment: .topLeading)", result)

    def test_overlay_alignment_top_trailing(self):
        """OVERLAY の alignment が .topTrailing になるテスト"""
        node = {
            "type": "OVERLAY",
            "position": {"right": 8, "top": 8},
            "child": {"type": "TEXT", "text": "Badge"}
        }
        result = toSwiftUi.emit_node(node, 1)
        self.assertIn("ZStack(alignment: .topTrailing)", result)

    def test_overlay_alignment_bottom_leading(self):
        """OVERLAY の alignment が .bottomLeading になるテスト"""
        node = {
            "type": "OVERLAY",
            "position": {"left": 8, "bottom": 8},
            "child": {"type": "TEXT", "text": "Badge"}
        }
        result = toSwiftUi.emit_node(node, 1)
        self.assertIn("ZStack(alignment: .bottomLeading)", result)

    def test_overlay_alignment_center(self):
        """OVERLAY の alignment が .center になるテスト"""
        node = {
            "type": "OVERLAY",
            "position": {"left": 8, "right": 8, "top": 8, "bottom": 8},
            "child": {"type": "TEXT", "text": "Center"}
        }
        result = toSwiftUi.emit_node(node, 1)
        self.assertIn("ZStack(alignment: .center)", result)

    def test_calculate_swiftui_alignment(self):
        """calculate_swiftui_alignment 関数のテスト"""
        # topLeading
        self.assertEqual(toSwiftUi.calculate_swiftui_alignment({"left": 8, "top": 8}), ".topLeading")
        # topTrailing
        self.assertEqual(toSwiftUi.calculate_swiftui_alignment({"right": 8, "top": 8}), ".topTrailing")
        # bottomLeading
        self.assertEqual(toSwiftUi.calculate_swiftui_alignment({"left": 8, "bottom": 8}), ".bottomLeading")
        # bottomTrailing
        self.assertEqual(toSwiftUi.calculate_swiftui_alignment({"right": 8, "bottom": 8}), ".bottomTrailing")
        # center
        self.assertEqual(toSwiftUi.calculate_swiftui_alignment({}), ".center")
        # top
        self.assertEqual(toSwiftUi.calculate_swiftui_alignment({"top": 8}), ".top")
        # bottom
        self.assertEqual(toSwiftUi.calculate_swiftui_alignment({"bottom": 8}), ".bottom")
        # leading
        self.assertEqual(toSwiftUi.calculate_swiftui_alignment({"left": 8}), ".leading")
        # trailing
        self.assertEqual(toSwiftUi.calculate_swiftui_alignment({"right": 8}), ".trailing")

    def test_repeat_with_foreach(self):
        """repeat を使った ForEach のテスト"""
        node = {
            "type": "FRAME",
            "layout": {"direction": "VERTICAL", "spacing": 8},
            "repeat": {"for": "items", "as": "item"},
            "children": [
                {"type": "TEXT", "text": "{{item.name}}"}
            ]
        }
        result = toSwiftUi.emit_node(node, 1)
        self.assertIn("ForEach(items.indices", result)
        self.assertIn("let item = items[idx]", result)
        self.assertIn("Text(item.name)", result)

if __name__ == "__main__":
    unittest.main()