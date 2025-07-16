import time
from PIL import ImageDraw

from epd_dashboard.EPaper import EPaperInterface
from epd_dashboard.Navigation import *
from epd_dashboard.components.PageComponents import *

class Settings(Page):
    def __init__(self, page_index, router, ui):
        super().__init__(page_index, router, ui)
        self.widgets = []
        self.current_widget_index = 0
        icon_bounding_box = BoundingBox(0,Icon.ICON_SIZE, 0, Icon.ICON_SIZE)
        self.backspace_icon = Icon(icon_bounding_box, "backspace.bmp")

        alignment_data = ui.get_image_alignment(
            Widget.WIDGET_SIZE, Widget.WIDGET_SIZE)
        bounding_box = BoundingBox(alignment_data["horizontal_center"], alignment_data["horizontal_center"] +
                                    Widget.WIDGET_SIZE, alignment_data["vertical_center"], alignment_data["vertical_center"] + Widget.WIDGET_SIZE)
        
        self.widgets.append(NavigationWidget("Bluetooth", "bluetooth.bmp", bounding_box, Router.BLUETOOTH))
        
    def update(self):
        self.ui.reset_canvas()
        backspace_image = self.backspace_icon.get_icon_image()
        bounging_box = self.backspace_icon.bounding_box
        self.ui.canvas.paste(backspace_image, (bounging_box.min_x, bounging_box.min_y))
        current_widget = self.widgets[self.current_widget_index]
        self.ui.canvas.paste(current_widget.get_widget_image(), (current_widget.bounding_box.min_x, current_widget.bounding_box.min_y))
        draw = ImageDraw.Draw(self.ui.canvas)
        text = current_widget.name
        align_text = self.ui.get_alignment(text, EPaperInterface.FONT_12)
        draw.text((align_text["center_align"], current_widget.bounding_box.min_y +
                  Widget.WIDGET_SIZE), text, font=EPaperInterface.FONT_12)
        self.ui.request_render()
    
    def change_current_widget(self, widget_index):
        self.current_widget_index = widget_index
        self.update()

    def touch_listener(self):
        while self.touch_flag and self.ui.app_is_running:
            if self.ui.app_is_running and self.router.current_page_index == self.page_index:
                self.ui.detect_screen_interaction()
                if self.ui.screen_is_active and self.ui.did_swipe:
                    if self.ui.swipe_direction == EPaperInterface.SWIPE_LEFT:
                        new_index = min(
                            len(self.widgets) - 1, self.current_widget_index + 1)
                        self.change_current_widget(new_index)
                    elif self.ui.swipe_direction == EPaperInterface.SWIPE_RIGHT:
                        new_index = max(
                            0, self.current_widget_index - 1)
                        self.change_current_widget(new_index)
                elif self.ui.screen_is_active and self.ui.did_tap:
                    current_widget = self.widgets[self.current_widget_index]
                    if current_widget.is_tap_within_bounding_box(self.ui.tap_x, self.ui.tap_y):
                        self.router.navigateTo(current_widget.page_index)
                    if self.backspace_icon.is_tap_within_bounding_box(self.ui.tap_x, self.ui.tap_y):
                        self.router.navigateTo(Router.DASHBOARD)
            time.sleep(0.02)