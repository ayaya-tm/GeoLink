# 🌿 LeafCast コード完全解説

## 📋 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [app.py - メインアプリケーション](#apppy---メインアプリケーション)
3. [jaxa_api.py - 衛星データ取得](#jaxa_apipy---衛星データ取得)
4. [future_prefiction.py - 予測モデル](#future_prefictionpy---予測モデル)
5. [データフロー図](#データフロー図)
6. [技術的な設計判断](#技術的な設計判断)

---

## プロジェクト概要

LeafCastは、JAXA/NASAの衛星データを使用して地表面温度(LST)と植生指数(NDVI)を分析し、未来予測と緑化シミュレーションを行うStreamlitアプリケーションです。

### アーキテクチャ

```
┌─────────────────────────────────────────┐
│          app.py (UI Layer)              │
│  - Streamlit Interface                  │
│  - Session Management                   │
│  - Data Visualization                   │
└──────────────┬──────────────────────────┘
               │
               ├──────────────┐
               │              │
               ▼              ▼
┌──────────────────────┐  ┌──────────────────────┐
│   jaxa_api.py        │  │ future_prefiction.py │
│   (Data Layer)       │  │ (Model Layer)        │
│  - JAXA API Client   │  │ - Linear Regression  │
│  - Image Processing  │  │ - Prediction Graph   │
│  - Data Conversion   │  │ - Simulation         │
└──────────────────────┘  └──────────────────────┘
```

---

## app.py - メインアプリケーション

### 1. 初期設定とインポート

```python
import streamlit as st
from streamlit_folium import st_folium
import folium
from jaxa_api import JaxaDataProvider
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from future_prefiction import create_future_prediction_graph, simulate_greening_effect
```

**解説:**
- `streamlit`: Webアプリケーションフレームワーク
- `folium`: インタラクティブ地図ライブラリ
- `streamlit_folium`: StreamlitでFoliumを使用するためのブリッジ
- カスタムモジュール: データ取得と予測機能

### 2. ページ設定

```python
st.set_page_config(
    page_title="LeafCast - 未来地表温度予測",
    layout="wide",
    initial_sidebar_state="collapsed"
)
```

**解説:**
- `layout="wide"`: 画面幅を最大限活用
- `initial_sidebar_state="collapsed"`: サイドバーを初期状態で非表示
- ユーザー体験を向上させるための設定

### 3. カスタムCSS

```python
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2e7d32;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #e8f5e9;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4caf50;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3e0;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #ff9800;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)
```

**解説:**
- **main-header**: タイトル用のスタイル（緑色、大きめ）
- **info-box**: 情報表示用のボックス（緑背景、左に緑ライン）
- **warning-box**: 注意事項用のボックス（オレンジ背景）
- **stButton**: ボタンを全幅、丸角、高さ調整

### 4. セッション状態の初期化

```python
if 'lst_images' not in st.session_state:
    st.session_state.lst_images = None
if 'lst_number_datas' not in st.session_state:
    st.session_state.lst_number_datas = None
if 'ndvi_images' not in st.session_state:
    st.session_state.ndvi_images = None
if 'ndvi_number_datas' not in st.session_state:
    st.session_state.ndvi_number_datas = None
if 'last_bbox_key' not in st.session_state:
    st.session_state.last_bbox_key = ""
```

**解説:**
- **セッション状態**: Streamlitのページリロード間でデータを保持
- **lst_images**: 地表面温度の画像データ
- **ndvi_images**: 植生指数の画像データ
- **number_datas**: 実際の数値データ（計算用）
- **last_bbox_key**: 前回の地図範囲（重複取得を防ぐ）

**なぜ必要か:**
Streamlitは各操作でスクリプトを再実行するため、データを保持する仕組みが必要です。

### 5. インタラクティブ地図表示

```python
col_map1, col_map2, col_map3 = st.columns([1, 4, 1])
with col_map2:
    m_base = folium.Map(location=[35.68, 139.76], zoom_start=10)
    output = st_folium(m_base, width=900, height=500, key="base_map", returned_objects=["bounds"])
```

**解説:**
- **columns**: 3列レイアウト（1:4:1の比率で中央に配置）
- **folium.Map**: 東京（35.68, 139.76）を中心とした地図
- **returned_objects=["bounds"]**: 地図の表示範囲を返す

### 6. データ取得ロジック

```python
if output and output.get('bounds'):
    b = output['bounds']
    if b.get('_southWest') and b.get('_northEast'):
        sw, ne = b['_southWest'], b['_northEast']
        if sw.get('lng') is not None:
            # BBox作成
            current_bbox = [
                round(sw['lng']),
                round(sw['lat']),
                round(ne['lng']),
                round(ne['lat'])
            ]
            bbox_key = f"{current_bbox[0]:.4f},{current_bbox[1]:.4f},{current_bbox[2]:.4f},{current_bbox[3]:.4f}"
            
            # 範囲が変わった時だけ取得
            if st.session_state.last_bbox_key != bbox_key:
                st.session_state.last_bbox_key = bbox_key
                # データをリセット
                st.session_state.lst_images = None
                st.session_state.lst_number_datas = None
                st.session_state.ndvi_images = None
                st.session_state.ndvi_number_datas = None
                
                with st.spinner("🛰️ 衛星データを取得中... しばらくお待ちください"):
                    provider = JaxaDataProvider()
                    # LSTデータ取得
                    st.session_state.lst_images, st.session_state.lst_number_datas = provider.get_land_cover_images(
                        current_bbox,
                        START_YEAR,
                        num_years=10
                    )
                    # NDVIデータ取得
                    st.session_state.ndvi_images, st.session_state.ndvi_number_datas = provider.get_ndvi_images(
                        current_bbox,
                        START_YEAR,
                        num_years=10
                    )
                st.rerun()
```

**解説:**
1. **bounds取得**: 地図の表示範囲（南西・北東の座標）を取得
2. **BBox作成**: `[西経度, 南緯度, 東経度, 北緯度]`形式に変換
3. **重複チェック**: `bbox_key`で範囲が変わったかを確認
4. **データ取得**: 新しい範囲の場合のみAPIを呼び出し
5. **st.rerun()**: データ取得後にページを再読み込み

**最適化のポイント:**
- 同じエリアで何度もAPIを呼ばないようにキャッシュ機能を実装
- ユーザー体験向上のためスピナー表示

### 7. データ検証と整形

```python
if st.session_state.lst_images and st.session_state.ndvi_images:
    # 取得成功した画像のみ抽出（両方のデータが揃っている年のみ）
    valid_data = []
    for i in range(len(st.session_state.lst_images)):
        lst_img = st.session_state.lst_images[i]
        ndvi_img = st.session_state.ndvi_images[i]
        lst_num = st.session_state.lst_number_datas[i]
        ndvi_num = st.session_state.ndvi_number_datas[i]
        
        if lst_img is not None and ndvi_img is not None:
            valid_data.append({
                'year': START_YEAR + i,
                'lst_image': lst_img,
                'ndvi_image': ndvi_img,
                'lst_data': lst_num,
                'ndvi_data': ndvi_num
            })
```

**解説:**
- **データペアリング**: LSTとNDVI両方が存在する年のみ使用
- **辞書形式**: 年、画像、数値データをまとめて管理
- **None除外**: データ取得失敗の年を除外

### 8. 衛星画像表示（スライダー付き）

```python
selected_idx = st.select_slider(
    "📅 表示年を選択してください",
    options=list(range(len(valid_data))),
    format_func=lambda x: f"{valid_data[x]['year']}年"
)

selected_data = valid_data[selected_idx]

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"#### 🌡️ 地表面温度（LST）")
    st.image(
        selected_data['lst_image'],
        caption=f"{selected_data['year']}年4月のLSTデータ",
        use_container_width=True
    )
```

**解説:**
- **select_slider**: 年を選択するスライダー
- **format_func**: インデックスを年表示に変換
- **2列レイアウト**: LSTとNDVIを横並び表示

### 9. 未来予測グラフの生成

```python
# LSTとNDVIの平均値を計算
lst_values = []
ndvi_values = []
years = []

for data in valid_data:
    years.append(data['year'])
    if data['lst_data'] is not None:
        lst_values.append(np.nanmean(data['lst_data']))
    else:
        lst_values.append(0)
    
    if data['ndvi_data'] is not None:
        ndvi_values.append(np.nanmean(data['ndvi_data']))
    else:
        ndvi_values.append(0)

# 未来予測の計算
from sklearn.linear_model import LinearRegression

years_obs = np.array(years).reshape(-1, 1)
ndvi_obs = np.array(ndvi_values).reshape(-1, 1)
lst_obs = np.array(lst_values).reshape(-1, 1)

model_ndvi = LinearRegression().fit(years_obs, ndvi_obs)
model_lst = LinearRegression().fit(ndvi_obs, lst_obs)

# 未来20年分の予測
last_year = years[-1]
years_future = list(range(last_year + 1, last_year + 21))
ndvi_future = []
lst_future = []

for year in years_future:
    predicted_ndvi = model_ndvi.predict([[year]])[0][0]
    predicted_lst = model_lst.predict([[predicted_ndvi]])[0][0]
    ndvi_future.append(predicted_ndvi)
    lst_future.append(predicted_lst)

# 未来予測グラフを生成
fig = create_future_prediction_graph(years, ndvi_values, lst_values, START_YEAR, predict_years=20)
st.pyplot(fig)
```

**解説:**
1. **平均値計算**: 各年のLST/NDVIをエリア全体で平均
2. **モデル構築**:
   - `model_ndvi`: 年 → NDVI の予測
   - `model_lst`: NDVI → LST の予測
3. **予測**: 20年先までのNDVIとLSTを計算
4. **可視化**: カスタムグラフ関数で表示

### 10. データテーブル表示（タブ形式）

```python
tab1, tab2, tab3 = st.tabs(["📊 観測データのみ", "🔮 観測 + 予測データ", "📈 統計情報"])

with tab1:
    # 観測データのみ
    df_obs = pd.DataFrame({
        '年': years,
        'NDVI(植生指数)': [f"{v:.4f}" for v in ndvi_values],
        'LST(地表面温度 ℃)': [f"{v:.2f}" for v in lst_values]
    })
    st.dataframe(df_obs, use_container_width=True, hide_index=True)

with tab2:
    # 観測データと予測データを結合
    all_years = years + years_future
    all_ndvi = ndvi_values + ndvi_future
    all_lst = lst_values + lst_future
    data_type = ['✅ 観測'] * len(years) + ['🔮 予測'] * len(years_future)
    
    df_all = pd.DataFrame({
        '年': all_years,
        '種別': data_type,
        'NDVI(植生指数)': [f"{v:.4f}" for v in all_ndvi],
        'LST(地表面温度 ℃)': [f"{v:.2f}" for v in all_lst]
    })
    
    st.dataframe(df_all, use_container_width=True, hide_index=True)
```

**解説:**
- **tab1**: 観測データのみを表示
- **tab2**: 観測と予測を統合（✅/🔮で識別）
- **tab3**: 統計情報（平均、最大、最小、標準偏差）

**データ形式:**
- 小数点以下の桁数を制御（NDVI: 4桁、LST: 2桁）
- `hide_index=True`: 行番号を非表示

### 11. 緑化シミュレーション

```python
col_sim1, col_sim2 = st.columns([1, 1])

with col_sim1:
    st.markdown("#### ⚙️ シミュレーション設定")
    target_year = st.number_input(
        "対象年",
        min_value=years[-1] + 1,
        max_value=years[-1] + 20,
        value=years[-1] + 5,
        step=1
    )
    
    increase_rate = st.slider(
        "NDVI向上率（%）",
        min_value=1,
        max_value=20,
        value=5,
        step=1
    ) / 100
    
    run_simulation = st.button("🚀 シミュレーション実行", type="primary")

with col_sim2:
    st.markdown("#### 📊 シミュレーション結果")
    
    if run_simulation:
        # 通常の予測
        base_ndvi = model_ndvi.predict([[target_year]])[0][0]
        base_lst = model_lst.predict([[base_ndvi]])[0][0]
        
        # 緑化シミュレーション
        sim_ndvi = base_ndvi * (1 + increase_rate)
        sim_lst = model_lst.predict([[sim_ndvi]])[0][0]
        
        lst_change_val = sim_lst - base_lst
        lst_change_percent = (lst_change_val / base_lst) * 100
        
        # 結果表示
        result_df = pd.DataFrame({
            '項目': ['通常予測', '緑化後', '変化量'],
            'NDVI': [
                f"{base_ndvi:.4f}",
                f"{sim_ndvi:.4f}",
                f"+{sim_ndvi - base_ndvi:.4f} (+{increase_rate*100:.0f}%)"
            ],
            'LST(℃)': [
                f"{base_lst:.2f}",
                f"{sim_lst:.2f}",
                f"{lst_change_val:.2f} ({lst_change_percent:.2f}%)"
            ]
        })
        
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        
        # 効果の解説
        if lst_change_val < 0:
            st.success(f"✅ {target_year}年にNDVIを{increase_rate*100:.0f}%向上させることで、地表面温度を約**{abs(lst_change_val):.2f}℃**低減できる可能性があります。")
            st.markdown("🌳 **具体的な緑化施策例**：街路樹の増設、屋上緑化、壁面緑化、公園の整備など")
```

**解説:**
1. **設定入力**:
   - 対象年: 最終観測年+1から+20まで
   - NDVI向上率: 1%〜20%
2. **計算ロジック**:
   - ベースライン: 通常の予測値
   - シミュレーション: NDVI × (1 + 向上率)
   - 温度差: シミュレーション - ベースライン
3. **結果表示**: 3行のテーブル（通常/緑化後/変化量）

**条件分岐:**
- 温度が下がった場合（負の変化）→ success メッセージ
- 温度が上がった場合（正の変化）→ info メッセージ

---

## jaxa_api.py - 衛星データ取得

### クラス構造

```python
class JaxaDataProvider:
    """JAXA衛星データ取得クラス"""
```

### 1. メインメソッド: get_data_array

```python
def get_data_array(self, bbox, coll, band, start_year, num_years=5):
    """
    指定範囲のデータ画像を取得
    
    Args:
        bbox (list): [西経度, 南緯度, 東経度, 北緯度]
        coll (str): コレクション名（データセット識別子）
        band (str): バンド名（'LST', 'ndvi'など）
        start_year (int): 開始年
        num_years (int): 取得年数
    
    Returns:
        tuple: (画像リスト, 数値データリスト)
    """
```

**解説:**
- **bbox**: 地図の境界ボックス（緯度経度の範囲）
- **coll**: JAXAのデータコレクション識別子
- **band**: 取得するデータバンド（LST or NDVI）

### 2. データ取得ループ

```python
images = []
number_datas = []

for i in range(num_years):
    target_year = start_year + i
    
    try:
        # JAXA APIでデータ取得
        data = je.ImageCollection(
            collection=coll,
            ssl_verify=True
        ).filter_date(
            dlim=[f"{target_year}-04-01T00:00:00", f"{target_year}-04-01T00:00:00"]
        ).filter_resolution(
            ppu=20
        ).filter_bounds(
            bbox=bbox
        ).select(
            band=band
        ).get_images()
```

**解説:**
1. **ImageCollection**: JAXAデータコレクションのインスタンス生成
2. **filter_date**: 日付範囲の指定（毎年4月1日のデータ）
3. **filter_resolution**: 解像度指定（ppu=20）
4. **filter_bounds**: 地理的範囲の指定
5. **select**: バンドの選択
6. **get_images**: データ取得の実行

**なぜ4月1日か:**
- 春季の代表的な時期
- 積雪の影響が少ない
- 植生が活発になる時期

### 3. 画像生成とデータ保存

```python
if data:
    # 数値データを保存
    raster_data = data.raster.img[0]
    number_datas.append(raster_data)
    
    # 直接imshowで画像を生成
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 緯度経度の範囲を取得
    extent = [bbox[0], bbox[2], bbox[1], bbox[3]]  # [west, east, south, north]
    
    # LSTの場合は摂氏変換して表示範囲を設定
    if band == 'LST':
        # ケルビンから摂氏に変換
        raster_data_celsius = raster_data - 273.15
        im = ax.imshow(raster_data_celsius, extent=extent, aspect='auto', origin='upper', cmap='jet')
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Temperature (°C)', rotation=270, labelpad=20)
    else:
        im = ax.imshow(raster_data, extent=extent, aspect='auto', origin='upper', vmin=0, vmax=1, cmap='jet')
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(band, rotation=270, labelpad=20)
    
    ax.set_xlabel('Longitude (°E)')
    ax.set_ylabel('Latitude (°N)')
    ax.set_title(f'{band} - {target_year}')
```

**解説:**
1. **ラスターデータ取得**: `data.raster.img[0]`から数値配列を取得
2. **温度変換**: LSTの場合、ケルビン→摂氏（-273.15）
3. **imshow**: 2D配列をヒートマップ表示
   - `extent`: 緯度経度の範囲を指定
   - `origin='upper'`: 画像の原点を左上に
   - `cmap='jet'`: カラーマップ（青→緑→黄→赤）
4. **カラーバー**: 値の範囲を視覚化

**カラーマップの選択:**
- `jet`: 温度やNDVIに適した連続的なカラースケール
- 代替案: `viridis`（色覚多様性に配慮）

### 4. PIL Imageへの変換

```python
# PIL Imageに変換
buf = io.BytesIO()
fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
buf.seek(0)
pil_img = Image.open(buf).copy()
images.append(pil_img)

# メモリ解放
plt.close(fig)
buf.close()
```

**解説:**
1. **BytesIO**: メモリ内のバッファ（ディスクI/O不要）
2. **savefig**: matplotlibのfigureをPNGとして保存
3. **PIL.Image.open**: バッファから画像を読み込み
4. **copy()**: バッファが閉じられても画像を保持
5. **メモリ解放**: figureとバッファを明示的にクローズ

**なぜPIL Imageか:**
- Streamlitが直接表示可能
- メモリ効率が良い
- 複数フォーマットに変換可能

### 5. エラーハンドリング

```python
except Exception as e:
    print(f"Error {target_year}: {e}")
    images.append(None)
    number_datas.append(None)
    plt.close('all')
```

**解説:**
- データ取得失敗時は`None`を追加
- エラーメッセージを出力
- すべてのmatplotlibのfigureをクローズ

### 6. 専用メソッド

```python
def get_land_cover_images(self, bbox, start_year, num_years=5):
    images, kelvin_array = self.get_data_array(
        bbox, 
        coll='NASA.EOSDIS_Terra.MODIS_MOD11C3-LST.daytime.v061_global_monthly', 
        band='LST', 
        start_year=start_year, 
        num_years=num_years
    )
    celsius_datas = []

    for kelvin_array in kelvin_array:
        if kelvin_array is not None:
            celsius_array = kelvin_array - 273.15
            celsius_datas.append(celsius_array)
        else:
            celsius_datas.append(None)
    
    return images, celsius_datas

def get_ndvi_images(self, bbox, start_year, num_years=5):
    return self.get_data_array(
        bbox, 
        coll='JAXA.JASMES_Terra.MODIS-Aqua.MODIS_ndvi.v811_global_monthly', 
        band='ndvi', 
        start_year=start_year, 
        num_years=num_years
    )
```

**解説:**
- **get_land_cover_images**: LSTデータを取得し、摂氏に変換
- **get_ndvi_images**: NDVIデータを取得（変換不要）

**データセット:**
- **LST**: NASA MODIS MOD11C3（日中の地表面温度）
- **NDVI**: JAXA MODIS NDVI v811（植生指数）

---

## future_prefiction.py - 予測モデル

### 1. 未来予測グラフ作成

```python
def create_future_prediction_graph(years, ndvi_values, lst_values, start_year=2002, predict_years=20):
    """
    LSTとNDVIの実測値から未来予測グラフを作成
    
    Args:
        years (list): 観測年のリスト
        ndvi_values (list): NDVIの実測値リスト
        lst_values (list): LSTの実測値リスト
        start_year (int): 開始年
        predict_years (int): 予測する年数
    
    Returns:
        matplotlib.figure.Figure: 生成されたグラフのfigureオブジェクト
    """
```

### 2. データ準備

```python
# データをNumPy配列に変換
years_obs = np.array(years).reshape(-1, 1)
ndvi_obs = np.array(ndvi_values)
lst_obs = np.array(lst_values)

# 未来予測用の年の配列を作成
last_year = years[-1]
years_future = np.array(range(last_year + 1, last_year + 1 + predict_years)).reshape(-1, 1)
```

**解説:**
- **reshape(-1, 1)**: 1次元配列を2次元配列に変換（sklearn要件）
- **years_future**: 最終観測年の翌年から20年分

### 3. 予測モデルの構築

```python
# NDVI予測モデル (Year -> NDVI)
model_ndvi = LinearRegression().fit(years_obs, ndvi_obs)
ndvi_future = model_ndvi.predict(years_future)

# LST予測モデル (NDVI -> LST)
model_lst = LinearRegression().fit(ndvi_obs.reshape(-1, 1), lst_obs)
lst_future = model_lst.predict(ndvi_future.reshape(-1, 1))
```

**解説:**

**モデル1: Year → NDVI**
```
NDVI(t) = α × Year + β
```
- **α**: 年あたりのNDVI変化率（傾き）
- **β**: 切片（基準年のNDVI）
- **仮定**: NDVIは年々線形に変化

**モデル2: NDVI → LST**
```
LST(t) = γ × NDVI(t) + δ
```
- **γ**: NDVIあたりの温度変化率（傾き）
- **δ**: 切片（NDVI=0の理論温度）
- **仮定**: NDVIとLSTに負の相関がある

**2段階予測の理由:**
1. 年からNDVIを予測（都市化・緑化のトレンド）
2. NDVIからLSTを予測（植生と温度の関係）

### 4. データ結合

```python
# 全期間データの結合
years_all = np.concatenate([years_obs.flatten(), years_future.flatten()])
ndvi_all = np.concatenate([ndvi_obs, ndvi_future])
lst_all = np.concatenate([lst_obs, lst_future])
```

**解説:**
- 観測データと予測データを1つの配列に統合
- グラフ描画を簡単にするため

### 5. グラフ描画（2軸グラフ）

```python
# グラフ作成
fig, ax1 = plt.subplots(figsize=(12, 6))

# NDVIのプロット（左軸）
obs_len = len(years_obs)
ax1.plot(years_all[:obs_len], ndvi_all[:obs_len], color='green', marker='o', linewidth=2, markersize=8, label='NDVI (実測値)')
ax1.plot(years_all[obs_len-1:], ndvi_all[obs_len-1:], color='green', linestyle='--', linewidth=2, marker='o', markersize=6, alpha=0.7, label='NDVI (予測値)')
ax1.set_xlabel('年', fontsize=12)
ax1.set_ylabel('NDVI(植生指数)', color='green', fontsize=12)
ax1.tick_params(axis='y', labelcolor='green')
ax1.grid(True, which='both', linestyle='--', alpha=0.3)

# LSTのプロット（右軸）
ax2 = ax1.twinx()
ax2.plot(years_all[:obs_len], lst_all[:obs_len], color='orangered', marker='s', linewidth=2, markersize=8, label='LST (実測値)')
ax2.plot(years_all[obs_len-1:], lst_all[obs_len-1:], color='orangered', linestyle='--', linewidth=2, marker='s', markersize=6, alpha=0.7, label='LST (予測値)')
ax2.set_ylabel('LST 地表面温度 (℃)', color='orangered', fontsize=12)
ax2.tick_params(axis='y', labelcolor='orangered')
```

**解説:**

**2軸グラフの理由:**
- NDVIとLSTはスケールが異なる（NDVI: 0-1, LST: 10-40℃）
- 両方のトレンドを同時に可視化

**グラフ要素:**
- **実線**: 観測データ（過去）
- **破線**: 予測データ（未来）
- **マーカー**: データポイント（'o' = NDVI, 's' = LST）
- **alpha=0.7**: 予測部分を半透明に

**色の選択:**
- 緑: 植生を連想（NDVI）
- オレンジ赤: 温度を連想（LST）

### 6. 凡例の統合

```python
# タイトルと凡例
ax1.set_title(f'地表面温度(LST)と植生指数(NDVI)の推移と予測 ({start_year}-{years_all[-1]:.0f})', 
              fontsize=14, fontweight='bold')

# 凡例を統合
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

plt.tight_layout()

return fig
```

**解説:**
- **get_legend_handles_labels()**: 各軸の凡例情報を取得
- **統合**: 4つの系列（NDVI実測/予測、LST実測/予測）を1つの凡例に
- **tight_layout()**: グラフ要素の重なりを自動調整

### 7. 緑化シミュレーション

```python
def simulate_greening_effect(years, ndvi_values, lst_values, target_year, increase_rate=0.01):
    """
    来年のNDVIが想定よりX%上昇した場合のLST抑制効果をシミュレーションする
    """
    # 1. モデルの準備
    years_obs = np.array(years).reshape(-1, 1)
    ndvi_obs = np.array(ndvi_values).reshape(-1, 1)
    lst_obs = np.array(lst_values).reshape(-1, 1)

    model_ndvi = LinearRegression().fit(years_obs, ndvi_obs)
    model_lst = LinearRegression().fit(ndvi_obs, lst_obs)

    # 2. 通常の予測（ベースライン）
    base_ndvi = model_ndvi.predict([[target_year]])[0][0]
    base_lst = model_lst.predict([[base_ndvi]])[0][0]

    # 3. 緑化シミュレーション（NDVIを1%など底上げ）
    sim_ndvi = base_ndvi * (1 + increase_rate)
    sim_lst = model_lst.predict([[sim_ndvi]])[0][0]

    # 4. 変化率の計算
    lst_change_val = sim_lst - base_lst
    lst_change_percent = (lst_change_val / base_lst) * 100

    print(f"--- {target_year}年 緑化シミュレーション ---")
    print(f"想定NDVI: {base_ndvi:.4f} → シミュレーションNDVI: {sim_ndvi:.4f} (+{increase_rate*100}%)")
    print(f"想定温度: {base_lst:.2f}℃ → シミュレーション温度: {sim_lst:.2f}℃")
    print(f"温度変化: {lst_change_val:.2f}℃ ({lst_change_percent:.2f}%)")
    
    return sim_lst
```

**解説:**

**シミュレーション手順:**
1. **ベースライン予測**: 対象年の通常予測値を計算
2. **NDVI向上**: ベースラインのNDVIに増加率を適用
3. **LST再計算**: 向上したNDVIから新しいLSTを予測
4. **差分計算**: ベースラインとの温度差を算出

**数式:**
```
NDVI_sim = NDVI_base × (1 + 増加率)
LST_sim = γ × NDVI_sim + δ
ΔT = LST_sim - LST_base
```

**増加率の意味:**
- 5% = 現状の1.05倍のNDVI
- 例: NDVI=0.5 → 0.525（+0.025）

---

## データフロー図

```
┌─────────────────────────────────────────────────────────┐
│                    1. ユーザー入力                       │
│            (地図操作 → BBox取得)                          │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              2. JAXADataProvider                        │
│         (API呼び出し → 画像生成 → データ保存)            │
│                                                         │
│  ┌──────────────┐        ┌──────────────┐             │
│  │ get_lst      │        │ get_ndvi     │             │
│  │ images()     │        │ images()     │             │
│  └──────┬───────┘        └──────┬───────┘             │
│         │                       │                      │
│         └───────────┬───────────┘                      │
│                     ▼                                   │
│          [lst_images, lst_data]                         │
│          [ndvi_images, ndvi_data]                       │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│            3. データ検証と整形                           │
│      (valid_data作成 → 平均値計算)                       │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ├──────────┬──────────┐
                        ▼          ▼          ▼
            ┌───────────────┐ ┌───────┐ ┌──────────┐
            │  画像表示     │ │ テーブル│ │グラフ   │
            │  (スライダー)  │ │ 表示  │ │生成     │
            └───────────────┘ └───────┘ └────┬─────┘
                                                │
                                                ▼
                        ┌──────────────────────────────┐
                        │  4. 予測モデル               │
                        │  (LinearRegression)          │
                        │                              │
                        │  Year → NDVI → LST           │
                        └──────────┬───────────────────┘
                                   │
                                   ├──────────┬─────────┐
                                   ▼          ▼         ▼
                        ┌──────────┐ ┌──────────┐ ┌─────────┐
                        │ 予測グラフ │ │予測テーブル│ │シミュ   │
                        │          │ │          │ │レーション│
                        └──────────┘ └──────────┘ └─────────┘
```

---

## 技術的な設計判断

### 1. なぜStreamlitか？

**選択理由:**
- **迅速な開発**: Pythonのみでフルスタックアプリ構築
- **リアクティブ**: 自動的にUI更新
- **データサイエンス特化**: Pandas、Matplotlibと統合

**代替案:**
- Flask + React: より柔軟だが開発時間増
- Dash: Streamlit類似だがカスタマイズ性低い

### 2. セッション状態の管理

**問題:**
Streamlitは各操作でスクリプトを再実行する

**解決策:**
```python
if 'lst_images' not in st.session_state:
    st.session_state.lst_images = None
```

**メリット:**
- データを再取得せずに保持
- APIコール回数削減
- ユーザー体験向上

### 3. BBoxキャッシング

```python
bbox_key = f"{current_bbox[0]:.4f},{current_bbox[1]:.4f},{current_bbox[2]:.4f},{current_bbox[3]:.4f}"

if st.session_state.last_bbox_key != bbox_key:
    # データ取得
```

**理由:**
- 同じエリアでの重複取得防止
- API負荷軽減
- レスポンス時間短縮

### 4. エラーハンドリング戦略

```python
try:
    data = je.ImageCollection(...).get_images()
except Exception as e:
    images.append(None)
    number_datas.append(None)
```

**設計判断:**
- **部分的失敗を許容**: 一部の年のデータ取得失敗でも続行
- **Noneで埋める**: 後続処理でフィルタリング可能
- **ユーザーへの影響最小化**: 取得できたデータは表示

### 5. 画像生成のメモリ管理

```python
buf = io.BytesIO()
fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
buf.seek(0)
pil_img = Image.open(buf).copy()

plt.close(fig)
buf.close()
```

**重要ポイント:**
- **BytesIO**: ディスクI/O不要（高速）
- **copy()**: バッファクローズ後も画像保持
- **明示的クローズ**: メモリリーク防止

### 6. 2段階予測モデルの選択

**Year → NDVI → LST**

**理由:**
1. **因果関係の明確化**: 都市化がNDVIを減少、NDVIがLSTに影響
2. **解釈可能性**: 各段階の関係を可視化
3. **シミュレーション対応**: NDVIを操作して効果測定

**代替案:**
- **直接予測**: Year → LST（シンプルだが解釈困難）
- **機械学習**: LSTM、XGBoost（精度向上だが複雑）

### 7. データ可視化の選択

**グラフ: Matplotlib**
- 高度なカスタマイズ可能
- 2軸グラフが簡単
- PNG出力でStreamlitに最適

**地図: Folium**
- インタラクティブ
- BBox取得が容易
- OpenStreetMap統合

**テーブル: Pandas DataFrame**
- フォーマット制御容易
- ソート・フィルタ機能
- Streamlitネイティブサポート

### 8. 定数の配置

```python
START_YEAR = 2002
```

**理由:**
- MODISデータの開始年（2002年）
- 変更時に1箇所のみ修正

### 9. UI/UXの工夫

**タブ形式:**
```python
tab1, tab2, tab3 = st.tabs(["観測", "観測+予測", "統計"])
```
- 情報過多を防ぐ
- ユーザーが必要な情報を選択

**スライダー:**
```python
st.select_slider("年を選択", options=years)
```
- 年次変化を視覚的に確認
- アニメーション的な体験

**カラム:**
```python
col1, col2 = st.columns(2)
```
- LSTとNDVIを比較しやすく
- 画面スペース有効活用

### 10. 今後の改善点

**パフォーマンス:**
- データキャッシングの拡張（@st.cache_data）
- 非同期データ取得
- プログレスバーの詳細化

**機能:**
- 複数エリア同時比較
- 季節別データ取得
- 他の予測モデル（LSTM、Prophet）

**UI:**
- レスポンシブデザイン
- ダークモード
- 多言語対応

---

## まとめ

### コードの強み

1. **モジュール性**: 3つのファイルが明確な責務分担
2. **エラー耐性**: 部分的失敗でも動作継続
3. **ユーザー体験**: インタラクティブで直感的
4. **可視化**: 複雑なデータを理解しやすく表示
5. **拡張性**: 新機能追加が容易

### 学習ポイント

1. **Streamlitのセッション管理**
2. **JAXA APIの使用方法**
3. **Matplotlibの高度な可視化**
4. **線形回帰の実践的応用**
5. **大規模データの効率的処理**

---

このドキュメントが、LeafCastプロジェクトの理解を深める助けになれば幸いです！ 🌿
