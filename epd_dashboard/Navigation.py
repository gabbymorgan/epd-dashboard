import threading
import time

from epd_dashboard.EPaper import EPaperInterface

class Router:
    DASHBOARD =  0
    SETTINGS =   1
    BLUETOOTH =  2

    def __init__(self):
        self.pages = []
        self.current_page_index = 0

    def navigateTo(self, page_index):
        self.current_page_index = page_index
        current_page = self.pages[self.current_page_index]
        current_page.update()

class Page:
    def __init__(self, page_index, router:Router, ui:EPaperInterface):
        self.page_index = page_index
        self.router = router
        self.ui = ui
        self.touch_flag = True
        self.touch_thread = threading.Thread(daemon=False, target=self.touch_listener)

        self.touch_thread.start()

    def update(self):
        return
    
    def touch_listener(self):
        while self.touch_flag:
            if self.ui.app_is_running and self.router.current_page_index == self.page_index:
                self.ui.detect_screen_interaction()
                if self.ui.screen_is_active and (self.ui.did_tap or self.ui.did_swipe):
                    print(f"You have navigated to page {self.page_index}, and it appears not to be set up yet. Hope this helps!")
            time.sleep(0.02)