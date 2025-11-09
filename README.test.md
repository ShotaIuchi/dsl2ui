# DSL2UI テストガイド

このドキュメントでは、DSL2UI 変換ツールのテスト実行方法について説明します。

## 必要要件

- Python 3.6 以上
- unittest（Python 標準ライブラリに含まれています）

## テストファイル構成

```
dsl2ui/
├── toSwiftUi.py           # SwiftUI変換器本体
├── toJetpakCompose.py     # Jetpack Compose変換器本体
├── test_toSwiftUi.py      # SwiftUI変換器テスト
└── test_toJetpakCompose.py # Jetpack Compose変換器テスト
```

## テスト実行方法

### 個別のテスト実行

#### SwiftUI変換器のテスト
```bash
python3 -m unittest test_toSwiftUi.py -v
```

#### Jetpack Compose変換器のテスト
```bash
python3 -m unittest test_toJetpakCompose.py -v
```

### すべてのテストを一括実行

```bash
# カレントディレクトリ内のすべてのテストを検出して実行
python3 -m unittest discover -v

# パターンを指定してテストを実行
python3 -m unittest discover -p "test_*.py" -v
```

### 特定のテストケースのみ実行

```bash
# 特定のテストクラスを実行
python3 -m unittest test_toSwiftUi.TestToSwiftUi -v

# 特定のテストメソッドを実行
python3 -m unittest test_toSwiftUi.TestToSwiftUi.test_emit_node_text -v
```

## テストカバレッジ

### SwiftUI変換器テスト（18テストケース）

#### ユーティリティ関数テスト
- `test_px` - ピクセル値変換
- `test_indent` - インデント生成
- `test_to_pascal` - PascalCase変換
- `test_to_swift_name` - Swift名前変換
- `test_edge_insets` - EdgeInsets生成
- `test_apply_frame` - フレーム修飾子適用
- `test_stack_head` - スタックヘッダー生成
- `test_stringify_prop` - プロパティ文字列化

#### ノード出力テスト
- `test_emit_node_text` - TEXTノード
- `test_emit_node_spacer` - SPACERノード
- `test_emit_node_instance` - INSTANCEノード
- `test_emit_node_frame_simple` - シンプルなFRAMEノード
- `test_emit_node_with_repeat` - repeat付きFRAMEノード
- `test_emit_node_overlay` - OVERLAYノード
- `test_emit_node_with_visibility` - 条件付き表示ノード

#### 統合テスト
- `test_wrap_file` - ファイルラッパー
- `test_main_with_simple_dsl` - シンプルなDSL変換
- `test_main_with_complex_dsl` - 複雑なDSL変換

### Jetpack Compose変換器テスト（19テストケース）

#### ユーティリティ関数テスト
- `test_dp` - dp値変換
- `test_indent` - インデント生成
- `test_apply_size` - サイズ修飾子適用
- `test_map_arrangement` - 配置設定マッピング
- `test_map_container` - コンテナマッピング
- `test_to_compose_name` - Compose名前変換
- `test_to_pascal` - PascalCase変換
- `test_stringify_prop` - プロパティ文字列化

#### ノード出力テスト
- `test_emit_node_text` - TEXTノード
- `test_emit_node_spacer` - SPACERノード（方向別）
- `test_emit_node_instance` - INSTANCEノード
- `test_emit_node_frame_simple` - シンプルなFRAMEノード
- `test_emit_node_with_repeat` - repeat付きFRAMEノード
- `test_emit_node_overlay` - OVERLAYノード
- `test_emit_node_with_visibility` - 条件付き表示ノード

#### 統合テスト
- `test_wrap_file` - ファイルラッパー
- `test_main_with_simple_dsl` - シンプルなDSL変換
- `test_main_with_complex_dsl` - 複雑なDSL変換
- `test_main_with_lazy_row` - LazyRow使用ケース

## テスト結果の読み方

### 成功時の出力
```
test_px (test_toSwiftUi.TestToSwiftUi)
px関数のテスト ... ok
```

### 失敗時の出力
```
test_px (test_toSwiftUi.TestToSwiftUi)
px関数のテスト ... FAIL

======================================================================
FAIL: test_px (test_toSwiftUi.TestToSwiftUi)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_toSwiftUi.py", line 19, in test_px
    self.assertEqual(toSwiftUi.px(10.5), "11")
AssertionError: '10' != '11'
```

## テストデータ

テストでは以下のようなDSL構造を使用しています：

```json
{
  "type": "FRAME",
  "name": "TestScreen",
  "layout": {
    "direction": "VERTICAL",
    "spacing": 16,
    "padding": [16, 16, 16, 16]
  },
  "children": [
    {
      "type": "TEXT",
      "text": "Hello World"
    },
    {
      "type": "SPACER"
    }
  ]
}
```

## トラブルシューティング

### ModuleNotFoundError
```bash
# Python 3がインストールされているか確認
python3 --version

# unittestモジュールの確認（標準ライブラリのため通常は不要）
python3 -c "import unittest; print(unittest.__version__)"
```

### テストが見つからない場合
```bash
# ファイル名がtest_で始まることを確認
ls test_*.py

# テストメソッドがtest_で始まることを確認
grep "def test_" test_*.py
```

## CI/CD統合

GitHub Actionsでの自動テスト実行例：

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Run tests
      run: |
        python3 -m unittest discover -v
```

## 今後の改善案

- カバレッジ計測の追加（coverage.pyの利用）
- パフォーマンステストの追加
- プロパティベーステストの導入（hypothesis）
- エッジケースのテスト強化
- エラーハンドリングのテスト追加