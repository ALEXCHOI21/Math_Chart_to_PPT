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
        GRAY   = '#bbbbbb'
        LW_AX  = 1.5   # Professional thin axes
        LW_CRV = 2.5   # Elegant curve thickness
        LW_DSH = 1.0   # Delicate dashed lines
        FS     = 18    # Standard academic font size (Increased)

        # ── 1. 축 범위 설정 ──────────────────────────────────────
        axes_data = data.get("axes", {})
        x_min, x_max = axes_data.get("x_range", [-1, 5])
        y_min, y_max = axes_data.get("y_range", [-1, 4])

        # Padding for aesthetic breathing room
        x_pad = (x_max - x_min) * 0.1
        y_pad = (y_max - y_min) * 0.1

        # ── 2. x축 · y축 화살표 (Fancy arrowheads) ────────────────────────
        ax.annotate('', xy=(x_max + x_pad*0.2, 0), xytext=(x_min, 0),
                    arrowprops=dict(arrowstyle="-|>", color=WHITE, lw=LW_AX, mutation_scale=15))
        ax.annotate('', xy=(0, y_max + y_pad*0.2), xytext=(0, y_min),
                    arrowprops=dict(arrowstyle="-|>", color=WHITE, lw=LW_AX, mutation_scale=15))

        # ── 3. 원점 · 축 끝 라벨 ────────────────────────────────
        ox = axes_data.get("origin_label", "O")
        xl = axes_data.get("x_label", "x")
        yl = axes_data.get("y_label", "y")

        # Normalize labels
        if xl and len(set(xl)) == 1 and len(xl) > 1: xl = xl[0]
        if yl and len(set(yl)) == 1 and len(yl) > 1: yl = yl[0]

        label_offset_x = (x_max - x_min) * 0.03
        label_offset_y = (y_max - y_min) * 0.03

        ax.text(x_max + x_pad*0.1, -label_offset_y*1.5, f"${xl}$", fontsize=FS+2, color=WHITE, ha='center', fontweight='bold')
        ax.text(-label_offset_x*1.5, y_max + y_pad*0.1, f"${yl}$", fontsize=FS+2, color=WHITE, va='center', fontweight='bold')
        ax.text(-label_offset_x, -label_offset_y, f"${ox}$", fontsize=FS, color=WHITE, ha='right', va='top')

        # ── 4. 그래프 곡선 (Parametric Spline Smoothing) ────────────────
        from scipy.interpolate import make_interp_spline
        
        for curve in data.get("curves", []):
            pts = np.array(curve.get("points", []))
            if len(pts) < 2: continue
            
            style = "--" if curve.get("style") == "dashed" else "-"
            # Premium color palette (Force WHITE for all non-dashed curves)
            curve_color = WHITE if curve.get("style") != "dashed" else GRAY
            lw = curve.get("width", LW_CRV)
            
            if len(pts) >= 3:
                try:
                    # Parametric interpolation handles all curve shapes smoothly
                    t = np.linspace(0, 1, len(pts))
                    t_new = np.linspace(0, 1, 400)
                    k = min(3, len(pts) - 1)
                    spl_x = make_interp_spline(t, pts[:, 0], k=k)(t_new)
                    spl_y = make_interp_spline(t, pts[:, 1], k=k)(t_new)
                    
                    # Premium glow effect (subtle)
                    ax.plot(spl_x, spl_y, color=curve_color, linewidth=lw+2, alpha=0.1, zorder=3)
                    ax.plot(spl_x, spl_y, color=curve_color, linestyle=style, linewidth=lw, solid_capstyle='round', zorder=4)
                except Exception as e:
                    ax.plot(pts[:, 0], pts[:, 1], color=curve_color, linestyle=style, linewidth=lw, solid_capstyle='round', zorder=4)
            else:
                ax.plot(pts[:, 0], pts[:, 1], color=curve_color, linestyle=style, linewidth=lw, solid_capstyle='round', zorder=4)

        # ── 5. 점선 (dashed_lines) ───────────────────────────────
        for dl in data.get("dashed_lines", []):
            dl_type = dl.get("type", "")
            val = dl.get("val")
            if dl_type == "horizontal":
                y_val = val if val is not None else dl.get("y", 0)
                x_start = dl.get("x_start", 0)
                x_end = dl.get("x_end", x_max)
                ax.plot([x_start, x_end], [y_val, y_val], color='#999999', linestyle=':', linewidth=LW_DSH, zorder=2)
            elif dl_type == "vertical":
                x_val = val if val is not None else dl.get("x", 0)
                y_start = dl.get("y_start", 0)
                y_end = dl.get("y_end", y_max)
                ax.plot([x_val, x_val], [y_start, y_end], color='#999999', linestyle=':', linewidth=LW_DSH, zorder=2)

        # ── 6. 특수점 (hollow / filled) ──────────────────────────
        for pt in data.get("points", []):
            px, py  = pt.get("x", 0), pt.get("y", 0)
            pt_type = pt.get("type", "filled")
            color = pt.get("color", WHITE)

            if pt_type == "hollow":
                ax.scatter(px, py, facecolors='black', edgecolors=color, s=120, linewidth=2.5, zorder=6)
            else:
                ax.scatter(px, py, color=color, s=120, zorder=6)

        # ── 7. 라벨 처리 (labels) ─────────────────────────────
        import matplotlib.patheffects as PathEffects
        outline = [PathEffects.withStroke(linewidth=3, foreground="#1e1e23")]
        
        # 'labels'와 'axis_labels'(하위호환) 모두 지원
        all_labels = data.get("labels", []) + data.get("axis_labels", [])
        for lb in all_labels:
            pos = lb.get("pos", [0, 0])
            text = lb.get("text", "")
            color = lb.get("color", WHITE)
            if not text: continue
            
            txt_obj = ax.text(pos[0], pos[1], f"${text}$",
                    fontsize=FS+2, color=color,
                    ha='center', va='center', zorder=7)
            txt_obj.set_path_effects(outline)

        # ── 8. 극한 화살표 (곡선형 화살표 고도화) ─────────────────────
        for arr in data.get("arrows", []):
            fx, fy = arr.get("from", [0, 0])
            tx, ty = arr.get("to",   [0, 0])
            is_curved = arr.get("is_curved", False)
            curve_pts = arr.get("points", [])

            if is_curved and len(curve_pts) >= 3:
                try:
                    from scipy.interpolate import make_interp_spline
                    pts = np.array(curve_pts)
                    t = np.linspace(0, 1, len(pts))
                    t_new = np.linspace(0, 1, 100)
                    spl_x = make_interp_spline(t, pts[:, 0], k=min(3, len(pts)-1))(t_new)
                    spl_y = make_interp_spline(t, pts[:, 1], k=min(3, len(pts)-1))(t_new)
                    
                    arrow_color = arr.get("color", "#CCCCCC")
                    # 곡선 경로
                    ax.plot(spl_x, spl_y, color=arrow_color, linewidth=1.5, zorder=4)
                    
                    # 화살표 머리 (끝부분 곡률에 맞춤)
                    idx = -1
                    ax.annotate('', xy=(spl_x[idx], spl_y[idx]), 
                                xytext=(spl_x[idx-5], spl_y[idx-5]),
                                arrowprops=dict(arrowstyle="-|>", color=arrow_color, 
                                                lw=1.5, mutation_scale=12),
                                zorder=4)
                except:
                    ax.annotate('', xy=(tx, ty), xytext=(fx, fy),
                                arrowprops=dict(arrowstyle="-|>", color="#CCCCCC", lw=1.5),
                                zorder=4)
            else:
                arrow_color = arr.get("color", WHITE)
                ax.annotate('', xy=(tx, ty), xytext=(fx, fy),
                            arrowprops=dict(arrowstyle="-|>", color=arrow_color, lw=1.5),
                            zorder=4)

        # ── 9. 수식/텍스트 라벨 ─────────────────────────────────
        for label in data.get("labels", []):
            lx, ly = label.get("pos", [0, 0])
            text   = label.get("text", "")
            if not text: continue
            
            # LaTeX 수식 자동 변환 ($ 추가)
            if any(c in text for c in ['=', '(', ')', '^', '_']):
                text = f"${text}$"
                
            txt_obj = ax.text(lx, ly, text,
                    fontsize=FS+4, color=WHITE,
                    fontweight='bold', zorder=6)
            # Remove outline for cleaner look on black background
            # txt_obj.set_path_effects(outline)

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
                    bbox_inches='tight', pad_inches=0.1)
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
