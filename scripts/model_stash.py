import os

import gradio as gr
from modules import scripts, script_callbacks, shared

EXTENSION_NAME = "Model Stash"
BASE_DIR = scripts.basedir()  # この拡張のフォルダ


def stash_dir():
    """しまっておくモデルのフォルダ。設定が空なら拡張内の models/ を使う"""
    d = shared.opts.data.get("model_stash_dir", "")
    return d if d else os.path.join(BASE_DIR, "models")


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
        shared.OptionInfo("", "しまっておくモデルのフォルダ（空なら拡張内の models/）", section=section),
    )


script_callbacks.on_ui_settings(on_ui_settings)
