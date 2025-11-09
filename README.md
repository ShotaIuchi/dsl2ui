# DSL2UI - UI Code Generator

DSL（Domain Specific Language）から SwiftUI と Jetpack Compose のコードを自動生成するツールです。

## 概要

DSL2UI は、JSON形式で記述されたUIの構造定義（DSL）を読み込み、ネイティブのUIフレームワーク用コードに変換します。これにより、クロスプラットフォームでの UI 開発を効率化し、デザインシステムの一貫性を保ちながら、iOS と Android のネイティブコードを生成できます。

## 特徴

- **JSON DSL**: シンプルで理解しやすいJSON形式でUIを定義
- **SwiftUI 対応**: iOS/macOS向けのSwiftUIコードを生成
- **Jetpack Compose 対応**: Android向けのJetpack Composeコードを生成
- **コンポーネントベース**: 再利用可能なコンポーネントをサポート
- **レイアウトシステム**: 柔軟なレイアウト定義（方向、スペーシング、パディング）
- **動的コンテンツ**: データバインディングとループ処理をサポート
- **条件付き表示**: 表示/非表示の条件分岐をサポート

## インストール

### 必要要件

- Python 3.6 以上
- macOS（SwiftUI開発の場合）
- Android Studio（Jetpack Compose開発の場合）

### セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/yourname/dsl2ui.git
cd dsl2ui

# 実行権限の付与
chmod +x toSwiftUi.py
chmod +x toJetpakCompose.py
```

## 使い方

### 基本的な使用方法

#### SwiftUIコードの生成

```bash
# ファイルから変換
./toSwiftUi.py dsl.json > InventoryScreen.swift

# パイプ経由で変換
cat dsl.json | ./toSwiftUi.py > InventoryScreen.swift
```

#### Jetpack Composeコードの生成

```bash
# ファイルから変換
./toJetpakCompose.py dsl.json > InventoryScreen.kt

# パイプ経由で変換
cat dsl.json | ./toJetpakCompose.py > InventoryScreen.kt
```

## DSL 仕様

### 基本構造

```json
{
  "type": "FRAME",
  "name": "ScreenName",
  "layout": {
    "direction": "VERTICAL",
    "spacing": 12,
    "padding": [16, 16, 16, 16]
  },
  "children": [...]
}
```

### ノードタイプ

#### FRAME
コンテナとして機能し、子要素を持つことができます。

```json
{
  "type": "FRAME",
  "layout": {
    "direction": "VERTICAL" | "HORIZONTAL",
    "spacing": 数値,
    "width": {"mode": "FILL" | "FIXED" | "HUG", "value": 数値},
    "height": {"mode": "FILL" | "FIXED" | "HUG", "value": 数値},
    "padding": [左, 上, 右, 下]
  },
  "scroll": "vertical" | "horizontal",
  "children": []
}
```

#### TEXT
テキストを表示します。

```json
{
  "type": "TEXT",
  "text": "表示するテキスト"
}
```

#### SPACER
スペースを挿入します（FlexboxのSpacerに相当）。

```json
{
  "type": "SPACER"
}
```

#### INSTANCE
カスタムコンポーネントのインスタンスを配置します。

```json
{
  "type": "INSTANCE",
  "name": "ComponentName",
  "props": {
    "propName": "value"
  },
  "layout": {...}
}
```

#### OVERLAY
要素を重ねて配置します。

```json
{
  "type": "OVERLAY",
  "position": {
    "top": 数値,
    "right": 数値,
    "bottom": 数値,
    "left": 数値
  },
  "child": {...}
}
```

### 高度な機能

#### リピート（ループ）
配列データに基づいて要素を繰り返し生成します。

```json
{
  "type": "FRAME",
  "repeat": {
    "for": "items",
    "as": "item"
  },
  "children": [
    {
      "type": "TEXT",
      "text": "{{item.name}}"
    }
  ]
}
```

#### 条件付き表示
条件に基づいて要素の表示/非表示を制御します。

```json
{
  "type": "TEXT",
  "text": "条件付きテキスト",
  "visible": "{{showText}}"
}
```

#### データバインディング
二重波括弧 `{{}}` を使用してデータをバインドします。

```json
{
  "type": "INSTANCE",
  "name": "ItemRow",
  "props": {
    "title": "{{item.name}}",
    "count": "{{item.quantity}}"
  }
}
```

## 実例

### シンプルな画面

```json
{
  "type": "FRAME",
  "name": "SimpleScreen",
  "layout": {
    "direction": "VERTICAL",
    "spacing": 16,
    "padding": [16, 16, 16, 16]
  },
  "children": [
    {
      "type": "TEXT",
      "text": "Welcome to DSL2UI"
    },
    {
      "type": "SPACER"
    },
    {
      "type": "INSTANCE",
      "name": "Button",
      "props": {
        "label": "Get Started"
      }
    }
  ]
}
```

### 在庫管理画面の例

```json
{
  "type": "FRAME",
  "name": "InventoryScreen",
  "layout": {
    "direction": "VERTICAL",
    "spacing": 12,
    "padding": [16, 16, 16, 16]
  },
  "scroll": "vertical",
  "children": [
    {
      "type": "FRAME",
      "name": "Header",
      "layout": {
        "direction": "HORIZONTAL",
        "spacing": 8,
        "width": {"mode": "FILL"},
        "height": {"mode": "FIXED", "value": 56}
      },
      "children": [
        {"type": "TEXT", "text": "在庫一覧"},
        {"type": "SPACER"},
        {
          "type": "INSTANCE",
          "name": "IconButton",
          "props": {"icon": "search"}
        }
      ]
    },
    {
      "type": "FRAME",
      "name": "List",
      "layout": {
        "direction": "VERTICAL",
        "spacing": 8
      },
      "repeat": {
        "for": "items",
        "as": "item"
      },
      "children": [
        {
          "type": "INSTANCE",
          "name": "ItemRow",
          "props": {
            "title": "{{item.name}}",
            "badge": "{{item.qty}}"
          }
        }
      ]
    }
  ]
}
```

## 生成されるコード例

### SwiftUI

```swift
import SwiftUI

struct InventoryScreen: View {
    var items: [Any] = []

    var body: some View {
        ZStack(alignment: .center) {
            ScrollView(.vertical, showsIndicators: true) {
                VStack(spacing: 12) {
                    // ... generated content
                }
            }
        }
    }
}
```

### Jetpack Compose

```kotlin
@Composable
fun InventoryScreen(
    items: List<Any> = emptyList()
) {
    Box(Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier.verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // ... generated content
        }
    }
}
```

## プロジェクト構成

```
dsl2ui/
├── README.md                # このファイル
├── README.test.md          # テストガイド
├── toSwiftUi.py           # SwiftUI変換器
├── toJetpakCompose.py     # Jetpack Compose変換器
├── test_toSwiftUi.py      # SwiftUIテスト
├── test_toJetpakCompose.py # Jetpack Composeテスト
├── dsl.json               # サンプルDSL
├── 1.kt                   # 生成例（Kotlin）
├── 2.kt                   # 生成例（Kotlin）
└── s1.swift               # 生成例（Swift）
```

## テスト

テストの実行方法については [README.test.md](README.test.md) を参照してください。

```bash
# すべてのテストを実行
python3 -m unittest discover -v
```

## 制限事項

- アニメーションはサポートされていません
- カスタムスタイルの定義は限定的です
- 生成されたコードは手動での調整が必要な場合があります
- コンポーネント名のマッピングはプロジェクトに応じて調整が必要です

## 今後の機能追加予定

- [ ] テーマ/スタイルシステムのサポート
- [ ] アニメーション定義のサポート
- [ ] より多くのUIコンポーネントタイプ
- [ ] TypeScript/React Native対応
- [ ] Flutter対応
- [ ] カスタムプロパティの拡張
- [ ] ビジュアルプレビュー機能
- [ ] DSLバリデーション機能

## コントリビューション

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容について議論してください。

テストの追加も忘れずにお願いします。

## ライセンス

[MIT](https://choosealicense.com/licenses/mit/)

## 作者

Iuchi Shota

## サポート

問題や質問がある場合は、GitHubのissueを作成してください。