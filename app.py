import streamlit as st
from streamlit_folium import st_folium
import folium
from jaxa_api import JaxaDataProvider
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from future_prefiction import create_future_prediction_graph, simulate_greening_effect

# ページ設定
st.set_page_config(layout="wide")
st.title("～LeafCast：未来地表温度予測～")
st.subheader("23年間の緑地指数と地表面温度から未来の数値を予測する")

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

# 地図表示
st.subheader("① 調査エリアを選択")
m_base = folium.Map(location=[35.68, 139.76], zoom_start=10)
output = st_folium(m_base, width=1200, height=500, key="base_map", returned_objects=["bounds"])

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
                
                with st.spinner("データを取得中..."):
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

# 画像表示
st.markdown("---")
if st.session_state.lst_images and st.session_state.ndvi_images:
    st.subheader("② 衛星観測データ")
    
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
        # スライダー
        selected_idx = st.select_slider(
            "表示年を選択",
            options=list(range(len(valid_data))),
            format_func=lambda x: f"{valid_data[x]['year']}年"
        )
        
        # 選択されたデータ
        selected_data = valid_data[selected_idx]
        
        # 画像を上下に並べて表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(
                selected_data['lst_image'],
                caption=f"{selected_data['year']}年のLSTデータ（地表面温度）",
                use_container_width=True
            )
        
        with col2:
            st.image(
                selected_data['ndvi_image'],
                caption=f"{selected_data['year']}年のNDVIデータ（植生指数）",
                use_container_width=True
            )
        
        # 折れ線グラフ作成（未来予測付き）
        st.markdown("---")
        st.subheader("③ 数値データの比較と未来予測")
        
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
        
        # 未来予測グラフを生成
        fig = create_future_prediction_graph(years, ndvi_values, lst_values, START_YEAR, predict_years=20)
        st.pyplot(fig)
        
        # データテーブル表示
        st.markdown("---")
        st.subheader("④ 観測データ一覧")
        
        # DataFrameの作成
        df = pd.DataFrame({
            '年': years,
            'NDVI（植生指数）': [f"{v:.4f}" for v in ndvi_values],
            'LST（地表面温度 ℃）': [f"{v:.2f}" for v in lst_values]
        })
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 緑化シミュレーション
        st.markdown("---")
        st.subheader("⑤ 緑化シミュレーション")
        
        st.markdown("""
        ### 🌳 緑化による温度抑制効果の予測
        
        NDVIを数%向上させた場合、地表面温度（LST）がどの程度抑制されるかをシミュレーションします。
        """)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # シミュレーション設定
            target_year = st.number_input(
                "シミュレーション対象年",
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
        
        with col2:
            if st.button("シミュレーション実行", type="primary"):
                st.markdown("#### シミュレーション結果")
                
                # シミュレーション実行
                from sklearn.linear_model import LinearRegression
                
                years_obs = np.array(years).reshape(-1, 1)
                ndvi_obs = np.array(ndvi_values).reshape(-1, 1)
                lst_obs = np.array(lst_values).reshape(-1, 1)
                
                model_ndvi = LinearRegression().fit(years_obs, ndvi_obs)
                model_lst = LinearRegression().fit(ndvi_obs, lst_obs)
                
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
                    '項目': ['通常予測', '緑化シミュレーション', '変化量'],
                    'NDVI': [
                        f"{base_ndvi:.4f}",
                        f"{sim_ndvi:.4f} (+{increase_rate*100:.0f}%)",
                        f"+{sim_ndvi - base_ndvi:.4f}"
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
                else:
                    st.info(f"ℹ️ このシミュレーションでは温度抑制効果が見られませんでした。")
        
        # 計算式の説明
        st.markdown("---")
        st.subheader("📐 予測モデルの計算式")
        
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
        - ⚠️ **注意**: 線形回帰は過去のトレンドが将来も継続することを仮定しています
        - ⚠️ **限界**: 急激な都市開発や気候変動など、非線形な変化は考慮されません
        - 💡 **推奨**: あくまで参考値として、複数のシナリオを検討することが重要です
        """)
        
        # 凡例
        st.markdown("---")
        st.markdown("""
        ### 📊 データの見方
        
        **LST (Land Surface Temperature / 地表面温度)**
        - 温度が高いほど地表が熱い
        - 都市化が進むとヒートアイランド現象により上昇傾向
        
        **NDVI (Normalized Difference Vegetation Index / 植生指数)**
        - 値が高いほど植生が豊か（-1～1の範囲）
        - 森林伐採や都市化により減少傾向
        
        **予測について**
        - 実線：実測値（衛星データから取得）
        - 破線：予測値（線形回帰モデルによる推定）
        - 予測は過去のトレンドを基に計算されています
        
        💡 スライダーを動かして年次変化を確認できます
        """)
    else:
        st.error("画像の取得に失敗しました")
else:
    st.info("地図を動かすとデータ取得が開始されます")