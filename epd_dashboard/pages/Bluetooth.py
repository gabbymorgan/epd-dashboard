import subprocess
import asyncio
from PIL import ImageDraw

from epd_dashboard.EPaper import *
from epd_dashboard.components.PageComponents import *
from epd_dashboard.services.error import log_error
import epd_dashboard.services.bluetoothctl as bluetoothctl


class Bluetooth(Component):
    def __init__(self, parent):
        super().__init__(parent)
        self.options_list = OptionsList(self, [])
        self.loading = False
        self.options_loaded = False
        self.options_visible_start = 0
        self.options_visible_end = 3

        self.backspace_icon = Icon(self, BoundingBox(
            0, Icon.ICON_SIZE, 0, Icon.ICON_SIZE), "backspace.bmp")

        icon_alignment = self.ui.get_alignment(Icon.ICON_SIZE, Icon.ICON_SIZE)
        self.refresh_icon = Icon(self, BoundingBox(
            icon_alignment["x_right"], self.ui.height, 0, Icon.ICON_SIZE), "refresh.bmp")
        self.down_icon = Icon(self, BoundingBox(
            icon_alignment["x_center"], icon_alignment["x_center"] + Icon.ICON_SIZE, icon_alignment["y_bottom"], self.ui.width), "caret-down.bmp")
        self.up_icon = Icon(self, BoundingBox(
            icon_alignment["x_center"], icon_alignment["x_center"] + Icon.ICON_SIZE,  0, Icon.ICON_SIZE), "caret-up.bmp")

        widget_alignment = self.ui.get_alignment(
            Widget.WIDGET_SIZE, Widget.WIDGET_SIZE)
        bounding_box = BoundingBox(widget_alignment["x_center"], widget_alignment["x_center"] +
                                   Widget.WIDGET_SIZE, widget_alignment["y_center"], widget_alignment["y_center"] + Widget.WIDGET_SIZE)
        self.loading_widget = AnimatedWidget(self, "Loading", [
                                             "loader-1.bmp", "loader-2.bmp", "loader-3.bmp", "loader-4.bmp"], bounding_box)

        self.keyboard_thread = threading.Thread(
            daemon=False, target=self.keyboard_listener)
        self.keyboard_thread.start()

    async def load_options(self):
        self.loading = True
        loading_widget = asyncio.create_task(self.render_loading_widget())
        await bluetoothctl.scan_for_seconds(10)
        bluetooth_devices = await bluetoothctl.get_available_devices()
        self.options_list.options = [
            Option(self, device["name"], device["value"]) for device in bluetooth_devices]
        self.options_list.selected_option_index = 0 if len(self.options_list.options) else None
        self.loading = False
        self.options_loaded = True
        await loading_widget

    async def render_loading_widget(self):
        while self.loading:
            draw = ImageDraw.Draw(self.ui.canvas)
            text = self.loading_widget.name
            text_width, text_height = self.ui.get_text_dimensions(
                text, EPaperInterface.FONT_12)
            align_text = self.ui.get_alignment(
                text_width, text_height)
            draw.text((align_text["x_center"], self.loading_widget.bounding_box.min_y +
                       Widget.WIDGET_SIZE), text, font=EPaperInterface.FONT_12)
            self.ui.canvas.paste(self.loading_widget.get_widget_image(
            ), (self.loading_widget.bounding_box.min_x, self.loading_widget.bounding_box.min_y))
            self.ui.request_render()
            self.loading_widget.next_frame()
            await asyncio.sleep(1)

    def update(self):
        if self.router.current_page_index != EPaperInterface.PAGE_INDEX_BLUETOOTH:
            return
        self.ui.reset_canvas()
        draw = ImageDraw.Draw(self.ui.canvas)

        self.ui.canvas.paste(self.backspace_icon.get_icon_image(
        ), (self.backspace_icon.bounding_box.min_x, self.backspace_icon.bounding_box.min_y))

        self.ui.canvas.paste(self.refresh_icon.get_icon_image(
        ), (self.refresh_icon.bounding_box.min_x, self.refresh_icon.bounding_box.min_y))

        if not self.loading and not self.options_loaded:
            asyncio.run(self.load_options())
            self.ui.request_render()

        whiteout_box = self.loading_widget.bounding_box
        draw.rectangle((whiteout_box.min_x, whiteout_box.min_y,
                        whiteout_box.max_x, self.ui.width), fill=255)
        option_y = Icon.ICON_SIZE
        for option_index, option in enumerate(self.options_list.options):
            if option_index < self.options_visible_start or option_index > self.options_visible_end:
                option.bounding_box = None
            else:
                text_width, text_height = self.ui.get_text_dimensions(
                    option.name, EPaperInterface.FONT_15)
                alignment_data = self.ui.get_alignment(
                    text_width, text_height)
                bounding_box = BoundingBox(alignment_data["x_center"], alignment_data["x_center"] +
                                           text_width, option_y, option_y + text_height)
                option.bounding_box = bounding_box
                option_y += text_height + 5
                draw.text((option.bounding_box.min_x, option.bounding_box.min_y),
                          option.name, font=EPaperInterface.FONT_15)
                if (option_index == self.options_list.selected_option_index):
                    draw.text((option.bounding_box.min_x - 10, option.bounding_box.min_y), '>', font=EPaperInterface.FONT_15)

        self.down_icon.is_enabled = self.options_visible_end < len(
            self.options_list.options) - 1
        self.up_icon.is_enabled = self.options_visible_start > 0

        if self.down_icon.is_enabled:
            self.ui.canvas.paste(self.down_icon.get_icon_image(
            ), (self.down_icon.bounding_box.min_x, self.down_icon.bounding_box.min_y))

        if self.up_icon.is_enabled:
            self.ui.canvas.paste(self.up_icon.get_icon_image(
            ), (self.up_icon.bounding_box.min_x, self.up_icon.bounding_box.min_y))

        self.ui.request_render()

    async def connect_to_device(self, bluetooth_id):
        self.loading = True
        connection_task = asyncio.create_task(
            bluetoothctl.connect_to_device(bluetooth_id))
        render_loading_widget = asyncio.create_task(
            self.render_loading_widget(connection_task))
        await connection_task
        self.loading = False
        await render_loading_widget

    def keyboard_listener(self):
        while self.ui.app_is_running:
            if self.router.current_page_index == EPaperInterface.PAGE_INDEX_BLUETOOTH:
                incoming_char = self.ui.incoming_char
                match incoming_char:
                    case 'b':
                        self.router.navigate(
                            EPaperInterface.PAGE_INDEX_SETTINGS)
                    case 'r':
                        if self.loading:
                            return
                        self.options_visible_start = 0
                        self.options_visible_end = 3
                        self.options_list.selected_option_index = 0
                        asyncio.run(self.load_options())
                        self.update()
                    case readchar.key.DOWN:
                        self.options_visible_start = min(
                            max(0, len(self.options_list.options) - 4), self.options_visible_start + 1)
                        self.options_visible_end = min(
                            len(self.options_list.options) - 1, self.options_visible_end + 1)
                        self.options_list.update_selected_option_index(self.options_list.selected_option_index + 1)
                        self.update()
                    case readchar.key.UP:
                        self.options_visible_start = max(
                            0, self.options_visible_start - 1)
                        self.options_visible_end = max(
                            3, self.options_visible_end - 1)
                        self.options_list.update_selected_option_index(self.options_list.selected_option_index - 1)
                        self.update()
                    case readchar.key.ENTER:
                        asyncio.run(self.connect_to_device(
                            self.options_list.options[self.options_list.selected_option_index].value))
                        self.update()
            time.sleep(0.02)
