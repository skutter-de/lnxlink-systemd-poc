"""Controls systemd services"""
import logging
from time import sleep
#from lnxlink.modules.scripts.helpers import syscommand, import_install_package
from pystemd.systemd1 import Unit

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "SystemD"
        self.lnxlink = lnxlink
        self.services = self.lnxlink.config["settings"].get("systemd_control", [])
        self.services: list[str] = [] if self.services is None else self.services
        self.units: dict[str, Unit] = {}
        for service in self.services:
            self.units[service.rstrip(".service")] = Unit(service)
        if len(self.services) == 0:
            logger.info("No systemd settings found on configuration.")
        # self._requirements()

    # def _requirements(self):
    #     dasbus = import_install_package("dasbus", ">=1.7", "dasbus.connection")
    #     self.bus = dasbus.connection.SystemMessageBus()

    def get_info(self):
        """Gather information from the system"""
        info = {}
        for name, unit in self.units.items():
            unit.load() # refresh unit
            if unit.Unit.ActiveState.decode("utf-8") == "active":
                status = "ON"
            else:
                status = "OFF"
            info[name] = status
        return info

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for service in self.units.keys():
            discovery_info[f"Systemd Control {service}"] = {
                "type": "switch",
                "icon": "mdi:application-cog",
                "value_template": f"{{{{ value_json.get('{service}') }}}}",
            }
        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        unit = self.units[topic[1].replace("systemd_", "")]
        unit.load() # refresh unit
        
        if data.lower() == "off":
            if unit.Unit.ActiveState.decode("utf-8") == "active":
                unit.Unit.Stop(b'replace')
                while not unit.Unit.ActiveState.decode("utf-8") == "inactive":
                    unit.load()
                    sleep(1)
            
        elif data.lower() == "on":
            if unit.Unit.ActiveState.decode("utf-8") != "active":
                unit.Unit.Start(b'replace')
                while not unit.Unit.ActiveState.decode("utf-8") == "active":
                    unit.load()
                    sleep(1)

### TEMP main code

if __name__ == "__main__":
    class Lnxlink:
        config = {}

        def __init__(self, config):
            self.config = config

    import yaml
    lnxlink = Lnxlink(yaml.load(open("config.yaml", "r"), Loader=yaml.FullLoader))

    addon = Addon(lnxlink)
    print(addon.exposed_controls())
    print(addon.get_info())
    addon.start_control(["", "systemd_httpd"], "on")
    print(addon.get_info())
    addon.start_control(["", "systemd_httpd"], "off")
    print(addon.get_info())
