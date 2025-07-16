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

    def load_options(self):
        option_y = 0
        proc = subprocess.run(['bluetoothctl', '--timeout', '10',
                              'scan', 'on'], encoding='utf-8', stdout=subprocess.PIPE)
        for line in proc.stdout.split('\n'):
            terms = line.split(" ")
            print(terms)
            if len(terms) == 4 and terms[1] == "Device":
                name = terms[3]
                value = terms[2]
                alignment_data = self.ui.get_alignment(
                    name, EPaperInterface.FONT_20)
                bounding_box = BoundingBox(alignment_data["center_align"], alignment_data["center_align"] +
                                           alignment_data["text_width"], option_y, option_y + alignment_data["text_height"])
                option_y += alignment_data["text_height"] + 10
                self.options_list.options.append(
                    Option(name, value, bounding_box))
        self.options_loaded = True

    def update(self):
        self.ui.reset_canvas()
        if not self.options_loaded:
            self.load_options()
        draw = ImageDraw.Draw(self.ui.canvas)
        for option in self.options_list.options:
            draw.text((option.bounding_box.min_x, option.bounding_box.min_y),
                      option.name, font=EPaperInterface.FONT_20)
        self.ui.request_render()

    def connect_to_device(self, bluetooth_id):
        proc = subprocess.run(['bluetoothctl', 'connect', bluetooth_id], encoding='utf-8', stdout=subprocess.PIPE)
        for line in proc.stdout.split("\n"):
            print(line)

    def touch_listener(self):
        while self.touch_flag:
            if self.ui.app_is_running and self.router.current_page_index == self.page_index:
                self.ui.detect_screen_interaction()
                if self.ui.did_tap:
                    self.options_list.scan_for_selection(self.ui.tap_x, self.ui.tap_y)
                    self.connect_to_device(self.options_list.selected_option.value)
            time.sleep(0.02)
