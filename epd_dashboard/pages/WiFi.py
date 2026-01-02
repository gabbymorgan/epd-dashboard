import asyncio
from math import ceil
import nmcli
from PIL import ImageDraw

from epd_dashboard.EPaper import *
from epd_dashboard.components.PageComponents import *
from epd_dashboard.services.error import log_error
import epd_dashboard.services.bluetoothctl as bluetoothctl


class WiFi(Component):
    VISIBLE_OPTIONS_RANGE = 3

    def __init__(self, parent):
        super().__init__(parent)
        self.options_list = OptionsList(self, [])
        self.loading = False
        self.options_loaded = False
        self.options_visible_start = 0
        self.options_visible_end = self.options_visible_start + WiFi.VISIBLE_OPTIONS_RANGE
        self.show_password_input = False
        self.password = ""

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
        access_points = nmcli.device.wifi()
        self.options_list.options = [
            Option(self, device.ssid if device.ssid else device.bssid, device.bssid) for device in access_points]
        self.options_list.selected_option_index = 0 if len(
            self.options_list.options) else None
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
        if self.router.current_page_index != EPaperInterface.PAGE_INDEX_WIFI:
            return
        self.ui.reset_canvas()
        draw = ImageDraw.Draw(self.ui.canvas)

        self.ui.canvas.paste(self.backspace_icon.get_icon_image(
        ), (self.backspace_icon.bounding_box.min_x, self.backspace_icon.bounding_box.min_y))

        self.ui.canvas.paste(self.refresh_icon.get_icon_image(
        ), (self.refresh_icon.bounding_box.min_x, self.refresh_icon.bounding_box.min_y))

        if not self.loading and not self.options_loaded:
            asyncio.run(self.load_options())

        whiteout_box = self.loading_widget.bounding_box
        draw.rectangle((whiteout_box.min_x, whiteout_box.min_y,
                        whiteout_box.max_x, self.ui.width), fill=255)
        left, top, right, bottom = EPaperInterface.FONT_15.getbbox("example")
        text_height = bottom - top
        y_offset = text_height * 2 #arbitrary
        for option_index, option in enumerate(self.options_list.options):
            if option_index < self.options_visible_start or option_index > self.options_visible_end:
                option.bounding_box = None
            else:
                init_x, init_y, final_x, final_y = self.ui.get_box_for_text(
                    option.name, EPaperInterface.FONT_15, "center", "top", y_offset=y_offset)
                bounding_box = BoundingBox(init_x, final_x, init_y, final_y)
                option.bounding_box = bounding_box
                draw.text((option.bounding_box.min_x, option.bounding_box.min_y),
                          option.name, font=EPaperInterface.FONT_15)
                if (option_index == self.options_list.selected_option_index):
                    draw.text((option.bounding_box.min_x - 10,
                              option.bounding_box.min_y), '>', font=EPaperInterface.FONT_15)

                y_offset += text_height

        self.down_icon.is_enabled = self.options_visible_end < len(
            self.options_list.options) - 1
        self.up_icon.is_enabled = self.options_visible_start > 0

        if self.down_icon.is_enabled:
            self.ui.canvas.paste(self.down_icon.get_icon_image(
            ), (self.down_icon.bounding_box.min_x, self.down_icon.bounding_box.min_y))

        if self.up_icon.is_enabled:
            self.ui.canvas.paste(self.up_icon.get_icon_image(
            ), (self.up_icon.bounding_box.min_x, self.up_icon.bounding_box.min_y))

        if self.show_password_input:
            self.password_input_display()

        self.ui.request_render()

    def password_input_display(self):
        print(self.password)
        masked_input = "*" * len(self.password)
        modal_width = ceil(self.ui.height * .75)
        modal_height = ceil(self.ui.width * .50)
        self.ui.draw_rectangle(modal_width, modal_height,
                               "center", "center", outline=0)
        self.ui.draw_text("enter password", EPaperInterface.FONT_15,
                          "center", "center", y_offset=-20)
        self.ui.draw_text(
            masked_input, EPaperInterface.FONT_15, "center", "center")

    def timed_message_popup(self, duration: int, error_message: str):
        modal_width = ceil(self.ui.height * .90)
        modal_height = ceil(self.ui.width * .50)
        self.ui.draw_rectangle(modal_width, modal_height,
                               "center", "center", outline=0)
        self.ui.draw_text(
            error_message, EPaperInterface.FONT_15, "center", "center")
        self.ui.request_render()
        time.sleep(duration)
        self.update()

    async def connect_to_access_point(self, ssid):
        self.show_password_input = False
        self.loading = True
        try:
            render_loading_widget = asyncio.create_task(
                self.render_loading_widget())
            nmcli.device.wifi_connect(ssid, self.password)
            self.loading = False
            self.password = ""
            await render_loading_widget
            self.timed_message_popup(3, f"Connected to {ssid}.")
            self.update()
        except Exception as e:
            print(e)
            self.loading = False
            self.password = ""
            self.timed_message_popup(3, str(e))

    def scroll_to_location(self, location):
        self.options_visible_start = location
        self.options_visible_end = location + WiFi.VISIBLE_OPTIONS_RANGE

    def next_option(self):
        new_selected_option_index = min(len(self.options_list.options), self.options_list.selected_option_index + 1)
        self.options_list.update_selected_option_index(new_selected_option_index)
        if new_selected_option_index > self.options_visible_end:
            self.scroll_to_location(new_selected_option_index)
        self.update()
        
    def previous_option(self):
        new_selected_option_index = max(0, self.options_list.selected_option_index - 1)
        self.options_list.update_selected_option_index(new_selected_option_index)
        if new_selected_option_index < self.options_visible_start:
            self.scroll_to_location(new_selected_option_index - WiFi.VISIBLE_OPTIONS_RANGE)
        self.update()

    def keyboard_listener(self):
        while self.ui.app_is_running:
            if self.router.current_page_index == EPaperInterface.PAGE_INDEX_WIFI:
                incoming_char = self.ui.incoming_char
                if incoming_char == None:
                    continue
                match incoming_char:
                    case readchar.key.CTRL_B:
                        self.router.navigate(
                            EPaperInterface.PAGE_INDEX_SETTINGS)
                    case readchar.key.CTRL_R:
                        if self.loading:
                            return
                        self.scroll_to_location(0)
                        self.options_list.selected_option_index = 0
                        asyncio.run(self.load_options())
                        self.update()
                    case readchar.key.DOWN:
                        self.next_option()
                    case readchar.key.UP:
                        self.previous_option()
                    case readchar.key.ENTER:
                        if self.show_password_input == False:
                            self.show_password_input = True
                            self.update()
                        else:
                            asyncio.run(self.connect_to_access_point(
                                self.options_list.options[self.options_list.selected_option_index].value))
                    case readchar.key.BACKSPACE:
                        if self.show_password_input == True:
                            self.password = self.password[:-1]
                            self.update()
                    case _:
                        if self.show_password_input == True:
                            self.password += incoming_char
                            self.update()
            time.sleep(0.02)
