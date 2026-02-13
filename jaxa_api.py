from jaxa.earth import je
import numpy as np
import PIL.Image
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import io

class JaxaDataProvider:
    def get_land_cover_images(self, bbox, start_year, num_years=5):
        """
        指定された範囲のNDVI画像を取得（JAXAのデフォルトカラーマップ適用済み）
        
        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            start_year: 開始年
            num_years: 取得する年数（デフォルト5年）
        
        Returns:
            PIL.Image のリスト（カラーマップ適用済み）
        """
        results = []
        
        for i in range(num_years):
            target_year = start_year + i
            dlim = [f"{target_year}-01-01T00:00:00", f"{target_year}-01-01T23:59:59"]
            ppu = 20

            print(f"\n{'='*60}")
            print(f"📡 {target_year}年のデータを取得中...")
            print(f"{'='*60}")
            
            try:
                data = je.ImageCollection(
                    collection="JAXA.JASMES_Terra.MODIS-Aqua.MODIS_ndvi.v811_global_monthly", 
                    ssl_verify=True
                ).filter_date(dlim=dlim)\
                    .filter_resolution(ppu=ppu)\
                    .filter_bounds(bbox=bbox)\
                    .select(band="ndvi")\
                    .get_images()
                
                if data:
                    # ✅ show_images() でカラーマップ適用済みの画像を生成
                    je.ImageProcess(data).show_images()
                    
                    # matplotlibのfigureから画像をキャプチャ
                    fig = plt.gcf()
                    
                    # バッファに保存
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
                    buf.seek(0)
                    
                    # PIL Imageとして読み込み
                    pil_img = PIL.Image.open(buf).copy()  # .copy()でバッファから独立させる
                    
                    results.append(pil_img)
                    print(f"  ✅ 成功: {pil_img.size} (W x H), mode={pil_img.mode}")
                    
                    # figureをクローズして次の画像のために準備
                    plt.close(fig)
                    
                else:
                    print(f"  ⚠️ データが取得できませんでした")
                    results.append(None)
                    
            except Exception as e:
                print(f"  ❌ エラー: {e}")
                import traceback
                traceback.print_exc()
                results.append(None)
                plt.close('all')  # エラー時もfigureをクローズ

        print(f"\n{'='*60}")
        print(f"✅ 完了: {len([r for r in results if r is not None])}/{len(results)} 件取得成功")
        print(f"{'='*60}\n")
        
        return results
