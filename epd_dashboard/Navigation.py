import os

from .pages.Dashboard import Dashboard
from .pages.Settings import Settings
from .pages.Bluetooth import Bluetooth
from .pages.WiFi import WiFi
from .EPaper import *
from .components.PageComponents import *

fontdir = os.path.join(os.path.dirname(os.path.dirname(
    os.path.realpath(__file__))), 'epaperui/assets/fonts')
picdir = os.path.join(os.path.dirname(os.path.dirname(
    os.path.realpath(__file__))), 'epaperui/assets')


class MainDisplay(Component):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.height = self.ui.display.height
        self.width = self.ui.display.width
        self.app_is_running = True

        self.router = Router(self)


    def update(self):
        return

class Router(Component):
    def __init__(self, parent):
        super().__init__(parent)
        self.router = self
        self.height = round(self.ui.height * .9)
        self.width = self.ui.width
        self.current_page_index = EPaperInterface.PAGE_INDEX_DASHBOARD
        self.prev_page_index = EPaperInterface.PAGE_INDEX_DASHBOARD
        self.dashboard_display = Dashboard(self)
        self.settings_display = Settings(self)
        self.bluetooth_display = Bluetooth(self)
        self.wifi_display = WiFi(self)
        self.pages = [self.dashboard_display, self.settings_display, self.bluetooth_display, self.wifi_display]

        self.start()

    def start(self):
        for page in self.pages:
            page.start()
        self.update()


    def navigate(self, page_index):
        self.prev_page_index = self.current_page_index
        self.current_page_index = page_index
        current_page = self.pages[self.current_page_index]
        current_page.update()
