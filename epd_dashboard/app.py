import json
import shlex
import subprocess
import sys
import threading
import time

from PIL import Image, ImageDraw
from epd_dashboard.EPaper import *


class BoundingBox:
    def __init__(self, min_x, max_x, min_y, max_y):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y


class Widget:
    WIDGET_SIZE = 70

    def __init__(self, name: str, command: str, imageUrl: str, bounding_box: BoundingBox):
        self.name = name
        self.command = command
        self.imageUrl = imageUrl
        self.bounding_box = bounding_box

    def tapIsWithinBoundingBox(self, touch_x, touch_y):
        within_vertical_bounds = touch_x > self.bounding_box.min_x and touch_x < self.bounding_box.max_x
        within_horizontal_bounds = touch_y > self.bounding_box.min_y and touch_y < self.bounding_box.max_y
        if within_vertical_bounds and within_horizontal_bounds:
            return True
        else:
            return False


class Dashboard:
    def __init__(self, widgets: list[Widget]):
        self.ui = EPaperInterface()
        self.widgets = widgets
        self.current_widget_index = 0
        self.touch_flag = True

        self.touch_thread = threading.Thread(
            daemon=False, target=self.touch_listener)
        self.touch_thread.start()

    def render_current_widget(self):
        current_widget = self.widgets[self.current_widget_index]
        image = Image.open(os.path.join(
            picdir, current_widget.imageUrl))
        self.ui.reset_canvas()
        align_image = self.ui.get_image_alignment(Widget.WIDGET_SIZE, Widget.WIDGET_SIZE)
        self.ui.canvas.paste(image, (align_image["horizontal_center"], align_image["vertical_center"]))
        draw = ImageDraw.Draw(self.ui.canvas)
        text = current_widget.name
        align_text = self.ui.get_alignment(text, EPaperInterface.FONT_12)
        draw.text((align_text["center_align"], align_image["vertical_center"] + Widget.WIDGET_SIZE), text, font=EPaperInterface.FONT_12)
        self.ui.request_render()

    def change_current_widget(self, widget_index):
        self.current_widget_index = widget_index
        self.render_current_widget()

    def launch_widget(self, widget):
        print(f"launching {widget.name}...")
        self.touch_flag = False
        self.ui.shutdown()
        command = shlex.split(widget.command)
        subprocess.Popen(command, shell=True, start_new_session=True)
        sys.exit(0)

    def touch_listener(self):
        while self.touch_flag:
            if self.ui.app_is_running:
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
                    if current_widget.tapIsWithinBoundingBox(self.ui.tap_x, self.ui.tap_y):
                        self.launch_widget(current_widget)
            time.sleep(0.02)


def main():
    if not os.path.exists("apps.json"):
        os.mknod("apps.json")
        with open('apps.json', 'w') as apps:
            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "apps.json"), 'r') as default_apps:
                apps.write(default_apps.read())
    with open('apps.json', 'r') as widget_file:
        widget_objects = json.load(widget_file)
        widgets = []
        for widget_object in widget_objects:
            widget = Widget(widget_object["name"], widget_object["command"],
                            widget_object["imageUrl"], BoundingBox(0, 122, 0, 250))
            widgets.append(widget)
        dashboard = Dashboard(widgets)
        dashboard.render_current_widget()


if __name__ == "__main__":
    main()
