from epd_dashboard.EPaper import *
from epd_dashboard.pages.Settings import *
from epd_dashboard.pages.Dashboard import *
from epd_dashboard.pages.Bluetooth import *
from epd_dashboard.Navigation import *
from epd_dashboard.services.error import *


def main():
    ui = EPaperInterface()
    try:
        if not os.path.exists("./apps.json"):
            os.mknod("./apps.json")
            with open('./apps.json', 'w') as apps:
                with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "./apps.json"), 'r') as default_apps:
                    apps.write(default_apps.read())
        init_error_file()
        MainDisplay(ui)
    except Exception as e:
        log_error(str(e))
        ui.shutdown()


if __name__ == "__main__":
    main()
