import matplotlib.pyplot as plt
import numpy as np
import os

class PNGGenerator:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_transparent_png(self, data, filename):
        """
        분석된 데이터를 바탕으로 투명 배경 PNG 생성
        """
        # Matplotlib 설정
        plt.figure(figsize=(10, 6))
        ax = plt.gca()
        ax.patch.set_alpha(0.0) # 축 배경 투명
        plt.gcf().patch.set_alpha(0.0) # 피규어 배경 투명
        
        # 1. 축 그리기
        axes_data = data.get("axes", {})
        x_min, x_max = axes_data.get("x_range", [-10, 10])
        y_min, y_max = axes_data.get("y_range", [-10, 10])
        
        plt.axhline(0, color='white', linewidth=1.5)
        plt.axvline(0, color='white', linewidth=1.5)
        
        # 2. 곡선 그리기
        for curve in data.get("curves", []):
            points = np.array(curve.get("points", []))
            if len(points) > 1:
                color = curve.get("color", "cyan")
                style = "-" if curve.get("style") != "dashed" else "--"
                plt.plot(points[:, 0], points[:, 1], color=color, linestyle=style, linewidth=2.5)

        # 3. 점 및 라벨
        for point in data.get("points", []):
            px = point.get("x") or (point.get("coord", [0, 0])[0])
            py = point.get("y") or (point.get("coord", [0, 0])[1])
            plt.plot(px, py, 'o', color='yellow', markersize=8)
            
        for label in data.get("labels", []):
            lx = label.get("x") or (label.get("pos", [0, 0])[0])
            ly = label.get("y") or (label.get("pos", [0, 0])[1])
            plt.text(lx, ly, label.get("text", ""), color='white', fontsize=12, fontweight='bold')

        # 스타일링
        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)
        plt.axis('off') # 기본 축 숨기기 (직접 그렸으므로)
        
        output_path = os.path.join(self.output_dir, filename.replace(".pptx", ".png").replace(".jpg", ".png"))
        plt.savefig(output_path, transparent=True, dpi=300, bbox_inches='tight', pad_inches=0.1)
        plt.close()
        return output_path

if __name__ == "__main__":
    # 간단한 테스트용
    gen = PNGGenerator()
    test_data = {
        "axes": {"x_range": [-5, 5], "y_range": [-5, 5]},
        "curves": [{"points": [[-5, 25], [0, 0], [5, 25]], "color": "cyan"}]
    }
    gen.generate_transparent_png(test_data, "test_render.png")
