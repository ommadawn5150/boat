# minilogue-xd-user-fx

Korg minilogue xd 向け logue SDK v1 自作 User FX テンプレート集です。

## 構成

```
├── osc/my_osc/      # User Oscillator テンプレート
├── delfx/my_delay/  # User Delay FX テンプレート
└── revfx/my_rev/    # User Reverb FX テンプレート
```

## セットアップ

### 1. logue-sdk を取得

```bash
git clone https://github.com/korginc/logue-sdk.git ~/logue-sdk
```

### 2. ツールチェーンのインストール

[logue-sdk の README](https://github.com/korginc/logue-sdk) に従い `arm-none-eabi-gcc` をインストールしてください。

## ビルド方法

```bash
# User Oscillator
cd osc/my_osc
make

# Delay FX
cd delfx/my_delay
make

# Reverb FX
cd revfx/my_rev
make
```

ビルド成功すると `.mnlgxdunit` ファイルが生成されます。  
Korg Sound Librarian または logue-cli で minilogue xd に転送してください。

## SDK パスのカスタマイズ

`LOGUE_SDK` 環境変数で SDK のパスを指定できます。

```bash
make LOGUE_SDK=/path/to/logue-sdk
```

## 参考

- [logue SDK GitHub](https://github.com/korginc/logue-sdk)
- [minilogue xd SDK ページ (KORG)](https://www.korg.com/us/products/synthesizers/minilogue_xd/sdk.php)
