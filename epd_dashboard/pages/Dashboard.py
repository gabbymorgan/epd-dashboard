import json
import os
import shlex
import subprocess
import sys
import threading
import time

from PIL import Image, ImageDraw
from epd_dashboard.components.PageComponents import *
from epd_dashboard.EPaper import EPaperInterface, picdir
from epd_dashboard.Navigation import *


class Dashboard(Page):
    def __init__(self, page_index, router, ui):
        super().__init__(page_index, router, ui)
        self.current_widget_index = 0

        with open('apps.json', 'r') as widget_file:
            widget_objects = json.load(widget_file)
            self.widgets = []
            alignment_data = ui.get_image_alignment(
                Widget.WIDGET_SIZE, Widget.WIDGET_SIZE)
            bounding_box = BoundingBox(alignment_data["horizontal_center"], alignment_data["horizontal_center"] +
                                       Widget.WIDGET_SIZE, alignment_data["vertical_center"], alignment_data["vertical_center"] + Widget.WIDGET_SIZE)
            for widget_object in widget_objects:
                widget = Widget(widget_object["name"], widget_object["command"],
                                widget_object["imageUrl"], bounding_box)
                self.widgets.append(widget)

        alignment_data = ui.get_image_alignment(
            Icon.ICON_SIZE,   Icon.ICON_SIZE)
        icon_bounding_box = BoundingBox(alignment_data["right"], alignment_data["right"] + Icon.ICON_SIZE,
                                        alignment_data["top"], alignment_data["top"] + Icon.ICON_SIZE)
        self.settings_icon = Icon(icon_bounding_box, "settings.png")

        self.touch_thread = threading.Thread(
            daemon=False, target=self.touch_listener)
        self.touch_thread.start()

    def update(self):
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
        self.update()

    def launch_widget(self, widget):
        print(f"launching {widget.name}...")
        self.touch_flag = False
        self.ui.shutdown()
        command = shlex.split(widget.command)
        subprocess.Popen(command, shell=True, start_new_session=True)
        sys.exit(0)

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
                    current_widget = self.widgets[self.current_widget_index]
                    if current_widget.tapIsWithinBoundingBox(self.ui.tap_x, self.ui.tap_y):
                        self.launch_widget(current_widget)
                    elif self.settings_icon.tapIsWithinBoundingBox(self.ui.tap_x, self.ui.tap_y):
                        self.router.navigateTo(Router.SETTINGS)
            time.sleep(0.02)

