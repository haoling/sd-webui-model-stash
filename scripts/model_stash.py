import os

import gradio as gr
from modules import hashes, paths, scripts, script_callbacks, sd_models, shared

EXTENSION_NAME = "Model Stash"
OVERRIDE_PREFIX = "Model hash:"
DEFAULT_STASH_DIR = os.path.join(paths.models_path, "Stash")  # WebUI の models/Stash
MODEL_EXTS = (".safetensors", ".ckpt")
VAE_EXTS = (".vae.safetensors", ".vae.ckpt")  # A1111 と同じく VAE はモデル扱いしない


def stash_dir():
    """しまっておくモデルのフォルダ。設定が空なら WebUI の models/Stash を使い、なければ作る"""
    d = shared.opts.data.get("model_stash_dir", "") or DEFAULT_STASH_DIR
    os.makedirs(d, exist_ok=True)
    return d


def is_model_file(filename):
    f = filename.lower()
    return f.endswith(MODEL_EXTS) and not f.endswith(VAE_EXTS)


def list_models_in(root):
    """root 以下のモデルを root からの相対パスで返す"""
    if not os.path.isdir(root):
        return []
    out = []
    for cur, _, files in os.walk(root, followlinks=True):
        for f in files:
            if is_model_file(f):
                out.append(os.path.relpath(os.path.join(cur, f), root))
    return sorted(out, key=str.lower)


def list_stashed():
    return list_models_in(stash_dir())


def stashed_path(rel):
    """しまったモデルの絶対パス。フォルダの外を指していたら None"""
    root = stash_dir()
    path = os.path.abspath(os.path.join(root, rel))
    try:
        inside = path != root and os.path.commonpath([path, root]) == root
    except ValueError:  # Windows で別ドライブ
        inside = False
    return path if inside and os.path.isfile(path) else None


# ---------------------------------------------------------------------------
# モデルの登録
#
# A1111 はモデルを2か所で管理している。
#   sd_models.checkpoints_list   : 通常のモデル一覧に出るもの
#   sd_models.checkpoint_aliases : 名前やハッシュからモデルを探す辞書
# しまったモデルは checkpoint_aliases にだけ登録する。こうすると一覧には出ないが、
# Override settings の "Model hash: xxx" から読み込める。
# ---------------------------------------------------------------------------

def make_info(rel, compute_hash=False):
    """しまったモデルの CheckpointInfo を作る。
    名前は通常のモデルとぶつからないよう Stash/<相対パス> にする。
    compute_hash=False のときは、計算済み (キャッシュにある) ハッシュだけを使う。"""
    path = stashed_path(rel)
    if path is None:
        return None

    info = sd_models.CheckpointInfo(path)
    name = "Stash/" + rel.replace(os.sep, "/")
    cache_key = f"checkpoint/{name}"
    sha256 = hashes.sha256(path, cache_key) if compute_hash else hashes.sha256_from_cache(path, cache_key)

    info.name = name
    info.model_name = os.path.splitext(name.replace("/", "_"))[0]
    info.sha256 = sha256
    info.shorthash = sha256[:10] if sha256 else None
    info.title = name if info.shorthash is None else f"{name} [{info.shorthash}]"
    info.short_title = info.name_for_extra if info.shorthash is None else f"{info.name_for_extra} [{info.shorthash}]"
    # 通常のモデルとぶつかりやすいファイル名だけの名前や旧形式のハッシュは登録しない
    info.ids = [info.model_name, info.title, name]
    if info.shorthash:
        info.ids += [info.shorthash, info.sha256, f"{info.name_for_extra} [{info.shorthash}]"]
    return info


def register(info):
    """checkpoint_aliases にだけ登録する。通常のモデルが使っている名前は上書きしない"""
    for key in info.ids:
        sd_models.checkpoint_aliases.setdefault(key, info)


def register_all_stashed():
    """しまったモデルを全部登録する (ハッシュは計算済みのものだけ使う)。
    通常一覧の 🔄 で checkpoint_aliases が作り直されても使えるように、生成のたびに呼ぶ"""
    for rel in list_stashed():
        info = make_info(rel)
        if info is not None:
            register(info)


def set_override(rel, current):
    """Override settings 欄に "Model hash: xxx" を入れる。他の上書き項目は残す"""
    if not rel:
        return gr.update(), "しまったモデルを選んでね"
    info = make_info(rel, compute_hash=True)  # 初回はハッシュ計算に時間がかかる
    if info is None:
        return gr.update(), f"見つからない: `{rel}`"
    if not info.shorthash:
        return gr.update(), f"ハッシュを計算できなかった: `{rel}`"
    register(info)

    entry = f"{OVERRIDE_PREFIX} {info.shorthash}"
    values = [v for v in (current or []) if not v.startswith(OVERRIDE_PREFIX)] + [entry]
    message = f"上書きに設定した: `{rel}`（{entry}）\n\n外すまで、このモデルで生成する。外すときは Override settings 欄の × を押してね"
    return gr.update(value=values, choices=values, visible=True), message


# ---------------------------------------------------------------------------
# Override settings 欄とのつなぎ込み
#
# Override settings 欄と、この拡張の UI のどちらが先に作られるかは、
# 設定の「UI item order for txt2img/img2img tabs」などで変わる。
# どちらが先でも動くよう、欄が見つかった時点とボタンを作った時点の両方でつなぐ。
# ---------------------------------------------------------------------------

_override_components = {}  # タブ名 -> Override settings 欄
_pending_wires = {}        # タブ名 -> 欄が見つかったら呼ぶ関数のリスト


def _tab_of(component, kwargs):
    elem_id = getattr(component, "elem_id", None) or kwargs.get("elem_id")
    for tab in ("txt2img", "img2img"):
        if elem_id == f"{tab}_override_settings":
            return tab
    return None


def _on_after_component(component, **kwargs):
    tab = _tab_of(component, kwargs)
    if tab is None:
        return
    _override_components[tab] = component
    for wire in _pending_wires.pop(tab, []):
        wire(component)


def _on_before_ui():
    # 「Reload UI」で作り直すときに、前回の欄を使わないようにする
    _override_components.clear()
    _pending_wires.clear()


def connect_override(tab, wire):
    component = _override_components.get(tab)
    if component is not None:
        wire(component)
    else:
        _pending_wires.setdefault(tab, []).append(wire)


class ModelStashScript(scripts.Script):
    def title(self):
        return EXTENSION_NAME

    def show(self, is_img2img):
        # txt2img / img2img の下に常に表示する
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        tab = "img2img" if is_img2img else "txt2img"
        with gr.Accordion(EXTENSION_NAME, open=False):
            with gr.Row():
                stashed = gr.Dropdown(label="しまったモデル", choices=list_stashed())
                refresh_btn = gr.Button("🔄 一覧を更新")
            override_btn = gr.Button("上書きに設定")
            status = gr.Markdown()

        refresh_btn.click(lambda: gr.update(choices=list_stashed()), outputs=[stashed])

        connected = {"done": False}

        def wire(component):
            connected["done"] = True
            override_btn.click(set_override, inputs=[stashed, component], outputs=[component, status])

        # 最後まで欄が見つからなかったときに、押しても何も起きないままにしない
        override_btn.click(
            lambda: gr.update() if connected["done"]
            else "Override settings 欄が見つからないので、上書きに設定できない",
            outputs=[status],
        )
        connect_override(tab, wire)
        return []

    def before_process(self, p, *args):
        # 生成直前に登録し直す。A1111 は直後に Override のモデルが見つかるか確かめ、
        # 見つからなければ上書きを捨ててしまうため
        if "sd_model_checkpoint" in p.override_settings:
            register_all_stashed()


def on_ui_settings():
    section = ("model_stash", EXTENSION_NAME)
    shared.opts.add_option(
        "model_stash_dir",
        shared.OptionInfo("", "しまっておくモデルのフォルダ（空なら WebUI の models/Stash）", section=section),
    )


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_before_ui(_on_before_ui)
script_callbacks.on_after_component(_on_after_component)
script_callbacks.on_app_started(lambda *_: stash_dir())
