#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, json, re
from typing import Optional  # ← 追加

def px(n):
    if n is None: return None
    if isinstance(n, (int, float)):
        return f"{int(round(n))}"
    return None

def indent(n): return "  " * n

def to_pascal(s: str) -> str:
    parts = [p for p in re.sub(r"[^0-9A-Za-z]+", " ", s).split() if p]
    return "".join(p[:1].upper() + p[1:] for p in parts) or "GeneratedScreen"

def to_swift_name(name: str) -> str:
    # "Za/FooBar" -> "ZaFooBar", "My Component/Sub Page" -> "MyComponentSubPage"
    # 階層区切りで分割
    parts = [p for p in name.split("/") if p]
    result_parts = []
    for part in parts:
        # 各パート内のハイフン・アンダースコア・スペースで単語分割
        words = [w for w in re.sub(r"[-_\s]+", " ", part).split() if w]
        # PascalCase化
        pascal = "".join(w[:1].upper() + w[1:] for w in words)
        result_parts.append(pascal)
    # 階層を結合
    out = "".join(result_parts) if result_parts else "Unknown"
    # 非英数字を除去（念のため）
    out = re.sub(r"[^A-Za-z0-9]", "", out)
    # 数字始まりの場合は先頭にアンダースコアを追加
    if re.match(r"^[0-9]", out): out = "_" + out
    return out

def edge_insets(pad):
    if not isinstance(pad, list) or len(pad) != 4: return None
    l,t,r,b = [int(round(x or 0)) for x in pad]
    return f"EdgeInsets(top: {t}, leading: {l}, bottom: {b}, trailing: {r})"

def apply_frame(layout: dict) -> str:
    if not layout: return ""
    mods = []
    w = layout.get("width") or {}
    h = layout.get("height") or {}
    if w.get("mode") == "FILL":  mods.append("maxWidth: .infinity")
    elif w.get("mode") == "FIXED" and w.get("value") is not None: mods.append(f"width: {px(w['value'])}")
    if h.get("mode") == "FILL":  mods.append("maxHeight: .infinity")
    elif h.get("mode") == "FIXED" and h.get("value") is not None: mods.append(f"height: {px(h['value'])}")
    out = ""
    if mods: out += f".frame({', '.join(mods)})"
    ei = edge_insets(layout.get("padding"))
    if ei: out += f".padding({ei})"
    return out

# ↓ ここを Optional[str] に修正（3.8/3.9対応）
def stack_head(layout: dict, scroll: Optional[str]):
    direction = (layout or {}).get("direction")
    spacing = layout.get("spacing") if layout else None
    sp_arg = f"spacing: {int(round(spacing))}" if spacing else ""
    if scroll == "horizontal":
        return ("ScrollView(.horizontal, showsIndicators: false)", f"HStack({sp_arg})")
    if direction == "HORIZONTAL":
        return (f"HStack({sp_arg})", None)
    if scroll == "vertical":
        return ("ScrollView(.vertical, showsIndicators: true)", f"VStack({sp_arg})")
    return (f"VStack({sp_arg})", None)

def calculate_swiftui_alignment(position):
    """
    position から SwiftUI の Alignment を計算
    """
    if not position:
        return ".center"

    has_left = "left" in position
    has_right = "right" in position
    has_top = "top" in position
    has_bottom = "bottom" in position

    # 垂直方向
    if has_top and not has_bottom:
        v_align = "top"
    elif has_bottom and not has_top:
        v_align = "bottom"
    else:
        v_align = "center"

    # 水平方向
    if has_left and not has_right:
        h_align = "Leading"
    elif has_right and not has_left:
        h_align = "Trailing"
    else:
        h_align = ""

    # 組み合わせ
    if v_align == "top":
        if h_align == "Leading": return ".topLeading"
        if h_align == "Trailing": return ".topTrailing"
        return ".top"
    elif v_align == "bottom":
        if h_align == "Leading": return ".bottomLeading"
        if h_align == "Trailing": return ".bottomTrailing"
        return ".bottom"
    else:  # center
        if h_align == "Leading": return ".leading"
        if h_align == "Trailing": return ".trailing"
        return ".center"

def stringify_prop(k, v):
    if isinstance(v, bool):  return f"{k}: {str(v).lower()}"
    if isinstance(v, (int, float)): return f"{k}: {int(round(v))}"
    if isinstance(v, str):
        if v.startswith("{{") and v.endswith("}}"):
            return f"{k}: {v[2:-2].strip()}"
        esc = v.replace('"','\\"')
        return f'{k}: "{esc}"'
    return f"/* unsupported prop {k} */"

def emit_node(n, level, flow_dir=None):
    ind = indent(level)

    vis = n.get("visible")
    if isinstance(vis, str) and vis.startswith("{{") and vis.endswith("}}"):
        expr = vis[2:-2].strip()
        inner = emit_node({**n, "visible": None}, level + 1, flow_dir)
        return f"{ind}if {expr} {{\n{inner}\n{ind}}}"

    t = n.get("type")
    if t == "TEXT":
        txt = n.get("text") or ""
        # {{...}} を展開
        if txt.startswith("{{") and txt.endswith("}}"):
            expr = txt[2:-2].strip()
            return f'{ind}Text({expr})'
        else:
            esc = txt.replace('"','\\"')
            return f'{ind}Text("{esc}")'

    if t == "SPACER":
        return f"{ind}Spacer()"

    if t == "INSTANCE":
        call = to_swift_name(n.get("name","Unknown"))
        args = []
        for k, v in (n.get("props") or {}).items():
            args.append(stringify_prop(k, v))
        line = f"{ind}{call}({', '.join(a for a in args if a)})"
        line += apply_frame(n.get("layout") or {})
        return line

    if t == "FRAME":
        layout = n.get("layout") or {}
        scroll = n.get("scroll")
        if n.get("repeat"):
            rp = n["repeat"]
            arrname, alias = rp.get("for", "items"), rp.get("as", "item")
            head, inner = stack_head(layout, None)
            sz = apply_frame(layout)
            lines = []
            if inner:
                lines.append(f"{indent(level)}{head} {{")
                lines.append(f"{indent(level+1)}{inner} {{")
                lines.append(f"{indent(level+2)}ForEach({arrname}.indices, id: \\.self) {{ idx in")
                lines.append(f"{indent(level+3)}let {alias} = {arrname}[idx]")
                for ch in (n.get("children") or []):
                    lines.append(emit_node(ch, level+3, layout.get("direction")))
                lines.append(f"{indent(level+2)}}}")
                lines.append(f"{indent(level+1)}}}")
                lines.append(f"{indent(level)}}}{sz}")  # 末尾の '}' を '}}' でエスケープ
            else:
                lines.append(f"{indent(level)}{head} {{")
                lines.append(f"{indent(level+1)}ForEach({arrname}.indices, id: \\.self) {{ idx in")
                lines.append(f"{indent(level+2)}let {alias} = {arrname}[idx]")
                for ch in (n.get("children") or []):
                    lines.append(emit_node(ch, level+2, layout.get("direction")))
                lines.append(f"{indent(level+1)}}}")
                lines.append(f"{indent(level)}}}{sz}")
            return "\n".join(lines)

        head, inner = stack_head(layout, scroll)
        sz = apply_frame(layout)
        lines = []
        if inner:
            lines.append(f"{ind}{head} {{")
            lines.append(f"{indent(level+1)}{inner} {{")
            for ch in (n.get("children") or []):
                lines.append(emit_node(ch, level+2, layout.get("direction")))
            lines.append(f"{indent(level+1)}}}")
            lines.append(f"{ind}}}{sz}")
        else:
            lines.append(f"{ind}{head} {{")
            for ch in (n.get("children") or []):
                lines.append(emit_node(ch, level+1, layout.get("direction")))
            lines.append(f"{ind}}}{sz}")
        return "\n".join(lines)

    if t == "OVERLAY":
        pos = n.get("position") or {}
        # Alignment を計算
        alignment = calculate_swiftui_alignment(pos)
        # padding を計算
        pad = ""
        if "right" in pos:  pad += f".padding(.trailing, {px(pos['right'])})"
        if "left"  in pos:  pad += f".padding(.leading, {px(pos['left'])})"
        if "top"   in pos:  pad += f".padding(.top, {px(pos['top'])})"
        if "bottom" in pos: pad += f".padding(.bottom, {px(pos['bottom'])})"
        child = emit_node(n.get("child") or {}, level+1, None)
        return f"{ind}ZStack(alignment: {alignment}) {{\n{child}\n{ind}}}{pad}"

    return f"{ind}// TODO unsupported type: {t}"

def wrap_file(screen_name: str, body: str) -> str:
    return f"""import SwiftUI

struct {screen_name}: View {{
    var items: [Any] = []

    var body: some View {{
        ZStack(alignment: .center) {{
{body}
        }}
    }}
}}

#Preview {{
    {screen_name}()
}}
"""

def main():
    data = sys.stdin.read() if len(sys.argv) < 2 else open(sys.argv[1], "r", encoding="utf-8").read()
    dsl = json.loads(data)
    screen = to_pascal(dsl.get("name", "GeneratedScreen"))
    body = emit_node(dsl, 2, None)
    print(wrap_file(screen, body))

if __name__ == "__main__":
    main()
