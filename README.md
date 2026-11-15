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

## ファイル構成

```
sd-webui-model-stash/
├── scripts/
│   └── model_stash.py   # WebUI が読み込むスクリプト
└── README.md
```

## 動作確認したバージョン

- AUTOMATIC1111: (未確認)
