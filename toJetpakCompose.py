#!/usr/bin/env python3
import sys, json, math

def dp(n):
    if n is None or (isinstance(n, (int, float)) and n == 0):
        return None
    return f"{int(round(n))}.dp"

def indent(n): return "  " * n

def apply_size(layout):
    if not layout: return ""
    mods = []
    w = layout.get("width")
    h = layout.get("height")
    if w and w.get("mode") == "FILL": mods.append("fillMaxWidth()")
    if h and h.get("mode") == "FILL": mods.append("fillMaxHeight()")
    if w and w.get("mode") == "FIXED" and w.get("value"): mods.append(f"width({dp(w['value'])})")
    if h and h.get("mode") == "FIXED" and h.get("value"): mods.append(f"height({dp(h['value'])})")
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
    # name, extraMods(list), lazy(bool)
    if scroll == "horizontal": return ("LazyRow", [], True)
    d = (layout or {}).get("direction")
    if d == "HORIZONTAL":
        extras = ["horizontalScroll(rememberScrollState())"] if scroll == "vertical" else []
        return ("Row", extras, False)
    extras = ["verticalScroll(rememberScrollState())"] if scroll == "vertical" else []
    return ("Column", extras, False)

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
        txt = n.get("text", "").replace('"', '\\"')
        return f'{ind}Text("{txt}")'

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
        # repeat
        if n.get("repeat"):
            rp = n["repeat"]
            arrname, alias = rp.get("for", "items"), rp.get("as", "item")
            cont, extras, _ = map_container(layout, None)
            head_args = [x for x in [apply_size(layout), map_arrangement(layout)] if x]
            head = f"{ind}{cont}({', '.join(head_args)}) {{"
            lines = [f"{indent(level+1)}{arrname}.forEach {{ {alias} ->"]
            for ch in n.get("children") or []:
                lines.append(emit_node(ch, level+2, layout.get("direction")))
            lines.append(f"{indent(level+1)}}}")
            tail = f"{ind}}}"
            return "\n".join([head] + lines + [tail])

        cont, extras, lazy = map_container(layout, scroll)
        args = [x for x in [apply_size(layout), map_arrangement(layout)] if x]
        head = f"{ind}{cont}({', '.join(args)}) {{"
        body = "\n".join(emit_node(ch, level+1, layout.get("direction")) for ch in (n.get("children") or []))
        tail = f"{ind}}}"
        return "\n".join([head, body, tail])

    if t == "OVERLAY":
        pos = n.get("position") or {}
        pads = []
        if "left"   in pos: pads.append(f"start = {dp(pos['left'])}")
        if "top"    in pos: pads.append(f"top = {dp(pos['top'])}")
        if "right"  in pos: pads.append(f"end = {dp(pos['right'])}")
        if "bottom" in pos: pads.append(f"bottom = {dp(pos['bottom'])}")
        pad = f".padding({', '.join(pads)})" if pads else ""
        child = emit_node(n.get("child") or {}, level+1, flow_dir)
        return f"{ind}Box(Modifier.align(Alignment.BottomEnd){pad}) {{\n{child}\n{ind}}}"

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
import androidx.compose.foundation.lazy.LazyRow
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
