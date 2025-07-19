import subprocess
import asyncio
from PIL import ImageDraw

from epd_dashboard.EPaper import *
from epd_dashboard.Navigation import *
from epd_dashboard.components.PageComponents import *
import epd_dashboard.bluetooth.bluetoothctl as bluetoothctl


class Bluetooth(Page):
    def __init__(self, page_index, router, ui):
        super().__init__(page_index, router, ui)
        self.options_list = OptionsList(router, self, [])
        self.options_loaded = False
        self.options_visible_start = 0
        self.options_visible_end = 2

        self.backspace_icon = Icon(BoundingBox(
            0, Icon.ICON_SIZE, 0, Icon.ICON_SIZE), "backspace.bmp")

        icon_alignment = ui.get_image_alignment(Icon.ICON_SIZE, Icon.ICON_SIZE)
        self.refresh_icon = Icon(BoundingBox(
            icon_alignment["right"], self.ui.height, 0, Icon.ICON_SIZE), "refresh.bmp")
        self.down_icon = Icon(BoundingBox(
            icon_alignment["horizontal_center"], icon_alignment["horizontal_center"] + Icon.ICON_SIZE, icon_alignment["bottom"], self.ui.width), "caret-down.bmp")
        self.up_icon = Icon(BoundingBox(
            icon_alignment["horizontal_center"], icon_alignment["horizontal_center"] + Icon.ICON_SIZE,  0, Icon.ICON_SIZE), "caret-up.bmp")

        widget_alignment = ui.get_image_alignment(
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

    async def connect_to_device(self, bluetooth_id):
        connection_task = asyncio.create_task(bluetoothctl.connect_to_device(bluetooth_id))
        render_loading_widget = asyncio.create_task(
            self.render_loading_widget(connection_task))
        await render_loading_widget


    def touch_listener(self):
        while self.touch_flag and self.ui.app_is_running:
            if self.router.current_page_index == self.page_index:
                self.ui.detect_screen_interaction()
                if self.ui.screen_is_active and self.ui.did_tap:
                    if self.backspace_icon.is_tap_within_bounding_box(self.ui.tap_x, self.ui.tap_y):
                        self.router.navigateTo(self.router.SETTINGS)
                    elif self.refresh_icon.is_tap_within_bounding_box(self.ui.tap_x, self.ui.tap_y):
                        self.options_loaded = False
                        self.options_visible_start = 0
                        self.options_visible_end = 2
                        asyncio.run(self.update())
                    elif self.down_icon.is_tap_within_bounding_box(self.ui.tap_x, self.ui.tap_y):
                        self.options_visible_start = min(
                            len(self.options_list.options), self.options_visible_start + 1)
                        self.options_visible_end = min(
                            len(self.options_list.options), self.options_visible_end + 1)
                        asyncio.run(self.update())
                    elif self.up_icon.is_tap_within_bounding_box(self.ui.tap_x, self.ui.tap_y):
                        self.options_visible_start = max(
                            0, self.options_visible_start - 1)
                        self.options_visible_end = max(
                            0, self.options_visible_end - 1)
                        asyncio.run(self.update())
                    else:
                        self.options_list.scan_for_selection(
                            self.ui.tap_x, self.ui.tap_y)
                        if self.options_list.selected_option:
                            asyncio.run(self.connect_to_device(
                                self.options_list.selected_option.value))
                            asyncio.run(self.update())
            time.sleep(0.02)
