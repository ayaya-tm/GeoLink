import streamlit as st
from streamlit_folium import st_folium
import folium
from jaxa_api import JaxaDataProvider

# ページ設定
st.set_page_config(layout="wide")
st.title("街の履歴書 ～あの日、森が消えた場所～")

START_YEAR = 2002

# セッション状態の初期化
if 'jaxa_data_list' not in st.session_state:
    st.session_state.jaxa_data_list = None
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
                round(sw['lng'], 1),
                round(sw['lat'], 1),
                round(ne['lng'], 1),
                round(ne['lat'], 1)
            ]
            bbox_key = str(current_bbox)
            
            # 範囲が変わった時だけ取得
            if st.session_state.last_bbox_key != bbox_key:
                st.session_state.last_bbox_key = bbox_key
                st.session_state.jaxa_data_list = None
                
                with st.spinner("データを取得中..."):
                    provider = JaxaDataProvider()
                    st.session_state.jaxa_data_list = provider.get_land_cover_images(
                        current_bbox,
                        START_YEAR,
                        num_years=23
                    )
                st.rerun()

# 画像表示
st.markdown("---")
if st.session_state.jaxa_data_list:
    st.subheader("② 衛星観測データ")
    
    # 取得成功した画像のみ抽出
    valid_data = []
    for i, img in enumerate(st.session_state.jaxa_data_list):
        if img is not None:
            valid_data.append({
                'year': START_YEAR + i,
                'image': img
            })
    
    if len(valid_data) > 0:
        # スライダー
        selected_idx = st.select_slider(
            "表示年を選択",
            options=list(range(len(valid_data))),
            format_func=lambda x: f"{valid_data[x]['year']}年"
        )
        
        # 画像表示
        selected_data = valid_data[selected_idx]
        st.image(
            selected_data['image'],
            caption=f"{selected_data['year']}年のNDVIデータ",
            use_container_width=True
        )
        
        # 凡例
        st.markdown("""
        ### 📊 カラーマップの見方
        - **青色**: 水域
        - **茶色・黄色**: 裸地、低植生（都市部、農地）
        - **緑色**: 森林、密な植生
        
        💡 スライダーを動かして年次変化を確認できます
        """)
    else:
        st.error("画像の取得に失敗しました")
else:
    st.info("地図を動かすとデータ取得が開始されます")
