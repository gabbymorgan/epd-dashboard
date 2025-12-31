import json
import os
import shlex
import subprocess
import sys
import threading
import time
import readchar

from PIL import Image, ImageDraw
from epd_dashboard.components.PageComponents import *
from epd_dashboard.EPaper import EPaperInterface, picdir
from epd_dashboard.services.error import log_error


class Dashboard(Component):
    def __init__(self, parent):
        super().__init__(parent)
        self.current_widget_index = 0

        with open('apps.json', 'r') as widget_file:
            widget_objects = json.load(widget_file)
            self.widgets = []
            alignment_data = self.ui.get_alignment(
                Widget.WIDGET_SIZE, Widget.WIDGET_SIZE)
            bounding_box = BoundingBox(alignment_data["x_center"], alignment_data["x_center"] +
                                       Widget.WIDGET_SIZE, alignment_data["y_center"], alignment_data["y_center"] + Widget.WIDGET_SIZE)
            for widget_object in widget_objects:
                widget = CommandWidget(self, widget_object["name"],
                                       widget_object["imageUrl"], bounding_box, widget_object["command"])
                self.widgets.append(widget)

        alignment_data = self.ui.get_alignment(
            Icon.ICON_SIZE,   Icon.ICON_SIZE)
        icon_bounding_box = BoundingBox(alignment_data["x_right"], alignment_data["x_right"] + Icon.ICON_SIZE,
                                        0, Icon.ICON_SIZE)
        self.settings_icon = Icon(self, icon_bounding_box, "settings.png")

        self.keyboard_thread = threading.Thread(
            daemon=False, target=self.keyboard_listener)
        self.keyboard_thread.start()

    def update(self):
        current_widget = self.widgets[self.current_widget_index]
        image = Image.open(os.path.join(
            picdir, current_widget.imageUrl))
        self.ui.reset_canvas()
        self.ui.canvas.paste(
            image, (current_widget.bounding_box.min_x, current_widget.bounding_box.min_y))
        draw = ImageDraw.Draw(self.ui.canvas)
        text = current_widget.name
        left, top, right, bottom = EPaperInterface.FONT_15.getbbox(text)
        text_width = right - left
        text_height = bottom - top
        alignment_data = self.ui.get_alignment(text_width, text_height)
        draw.text((alignment_data["x_center"], current_widget.bounding_box.min_y +
                  Widget.WIDGET_SIZE), text, font=EPaperInterface.FONT_12)
        self.ui.canvas.paste(
            self.settings_icon.get_icon_image(), (self.settings_icon.bounding_box.min_x, self.settings_icon.bounding_box.min_y))
        self.ui.request_render()

    def change_current_widget(self, widget_index):
        self.current_widget_index = widget_index
        self.update()

    def launch_widget(self, widget):
        print(f"launching {widget.name}...")
        self.touch_flag = False
        self.ui.shutdown()
        command = shlex.split(widget.command)
        subprocess.Popen(command, shell=True, start_new_session=True)
        sys.exit(0)

    def keyboard_listener(self):
        while self.ui.app_is_running:
            if self.router.current_page_index == EPaperInterface.PAGE_INDEX_DASHBOARD:
                incoming_char = self.ui.incoming_char
                match incoming_char:
                    case "s":
                        self.router.navigate(EPaperInterface.PAGE_INDEX_SETTINGS)
                    case readchar.key.RIGHT:
                        self.change_current_widget(min(
                            len(self.widgets) - 1, self.current_widget_index + 1))
                    case readchar.key.LEFT:
                        self.change_current_widget(max(
                            0, self.current_widget_index - 1))
                    case readchar.key.ENTER:
                        self.launch_widget(self.widgets[
                            self.current_widget_index])
            time.sleep(0.02)
