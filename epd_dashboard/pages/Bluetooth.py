from PIL import ImageDraw

from epd_dashboard.EPaper import *
from epd_dashboard.Navigation import *

class Bluetooth(Page):
    def __init__(self, page_index, router, ui):
        super().__init__(page_index, router, ui)

    def update(self):
        self.ui.reset_canvas()
        draw = ImageDraw.Draw(self.ui.canvas)
        draw.text((0,0), "you ddeeedddd it", font=EPaperInterface.FONT_12)
        self.ui.request_render()