from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.dml.color import RGBColor
import math

class PPTConverter:
    def __init__(self):
        self.width = Inches(10)
        self.height = Inches(5.625)
        self.center_x = self.width / 2
        self.center_y = self.height / 2
        self.scale = Inches(0.5)  # 1 unit = 0.5 inch

    def create_ppt(self, data, output_path):
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        prs = Presentation()
        # 16:9 비율 설정
        prs.slide_width = self.width
        prs.slide_height = self.height
        
        slide_layout = prs.slide_layouts[6]  # Blank layout
        slide = prs.slides.add_slide(slide_layout)

        # 배경색 (다크 모드)
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(30, 30, 35)

        # 1. 축 그리기 (화살표 포함)
        self._draw_axes(slide, data.get("axes", {}))

        # 2. 곡선 그리기 (Smooth)
        for curve in data.get("curves", []):
            self._draw_curve(slide, curve)

        # 3. 점선 그리기
        for dl in data.get("dashed_lines", []):
            self._draw_dashed_line(slide, dl)

        # 4. 점 그리기
        for point in data.get("points", []):
            self._draw_point(slide, point)

        # 5. 화살표 그리기 (곡선 화살표 지원)
        for arrow in data.get("arrows", []):
            self._draw_arrow(slide, arrow)

        # 6. 라벨 그리기
        for label in data.get("labels", []):
            self._draw_label(slide, label)

        prs.save(output_path)
        return output_path

    def _to_ppt_coords(self, x, y):
        """그래프 좌표를 PPT 슬라이드 좌표로 변환"""
        ppt_x = self.center_x + (x * self.scale)
        ppt_y = self.center_y - (y * self.scale)  # Y축은 위가 양수
        return ppt_x, ppt_y

    def _draw_axes(self, slide, axes):
        x_range = axes.get("x_range", [-5, 5])
        y_range = axes.get("y_range", [-5, 5])
        
        # X축 (Professional thin line)
        sx, sy = self._to_ppt_coords(x_range[0], 0)
        ex, ey = self._to_ppt_coords(x_range[1], 0)
        line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, sx, sy, ex, ey)
        line.line.color.rgb = RGBColor(255, 255, 255)
        line.line.width = Pt(1.5)
        line.line.end_arrowhead = 5 # Stealth arrow

        # Y축 (Professional thin line)
        sx, sy = self._to_ppt_coords(0, y_range[0])
        ex, ey = self._to_ppt_coords(0, y_range[1])
        line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, sx, sy, ex, ey)
        line.line.color.rgb = RGBColor(255, 255, 255)
        line.line.width = Pt(1.5)
        line.line.end_arrowhead = 5 # Stealth arrow

    def _draw_curve(self, slide, curve):
        pts = curve.get("points", [])
        if len(pts) < 2:
            return

        # ── High-Fidelity Parametric Spline Interpolation ────────────────
        try:
            import numpy as np
            from scipy.interpolate import make_interp_spline
            pts_arr = np.array(pts)
            
            if len(pts_arr) >= 3:
                # Parametric interpolation: handles non-monotonic curves correctly
                t = np.linspace(0, 1, len(pts_arr))
                t_new = np.linspace(0, 1, 300)
                k = min(3, len(pts_arr) - 1)
                spl_x = make_interp_spline(t, pts_arr[:, 0], k=k)(t_new)
                spl_y = make_interp_spline(t, pts_arr[:, 1], k=k)(t_new)
                draw_pts = list(zip(spl_x, spl_y))
            else:
                draw_pts = pts
        except Exception as e:
            draw_pts = pts

        # FreeformBuilder로 매끄러운 선 생성
        start_x, start_y = self._to_ppt_coords(draw_pts[0][0], draw_pts[0][1])
        builder = slide.shapes.build_freeform(start_x, start_y)
        
        for i in range(1, len(draw_pts)):
            px, py = self._to_ppt_coords(draw_pts[i][0], draw_pts[i][1])
            builder.add_line_segments([(px, py)])
        
        shape = builder.convert_to_shape()
        # 색상 처리
        hex_color = curve.get("color", "#00E5FF").replace("#", "")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        
        shape.line.color.rgb = RGBColor(r, g, b)
        shape.line.width = Pt(curve.get("width", 2.5))
        if curve.get("style") == "dashed":
            shape.line.dash_style = 2

    def _draw_dashed_line(self, slide, dl):
        dl_type = dl.get("type", "")
        val = dl.get("val") or dl.get("y", 0) if dl_type == "horizontal" else dl.get("val") or dl.get("x", 0)
        
        if dl_type == "horizontal":
            sx, sy = self._to_ppt_coords(dl.get("start", 0), val)
            ex, ey = self._to_ppt_coords(dl.get("end", 5), val)
        else: # vertical
            sx, sy = self._to_ppt_coords(val, dl.get("start", 0))
            ex, ey = self._to_ppt_coords(val, dl.get("end", 5))
            
        line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, sx, sy, ex, ey)
        line.line.color.rgb = RGBColor(120, 120, 120)
        line.line.dash_style = 2
        line.line.width = Pt(1)

    def _draw_arrow(self, slide, arrow):
        is_curved = arrow.get("is_curved", False)
        pts = arrow.get("points", [])
        
        if is_curved and len(pts) >= 3:
            # 곡선 화살표도 촘촘한 보간 적용
            try:
                import numpy as np
                from scipy.interpolate import make_interp_spline
                pts_arr = np.array(pts)
                t = np.linspace(0, 1, len(pts_arr))
                t_new = np.linspace(0, 1, 100)
                spl_x = make_interp_spline(t, pts_arr[:, 0], k=min(3, len(pts)-1))(t_new)
                spl_y = make_interp_spline(t, pts_arr[:, 1], k=min(3, len(pts)-1))(t_new)
                draw_pts = list(zip(spl_x, spl_y))
            except:
                draw_pts = pts

            sx, sy = self._to_ppt_coords(draw_pts[0][0], draw_pts[0][1])
            builder = slide.shapes.build_freeform(sx, sy)
            for i in range(1, len(draw_pts)):
                px, py = self._to_ppt_coords(draw_pts[i][0], draw_pts[i][1])
                builder.add_line_segments([(px, py)])
            shape = builder.convert_to_shape()
            shape.line.color.rgb = RGBColor(180, 180, 180)
            shape.line.width = Pt(1.5)
            shape.line.end_arrowhead = 1
        else:
            fx, fy = arrow.get("from", [0, 0])
            tx, ty = arrow.get("to", [0, 0])
            sx, sy = self._to_ppt_coords(fx, fy)
            ex, ey = self._to_ppt_coords(tx, ty)
            line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, sx, sy, ex, ey)
            line.line.color.rgb = RGBColor(180, 180, 180)
            line.line.width = Pt(1.2)
            line.line.end_arrowhead = 1

    def _draw_point(self, slide, point):
        coord = point.get("coord") or [point.get("x", 0), point.get("y", 0)]
        x, y = self._to_ppt_coords(coord[0], coord[1])
        size = Pt(8)
        shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, x - size/2, y - size/2, size, size)
        shp.line.color.rgb = RGBColor(255, 255, 255)
        shp.line.width = Pt(1.0)
        
        if point.get("type") == "hollow":
            shp.fill.solid()
            shp.fill.fore_color.rgb = RGBColor(10, 10, 10) # 배경과 유사한 어두운 색
        else:
            shp.fill.solid()
            shp.fill.fore_color.rgb = RGBColor(255, 255, 255)

    def _draw_label(self, slide, label):
        pos = label.get("pos") or [label.get("x", 0), label.get("y", 0)]
        x, y = self._to_ppt_coords(pos[0], pos[1])
        
        # 텍스트 상자 추가 (자동 크기 조정 지원)
        tx = slide.shapes.add_textbox(x - Pt(20), y - Pt(25), Pt(120), Pt(40))
        tf = tx.text_frame
        tf.word_wrap = False
        text = label.get("text", "")
        tf.text = text
        for para in tf.paragraphs:
            para.font.color.rgb = RGBColor(255, 255, 255)
            para.font.size = Pt(14)
            para.font.bold = True
            para.font.name = "Inter" # High-end font
