# 街の履歴書 - 完全ガイド

## 📦 必要なライブラリ一覧

### requirements.txt
```txt
streamlit==1.31.0
streamlit-folium==0.17.0
folium==0.15.1
jaxa==0.1.0
numpy==1.24.3
Pillow==10.2.0
matplotlib==3.8.2
```

### インストール方法
```bash
pip install -r requirements.txt
```

または個別にインストール：
```bash
pip install streamlit streamlit-folium folium jaxa numpy Pillow matplotlib
```

---

## 🗂️ ファイル構成

```
project/
│
├── app.py              # Streamlitアプリケーション（メイン）
├── jaxa_api.py         # JAXA APIラッパー
├── requirements.txt    # 依存ライブラリリスト
├── APP_GUIDE.md        # app.pyの詳細解説
└── JAXA_API_GUIDE.md   # jaxa_api.pyの詳細解説
```

---

## 🚀 起動方法

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 が自動で開く

---

## 📚 ライブラリの役割マップ

### フロントエンド層（app.py）
```
Streamlit ─┬─ 画面表示
           ├─ ユーザー入力受付
           └─ セッション管理

Folium ────┬─ 地図表示
           └─ 範囲選択

streamlit-folium ── StreamlitとFoliumの橋渡し
```

### バックエンド層（jaxa_api.py）
```
JAXA API ──┬─ 衛星データ取得
           └─ フィルタリング

NumPy ─────── 数値配列操作

Matplotlib ─┬─ カラーマップ適用
            └─ 図の描画

PIL ───────┬─ 画像変換
           └─ 保存・読み込み

io ────────── メモリストリーム
```

---

## 🔄 データの流れ（全体像）

```
ユーザー操作
    ↓
[Folium地図] 地図を移動
    ↓
[streamlit-folium] 範囲（bbox）を取得
    ↓
[Streamlit] session_stateで変化を検知
    ↓
[jaxa_api.py] JaxaDataProvider.get_land_cover_images()
    ↓
[JAXA API] 衛星データ取得
    ↓
[Matplotlib] カラーマップ適用・描画
    ↓
[io.BytesIO] メモリストリームに保存
    ↓
[PIL] 画像として読み込み
    ↓
[Streamlit] session_stateに保存
    ↓
[Streamlit] スライダーで年選択
    ↓
[Streamlit] 画像表示
```

---

## 🎯 各ライブラリの詳細

### 1. Streamlit
**公式サイト:** https://streamlit.io/

**役割:** Webアプリケーションフレームワーク

**特徴:**
- Pythonコードだけでウェブアプリが作れる
- データの再実行モデル（ページ更新ごとにスクリプト全体を実行）
- session_stateで状態管理

**使用例:**
```python
import streamlit as st

st.title("タイトル")
st.image(image)
value = st.slider("選択", 0, 100)
```

---

### 2. Folium
**公式サイト:** https://python-visualization.github.io/folium/

**役割:** インタラクティブ地図作成

**特徴:**
- Leaflet.jsのPythonラッパー
- OpenStreetMapやGoogle Mapsライクな地図
- マーカー、ポリゴン、ヒートマップなど豊富な機能

**使用例:**
```python
import folium

m = folium.Map(location=[35.68, 139.76], zoom_start=10)
m.save('map.html')
```

---

### 3. streamlit-folium
**公式サイト:** https://github.com/randyzwitch/streamlit-folium

**役割:** StreamlitでFolium地図を表示

**特徴:**
- FoliumとStreamlitの統合
- 地図の状態（範囲、クリック位置など）を取得可能

**使用例:**
```python
from streamlit_folium import st_folium

output = st_folium(folium_map, returned_objects=["bounds"])
bbox = output['bounds']
```

---

### 4. JAXA Earth API
**公式サイト:** https://data.earth.jaxa.jp/

**役割:** JAXA衛星データへのアクセス

**提供データ:**
- MODIS（Terra/Aqua衛星）のNDVI
- GCOM-C（しきさい）の海洋・大気データ
- ALOS（だいち）の地形データ
- など90種類以上

**使用例:**
```python
from jaxa.earth import je

data = je.ImageCollection(
    collection="JAXA.JASMES_Terra.MODIS-Aqua.MODIS_ndvi.v811_global_monthly"
).filter_date(dlim=["2020-01-01", "2020-12-31"])\
  .get_images()
```

---

### 5. NumPy
**公式サイト:** https://numpy.org/

**役割:** 数値計算・配列操作

**特徴:**
- 多次元配列（ndarray）のサポート
- 高速な数値演算
- 科学計算の基盤

**使用例:**
```python
import numpy as np

arr = np.array([[1, 2], [3, 4]])
mean = np.mean(arr)
arr[arr < 2] = 0  # 条件付き操作
```

---

### 6. Matplotlib
**公式サイト:** https://matplotlib.org/

**役割:** グラフ・図の描画

**特徴:**
- 科学計算で最も使われる可視化ライブラリ
- カラーマップ、軸ラベル、タイトルなど豊富な機能
- バックエンドの切り替え（GUI/非GUI）

**使用例:**
```python
import matplotlib.pyplot as plt

plt.plot([1, 2, 3], [1, 4, 9])
plt.savefig('graph.png')
plt.close()
```

---

### 7. Pillow (PIL)
**公式サイト:** https://pillow.readthedocs.io/

**役割:** 画像処理

**特徴:**
- JPEG、PNG、GIF、BMPなど主要形式に対応
- リサイズ、トリミング、フィルタ適用など
- NumPy配列との相互変換

**使用例:**
```python
from PIL import Image

img = Image.open('photo.jpg')
img = img.resize((800, 600))
img.save('resized.jpg')
```

---

### 8. io（標準ライブラリ）
**公式サイト:** https://docs.python.org/ja/3/library/io.html

**役割:** 入出力ストリーム操作

**特徴:**
- ファイルを書かずにメモリ内で処理
- BytesIO: バイナリデータ用
- StringIO: テキストデータ用

**使用例:**
```python
import io

buffer = io.BytesIO()
buffer.write(b'Hello')
buffer.seek(0)
data = buffer.read()
```

---

## 💾 データ構造の詳細

### 1. BBox（Bounding Box）
```python
bbox = [西経度, 南緯度, 東経度, 北緯度]
例: [139.0, 35.0, 140.0, 36.0]

# 東京周辺の1度×1度の範囲
# 西端: 139.0度
# 南端: 35.0度（北緯）
# 東端: 140.0度
# 北端: 36.0度
```

### 2. NDVI値
```python
値の範囲: -1.0 ～ +1.0

-1.0 ～ 0.0  : 水域、雲、雪
 0.0 ～ 0.2  : 裸地、都市部
 0.2 ～ 0.5  : 草地、農地
 0.5 ～ 0.8  : 森林
 0.8 ～ 1.0  : 非常に密な森林
```

### 3. session_state構造
```python
st.session_state = {
    'jaxa_data_list': [
        <PIL.Image>,  # 2002年
        <PIL.Image>,  # 2003年
        None,         # 2004年（取得失敗）
        <PIL.Image>,  # 2005年
        ...
    ],
    'last_bbox_key': "[139.0, 35.0, 140.0, 36.0]"
}
```

---

## 🔧 カスタマイズガイド

### 初期表示位置を変更
```python
# app.py 33行目付近
m_base = folium.Map(location=[34.69, 135.50], zoom_start=10)
# → 大阪に変更
```

### 取得年数を変更
```python
# app.py 60行目付近
num_years=25  # 25年分取得（2002-2026）
```

### 解像度を変更
```python
# jaxa_api.py 23行目
ppu = 40  # 2倍の解像度（処理時間も2倍）
```

### 画質を変更
```python
# jaxa_api.py 50行目付近
fig.savefig(buf, format='png', bbox_inches='tight', dpi=300)
# dpi: 100=低画質, 150=標準, 300=高画質
```

### レイアウトを変更
```python
# app.py 6行目
st.set_page_config(layout="centered")  # 中央寄せ
```

---

## 🐛 トラブルシューティング

### 問題1: 画像が表示されない
**症状:** スライダーは動くが画像が出ない
**原因:** データ取得失敗
**対処:**
```python
# サイドバーでBBoxを確認
# 範囲が海上や国外になっていないか確認
```

### 問題2: メモリ不足
**症状:** "MemoryError"
**対処:**
```python
# num_years を減らす
num_years=5  # 25→5に変更

# または解像度を下げる
ppu = 10  # 20→10に変更
```

### 問題3: 処理が遅い
**症状:** データ取得に時間がかかる
**対処:**
```python
# 解像度を下げる
ppu = 10

# 取得年数を減らす
num_years=5

# 範囲を狭くする（地図をズームイン）
```

### 問題4: "FigureCanvasAgg" 警告
**症状:**
```
UserWarning: FigureCanvasAgg is non-interactive
```
**対処:** 無視してOK（正常動作）

---

## 📊 パフォーマンス最適化

### 推奨設定（バランス型）
```python
num_years = 5      # 5年分
ppu = 20           # 標準解像度
dpi = 150          # 標準画質
```

### 高速設定（プロトタイプ）
```python
num_years = 2      # 2年分のみ
ppu = 10           # 低解像度
dpi = 100          # 低画質
```

### 高品質設定（最終版）
```python
num_years = 25     # 25年分
ppu = 40           # 高解像度
dpi = 300          # 高画質
```

---

## 🎓 学習リソース

### Streamlit
- 公式チュートリアル: https://docs.streamlit.io/library/get-started
- チートシート: https://docs.streamlit.io/library/cheatsheet

### JAXA Earth API
- ドキュメント: https://data.earth.jaxa.jp/en/
- データカタログ: https://data.earth.jaxa.jp/en/datasets

### NumPy
- クイックスタート: https://numpy.org/doc/stable/user/quickstart.html

### Matplotlib
- チュートリアル: https://matplotlib.org/stable/tutorials/index.html

### Pillow
- ハンドブック: https://pillow.readthedocs.io/en/stable/handbook/index.html

---

## 📝 ライセンス情報

### 使用データ
- JAXA MODISデータ: JAXA利用規約に準拠
- OpenStreetMap: ODbL (Open Database License)

### ライブラリライセンス
- Streamlit: Apache 2.0
- Folium: MIT
- NumPy: BSD
- Matplotlib: PSF (Python Software Foundation)
- Pillow: HPND (Historical Permission Notice and Disclaimer)

---

## 🚀 デプロイ

### Streamlit Cloud
```bash
# GitHub にpush後
# https://streamlit.io/cloud でデプロイ
```

### Heroku
```bash
# Procfile作成
web: streamlit run app.py --server.port=$PORT
```

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

---

## 📞 サポート

問題が発生した場合：
1. サイドバーのデバッグ情報を確認
2. ターミナルのログを確認
3. JAXA APIドキュメントを参照
4. Streamlitコミュニティフォーラムで質問

---

**作成:** 2026年2月
**バージョン:** 1.0.0
