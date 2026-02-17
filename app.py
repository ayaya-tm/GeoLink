import streamlit as st
from streamlit_folium import st_folium
import folium
from jaxa_api import JaxaDataProvider
import numpy as np
import pandas as pd
from future_prefiction import create_future_prediction_graph, simulate_greening_effect

# ページ設定
st.set_page_config(
    page_title="LeafCast - 未来地表温度予測",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2e7d32;
        text-align: left;
        padding: 1rem 0;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: left;
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

# ヘッダー
st.markdown('<div class="main-header">🌿 LeafCast：未来地表温度予測 🌍</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">23年間の緑地指数と地表面温度から未来の数値を予測する</div>', unsafe_allow_html=True)

START_YEAR = 2002

# セッション状態の初期化
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

# step1: 地図表示
st.markdown("---")
st.markdown("### 📍 step1：調査エリアを選択")
st.markdown("地図を操作して、調査エリアを表示してください。")


m_base = folium.Map(location=[33.66, 130.42], zoom_start=8)
output = st_folium(m_base, width=700, height=525, key="base_map", returned_objects=["bounds"])
# データ取得
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
                        num_years=23
                    )
                    # NDVIデータ取得
                    st.session_state.ndvi_images, st.session_state.ndvi_number_datas = provider.get_ndvi_images(
                        current_bbox,
                        START_YEAR,
                        num_years=23
                    )
                st.rerun()

# 画像表示
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
    
    if len(valid_data) > 0:
        # step2: 衛星データ表示
        st.markdown("---")
        st.markdown("### 🛰️ step2：衛星観測データの確認")
        
        # スライダー
        selected_idx = st.select_slider(
            "📅 表示年を選択してください",
            options=list(range(len(valid_data))),
            format_func=lambda x: f"{valid_data[x]['year']}年"
        )
        
        # 選択されたデータ
        selected_data = valid_data[selected_idx]
        
        # 画像を左右に並べて表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 🌡️ 地表面温度（LST）")
            st.image(
                selected_data['lst_image'],
                caption=f"{selected_data['year']}年4月のLSTデータ",
                use_container_width=True
            )
            st.markdown("""
            <div class="info-box">
            <b>LST (Land Surface Temperature)</b><br>
            温度が高いほど地表が熱く、ヒートアイランド現象の指標となります。
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"#### 🌿 植生指数（NDVI）")
            st.image(
                selected_data['ndvi_image'],
                caption=f"{selected_data['year']}年4月のNDVIデータ",
                use_container_width=True
            )
            st.markdown("""
            <div class="info-box">
            <b>NDVI (Normalized Difference Vegetation Index)</b><br>
            値が高いほど植生が豊かで、緑地の量を表します（0～1の範囲）。
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
                    注釈：取得元の地図と表示される画像の解像度に差分が出ることがありますが  
                    　　　API側の仕様によるもので、画像データ以外は取得元の地図と同じ範囲をカバーしています。
                    """)

        # 折れ線グラフ作成（未来予測付き）
        st.markdown("---")
        st.markdown("### 📊 step3：トレンド分析と未来予測")
        
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
        
        # 未来予測の計算（テーブル用）
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
        
        st.markdown("""
        <div class="warning-box">
        <b>💡 グラフの見方</b><br>
        • <b>実線</b>：過去の観測データ（衛星から取得した実測値）<br>
        • <b>破線</b>：未来予測データ（線形回帰モデルによる推定値）<br>
        • 左軸（緑）：NDVI（植生指数） / 右軸（赤）：LST（地表面温度）
        </div>
        """, unsafe_allow_html=True)
        
        # データテーブル表示
        st.markdown("---")
        st.markdown("### 📋 step4：詳細データ一覧")
        
        # タブで観測データと予測データを分ける
        tab1, tab2, tab3 = st.tabs(["📊 観測データのみ", "🔮 観測 + 予測データ", "📈 統計情報"])
        
        with tab1:
            # 観測データのみ
            df_obs = pd.DataFrame({
                '年': years,
                'NDVI（植生指数）': [f"{v:.4f}" for v in ndvi_values],
                'LST（地表面温度 ℃）': [f"{v:.2f}" for v in lst_values]
            })
            st.dataframe(df_obs, use_container_width=True, hide_index=True)
        
        with tab2:
            # 観測データと予測データを結合
            all_years = years + years_future
            all_ndvi = ndvi_values + ndvi_future
            all_lst = lst_values + lst_future
            data_type = ['✅ 観測'] * len(years) + ['🔮 予測'] * len(years_future)
            
            # DataFrameの作成
            df_all = pd.DataFrame({
                '年': all_years,
                '種別': data_type,
                'NDVI（植生指数）': [f"{v:.4f}" for v in all_ndvi],
                'LST（地表面温度 ℃）': [f"{v:.2f}" for v in all_lst]
            })
            
            st.dataframe(df_all, use_container_width=True, hide_index=True)
            
            st.info("💡 予測データは過去のトレンドを基にした推定値です。実際の値とは異なる可能性があります。")
        
        with tab3:
            # 統計情報
            col_stat1, col_stat2 = st.columns(2)
            
            with col_stat1:
                st.markdown("#### 📉 NDVI統計")
                ndvi_stats = pd.DataFrame({
                    '項目': ['平均値', '最大値', '最小値', '標準偏差'],
                    '観測値': [
                        f"{np.mean(ndvi_values):.4f}",
                        f"{np.max(ndvi_values):.4f}",
                        f"{np.min(ndvi_values):.4f}",
                        f"{np.std(ndvi_values):.4f}"
                    ]
                })
                st.dataframe(ndvi_stats, use_container_width=True, hide_index=True)
            
            with col_stat2:
                st.markdown("#### 🌡️ LST統計")
                lst_stats = pd.DataFrame({
                    '項目': ['平均値（℃）', '最高温度（℃）', '最低温度（℃）', '標準偏差'],
                    '観測値': [
                        f"{np.mean(lst_values):.2f}",
                        f"{np.max(lst_values):.2f}",
                        f"{np.min(lst_values):.2f}",
                        f"{np.std(lst_values):.4f}"
                    ]
                })
                st.dataframe(lst_stats, use_container_width=True, hide_index=True)
        
        # 緑化シミュレーション
        st.markdown("---")
        st.markdown("### 🌳 step5：緑化シミュレーション")
        
        st.markdown("""
        <div class="info-box">
        <b>緑化による温度抑制効果の予測</b><br>
        NDVIを数%向上させた場合、地表面温度（LST）がどの程度抑制されるかをシミュレーションします。
        </div>
        """, unsafe_allow_html=True)
        
        col_sim1, col_sim2 = st.columns([1, 1])
        
        with col_sim1:
            st.markdown("#### ⚙️ シミュレーション設定")
            # シミュレーション設定
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
                # ベースライン（通常予測）の計算
                from sklearn.linear_model import LinearRegression as _LR
                _years_obs = np.array(years).reshape(-1, 1)
                _ndvi_obs = np.array(ndvi_values).reshape(-1, 1)
                _lst_obs = np.array(lst_values).reshape(-1, 1)
                _model_ndvi_tmp = _LR().fit(_years_obs, _ndvi_obs)
                _model_lst_tmp = _LR().fit(_ndvi_obs, _lst_obs)
                base_ndvi = _model_ndvi_tmp.predict([[target_year]])[0][0]
                base_lst = _model_lst_tmp.predict([[base_ndvi]])[0][0]
                sim_ndvi = base_ndvi * (1 + increase_rate)
                
                # simulate_greening_effect() を呼び出してシミュレーション後のLSTを取得
                sim_lst = simulate_greening_effect(
                    years,
                    ndvi_values,
                    lst_values,
                    target_year=int(target_year),
                    increase_rate=increase_rate
                )
                
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
                    'LST（℃）': [
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
                else:
                    st.info(f"ℹ️ このシミュレーションでは温度抑制効果が見られませんでした。")
            else:
                st.info("👈 左側で設定を行い、「シミュレーション実行」ボタンを押してください")
        
        # 技術情報（折りたたみ）
        st.markdown("---")
        with st.expander("📐 予測モデルの詳細と計算式"):
            st.markdown("""
            ### 使用している予測モデル
            
            本アプリケーションでは、**線形回帰モデル（Linear Regression）**を使用して未来予測を行っています。
            
            #### 1. NDVI予測モデル
            ```
            NDVI(年) = α × 年 + β
            ```
            - **α（傾き）**: 年あたりのNDVI変化率
            - **β（切片）**: 基準年におけるNDVI値
            - 過去の観測データから最小二乗法により係数を推定
            
            #### 2. LST予測モデル
            ```
            LST(℃) = γ × NDVI + δ
            ```
            - **γ（傾き）**: NDVIあたりの温度変化率
            - **δ（切片）**: NDVI=0のときの理論温度
            - NDVIとLSTの相関関係から係数を推定
            
            #### 3. 緑化シミュレーション
            ```
            シミュレーションNDVI = 通常予測NDVI × (1 + 向上率)
            シミュレーションLST = γ × シミュレーションNDVI + δ
            温度低減効果 = シミュレーションLST - 通常予測LST
            ```
            
            ### モデルの特徴と注意点
            
            - ✅ **利点**: 過去のトレンドを基にした客観的な予測が可能
            - ⚠️ **注意**: 線形回帰は過去のトレンドが将来も継続することを仮定
            - ⚠️ **限界**: 急激な都市開発や気候変動など、非線形な変化は考慮されません
            - 💡 **推奨**: あくまで参考値として、複数のシナリオを検討することが重要
            """)
        
        with st.expander("📚 用語解説"):
            st.markdown("""
            ### LST (Land Surface Temperature / 地表面温度)
            - 衛星が観測した地表の温度
            - 都市化が進むとヒートアイランド現象により上昇傾向
            - 単位：℃（摂氏）
            
            ### NDVI (Normalized Difference Vegetation Index / 植生指数)
            - 植生の量と活力を示す指標
            - 値が高いほど植生が豊か（-1～1の範囲）
            - 森林伐採や都市化により減少傾向
            - 計算式：NDVI = (近赤外 - 赤) / (近赤外 + 赤)
            
            ### データソース
            - **MODIS**: NASAの地球観測衛星Terra/Aquaに搭載されたセンサー
            - **JAXA**: 宇宙航空研究開発機構が提供する衛星データ
            """)
    
    else:
        st.error("❌ 画像の取得に失敗しました。別のエリアを選択してください。")
else:
    st.markdown("""
    <div class="info-box">
    <b>👆 まずは地図を操作してください</b><br>
    地図を拡大・縮小・移動すると、そのエリアの衛星データ取得が開始されます。<br>
    データ取得には数十秒かかる場合があります。
    </div>
    """, unsafe_allow_html=True)

# フッター
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; padding: 2rem 0;">
    <p>LeafCast - Future Land Surface Temperature Prediction System</p>
    <p>データ提供: JAXA (宇宙航空研究開発機構) / NASA MODIS</p>
</div>
""", unsafe_allow_html=True)