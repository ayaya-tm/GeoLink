import streamlit as st
from streamlit_folium import st_folium
import folium
from jaxa_api_bk import JaxaDataProvider

st.set_page_config(layout="wide")
st.title("街の履歴書 ～あの日、森が消えた場所～")

START_YEAR = 2002 

if 'jaxa_data_list' not in st.session_state:
    st.session_state.jaxa_data_list = None
if 'last_bbox_key' not in st.session_state:
    st.session_state.last_bbox_key = ""

st.subheader("① 調査エリアを選択（地図を動かしてください）")

# デフォルトのズームレベルを調整（広めに表示）
m_base = folium.Map(location=[35.68, 139.76], zoom_start=10)

# --- ① 地図表示 ---
output = st_folium(m_base, width=1200, height=500, key="base_map", returned_objects=["bounds"])

# --- ② データ取得ロジック ---
if output and output.get('bounds'):
    b = output['bounds']
    if b.get('_southWest') and b.get('_northEast'):
        sw, ne = b['_southWest'], b['_northEast']
        if sw.get('lng') is not None:
            # BBoxを作成（小数点1桁で丸める）
            current_bbox = [
                round(sw['lng'], 1),
                round(sw['lat'], 1), 
                round(ne['lng'], 1), 
                round(ne['lat'], 1)
            ]
            bbox_key = str(current_bbox)

            # サイドバーにデバッグ情報を表示
            st.sidebar.write("**現在のBBox:**")
            st.sidebar.code(current_bbox)
            
            width = current_bbox[2] - current_bbox[0]
            height = current_bbox[3] - current_bbox[1]
            st.sidebar.write(f"範囲: {width:.2f}° × {height:.2f}°")

            # BBoxが変わった時だけデータ取得
            if st.session_state.last_bbox_key != bbox_key:
                st.session_state.last_bbox_key = bbox_key
                st.session_state.jaxa_data_list = None
                
                with st.spinner("データを取得中..."):
                    provider = JaxaDataProvider()
                    # 最初は5年分、後で25年に変更可能
                    st.session_state.jaxa_data_list = provider.get_land_cover_images(
                        current_bbox, 
                        START_YEAR,
                        num_years=5  # ここを25に変更すると25年分取得
                    )
                st.rerun()

# --- ③ 表示パート ---
st.markdown("---")
if st.session_state.jaxa_data_list:
    st.subheader("② 衛星観測データ（年次推移）")
    
    # 取得できた画像のインデックスと年のマッピングを作成
    valid_data = []
    for i, img in enumerate(st.session_state.jaxa_data_list):
        if img is not None:
            valid_data.append({
                'year': START_YEAR + i,
                'index': i,
                'image': img
            })
    
    if len(valid_data) > 0:
        st.sidebar.write(f"**取得画像数:** {len(valid_data)}/{len(st.session_state.jaxa_data_list)}")
        
        # 実際に取得できた画像だけでスライダーを作成
        selected_idx = st.select_slider(
            "表示年を選択", 
            options=list(range(len(valid_data))),
            format_func=lambda x: f"{valid_data[x]['year']}年"
        )
        
        # 選択された画像を表示
        selected_data = valid_data[selected_idx]
        st.image(
            selected_data['image'], 
            caption=f"{selected_data['year']}年のNDVIデータ（植生指数）",
            use_container_width=True
        )
        
        # 画像情報を表示
        st.sidebar.write(f"**現在表示中:**")
        st.sidebar.write(f"年: {selected_data['year']}")
        st.sidebar.write(f"サイズ: {selected_data['image'].size}")
        st.sidebar.write(f"モード: {selected_data['image'].mode}")
        
        # 取得できなかった年があれば表示
        missing_years = [START_YEAR + i for i, img in enumerate(st.session_state.jaxa_data_list) if img is None]
        if missing_years:
            st.sidebar.warning(f"取得失敗: {', '.join(map(str, missing_years))}年")
        
        # 凡例の説明
        st.markdown("""
        ### 📊 カラーマップの見方
        - **青色**: 水域
        - **茶色・黄色**: 裸地、低植生（都市部、農地）
        - **黄緑**: 草地
        - **緑色**: 森林、密な植生
        - **濃い緑**: 非常に密な森林
        
        💡 **変化を見る:** スライダーを動かして年次変化を確認してください。
        森林が減少した場所は緑→茶色に変化しています。
        """)
    else:
        st.error("画像データの取得に失敗しました。別のエリアを試してください。")
else:
    st.info("地図を動かすと解析が始まります。")
    st.markdown("""
    ### 使い方
    1. 上の地図をドラッグ・ズームして調査したいエリアを表示
    2. 地図を動かすと自動的にデータ取得が開始されます
    3. スライダーで年を変更して、植生の変化を観察できます
    """)
