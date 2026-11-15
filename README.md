# sd-webui-model-stash

Stable Diffusion WebUI (AUTOMATIC1111) 用の拡張機能。

普段使わないチェックポイントを通常のモデル一覧とは別の場所にしまっておき、この拡張の一覧からだけ選べるようにする。普段のモデル選択の邪魔にならない。

> 開発中。まだ機能は入っていない。

## インストール

1. WebUI の **Extensions** → **Install from URL** を開く
2. 「URL for extension's git repository」に次を入力して **Install**
   ```
   https://github.com/haoling/sd-webui-model-stash
   ```
3. **Installed** タブで **Apply and restart UI**

## モデルの置き場所

WebUI の `models/Stash/` にモデルを置く。フォルダがなければ WebUI の起動時に自動で作られる。

```
stable-diffusion-webui/
└── models/
    ├── Stable-diffusion/   ← 普段使い（通常のモデル一覧に出る）
    └── Stash/              ← しまっておくモデル（この拡張の一覧にだけ出る）
```

拡張のフォルダとは別の場所なので、拡張を削除・入れ直ししてもモデルは消えない。
別の場所に置きたい場合は、WebUI の **Settings** → **Model Stash** でフォルダを指定できる。
ただし `models/Stable-diffusion/` の中（サブフォルダを含む）を指定すると、通常の一覧にも出てしまう。

## 使い方

txt2img / img2img の下にある **Model Stash** を開く。

- **通常のモデル ＋ しまう**：選んだモデルを `models/Stash/` に移動する
- **しまったモデル**：`models/Stash/` に置いたモデルの一覧。サブフォルダの中も表示する
- **戻す**：選んだモデルを `models/Stable-diffusion/` に戻す
- **🔄 一覧を更新**：フォルダにモデルを追加・削除したあとに押す
- **上書きに設定**：選んだモデルを txt2img / img2img の **Override settings** 欄に `Model hash: xxxxxxxxxx` として入れる。
  Override settings 欄の × で外すまで、生成にはこのモデルが使われる。外すと次の生成から通常のモデルに戻る

しまう・戻すときは、フォルダの階層をそのまま保つ。

```
models/Stable-diffusion/AAA/BB.safetensors  ⇄  models/Stash/AAA/BB.safetensors
```

同じフォルダにある、モデルと同じ名前で拡張子だけが違うファイル（`BB.json`、`BB.html`、`BB.preview.png`、`BB.civitai.info`、`BB.vae.safetensors` など）も、付属ファイルとして一緒に移動する。
ただし、名前が似ているだけの別のモデル（`BB.v2.safetensors`）と、その付属ファイル（`BB.v2.json` など）は動かさない。
移動先に同じ名前のファイルがあるときは何もしない。
移動したあと、通常のモデル一覧に反映するには、そちらの 🔄 を押す。

上書きに設定したとき、そのモデルのハッシュを初めて計算する場合は少し時間がかかる（2回目からはキャッシュを使う）。
通常のモデル一覧の表示は変わらないので、実際に使われたモデルは生成結果の `Model:` / `Model hash:` で確認する。

## ファイル構成

```
sd-webui-model-stash/
├── scripts/
│   └── model_stash.py   # WebUI が読み込むスクリプト
└── README.md
```

## 動作確認したバージョン

- AUTOMATIC1111: (未確認)
