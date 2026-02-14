from jaxa.earth import je
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from PIL import Image


class JaxaDataProvider:
    """JAXA衛星データ取得クラス"""
    
    def get_land_cover_images(self, bbox, start_year, num_years=5):
        """
        指定範囲のNDVI画像を取得
        
        Args:
            bbox (list): [西経度, 南緯度, 東経度, 北緯度]
            start_year (int): 開始年
            num_years (int): 取得年数
        
        Returns:
            list: PIL.Imageのリスト（取得失敗時はNone）
        """
        results = []
        
        for i in range(num_years):
            target_year = start_year + i
            
            try:
                # JAXA APIでデータ取得
                data = je.ImageCollection(
                    collection="JAXA.JASMES_Terra.MODIS-Aqua.MODIS_ndvi.v811_global_monthly",
                    ssl_verify=True
                ).filter_date(
                    dlim=[f"{target_year}-01-01T00:00:00", f"{target_year}-01-01T23:59:59"]
                ).filter_resolution(
                    ppu=20
                ).filter_bounds(
                    bbox=bbox
                ).select(
                    band="ndvi"
                ).get_images()
                
                if data:
                    # カラーマップ適用済み画像を生成
                    je.ImageProcess(data).show_images()
                    
                    # matplotlibのfigureをキャプチャ
                    fig = plt.gcf()
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
                    buf.seek(0)
                    
                    # PIL Imageに変換
                    pil_img = Image.open(buf).copy()
                    results.append(pil_img)
                    
                    # メモリ解放
                    plt.close(fig)
                else:
                    results.append(None)
                    
            except Exception as e:
                print(f"Error {target_year}: {e}")
                results.append(None)
                plt.close('all')
        
        return results
