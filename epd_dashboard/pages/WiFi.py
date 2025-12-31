import subprocess
import asyncio
import nmcli

from PIL import ImageDraw
from epd_dashboard.EPaper import *
from epd_dashboard.Navigation import *
from epd_dashboard.components.PageComponents import *
from epd_dashboard.services.error import log_error
import epd_dashboard.services.bluetoothctl as bluetoothctl


class WiFi(Component):
    def __init__(self, parent):
        super().__init__(parent)
        self.options_list = OptionsList(self.router, self, [])
        self.options_loaded = False
        self.options_visible_start = 0
        self.options_visible_end = 2

        self.backspace_icon = Icon(self, BoundingBox(
            0, Icon.ICON_SIZE, 0, Icon.ICON_SIZE), "backspace.bmp")

        icon_alignment = self.ui.get_alignment(Icon.ICON_SIZE, Icon.ICON_SIZE)
        self.refresh_icon = Icon(self, BoundingBox(
            icon_alignment["right"], self.ui.height, 0, Icon.ICON_SIZE), "refresh.bmp")
        self.down_icon = Icon(self, BoundingBox(
            icon_alignment["horizontal_center"], icon_alignment["horizontal_center"] + Icon.ICON_SIZE, icon_alignment["bottom"], self.ui.width), "caret-down.bmp")
        self.up_icon = Icon(self, BoundingBox(
            icon_alignment["horizontal_center"], icon_alignment["horizontal_center"] + Icon.ICON_SIZE,  0, Icon.ICON_SIZE), "caret-up.bmp")

        widget_alignment = self.ui.get_alignment(
            Widget.WIDGET_SIZE, Widget.WIDGET_SIZE)
        bounding_box = BoundingBox(widget_alignment["horizontal_center"], widget_alignment["horizontal_center"] +
                                   Widget.WIDGET_SIZE, widget_alignment["vertical_center"], widget_alignment["vertical_center"] + Widget.WIDGET_SIZE)
        self.loading_widget = AnimatedWidget("Loading", [
                                             "loader-1.bmp", "loader-2.bmp", "loader-3.bmp", "loader-4.bmp"], bounding_box)
        
    async def load_options(self):
        await bluetoothctl.scan_for_seconds(10)
        bluetooth_devices = await bluetoothctl.get_available_devices()
        self.options_list.options = [Option(device["name"], device["value"]) for device in bluetooth_devices]
        self.options_loaded = True

    async def render_loading_widget(self, loading_task: asyncio.Task):
        while not loading_task.done():
            draw = ImageDraw.Draw(self.ui.canvas)
            text = self.loading_widget.name
            align_text = self.ui.get_alignment(
                text, EPaperInterface.FONT_12)
            draw.text((align_text["center_align"], self.loading_widget.bounding_box.min_y +
                       Widget.WIDGET_SIZE), text, font=EPaperInterface.FONT_12)
            self.ui.canvas.paste(self.loading_widget.get_widget_image(
            ), (self.loading_widget.bounding_box.min_x, self.loading_widget.bounding_box.min_y))
            self.ui.request_render()
            self.loading_widget.next_frame()
            await asyncio.sleep(1)

    async def update(self):
        self.ui.reset_canvas()
        draw = ImageDraw.Draw(self.ui.canvas)

        self.ui.canvas.paste(self.backspace_icon.get_icon_image(
        ), (self.backspace_icon.bounding_box.min_x, self.backspace_icon.bounding_box.min_y))

        self.ui.canvas.paste(self.refresh_icon.get_icon_image(
        ), (self.refresh_icon.bounding_box.min_x, self.refresh_icon.bounding_box.min_y))

        if not self.options_loaded:
            self.ui.request_render()
            load_options_task = asyncio.create_task(self.load_options())
            render_loading_widget = asyncio.create_task(
                self.render_loading_widget(load_options_task))
            await render_loading_widget

        whiteout_box = self.loading_widget.bounding_box
        draw.rectangle((whiteout_box.min_x, whiteout_box.min_y,
                        whiteout_box.max_x, self.ui.width), fill=255)
        option_y = Icon.ICON_SIZE
        for option_index, option in enumerate(self.options_list.options):
            if option_index < self.options_visible_start or option_index > self.options_visible_end:
                option.bounding_box = None
            else:
                alignment_data = self.ui.get_alignment(
                    option.name, EPaperInterface.FONT_20)
                bounding_box = BoundingBox(alignment_data["center_align"], alignment_data["center_align"] +
                                           alignment_data["text_width"], option_y, option_y + alignment_data["text_height"])
                option.bounding_box = bounding_box
                option_y += alignment_data["text_height"] + 5
                draw.text((option.bounding_box.min_x, option.bounding_box.min_y),
                          option.name, font=EPaperInterface.FONT_20)

        self.down_icon.is_enabled = self.options_visible_end < len(self.options_list.options) - 1
        self.up_icon.is_enabled = self.options_visible_start > 0

        if self.down_icon.is_enabled:
            self.ui.canvas.paste(self.down_icon.get_icon_image(
            ), (self.down_icon.bounding_box.min_x, self.down_icon.bounding_box.min_y))

        if self.up_icon.is_enabled:
            self.ui.canvas.paste(self.up_icon.get_icon_image(
            ), (self.up_icon.bounding_box.min_x, self.up_icon.bounding_box.min_y))

        self.ui.request_render()


    def keyboard_listener(self):
        while self.ui.app_is_running:
            if self.router.current_page_index == EPaperInterface.PAGE_INDEX_DASHBOARD:
                incoming_char = self.ui.incoming_char
                match incoming_char:
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