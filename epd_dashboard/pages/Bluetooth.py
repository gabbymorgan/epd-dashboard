import subprocess
from PIL import ImageDraw

from epd_dashboard.EPaper import *
from epd_dashboard.Navigation import *
from epd_dashboard.components.PageComponents import *


class Bluetooth(Page):
    def __init__(self, page_index, router, ui):
        super().__init__(page_index, router, ui)
        self.options_list = OptionsList(router, self, [])
        self.options_loaded = False
        self.options_visible_start = 0
        self.options_visible_end = 3
        self.backspace_icon = Icon(BoundingBox(
            0, Icon.ICON_SIZE, 0, Icon.ICON_SIZE), "backspace.bmp")

        alignment_data = ui.get_image_alignment(Icon.ICON_SIZE, Icon.ICON_SIZE)
        self.refresh_icon = Icon(BoundingBox(
            alignment_data["right"], self.ui.height, 0, Icon.ICON_SIZE), "refresh.bmp")

        self.down_icon = Icon(BoundingBox(
            alignment_data["horizontal_center"], alignment_data["horizontal_center"] + Icon.ICON_SIZE, alignment_data["bottom"], self.ui.width), "caret-down.bmp")

        alignment_data = ui.get_image_alignment(
            Widget.WIDGET_SIZE, Widget.WIDGET_SIZE)
        bounding_box = BoundingBox(alignment_data["horizontal_center"], alignment_data["horizontal_center"] +
                                   Widget.WIDGET_SIZE, alignment_data["vertical_center"], alignment_data["vertical_center"] + Widget.WIDGET_SIZE)
        self.loading_widget = Widget("Loading", "loader.bmp", bounding_box)

    def load_options(self):
        options = []
        scan_process = subprocess.run(
            ['bluetoothctl', '--timeout', '10', 'scan', 'on'])
        bluetooth_process = subprocess.run(['bluetoothctl', 'devices'],
                                           encoding='utf-8', stdout=subprocess.PIPE)
        for line in bluetooth_process.stdout.split('\n'):
            terms = line.split(" ")
            if terms[0] == "Device":
                name = " ".join(terms[2:])
                value = terms[1]
                options.append(
                    Option(name, value))
        self.options_list.options = options
        self.options_loaded = True

    def update(self):
        self.ui.reset_canvas()
        draw = ImageDraw.Draw(self.ui.canvas)

        self.ui.canvas.paste(self.backspace_icon.get_icon_image(
        ), (self.backspace_icon.bounding_box.min_x, self.backspace_icon.bounding_box.min_y))

        self.ui.canvas.paste(self.refresh_icon.get_icon_image(
        ), (self.refresh_icon.bounding_box.min_x, self.refresh_icon.bounding_box.min_y))

        if not self.options_loaded:
            self.ui.canvas.paste(self.loading_widget.get_widget_image(
            ), (self.loading_widget.bounding_box.min_x, self.loading_widget.bounding_box.min_y))
            self.ui.request_render()
            self.load_options()
            whiteout_box = self.loading_widget.bounding_box
            draw.rectangle((whiteout_box.min_x, whiteout_box.min_y,
                           whiteout_box.max_x, whiteout_box.max_y), fill=255)

        option_y = 0
        for option_index, option in enumerate(self.options_list.options):
            if option_index < self.options_visible_start or option_index > self.options_visible_end:
                 option.bounding_box = None
            else:
                alignment_data = self.ui.get_alignment(
                    option.name, EPaperInterface.FONT_20)
                bounding_box = BoundingBox(alignment_data["center_align"], alignment_data["center_align"] +
                                            alignment_data["text_width"], option_y, option_y + alignment_data["text_height"])
                option.bounding_box = bounding_box
                option_y += alignment_data["text_height"] + 10
                draw.text((option.bounding_box.min_x, option.bounding_box.min_y),
                        option.name, font=EPaperInterface.FONT_20)

        self.ui.canvas.paste(self.down_icon.get_icon_image(
        ), (self.down_icon.bounding_box.min_x, self.down_icon.bounding_box.min_y))

        self.ui.request_render()

    def connect_to_device(self, bluetooth_id):
        proc = subprocess.run(['bluetoothctl', 'connect', bluetooth_id],
                              encoding='utf-8', stdout=subprocess.PIPE)

    def touch_listener(self):
        while self.touch_flag:
            if self.ui.app_is_running and self.router.current_page_index == self.page_index:
                self.ui.detect_screen_interaction()
                if self.ui.did_tap:
                    if self.backspace_icon.is_tap_within_bounding_box(self.ui.tap_x, self.ui.tap_y):
                        self.router.navigateTo(self.router.SETTINGS)
                    elif self.refresh_icon.is_tap_within_bounding_box(self.ui.tap_x, self.ui.tap_y):
                        self.options_loaded = False
                        self.options_visible_start = 0
                        self.options_visible_end = 3
                        self.update()
                    elif self.down_icon.is_tap_within_bounding_box(self.ui.tap_x, self.ui.tap_y):
                        self.options_visible_start += 1
                        self.options_visible_end += 1
                        self.update()
                    else:
                        self.options_list.scan_for_selection(
                            self.ui.tap_x, self.ui.tap_y)
                        if self.options_list.selected_option:
                            self.connect_to_device(
                                self.options_list.selected_option.value)
            time.sleep(0.02)
