import time
import threading
import readchar
from PIL import ImageDraw

from epd_dashboard.components.PageComponents import *
from epd_dashboard.EPaper import EPaperInterface
from epd_dashboard.services.error import log_error


class Settings(Component):
    def __init__(self, parent):
        super().__init__(parent)
        self.widgets = []
        self.current_widget_index = 0
        icon_bounding_box = BoundingBox(0, Icon.ICON_SIZE, 0, Icon.ICON_SIZE)
        self.backspace_icon = Icon(self, icon_bounding_box, "backspace.bmp")

        alignment_data = self.ui.get_alignment(
            Widget.WIDGET_SIZE, Widget.WIDGET_SIZE)
        bounding_box = BoundingBox(alignment_data["x_center"], alignment_data["x_center"] +
                                   Widget.WIDGET_SIZE, alignment_data["y_center"], alignment_data["y_center"] + Widget.WIDGET_SIZE)

        self.widgets.append(NavigationWidget(self,
                                             "Bluetooth", "bluetooth.bmp", bounding_box, EPaperInterface.PAGE_INDEX_BLUETOOTH))

        self.widgets.append(NavigationWidget(self,
                                             "WiFi", "wifi.bmp", bounding_box, EPaperInterface.PAGE_INDEX_WIFI))
        

        self.keyboard_thread = threading.Thread(
            daemon=False, target=self.keyboard_listener)
        self.keyboard_thread.start()

    def update(self):
        if self.router.current_page_index != EPaperInterface.PAGE_INDEX_SETTINGS:
            return
        self.ui.reset_canvas()
        backspace_image = self.backspace_icon.get_icon_image()
        bounging_box = self.backspace_icon.bounding_box
        self.ui.canvas.paste(
            backspace_image, (bounging_box.min_x, bounging_box.min_y))
        current_widget = self.widgets[self.current_widget_index]
        self.ui.canvas.paste(current_widget.get_widget_image(
        ), (current_widget.bounding_box.min_x, current_widget.bounding_box.min_y))
        draw = ImageDraw.Draw(self.ui.canvas)
        text = current_widget.name
        left, top, right, bottom = EPaperInterface.FONT_15.getbbox(text)
        text_width = right - left
        text_height = bottom - top
        align_text = self.ui.get_alignment(text_width, text_height)
        draw.text((align_text["x_center"], current_widget.bounding_box.min_y +
                  Widget.WIDGET_SIZE), text, font=EPaperInterface.FONT_12)
        self.ui.request_render()

    def change_current_widget(self, widget_index):
        self.current_widget_index = widget_index
        self.update()

    def keyboard_listener(self):
        while self.ui.app_is_running:
            if self.router.current_page_index == EPaperInterface.PAGE_INDEX_SETTINGS:
                incoming_char = self.ui.incoming_char
                match incoming_char:
                    case readchar.key.RIGHT:
                        new_index = min(
                            len(self.widgets) - 1, self.current_widget_index + 1)
                        self.change_current_widget(new_index)
                    case readchar.key.LEFT:
                        new_index = max(
                            0, self.current_widget_index - 1)
                        self.change_current_widget(new_index)
                    case readchar.key.ENTER:
                        current_widget = self.widgets[self.current_widget_index]
                        self.router.navigate(current_widget.page_index)
                    case readchar.key.ESC:
                        self.router.navigate(
                            EPaperInterface.PAGE_INDEX_DASHBOARD)
                time.sleep(0.02)
