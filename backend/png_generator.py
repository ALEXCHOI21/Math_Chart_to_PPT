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
        분석된 데이터를 바탕으로 고품질 수학 그래프 PNG 생성 (투명 배경)
        """
        # 폰트 및 스타일 설정
        plt.rcParams['mathtext.fontset'] = 'cm' # Computer Modern (LaTeX 스타일)
        
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.patch.set_alpha(0.0)
        fig.patch.set_alpha(0.0)
        
        # 1. 축 설정 (화살표 포함)
        axes_data = data.get("axes", {})
        x_min, x_max = axes_data.get("x_range", [-5, 5])
        y_min, y_max = axes_data.get("y_range", [-5, 5])
        
        # 축 선 그리기
        ax.annotate('', xy=(x_max, 0), xytext=(x_min, 0),
                    arrowprops=dict(arrowstyle="->", color='black', lw=2))
        ax.annotate('', xy=(0, y_max), xytext=(0, y_min),
                    arrowprops=dict(arrowstyle="->", color='black', lw=2))
        
        # 원점 및 축 라벨
        ax.text(-0.3, -0.3, axes_data.get("origin_label", "O"), fontsize=16, fontweight='bold', fontstyle='italic')
        ax.text(x_max - 0.2, -0.5, axes_data.get("x_label", "x"), fontsize=16, fontstyle='italic')
        ax.text(-0.5, y_max - 0.2, axes_data.get("y_label", "y"), fontsize=16, fontstyle='italic')

        # 2. 곡선 그리기
        for curve in data.get("curves", []):
            points = np.array(curve.get("points", []))
            if len(points) > 1:
                color = "black" # 전문가용은 검은색이 기본
                style = "-" if curve.get("style") != "dashed" else "--"
                lw = curve.get("width", 2.5)
                ax.plot(points[:, 0], points[:, 1], color=color, linestyle=style, linewidth=lw, zorder=3)

        # 3. 점 및 가이드 라인 (점선)
        for pt in data.get("points", []):
            px, py = pt.get("x", 0), pt.get("y", 0)
            pt_type = pt.get("type", "solid")
            
            # 가이드 점선
            if pt.get("show_dashed_lines", True):
                ax.plot([px, px], [0, py], color='gray', linestyle=':', linewidth=1, zorder=1)
                ax.plot([0, px], [py, py], color='gray', linestyle=':', linewidth=1, zorder=1)
            
            # 점 렌더링
            if pt_type == "hollow":
                ax.plot(px, py, 'o', markerfacecolor='white', markeredgecolor='black', markersize=8, markeredgewidth=1.5, zorder=5)
            else:
                ax.plot(px, py, 'o', color='black', markersize=8, zorder=5)
            
            # 점 라벨
            if pt.get("label"):
                ax.text(px + 0.2, py + 0.2, pt["label"], fontsize=14)

        # 4. 추가 텍스트/LaTeX 라벨
        for label in data.get("labels", []):
            lx, ly = label.get("pos", [0, 0])
            text = label.get("text", "")
            if label.get("is_latex") and text:
                # 이미 $가 있으면 그대로 사용, 없으면 감쌈
                if not text.startswith("$"):
                    text = f"${text}$"
            ax.text(lx, ly, text, fontsize=15, zorder=6)

        # 최종 스타일링
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.axis('off')
        
        # 파일 저장
        output_path = os.path.join(self.output_dir, filename.replace(".pptx", ".png").replace(".jpg", ".png"))
        plt.savefig(output_path, transparent=True, dpi=300, bbox_inches='tight', pad_inches=0.2)
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
