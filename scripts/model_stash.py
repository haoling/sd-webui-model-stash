import os

import gradio as gr
from modules import paths, scripts, script_callbacks, shared

EXTENSION_NAME = "Model Stash"
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


class ModelStashScript(scripts.Script):
    def title(self):
        return EXTENSION_NAME

    def show(self, is_img2img):
        # txt2img / img2img の下に常に表示する
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Accordion(EXTENSION_NAME, open=False):
            with gr.Row():
                stashed = gr.Dropdown(label="しまったモデル", choices=list_stashed())
                refresh_btn = gr.Button("🔄 一覧を更新")

        refresh_btn.click(lambda: gr.update(choices=list_stashed()), outputs=[stashed])
        return []


def on_ui_settings():
    section = ("model_stash", EXTENSION_NAME)
    shared.opts.add_option(
        "model_stash_dir",
        shared.OptionInfo("", "しまっておくモデルのフォルダ（空なら WebUI の models/Stash）", section=section),
    )


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_app_started(lambda *_: stash_dir())
