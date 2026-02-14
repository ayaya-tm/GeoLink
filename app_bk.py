import streamlit as st
from streamlit_folium import st_folium
import folium
from jaxa_api import JaxaDataProvider
import matplotlib.pyplot as plt
import numpy as np

# ページ設定
st.set_page_config(layout="wide")
st.title("街の履歴書 ～あの日、森が消えた場所～")

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
        
        # 折れ線グラフ作成
        st.markdown("---")
        st.subheader("③ 数値データの比較")
        
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
        
        # 折れ線グラフを描画（1つのグラフに統合）
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # LST折れ線グラフ（左軸）
        color1 = 'orangered'
        ax1.set_xlabel('年', fontsize=12)
        ax1.set_ylabel('LST平均値 (℃)', color=color1, fontsize=12)
        line1 = ax1.plot(years, lst_values, color=color1, marker='o', linewidth=2, markersize=8, label='LST（地表面温度）')
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.grid(alpha=0.3)
        
        # NDVI折れ線グラフ（右軸）
        ax2 = ax1.twinx()
        color2 = 'green'
        ax2.set_ylabel('NDVI平均値', color=color2, fontsize=12)
        line2 = ax2.plot(years, ndvi_values, color=color2, marker='s', linewidth=2, markersize=8, label='NDVI（植生指数）')
        ax2.tick_params(axis='y', labelcolor=color2)
        
        # タイトルと凡例
        ax1.set_title('地表面温度（LST）と植生指数（NDVI）の推移', fontsize=14, fontweight='bold')
        
        # 凡例を統合
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=10)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # 凡例
        st.markdown("""
        ### 📊 データの見方
        
        **LST (Land Surface Temperature / 地表面温度)**
        - 温度が高いほど地表が熱い
        - 都市化が進むとヒートアイランド現象により上昇傾向
        
        **NDVI (Normalized Difference Vegetation Index / 植生指数)**
        - 値が高いほど植生が豊か（-1～1の範囲）
        - 森林伐採や都市化により減少傾向
        
        💡 スライダーを動かして年次変化を確認できます
        """)
    else:
        st.error("画像の取得に失敗しました")
else:
    st.info("地図を動かすとデータ取得が開始されます")