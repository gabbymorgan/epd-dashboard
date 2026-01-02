import copy
import threading
import os
import time
import readchar

from PIL import Image, ImageFont, ImageDraw
from epd_dashboard.lib import epd2in13_V4

fontdir = os.path.join(os.path.dirname(os.path.dirname(
    os.path.realpath(__file__))), 'epd_dashboard/assets/fonts')
picdir = os.path.join(os.path.dirname(os.path.dirname(
    os.path.realpath(__file__))), 'epd_dashboard/assets')


class EPaperInterface():
    # hardware and library constants
    MAX_PARTIAL_REFRESHES = 30
    MAX_REFRESH_INTERVAL = 24 * 60 * 60
    TIMEOUT_INTERVAL = 120
    FONT_15 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 15)
    FONT_12 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 12)

    # Routes

    PAGE_INDEX_DASHBOARD = 0
    PAGE_INDEX_SETTINGS = 1
    PAGE_INDEX_BLUETOOTH = 2
    PAGE_INDEX_WIFI = 3

    def __init__(self):
        try:
            self.display = epd2in13_V4.EPD()
            self.width = self.display.width
            self.height = self.display.height
            self.canvas = None
            self.display_thread_flag = True
            self.keyboard_thread_flag = True
            self.app_is_running = True
            self.screen_is_active = True
            self.should_render = False
            self.partial_refresh_counter = 0
            self.last_full_refresh = time.time()

            self._incoming_char = None
            self.last_keypress = time.time()

            self.keyboard_thread = threading.Thread(
                daemon=True, target=self.keyboard_loop
            )

            self.display_thread = threading.Thread(
                daemon=False, target=self.display_loop)

            self.reset_canvas()
            self.display.init()
            self.display.displayPartBaseImage(
                self.display.getbuffer(self.canvas))

            self.display_thread.start()
            self.keyboard_thread.start()

        except KeyboardInterrupt:
            self.shutdown()

        except Exception as e:
            print(e)

    @property
    def incoming_char(self):
        incoming_char = self._incoming_char
        self._incoming_char = None
        return incoming_char

    @incoming_char.setter
    def incoming_char(self, new_value):
        self._incoming_char = new_value
        self.last_keypress = time.time()

    def display_loop(self):
        while self.display_thread_flag:
            now = time.time()
            if self.should_render:
                self.render()
            elif self.screen_is_active and (now - self.last_keypress > self.TIMEOUT_INTERVAL):
                self.sleep()
            elif not self.screen_is_active and (now - self.last_keypress < self.TIMEOUT_INTERVAL):
                self.awaken()
            elif now - self.last_full_refresh > self.MAX_REFRESH_INTERVAL:
                self.clear_screen()
            time.sleep(.2)

    def keyboard_loop(self):
        while self.keyboard_thread_flag == True:
            self.incoming_char = readchar.readkey()

    def shutdown(self):
        self.display_thread_flag = False
        self.keyboard_thread_flag = False
        self.screen_is_active = False
        self.app_is_running = False
        self.sleep()
        self.display_thread.join()
        self.keyboard_thread.join()

    def sleep(self):
        self.screen_is_active = False
        self.clear_screen()
        time.sleep(2)
        self.display.sleep()

    def awaken(self):
        self.screen_is_active = True
        self.display.init()
        self.render(force_full_refresh=True)

    def clear_screen(self):
        self.display.init()
        self.display.Clear()

    def reset_canvas(self):
        self.canvas = Image.new('1', (self.height, self.width), 255)

    def render(self, force_full_refresh=False):
        self.should_render = False
        if not self.screen_is_active:
            return
        canvas = copy.deepcopy(self.canvas)
        canvas = canvas.rotate(180)
        if self.partial_refresh_counter >= EPaperInterface.MAX_PARTIAL_REFRESHES or force_full_refresh:
            self.display.init()
            self.display.displayPartBaseImage(
                self.display.getbuffer(canvas))
            self.partial_refresh_counter = 0
            time.sleep(.8)
        else:
            self.display.displayPartial(self.display.getbuffer(canvas))
            self.partial_refresh_counter += 1

    def request_render(self):
        self.should_render = True

    def get_alignment(self, width, height):
        return {
            'x_right': self.height-width,
            'x_center': (self.height-width)//2,
            'y_bottom': self.width - height,
            'y_center': (self.width-height)//2
        }
    
    def get_text_dimensions(self, text, font):
        left, top, right, bottom = font.getbbox(text)
        text_width = right - left
        text_height = bottom - top
        return text_width, text_height

    def get_box_for_dimensions(self, width, height, x_alignment, y_alignment, x_offset=0, y_offset=0):
        x_values = {
            "center": (self.height-width)//2 + x_offset,
            "left": x_offset,
            "right": self.height - width + x_offset
        }

        y_values = {
            "center": (self.width-height)//2 + y_offset,
            "top": y_offset,
            "bottom": self.width - height + y_offset
        }

        init_x = x_values[x_alignment]
        init_y = y_values[y_alignment]
        final_x = init_x + width
        final_y = init_y + height

        return (init_x, init_y, final_x, final_y)

    def get_box_for_text(self, text, font, x_alignment, y_alignment, x_offset=0, y_offset=0):
        left, top, right, bottom = font.getbbox(text)
        text_width = right - left
        text_height = bottom - top
        return self.get_box_for_dimensions(text_width, text_height, x_alignment, y_alignment, x_offset, y_offset)


    def draw_text(self, text, font, x_alignment, y_alignment, x_offset=0, y_offset=0):
        draw = ImageDraw.Draw(self.canvas)
        init_x, init_y, final_x, final_y = self.get_box_for_text(
            text, font, x_alignment, y_alignment, x_offset, y_offset)
        draw.text((init_x, init_y),
                  text, font=font)

    def draw_rectangle(self, width, height, x_alignment, y_alignment, x_offset=0, y_offset=0, outline=255, fill=255):
        draw = ImageDraw.Draw(self.canvas)
        init_x, init_y, final_x, final_y = self.get_box_for_dimensions(
            width, height, x_alignment, y_alignment, x_offset=x_offset, y_offset=y_offset)
        draw.rectangle((init_x, init_y, final_x, final_y), outline=outline, fill=fill)
