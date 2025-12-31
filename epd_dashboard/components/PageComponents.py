import os
from PIL import Image

from epd_dashboard.EPaper import picdir

class BoundingBox:
    def __init__(self, min_x, max_x, min_y, max_y):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

class Component:
    def __init__(self, parent=None):
        self.is_enabled = True
        self.parent = parent

        if self.parent:
            self.ui = self.parent.ui
            if hasattr(self.parent, "router"):
                self.router = self.parent.router

    def start(self):
        self.update()

    def update(self):
        return


class Widget(Component):
    WIDGET_SIZE = 70

    def __init__(self, parent: Component, name: str, imageUrl: str, bounding_box: BoundingBox):
        super().__init__(parent)
        self.bounding_box = bounding_box
        self.name = name
        self.imageUrl = imageUrl

    def get_widget_image(self):
        return Image.open(os.path.join(picdir, self.imageUrl))
        
class CommandWidget(Widget):
    def __init__(self, parent:Component, name, imageUrl, bounding_box, command: str):
        super().__init__(parent, name, imageUrl, bounding_box)
        self.command = command

class NavigationWidget(Widget):
    def __init__(self, parent: Component, name, imageUrl, bounding_box, page_index):
        super().__init__(parent, name, imageUrl, bounding_box)
        self.page_index = page_index

class AnimatedWidget(Widget):
    def __init__(self, parent: Component, name, file_paths, bounding_box):
        super().__init__(parent, name, file_paths[0], bounding_box)
        self.file_paths = file_paths
        self.current_imageUrl_index = 0

    def next_frame(self):
        self.current_imageUrl_index = (self.current_imageUrl_index + 1) % len(self.file_paths)
        self.imageUrl = self.file_paths[self.current_imageUrl_index]

class Icon(Component):
    ICON_SIZE = 24

    def __init__(self, parent: Component, bounding_box, file_path):
        super().__init__(parent)
        self.bounding_box = bounding_box
        self.file_path = file_path

    def get_icon_image(self):
        return Image.open(os.path.join(picdir, self.file_path))
        
class Option(Component):
    def __init__(self, parent: Component, name: str, value: str, bounding_box=None):
        super().__init__(parent)
        self.bounding_box = bounding_box
        self.name = name
        self.value = value

class OptionsList(Component):
    def __init__(self, parent: Component, options: list[Option]):
        self.parent = parent
        self.options = options
        self.selected_option = None
    
    def update(self):
        print(f"currently selected option: {self.selected_option}")
