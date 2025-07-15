from epd_dashboard.EPaper import *
from epd_dashboard.pages.Settings import *
from epd_dashboard.pages.Dashboard import *
from epd_dashboard.pages.Bluetooth import *
from epd_dashboard.Navigation import *


def main():
    if not os.path.exists("apps.json"):
        os.mknod("apps.json")
        with open('apps.json', 'w') as apps:
            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "apps.json"), 'r') as default_apps:
                apps.write(default_apps.read())
    ui = EPaperInterface()
    router = Router()
    dashboard_page = Dashboard(Router.DASHBOARD, router, ui)
    settings_page = Settings(Router.SETTINGS, router, ui)
    bluetooth_page = Bluetooth(Router.BLUETOOTH, router, ui)
    router.pages = [dashboard_page, settings_page, bluetooth_page]
    router.navigateTo(0)



if __name__ == "__main__":
    main()
