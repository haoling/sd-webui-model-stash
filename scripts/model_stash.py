import os
import shutil

import gradio as gr
from modules import paths, scripts, script_callbacks, sd_models, shared

EXTENSION_NAME = "Model Stash"
DEFAULT_STASH_DIR = os.path.join(paths.models_path, "Stash")  # WebUI の models/Stash
MODEL_EXTS = (".safetensors", ".ckpt")

# モデルと一緒に移動する付属ファイル (「モデル名 + これ」という名前のもの)
SIDECAR_SUFFIXES = (
    ".yaml", ".json", ".info", ".civitai.info", ".txt",
    ".png", ".jpg", ".jpeg", ".webp",
    ".preview.png", ".preview.jpg", ".preview.jpeg", ".preview.webp",
    ".vae.pt", ".vae.ckpt", ".vae.safetensors",
)


# ---------------------------------------------------------------------------
# フォルダ
# ---------------------------------------------------------------------------

def stash_dir():
    """しまっておくモデルのフォルダ。設定が空なら WebUI の models/Stash を使い、なければ作る"""
    d = shared.opts.data.get("model_stash_dir", "") or DEFAULT_STASH_DIR
    d = os.path.abspath(d)
    os.makedirs(d, exist_ok=True)
    return d


def checkpoint_roots():
    """通常のモデル一覧の元になるフォルダ。models/Stable-diffusion と --ckpt-dir"""
    roots = [os.path.abspath(sd_models.model_path)]
    ckpt_dir = getattr(shared.cmd_opts, "ckpt_dir", None)
    if ckpt_dir and os.path.isdir(ckpt_dir):
        roots.append(os.path.abspath(ckpt_dir))
    return roots


def is_inside(path, root):
    """path が root の中 (root 自身は除く) にあるか"""
    path, root = os.path.abspath(path), os.path.abspath(root)
    try:
        return path != root and os.path.commonpath([path, root]) == root
    except ValueError:  # Windows で別ドライブ
        return False


# ---------------------------------------------------------------------------
# 一覧
# ---------------------------------------------------------------------------

def list_models_in(root):
    """root 以下のモデルを root からの相対パスで返す"""
    if not os.path.isdir(root):
        return []
    out = []
    for cur, _, files in os.walk(root, followlinks=True):
        for f in files:
            if f.lower().endswith(MODEL_EXTS):
                out.append(os.path.relpath(os.path.join(cur, f), root))
    return sorted(out, key=str.lower)


def list_active():
    out = []
    for root in checkpoint_roots():
        for rel in list_models_in(root):
            if rel not in out:
                out.append(rel)
    return out


def list_stashed():
    return list_models_in(stash_dir())


# ---------------------------------------------------------------------------
# 移動
# ---------------------------------------------------------------------------

def sidecars(model_file):
    d = os.path.dirname(model_file)
    stem = os.path.splitext(os.path.basename(model_file))[0]
    out = []
    for suffix in SIDECAR_SUFFIXES:
        p = os.path.join(d, stem + suffix)
        if os.path.isfile(p):
            out.append(p)
    return out


def move_keeping_tree(src, src_root, dst_root):
    """src を src_root からの相対パスを保ったまま dst_root の下へ移動する。
    付属ファイルも一緒に移動し、途中で失敗したら移動済みの分を元に戻す。
    戻り値は移動した付属ファイルの数。"""
    rel = os.path.relpath(src, src_root)
    dst_dir = os.path.dirname(os.path.join(dst_root, rel))

    pairs = [(f, os.path.join(dst_dir, os.path.basename(f))) for f in [src] + sidecars(src)]
    clash = [d for _, d in pairs if os.path.exists(d)]
    if clash:
        raise FileExistsError("移動先に同じ名前のファイルがある: " + ", ".join(clash))

    os.makedirs(dst_dir, exist_ok=True)
    moved = []
    try:
        for s, d in pairs:
            shutil.move(s, d)
            moved.append((s, d))
    except Exception:
        for s, d in reversed(moved):
            shutil.move(d, s)
        raise
    return len(pairs) - 1


def find_active(rel):
    for root in checkpoint_roots():
        p = os.path.join(root, rel)
        if is_inside(p, root) and os.path.isfile(p):
            return root, p
    return None, None


def is_loaded(path):
    model = getattr(shared, "sd_model", None)
    info = getattr(model, "sd_checkpoint_info", None)
    return info is not None and os.path.abspath(info.filename) == os.path.abspath(path)


def result(message):
    return (
        message,
        gr.update(choices=list_active(), value=None),
        gr.update(choices=list_stashed(), value=None),
    )


def do_stash(rel):
    if not rel:
        return result("しまうモデルを選んでね")
    root, src = find_active(rel)
    if src is None:
        return result(f"見つからない: `{rel}`")
    loaded = is_loaded(src)
    try:
        n = move_keeping_tree(src, root, stash_dir())
    except Exception as e:
        return result(f"しまえなかった: {e}")
    sd_models.list_models()

    msg = f"しまった: `{rel}`"
    if n:
        msg += f"（付属ファイル {n} 個も一緒に）"
    if loaded:
        msg += "\n\n今読み込んでいるモデルだったので、通常のモデル一覧の 🔄 を押して別のモデルを選んでね"
    else:
        msg += "\n\n通常のモデル一覧に反映するには 🔄 を押してね"
    return result(msg)


def do_unstash(rel):
    if not rel:
        return result("戻すモデルを選んでね")
    root = stash_dir()
    src = os.path.join(root, rel)
    if not (is_inside(src, root) and os.path.isfile(src)):
        return result(f"見つからない: `{rel}`")
    try:
        n = move_keeping_tree(src, root, os.path.abspath(sd_models.model_path))
    except Exception as e:
        return result(f"戻せなかった: {e}")
    sd_models.list_models()

    msg = f"戻した: `{rel}`"
    if n:
        msg += f"（付属ファイル {n} 個も一緒に）"
    msg += "\n\n通常のモデル一覧に反映するには 🔄 を押してね"
    return result(msg)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

class ModelStashScript(scripts.Script):
    def title(self):
        return EXTENSION_NAME

    def show(self, is_img2img):
        # txt2img / img2img の下に常に表示する
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Accordion(EXTENSION_NAME, open=False):
            with gr.Row():
                active = gr.Dropdown(label="通常のモデル", choices=list_active())
                stash_btn = gr.Button("しまう")
            with gr.Row():
                stashed = gr.Dropdown(label="しまったモデル", choices=list_stashed())
                unstash_btn = gr.Button("戻す")
            refresh_btn = gr.Button("🔄 一覧を更新")
            status = gr.Markdown()

        outputs = [status, active, stashed]
        stash_btn.click(do_stash, inputs=[active], outputs=outputs)
        unstash_btn.click(do_unstash, inputs=[stashed], outputs=outputs)
        refresh_btn.click(lambda: result(""), outputs=outputs)
        return []


def on_ui_settings():
    section = ("model_stash", EXTENSION_NAME)
    shared.opts.add_option(
        "model_stash_dir",
        shared.OptionInfo("", "しまっておくモデルのフォルダ（空なら WebUI の models/Stash）", section=section),
    )


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_app_started(lambda *_: stash_dir())
