import os
from PIL import Image

from epd_dashboard.EPaper import picdir
from epd_dashboard.Navigation import *

class BoundingBox:
    def __init__(self, min_x, max_x, min_y, max_y):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

class TouchableObject:
    def __init__(self, bounding_box: BoundingBox):
        self.bounding_box = bounding_box

    def is_tap_within_bounding_box(self, touch_x, touch_y):
        within_vertical_bounds = touch_y > self.bounding_box.min_y and touch_y < self.bounding_box.max_y
        within_horizontal_bounds = touch_x > self.bounding_box.min_x and touch_x < self.bounding_box.max_x
        if within_vertical_bounds and within_horizontal_bounds:
            return True
        else:
            return False

class Widget(TouchableObject):
    WIDGET_SIZE = 70

    def __init__(self, name: str, imageUrl: str, bounding_box: BoundingBox):
        super().__init__(bounding_box)
        self.name = name
        self.imageUrl = imageUrl

    def get_widget_image(self):
        return Image.open(os.path.join(picdir, self.imageUrl))
        
class CommandWidget(Widget):
    def __init__(self, name, imageUrl, bounding_box, command: str):
        super().__init__(name, imageUrl, bounding_box)
        self.command = command

class NavigationWidget(Widget):
    def __init__(self, name, imageUrl, bounding_box, page_index):
        super().__init__(name, imageUrl, bounding_box)
        self.page_index = page_index

class Icon(TouchableObject):
    ICON_SIZE = 24

    def __init__(self, bounding_box, file_path):
        super().__init__(bounding_box)
        self.bounding_box = bounding_box
        self.file_path = file_path

    def get_icon_image(self):
        return Image.open(os.path.join(picdir, self.file_path))
        
class Option(TouchableObject):
    def __init__(self, name: str, value: str, bounding_box):
        super().__init__(bounding_box)
        self.name = name
        self.value = value

class OptionsList():
    def __init__(self, router:Router, parent: Page, options: list[Option]):
        self.router = router
        self.parent = parent
        self.options = options
        self.selected_option = None
    
    def update(self):
        print(f"currently selected option: {self.selected_option}")

    def scan_for_selection(self, touch_x, touch_y):
        for option in self.options:
            if option.is_tap_within_bounding_box(touch_x, touch_y):
                self.selected_option = option
