import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

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
    # データをNumPy配列に変換
    years_obs = np.array(years).reshape(-1, 1)
    ndvi_obs = np.array(ndvi_values)
    lst_obs = np.array(lst_values)
    
    # 未来予測用の年の配列を作成
    last_year = years[-1]
    years_future = np.array(range(last_year + 1, last_year + 1 + predict_years)).reshape(-1, 1)
    
    # NDVI予測モデル (Year -> NDVI)
    model_ndvi = LinearRegression().fit(years_obs, ndvi_obs)
    ndvi_future = model_ndvi.predict(years_future)
    
    # LST予測モデル (NDVI -> LST)
    model_lst = LinearRegression().fit(ndvi_obs.reshape(-1, 1), lst_obs)
    lst_future = model_lst.predict(ndvi_future.reshape(-1, 1))
    
    # 全期間データの結合
    years_all = np.concatenate([years_obs.flatten(), years_future.flatten()])
    ndvi_all = np.concatenate([ndvi_obs, ndvi_future])
    lst_all = np.concatenate([lst_obs, lst_future])
    
    # グラフ作成
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # NDVIのプロット（左軸）
    obs_len = len(years_obs)
    ax1.plot(years_all[:obs_len], ndvi_all[:obs_len], color='green', marker='o', linewidth=2, markersize=8, label='NDVI (実測値)')
    ax1.plot(years_all[obs_len-1:], ndvi_all[obs_len-1:], color='green', linestyle='--', linewidth=2, marker='o', markersize=6, alpha=0.7, label='NDVI (予測値)')
    ax1.set_xlabel('年', fontsize=12)
    ax1.set_ylabel('NDVI（植生指数）', color='green', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='green')
    ax1.grid(True, which='both', linestyle='--', alpha=0.3)
    
    # LSTのプロット（右軸）
    ax2 = ax1.twinx()
    ax2.plot(years_all[:obs_len], lst_all[:obs_len], color='orangered', marker='s', linewidth=2, markersize=8, label='LST (実測値)')
    ax2.plot(years_all[obs_len-1:], lst_all[obs_len-1:], color='orangered', linestyle='--', linewidth=2, marker='s', markersize=6, alpha=0.7, label='LST (予測値)')
    ax2.set_ylabel('LST 地表面温度 (℃)', color='orangered', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='orangered')
    
    # タイトルと凡例
    ax1.set_title(f'地表面温度（LST）と植生指数（NDVI）の推移と予測 ({start_year}-{years_all[-1]:.0f})', 
                  fontsize=14, fontweight='bold')
    
    # 凡例を統合
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    plt.tight_layout()
    
    return fig

def simulate_greening_effect(years, ndvi_values, lst_values, target_year, increase_rate=0.01):
    """
    来年のNDVIが想定よりX%上昇した場合のLST抑制効果をシミュレーションする
    
    新しい温度感度公式を使用:
    温度感度 = -32.35 × NDVI + 46.10
    ΔT = 温度感度 × ΔNDVI
    """
    # 1. モデルの準備（NDVI予測のみ）
    years_obs = np.array(years).reshape(-1, 1)
    ndvi_obs = np.array(ndvi_values).reshape(-1, 1)
    lst_obs = np.array(lst_values).reshape(-1, 1)

    model_ndvi = LinearRegression().fit(years_obs, ndvi_obs)
    model_lst = LinearRegression().fit(ndvi_obs, lst_obs)

    # 2. 通常の予測（ベースライン）
    base_ndvi = model_ndvi.predict([[target_year]])[0][0]
    base_lst = model_lst.predict([[base_ndvi]])[0][0]

    # 3. 緑化シミュレーション（NDVIを指定%増加）
    sim_ndvi = base_ndvi * (1 + increase_rate)
    
    # 新しい温度感度公式を使用
    # 温度感度 = -32.35 × NDVI + 46.10
    sensitivity = -32.3515 * base_ndvi + 46.1069
    
    # NDVI増加量
    delta_ndvi = sim_ndvi - base_ndvi
    
    # 温度変化を計算（温度感度 × NDVI増加量）
    temp_change_by_formula = sensitivity * delta_ndvi
    
    # シミュレーション後の温度
    sim_lst = base_lst + temp_change_by_formula

    # 4. 変化率の計算
    lst_change_val = sim_lst - base_lst
    lst_change_percent = (lst_change_val / base_lst) * 100

    print(f"--- {target_year}年 緑化シミュレーション ---")
    print(f"想定NDVI: {base_ndvi:.4f} → シミュレーションNDVI: {sim_ndvi:.4f} (+{increase_rate*100}%)")
    print(f"NDVI増加量: {delta_ndvi:.4f}")
    print(f"温度感度: {sensitivity:.4f}℃/NDVI（公式: -32.35 × {base_ndvi:.4f} + 46.10）")
    print(f"想定温度: {base_lst:.2f}℃ → シミュレーション温度: {sim_lst:.2f}℃")
    print(f"温度変化: {lst_change_val:.2f}℃ ({lst_change_percent:.2f}%)")
    
    return sim_lst
