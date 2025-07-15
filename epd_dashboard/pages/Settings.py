import time

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
        
    def update(self):
        self.ui.reset_canvas()
        backspace_image = self.backspace_icon.get_icon_image()
        bounging_box = self.backspace_icon.bounding_box
        self.ui.canvas.paste(backspace_image, (bounging_box.min_x, bounging_box.min_y))
        self.ui.request_render()
    
    def change_current_widget(self, widget_index):
        self.current_widget_index = widget_index
        self.update()

    def touch_listener(self):
        while self.touch_flag:
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
                    if self.backspace_icon.tapIsWithinBoundingBox(self.ui.tap_x, self.ui.tap_y):
                        self.router.navigateTo(Router.DASHBOARD)
            time.sleep(0.02)