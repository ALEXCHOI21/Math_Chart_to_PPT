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

        # 배경색 (선택 사항: 기존 플랫폼과 맞추려면 어두운 배경)
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(30, 30, 35)

        # 1. 축 그리기
        self._draw_axes(slide, data.get("axes", {}))

        # 2. 곡선 그리기
        for curve in data.get("curves", []):
            self._draw_curve(slide, curve)

        # 3. 점 그리기
        for point in data.get("points", []):
            self._draw_point(slide, point)

        # 4. 라벨 그리기
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
        x_min = axes.get("x_min", -5)
        x_max = axes.get("x_max", 5)
        y_min = axes.get("y_min", -5)
        y_max = axes.get("y_max", 5)

        # X축
        start_x, start_y = self._to_ppt_coords(x_min, 0)
        end_x, end_y = self._to_ppt_coords(x_max, 0)
        line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, start_x, start_y, end_x, end_y)
        line.line.color.rgb = RGBColor(255, 255, 255)
        line.line.width = Pt(1.5)

        # Y축
        start_x, start_y = self._to_ppt_coords(0, y_min)
        end_x, end_y = self._to_ppt_coords(0, y_max)
        line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, start_x, start_y, end_x, end_y)
        line.line.color.rgb = RGBColor(255, 255, 255)
        line.line.width = Pt(1.5)

    def _draw_curve(self, slide, curve):
        points = curve.get("points", [])
        if len(points) < 2:
            return

        # 여러 개의 짧은 선으로 곡선 근사 (PPT에서 Freeform 빌더는 복잡하므로 단순화)
        for i in range(len(points) - 1):
            x1, y1 = self._to_ppt_coords(points[i][0], points[i][1])
            x2, y2 = self._to_ppt_coords(points[i+1][0], points[i+1][1])
            line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
            line.line.color.rgb = RGBColor(0, 200, 255)  # Cyan 계열
            line.line.width = Pt(2)
            if curve.get("style") == "dashed":
                line.line.dash_style = 2

    def _draw_point(self, slide, point):
        x, y = self._to_ppt_coords(point["coord"][0], point["coord"][1])
        size = Pt(6)
        # 점 그리기 (원)
        shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, x - size/2, y - size/2, size, size)
        if point.get("type") == "hollow":
            shp.fill.no_fill()
            shp.line.color.rgb = RGBColor(255, 255, 255)
        else:
            shp.fill.solid()
            shp.fill.fore_color.rgb = RGBColor(255, 255, 255)
            shp.line.color.rgb = RGBColor(255, 255, 255)

    def _draw_label(self, slide, label):
        x, y = self._to_ppt_coords(label["pos"][0], label["pos"][1])
        tx = slide.shapes.add_textbox(x, y, Pt(50), Pt(20))
        tf = tx.text_frame
        tf.text = label["text"]
        for para in tf.paragraphs:
            para.font.color.rgb = RGBColor(255, 255, 255)
            para.font.size = Pt(12)
            para.font.name = "Inter"
