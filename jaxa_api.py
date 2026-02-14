from jaxa.earth import je
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from PIL import Image


class JaxaDataProvider:
    """JAXA衛星データ取得クラス"""
    def get_data_array(self, bbox, coll, band , start_year, num_years=5):
        """
        指定範囲のNDVI画像を取得
        
        Args:
            bbox (list): [西経度, 南緯度, 東経度, 北緯度]
            start_year (int): 開始年
            num_years (int): 取得年数
        
        Returns:
            list: PIL.Imageのリスト（取得失敗時はNone）
        """
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
                    images.append(pil_img)
                    
                    #数値データの保存
                    number_datas.append(data.raster.img[0])
                    # メモリ解放
                    plt.close(fig)
                else:
                    images.append(None)
                    number_datas.append(None)
                    
            except Exception as e:
                print(f"Error {target_year}: {e}")
                images.append(None)
                number_datas.append(None)
                plt.close('all')
        
        return images, number_datas
    
    def get_land_cover_images(self, bbox, start_year, num_years=5):
        images, kelvin_array = self.get_data_array(bbox, coll='NASA.EOSDIS_Terra.MODIS_MOD11C3-LST.daytime.v061_global_monthly', band='LST', start_year=start_year, num_years=num_years)
        celsius_datas = []

        for kelvin_array in kelvin_array:
            if kelvin_array is not None:
                celsius_array = kelvin_array - 273.15
                celsius_datas.append(celsius_array)
            else:
                celsius_datas.append(None)
        
        return images, celsius_datas
        return images, celsius
    def get_ndvi_images(self, bbox, start_year, num_years=5):
        return self.get_data_array(bbox, coll='JAXA.JASMES_Terra.MODIS-Aqua.MODIS_ndvi.v811_global_monthly', band='ndvi', start_year=start_year, num_years=num_years)