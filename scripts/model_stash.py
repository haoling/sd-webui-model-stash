import os

import gradio as gr
from modules import paths, scripts, script_callbacks, shared

EXTENSION_NAME = "Model Stash"
DEFAULT_STASH_DIR = os.path.join(paths.models_path, "Stash")  # WebUI の models/Stash


def stash_dir():
    """しまっておくモデルのフォルダ。設定が空なら WebUI の models/Stash を使い、なければ作る"""
    d = shared.opts.data.get("model_stash_dir", "") or DEFAULT_STASH_DIR
    os.makedirs(d, exist_ok=True)
    return d


class ModelStashScript(scripts.Script):
    def title(self):
        return EXTENSION_NAME

    def show(self, is_img2img):
        # txt2img / img2img の下に常に表示する
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Accordion(EXTENSION_NAME, open=False):
            gr.Markdown("開発中")
        return []


def on_ui_settings():
    section = ("model_stash", EXTENSION_NAME)
    shared.opts.add_option(
        "model_stash_dir",
        shared.OptionInfo("", "しまっておくモデルのフォルダ（空なら WebUI の models/Stash）", section=section),
    )


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_app_started(lambda *_: stash_dir())
