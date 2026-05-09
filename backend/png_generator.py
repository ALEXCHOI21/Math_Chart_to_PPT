import matplotlib
matplotlib.use('Agg')  # GUI 없이 렌더링
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

class PNGGenerator:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_transparent_png(self, data, filename):
        """
        분석된 JSON 데이터를 바탕으로 고품질 수학 그래프 PNG 생성
        - 배경: 투명
        - 색상: 흰색 (다크 슬라이드 최적화)
        - 지원: 곡선, 점선, 특수점, 축 라벨, 극한 화살표
        """
        plt.rcParams['mathtext.fontset'] = 'cm'  # LaTeX 스타일 폰트

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.patch.set_alpha(0.0)
        fig.patch.set_alpha(0.0)

        WHITE  = 'white'
        GRAY   = '#aaaaaa'
        LW_AX  = 2.0   # 축 선 굵기
        LW_CRV = 2.5   # 곡선 굵기
        LW_DSH = 1.2   # 점선 굵기
        FS     = 16    # 기본 폰트 크기

        # ── 1. 축 범위 설정 ──────────────────────────────────────
        axes_data = data.get("axes", {})
        x_min, x_max = axes_data.get("x_range", [-1, 5])
        y_min, y_max = axes_data.get("y_range", [-1, 4])

        # 축 여백 확보
        x_pad = (x_max - x_min) * 0.08
        y_pad = (y_max - y_min) * 0.08

        # ── 2. x축 · y축 화살표 ──────────────────────────────────
        ax.annotate('', xy=(x_max, 0), xytext=(x_min, 0),
                    arrowprops=dict(arrowstyle="->", color=WHITE, lw=LW_AX))
        ax.annotate('', xy=(0, y_max), xytext=(0, y_min),
                    arrowprops=dict(arrowstyle="->", color=WHITE, lw=LW_AX))

        # ── 3. 원점 · 축 끝 라벨 ────────────────────────────────
        ox = axes_data.get("origin_label", "O")
        xl = axes_data.get("x_label", "x")
        yl = axes_data.get("y_label", "y")

        label_offset_x = (x_max - x_min) * 0.04
        label_offset_y = (y_max - y_min) * 0.04

        ax.text(-label_offset_x * 1.5, -label_offset_y * 1.5,
                ox, fontsize=FS, fontstyle='italic', color=WHITE, ha='right', va='top')
        ax.text(x_max - label_offset_x, -label_offset_y * 1.8,
                xl, fontsize=FS, fontstyle='italic', color=WHITE)
        ax.text(-label_offset_x * 1.8, y_max - label_offset_y,
                yl, fontsize=FS, fontstyle='italic', color=WHITE)

        # ── 4. 곡선 그리기 ───────────────────────────────────────
        for curve in data.get("curves", []):
            pts = curve.get("points", [])
            if len(pts) < 2:
                continue
            pts = np.array(pts)
            style = "--" if curve.get("style") == "dashed" else "-"
            lw    = curve.get("width", LW_CRV)
            ax.plot(pts[:, 0], pts[:, 1],
                    color=WHITE, linestyle=style, linewidth=lw,
                    solid_capstyle='round', zorder=3)

        # ── 5. 점선 (dashed_lines) ───────────────────────────────
        for dl in data.get("dashed_lines", []):
            dl_type = dl.get("type", "")
            if dl_type == "horizontal":
                y_val   = dl.get("y", 0)
                x_start = dl.get("x_start", x_min)
                x_end   = dl.get("x_end", x_max)
                ax.plot([x_start, x_end], [y_val, y_val],
                        color=GRAY, linestyle='--', linewidth=LW_DSH, zorder=1)
            elif dl_type == "vertical":
                x_val   = dl.get("x", 0)
                y_start = dl.get("y_start", y_min)
                y_end   = dl.get("y_end", y_max)
                ax.plot([x_val, x_val], [y_start, y_end],
                        color=GRAY, linestyle='--', linewidth=LW_DSH, zorder=1)

        # ── 6. 특수점 (hollow / filled) ──────────────────────────
        for pt in data.get("points", []):
            px, py  = pt.get("x", 0), pt.get("y", 0)
            pt_type = pt.get("type", "filled")

            # 구형 방식 점선 폴백 (dashed_lines 없을 때)
            if pt.get("show_dashed_lines", False) and not data.get("dashed_lines"):
                ax.plot([px, px], [0, py], color=GRAY, linestyle='--', linewidth=LW_DSH, zorder=1)
                ax.plot([0, px], [py, py], color=GRAY, linestyle='--', linewidth=LW_DSH, zorder=1)

            if pt_type == "hollow":
                ax.plot(px, py, 'o',
                        markerfacecolor='none', markeredgecolor=WHITE,
                        markersize=9, markeredgewidth=2.0, zorder=5)
            else:
                ax.plot(px, py, 'o', color=WHITE, markersize=9, zorder=5)

        # ── 7. 축 값 라벨 (L, a 등) ─────────────────────────────
        for al in data.get("axis_labels", []):
            tx, ty = al.get("pos", [0, 0])
            text   = al.get("text", "")
            ax.text(tx, ty, text,
                    fontsize=FS, fontstyle='italic', color=WHITE,
                    ha='center', va='center', zorder=6)

        # ── 8. 극한 화살표 (x→a 등) ─────────────────────────────
        for arr in data.get("arrows", []):
            fx, fy = arr.get("from", [0, 0])
            tx, ty = arr.get("to",   [0, 0])
            ax.annotate('', xy=(tx, ty), xytext=(fx, fy),
                        arrowprops=dict(arrowstyle="->", color=WHITE, lw=1.5),
                        zorder=4)

        # ── 9. 수식/텍스트 라벨 ─────────────────────────────────
        for label in data.get("labels", []):
            lx, ly = label.get("pos", [0, 0])
            text   = label.get("text", "")
            if label.get("is_latex") and text and not text.startswith("$"):
                text = f"${text}$"
            ax.text(lx, ly, text,
                    fontsize=FS, color=WHITE, zorder=6)

        # ── 10. 최종 저장 ────────────────────────────────────────
        ax.set_xlim(x_min - x_pad, x_max + x_pad)
        ax.set_ylim(y_min - y_pad, y_max + y_pad)
        ax.axis('off')

        out_name = (filename
                    .replace(".pptx", ".png")
                    .replace(".jpg",  ".png")
                    .replace(".jpeg", ".png"))
        output_path = os.path.join(self.output_dir, out_name)
        plt.savefig(output_path, transparent=True, dpi=300,
                    bbox_inches='tight', pad_inches=0.25)
        plt.close(fig)
        return output_path


if __name__ == "__main__":
    # 간단 렌더링 테스트
    gen = PNGGenerator("output")
    test_data = {
        "axes": {"x_range": [-1, 5], "y_range": [-1, 4],
                 "origin_label": "O", "x_label": "x", "y_label": "y"},
        "curves": [{"points": [[-0.5, -1.5],[0,0],[1,0.8],[2,1.5],[3,2.1],[4,2.6],[5,3.0]], "style": "solid"}],
        "dashed_lines": [
            {"type": "horizontal", "y": 2.1, "x_start": 0, "x_end": 3.2},
            {"type": "vertical",   "x": 3.2, "y_start": 0, "y_end": 2.1}
        ],
        "points": [{"x": 3.2, "y": 2.1, "type": "hollow"}],
        "axis_labels": [
            {"text": "L", "pos": [-0.3, 2.1]},
            {"text": "a", "pos": [3.2, -0.3]}
        ],
        "arrows": [
            {"from": [1.5, 0.08], "to": [3.0, 0.08]},
            {"from": [4.5, 0.08], "to": [3.4, 0.08]}
        ],
        "labels": [{"text": "y=f(x)", "pos": [4.2, 2.8], "is_latex": False}]
    }
    path = gen.generate_transparent_png(test_data, "test_render.png")
    print(f"✅ 테스트 완료: {path}")
