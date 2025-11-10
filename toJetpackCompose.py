#!/usr/bin/env python3
import sys, json, math

def dp(n):
    if n is None or (isinstance(n, (int, float)) and n == 0):
        return None
    return f"{int(round(n))}.dp"

def indent(n): return "  " * n

def apply_size(layout, extras=None):
    """
    レイアウトから Modifier を生成
    extras: スクロール Modifier などの追加 Modifier リスト
    """
    if not layout and not extras: return ""
    mods = []
    # extras を先に追加（スクロール Modifier など）
    if extras:
        mods.extend(extras)
    # サイズ Modifier
    if layout:
        w = layout.get("width")
        h = layout.get("height")
        if w and w.get("mode") == "FILL": mods.append("fillMaxWidth()")
        if h and h.get("mode") == "FILL": mods.append("fillMaxHeight()")
        if w and w.get("mode") == "FIXED" and w.get("value"): mods.append(f"width({dp(w['value'])})")
        if h and h.get("mode") == "FIXED" and h.get("value"): mods.append(f"height({dp(h['value'])})")
        # padding
        pad = layout.get("padding")
        if isinstance(pad, list) and len(pad) == 4:
            l,t,r,b = (dp(p) or "0.dp" for p in pad)
            mods.append(f"padding(start = {l}, top = {t}, end = {r}, bottom = {b})")
    return f"modifier = Modifier.{'.'.join(mods)}" if mods else ""

def map_arrangement(layout):
    if not layout: return ""
    spacing = layout.get("spacing")
    if not spacing: return ""
    spaced = f"Arrangement.spacedBy({dp(spacing)})"
    d = layout.get("direction")
    if d == "VERTICAL":   return f"verticalArrangement = {spaced}"
    if d == "HORIZONTAL": return f"horizontalArrangement = {spaced}"
    return ""

def map_container(layout, scroll):
    """
    コンテナタイプと追加 Modifier、Lazy フラグを返す
    戻り値: (name, extraMods, lazy)
    """
    if scroll == "horizontal": return ("LazyRow", [], True)
    d = (layout or {}).get("direction")
    if d == "HORIZONTAL":
        extras = ["horizontalScroll(rememberScrollState())"] if scroll == "vertical" else []
        return ("Row", extras, False)
    extras = ["verticalScroll(rememberScrollState())"] if scroll == "vertical" else []
    return ("Column", extras, False)

def calculate_alignment(position):
    """
    position から Alignment を計算
    """
    if not position:
        return "Alignment.Center"

    has_left = "left" in position
    has_right = "right" in position
    has_top = "top" in position
    has_bottom = "bottom" in position

    # 垂直方向
    v_align = ""
    if has_top and not has_bottom:
        v_align = "Top"
    elif has_bottom and not has_top:
        v_align = "Bottom"
    else:
        v_align = "CenterVertically"

    # 水平方向
    h_align = ""
    if has_left and not has_right:
        h_align = "Start"
    elif has_right and not has_left:
        h_align = "End"
    else:
        h_align = "CenterHorizontally"

    # 組み合わせ
    if v_align == "Top":
        if h_align == "Start": return "Alignment.TopStart"
        if h_align == "End": return "Alignment.TopEnd"
        return "Alignment.TopCenter"
    elif v_align == "Bottom":
        if h_align == "Start": return "Alignment.BottomStart"
        if h_align == "End": return "Alignment.BottomEnd"
        return "Alignment.BottomCenter"
    else:  # CenterVertically
        if h_align == "Start": return "Alignment.CenterStart"
        if h_align == "End": return "Alignment.CenterEnd"
        return "Alignment.Center"

def to_compose_name(name: str) -> str:
    # "Za/FooBar" -> "ZaFooBar"
    parts = [p for p in name.replace("-", " ").replace("_", " ").split("/") if p]
    out = parts[0] if parts else "Unknown"
    for p in parts[1:]:
        out += p[:1].upper() + p[1:]
    return out

def stringify_prop(k, v):
    if isinstance(v, bool):  return f"{k} = {'true' if v else 'false'}"
    if isinstance(v, (int, float)): return f"{k} = {v}"
    if isinstance(v, str):
        if v.startswith("{{") and v.endswith("}}"):
            return f"{k} = {v[2:-2].strip()}"
        esc = v.replace('"', '\\"')
        return f'{k} = "{esc}"'
    return f"/* unsupported prop {k} */"

def emit_node(n, level, flow_dir=None):
    ind = indent(level)

    # visible guard
    vis = n.get("visible")
    if isinstance(vis, str) and vis.startswith("{{") and vis.endswith("}}"):
        expr = vis[2:-2].strip()
        body = emit_node({**n, "visible": None}, level + 1, flow_dir)
        return f"{ind}if ({expr}) {{\n{body}\n{ind}}}"

    t = n.get("type")
    if t == "TEXT":
        txt = n.get("text", "")
        # {{...}} を展開
        if txt.startswith("{{") and txt.endswith("}}"):
            expr = txt[2:-2].strip()
            return f'{ind}Text({expr})'
        else:
            esc = txt.replace('"', '\\"')
            return f'{ind}Text("{esc}")'

    if t == "SPACER":
        is_row = (flow_dir == "HORIZONTAL")
        if is_row:
            return f"{ind}Spacer(Modifier.width(0.dp).weight(1f))"
        else:
            return f"{ind}Spacer(Modifier.height(0.dp).weight(1f))"

    if t == "INSTANCE":
        name = n.get("name", "Unknown")
        call = to_compose_name(name)
        args = []
        props = n.get("props") or {}
        for k, v in props.items():
            args.append(stringify_prop(k, v))
        size_mod = apply_size(n.get("layout"))
        if size_mod: args.append(size_mod)
        return f"{ind}{call}({', '.join(args)})"

    if t == "FRAME":
        layout = n.get("layout") or {}
        scroll = n.get("scroll")
        cont, extras, lazy = map_container(layout, scroll)
        children = n.get("children") or []
        direction = layout.get("direction")

        # repeat がある場合
        if n.get("repeat"):
            rp = n["repeat"]
            arrname, alias = rp.get("for", "items"), rp.get("as", "item")

            if lazy:
                # LazyRow/LazyColumn の場合は items() を使用
                args = [x for x in [apply_size(layout, extras), map_arrangement(layout)] if x]
                head = f"{ind}{cont}({', '.join(args)}) {{"
                lines = [f"{indent(level+1)}items({arrname}) {{ {alias} ->"]
                for ch in children:
                    lines.append(emit_node(ch, level+2, direction))
                lines.append(f"{indent(level+1)}}}")
                tail = f"{ind}}}"
                return "\n".join([head] + lines + [tail])
            else:
                # 通常のコンテナの場合は forEach を使用
                args = [x for x in [apply_size(layout, extras), map_arrangement(layout)] if x]
                head = f"{ind}{cont}({', '.join(args)}) {{"
                lines = [f"{indent(level+1)}{arrname}.forEach {{ {alias} ->"]
                for ch in children:
                    lines.append(emit_node(ch, level+2, direction))
                lines.append(f"{indent(level+1)}}}")
                tail = f"{ind}}}"
                return "\n".join([head] + lines + [tail])

        # repeat がない場合
        if lazy:
            # LazyRow/LazyColumn の場合
            args = [x for x in [apply_size(layout, extras), map_arrangement(layout)] if x]
            head = f"{ind}{cont}({', '.join(args)}) {{"
            lines = []
            for ch in children:
                # 各子要素を item {} でラップ
                child_code = emit_node(ch, level+2, direction)
                lines.append(f"{indent(level+1)}item {{")
                lines.append(child_code)
                lines.append(f"{indent(level+1)}}}")
            tail = f"{ind}}}"
            return "\n".join([head] + lines + [tail])
        else:
            # 通常のコンテナの場合
            args = [x for x in [apply_size(layout, extras), map_arrangement(layout)] if x]
            head = f"{ind}{cont}({', '.join(args)}) {{"
            body = "\n".join(emit_node(ch, level+1, direction) for ch in children)
            tail = f"{ind}}}"
            return "\n".join([head, body, tail])

    if t == "OVERLAY":
        pos = n.get("position") or {}
        # Alignment を計算
        alignment = calculate_alignment(pos)
        # padding を計算
        pads = []
        if "left"   in pos: pads.append(f"start = {dp(pos['left'])}")
        if "top"    in pos: pads.append(f"top = {dp(pos['top'])}")
        if "right"  in pos: pads.append(f"end = {dp(pos['right'])}")
        if "bottom" in pos: pads.append(f"bottom = {dp(pos['bottom'])}")
        pad = f".padding({', '.join(pads)})" if pads else ""
        child = emit_node(n.get("child") or {}, level+1, flow_dir)
        return f"{ind}Box(Modifier.align({alignment}){pad}) {{\n{child}\n{ind}}}"

    return f"{ind}// TODO unsupported type: {t}"

def to_pascal(s: str) -> str:
    import re
    parts = [p for p in re.sub(r"[^0-9A-Za-z]+", " ", s).split() if p]
    return "".join(p[:1].upper() + p[1:] for p in parts) or "GeneratedScreen"

def wrap_file(screen_name: str, body: str) -> str:
    return f"""@file:Suppress("UnusedImport")

package ui.generated

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun {screen_name}(
    items: List<Any> = emptyList()
) {{
  Box(Modifier.fillMaxSize()) {{
{body}
  }}
}}
"""

def main():
    data = sys.stdin.read() if len(sys.argv) < 2 else open(sys.argv[1], "r", encoding="utf-8").read()
    dsl = json.loads(data)
    screen = to_pascal(dsl.get("name", "GeneratedScreen"))
    # ルートは Box 包みで OVERLAY 対応しやすく
    root = emit_node(dsl, 2, None)
    print(wrap_file(screen, root))

if __name__ == "__main__":
    main()
