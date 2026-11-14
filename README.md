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

この拡張のフォルダの中にある `models/` にモデルを置く。

```
stable-diffusion-webui/extensions/sd-webui-model-stash/models/
```

`models/` の中身は git の管理対象外なので、拡張を更新してもモデルは消えない。
別の場所に置きたい場合は、WebUI の **Settings** → **Model Stash** でフォルダを指定できる。

## ファイル構成

```
sd-webui-model-stash/
├── scripts/
│   └── model_stash.py   # WebUI が読み込むスクリプト
├── models/              # しまっておくモデルの置き場所
└── README.md
```

## 動作確認したバージョン

- AUTOMATIC1111: (未確認)
