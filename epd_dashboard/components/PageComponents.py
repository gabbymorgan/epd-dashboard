import os
from PIL import Image

from epd_dashboard.EPaper import picdir

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