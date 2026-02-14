import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# 1. データの準備（実測値）
years_obs = np.array(range(2002, 2023)).reshape(-1, 1)
ndvi_obs = np.array([0.5516, 0.5351, 0.5679, 0.5206, 0.4995, 0.5586, 0.5478, 0.5805, 0.5360, 0.5328, 0.5418, 0.5749, 0.5860, 0.5757, 0.6066, 0.5795, 0.6013, 0.5586, 0.5900, 0.6016, 0.6031])
lst_obs = np.array([17.9276, 16.9919, 19.3214, 19.1023, 15.1357, 16.0208, 17.5013, 19.5333, 15.4234, 18.1445, 16.5340, 17.1862, 18.6662, 19.3501, 18.4579, 17.6306, 20.6522, 16.9261, 17.0279, 18.5783, 19.0695])

# 2. モデルの作成と未来予測（2023-2042）
years_future = np.array(range(2023, 2043)).reshape(-1, 1)

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

# 3. グラフ作成
fig, ax1 = plt.subplots(figsize=(12, 6))

# NDVIのプロット（左軸）
ax1.plot(years_all[:21], ndvi_all[:21], color='green', marker='o', label='NDVI (Observed)')
ax1.plot(years_all[20:], ndvi_all[20:], color='green', linestyle='--', label='NDVI (Predicted)')
ax1.set_xlabel('Year')
ax1.set_ylabel('NDVI', color='green')
ax1.tick_params(axis='y', labelcolor='green')
ax1.grid(True, which='both', linestyle='--', alpha=0.5)

# LSTのプロット（右軸）
ax2 = ax1.twinx()
ax2.plot(years_all[:21], lst_all[:21], color='red', marker='s', label='LST (Observed)')
ax2.plot(years_all[20:], lst_all[20:], color='red', linestyle='--', label='LST (Predicted)')
ax2.set_ylabel('LST (°C)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# 仕上げ
plt.title('40-Year Trend & Forecast: NDVI and LST (2002-2042)')
fig.tight_layout()
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')

plt.show()