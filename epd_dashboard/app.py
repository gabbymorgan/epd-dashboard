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
        within_vertical_bounds = touch_y > self.bounding_box.min_y and touch_y < self.bounding_box.max_y
        within_horizontal_bounds = touch_x > self.bounding_box.min_x and touch_x < self.bounding_box.max_x
        if within_vertical_bounds and within_horizontal_bounds:
            return True
        else:
            return False


class Icon:
    ICON_SIZE = 24

    def __init__(self, bounding_box, file_path):
        self.bounding_box = bounding_box
        self.file_path = file_path

    def get_icon_image(self):
        return Image.open(os.path.join(picdir, self.file_path))

    def tapIsWithinBoundingBox(self, touch_x, touch_y):
        within_vertical_bounds = touch_x > self.bounding_box.min_x and touch_x < self.bounding_box.max_x
        within_horizontal_bounds = touch_y > self.bounding_box.min_y and touch_y < self.bounding_box.max_y
        if within_vertical_bounds and within_horizontal_bounds:
            return True
        else:
            return False


class Dashboard:
    def __init__(self, widgets: list[Widget], ui=None):
        self.widgets = widgets
        self.ui = ui
        self.current_widget_index = 0
        self.touch_flag = True

        alignment_data = ui.get_image_alignment(
            Icon.ICON_SIZE,   Icon.ICON_SIZE)
        icon_bounding_box = BoundingBox(alignment_data["right"], alignment_data["right"] + Icon.ICON_SIZE,
                                  alignment_data["top"], alignment_data["top"] + Icon.ICON_SIZE)
        self.settings_icon = Icon(icon_bounding_box, "settings.png")

        self.touch_thread = threading.Thread(
            daemon=False, target=self.touch_listener)
        self.touch_thread.start()

    def render_current_widget(self):
        current_widget = self.widgets[self.current_widget_index]
        image = Image.open(os.path.join(
            picdir, current_widget.imageUrl))
        self.ui.reset_canvas()
        self.ui.canvas.paste(
            image, (current_widget.bounding_box.min_x, current_widget.bounding_box.min_y))
        draw = ImageDraw.Draw(self.ui.canvas)
        text = current_widget.name
        align_text = self.ui.get_alignment(text, EPaperInterface.FONT_12)
        draw.text((align_text["center_align"], current_widget.bounding_box.min_y +
                  Widget.WIDGET_SIZE), text, font=EPaperInterface.FONT_12)
        self.ui.canvas.paste(
            self.settings_icon.get_icon_image(), (self.settings_icon.bounding_box.min_x, self.settings_icon.bounding_box.min_y))
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
                    print(self.ui.tap_x, self.ui.tap_y)
                    current_widget = self.widgets[self.current_widget_index]
                    if current_widget.tapIsWithinBoundingBox(self.ui.tap_x, self.ui.tap_y):
                        self.launch_widget(current_widget)
                    elif self.settings_icon.tapIsWithinBoundingBox(self.ui.tap_x, self.ui.tap_y):
                        print("settings time")
            time.sleep(0.02)


def main():
    ui = EPaperInterface()
    if not os.path.exists("apps.json"):
        os.mknod("apps.json")
        with open('apps.json', 'w') as apps:
            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "apps.json"), 'r') as default_apps:
                apps.write(default_apps.read())
    with open('apps.json', 'r') as widget_file:
        widget_objects = json.load(widget_file)
        widgets = []
        alignment_data = ui.get_image_alignment(
            Widget.WIDGET_SIZE, Widget.WIDGET_SIZE)
        bounding_box = BoundingBox(alignment_data["horizontal_center"], alignment_data["horizontal_center"] +
                             Widget.WIDGET_SIZE, alignment_data["vertical_center"], alignment_data["vertical_center"] + Widget.WIDGET_SIZE)
        for widget_object in widget_objects:
            widget = Widget(widget_object["name"], widget_object["command"],
                            widget_object["imageUrl"], bounding_box)
            widgets.append(widget)
        dashboard = Dashboard(widgets, ui)
        dashboard.render_current_widget()


if __name__ == "__main__":
    main()
