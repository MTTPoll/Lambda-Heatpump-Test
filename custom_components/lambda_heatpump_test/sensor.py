
from __future__ import annotations
from datetime import timedelta
from typing import Any, Dict, List
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo

from pymodbus.client import ModbusTcpClient
from pymodbus.version import version as pymodbus_version

from .lambda_heatpump_test_api import *  # reuse original API helpers if referenced

_LOGGER = logging.getLogger(__name__)
DOMAIN = "lambda_heatpump_test"

# ---- Embedded SENSORS from original integration ----
SENSORS: List[Dict[str, Any]] = [
    # General Ambient
    {"name": "Ambient Error Number", "register": 0, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "Ambient Operating State", "register": 1, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
     "description_map": ["Off", "Automatik", "Manual", "Error"]},
    {"name": "Ambient Temperature", "register": 2, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Ambient Temperature 1h", "register": 3, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Ambient Temperature Calculated", "register": 4, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},

    # General E-Manager
    {"name": "E-Manager Error Number", "register": 100, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "E-Manager Operating State", "register": 101, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
     "description_map": ["Off", "Automatik", "Manual", "Error", "Offline"]},
    {"name": "E-Manager Actual Power", "register": 102, "unit": "W", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "E-Manager Actual Power Consumption", "register": 103, "unit": "W", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "E-Manager Power Consumption Setpoint", "register": 104, "unit": "W", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},

    # Heat Pump No. 1
    {"name": "Heat Pump 1 Error State", "register": 1000, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
     "description_map": ["OK", "Message", "Warnung", "Alarm", "Fault"]},
    {"name": "Heat Pump 1 Error Number", "register": 1001, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "Heat Pump 1 State", "register": 1002, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
     "description_map": ["Init", "Reference", "Restart-Block", "Ready", "Start Pumps", "Start Compressor", "Pre-Regulation", "Regulation",
                         "Not Used", "Cooling", "Defrosting", "Not Used", "Not Used", "Not Used", "Not Used", "Not Used", "Not Used",
                         "Not Used", "Not Used", "Not Used", "Stopping", "Not Used", "Not Used", "Not Used", "Not Used", "Not Used",
                         "Not Used", "Not Used", "Not Used", "Not Used", "Not Used", "Fault-Lock", "Alarm-Block", "Not Used", "Not Used",
                         "Not Used", "Not Used", "Not Used", "Not Used", "Error-Reset"]},
    {"name": "Heat Pump 1 Operating State", "register": 1003, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
     "description_map": ["Standby", "Central Heating", "Domestic Hot Water", "Cold Climate", "Circulate", "Defrost", "Off", "Frost",
                         "Standby-Frost", "Not used", "Summer", "Holiday", "Error", "Warning", "Info-Message", "Time-Block", "Release-Block",
                         "Mintemp-Block", "Firmware-Download"]},
    {"name": "Heat Pump 1 Flow Line Temperature", "register": 1004, "unit": "°C", "scale": 0.01, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heat Pump 1 Return Line Temperature", "register": 1005, "unit": "°C", "scale": 0.01, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heat Pump 1 Volume Flow Heat Sink", "register": 1006, "unit": "l/h", "scale": 1, "precision": 1, "data_type": "int16", "state_class": "total"},
    {"name": "Heat Pump 1 Energy Source Inlet Temperature", "register": 1007, "unit": "°C", "scale": 0.01, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heat Pump 1 Energy Source Outlet Temperature", "register": 1008, "unit": "°C", "scale": 0.01, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heat Pump 1 Volume Flow Energy Source", "register": 1009, "unit": "l/min", "scale": 0.01, "precision": 1, "data_type": "int16", "state_class": "measurement"},
    {"name": "Heat Pump 1 Compressor Unit Rating", "register": 1010, "unit": "%", "scale": 0.01, "precision": 0, "data_type": "uint16", "state_class": "total"},
    {"name": "Heat Pump 1 Actual Heating Capacity", "register": 1011, "unit": "kW", "scale": 0.1, "precision": 1, "data_type": "int16", "state_class": "measurement"},
    {"name": "Heat Pump 1 Inverter Power Consumption", "register": 1012, "unit": "W", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "Heat Pump 1 COP", "register": 1013, "unit": "", "scale": 0.01, "precision": 2, "data_type": "int16", "state_class": "total"},
    {"name": "Heat Pump 1 Request Type", "register": 1015, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total",
     "description_map": ["No Request", "Flow Pump Circulation", "Central Heating", "Central Cooling", "Domestic Hot Water"]},
    {"name": "Heat Pump 1 Requested Flow Line Temperature", "register": 1016, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heat Pump 1 Requested Return Line Temperature", "register": 1017, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heat Pump 1 Requested Flow to Return Line Temperature Difference", "register": 1018, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heat Pump 1 Relais State 2nd Heating Stage", "register": 1019, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "Heat Pump 1 Compressor Power Consumption Accumulated", "register": [1020, 1021], "unit": "Wh", "scale": 1, "precision": 0, "data_type": "int32", "device_class": "energy", "state_class": "total_increasing"},
    {"name": "Heat Pump 1 Compressor Thermal Energy Output Accumulated", "register": [1022, 1023], "unit": "Wh", "scale": 1, "precision": 0, "data_type": "int32", "device_class": "energy", "state_class": "total_increasing"},

    # Boiler
    {"name": "Boiler Error Number", "register": 2000, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "Boiler Operating State", "register": 2001, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
     "description_map": ["Standby", "Domestic Hot Water", "Legio", "Summer", "Frost", "Holiday", "Prio-Stop", "Error", "Off", "Prompt-DHW",
                         "Trailing-Stop", "Temp-Lock", "Standby-Frost"]},
    {"name": "Boiler Actual High Temperature", "register": 2002, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Boiler Actual Low Temperature", "register": 2003, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Boiler Set Temperature", "register": 2050, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},

    # Buffer
    {"name": "Buffer Error Number", "register": 3000, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "Buffer Operating State", "register": 3001, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
     "description_map": ["Standby", "Heating", "Cooling", "Summer", "Frost", "Holiday", "Prio-Stop", "Error", "Off", "Standby-Frost"]},
    {"name": "Buffer Actual High Temperature", "register": 3002, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Buffer Actual Low Temperature", "register": 3003, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Buffer Set Temperature", "register": 3050, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},

    # Solar
#    {"name": "Solar Error Number", "register": 4000, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
#    {"name": "Solar Operating State", "register": 4001, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
#     "description_map": ["Standby", "Heating", "Error", "Off"]},
#    {"name": "Solar Actual Collector Temperature", "register": 4002, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
#    {"name": "Solar Actual Buffer Sensor 1 Temperature", "register": 4003, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
#    {"name": "Solar Actual Buffer Sensor 2 Temperature", "register": 4004, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
#    {"name": "Solar Set Max Buffer Temperature", "register": 4050, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
#    {"name": "Solar Set Buffer Changeover Temperature", "register": 4051, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},

    # Heating Circuit 1
    {"name": "Heating Circuit 1 Error Number", "register": 5000, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "Heating Circuit 1 Operating State", "register": 5001, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
     "description_map": ["Heating", "Eco", "Cooling", "Floor-dry", "Frost", "Max-Temp", "Error", "Service", "Holiday", "Central Heating Summer",
                         "Central Cooling Winter", "Prio-Stop", "Off", "Release-Off", "Time-Off", "Standby", "Standby-Heating", "Standby-Eco",
                         "Standby-Cooling", "Standby-Frost", "Standby-Floor-dry"]},
    {"name": "Heating Circuit 1 Flow Line Temperature", "register": 5002, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 1 Return Line Temperature", "register": 5003, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 1 Room Device Temperature", "register": 5004, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 1 Set Flow Line Temperature", "register": 5005, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 1 Operating Mode", "register": 5006, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total",
     "description_map": ["Off", "Manual", "Automatik", "Auto-Heating", "Auto-Cooling", "Frost", "Summer", "Floor-dry"]},
    {"name": "Heating Circuit 1 Set Flow Line Offset Temperature", "register": 5050, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 1 Set Heating Mode Room Temperature", "register": 5051, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 1 Set Cooling Mode Room Temperature", "register": 5052, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},

    # Heating Circuit 2
    {"name": "Heating Circuit 2 Error Number", "register": 5100, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "Heating Circuit 2 Operating State", "register": 5101, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
     "description_map": ["Heating", "Eco", "Cooling", "Floor-dry", "Frost", "Max-Temp", "Error", "Service", "Holiday", "Central Heating Summer",
                         "Central Cooling Winter", "Prio-Stop", "Off", "Release-Off", "Time-Off", "Standby", "Standby-Heating", "Standby-Eco",
                         "Standby-Cooling", "Standby-Frost", "Standby-Floor-dry"]},
    {"name": "Heating Circuit 2 Flow Line Temperature", "register": 5102, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 2 Return Line Temperature", "register": 5103, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 2 Room Device Temperature", "register": 5104, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 2 Set Flow Line Temperature", "register": 5105, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 2 Operating Mode", "register": 5106, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total",
     "description_map": ["Off", "Manual", "Automatik", "Auto-Heating", "Auto-Cooling", "Frost", "Summer", "Floor-dry"]},
    {"name": "Heating Circuit 2 Set Flow Line Offset Temperature", "register": 5150, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 2 Set Heating Mode Room Temperature", "register": 5151, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 2 Set Cooling Mode Room Temperature", "register": 5152, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},

    # Heating Circuit 3
    {"name": "Heating Circuit 3 Error Number", "register": 5200, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total"},
    {"name": "Heating Circuit 3 Operating State", "register": 5201, "unit": "", "scale": 1, "precision": 0, "data_type": "uint16", "state_class": "total",
     "description_map": ["Heating", "Eco", "Cooling", "Floor-dry", "Frost", "Max-Temp", "Error", "Service", "Holiday", "Central Heating Summer",
                         "Central Cooling Winter", "Prio-Stop", "Off", "Release-Off", "Time-Off", "Standby", "Standby-Heating", "Standby-Eco",
                         "Standby-Cooling", "Standby-Frost", "Standby-Floor-dry"]},
    {"name": "Heating Circuit 3 Flow Line Temperature", "register": 5202, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 3 Return Line Temperature", "register": 5203, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 3 Room Device Temperature", "register": 5204, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 3 Set Flow Line Temperature", "register": 5205, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 3 Operating Mode", "register": 5206, "unit": "", "scale": 1, "precision": 0, "data_type": "int16", "state_class": "total",
     "description_map": ["Off", "Manual", "Automatik", "Auto-Heating", "Auto-Cooling", "Frost", "Summer", "Floor-dry"]},
    {"name": "Heating Circuit 3 Set Flow Line Offset Temperature", "register": 5250, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 3 Set Heating Mode Room Temperature", "register": 5251, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
    {"name": "Heating Circuit 3 Set Cooling Mode Room Temperature", "register": 5252, "unit": "°C", "scale": 0.1, "precision": 1, "data_type": "int16", "device_class": "temperature", "state_class": "measurement"},
]

def combine_u32(reg0: int, reg1: int, word_order: str) -> int:
    if word_order == "little":
        low, high = reg0, reg1
    else:
        high, low = reg0, reg1
    return ((high & 0xFFFF) << 16) | (low & 0xFFFF)

def to_signed_32(v: int) -> int:
    return v - 0x100000000 if (v & 0x80000000) else v

def to_signed_16(v: int) -> int:
    v &= 0xFFFF
    return v - 0x10000 if (v & 0x8000) else v

class ModbusClientManager:
    def __init__(self, ip_address: str, word_order: str = "big"):
        self.client = ModbusTcpClient(ip_address)
        self.word_order = word_order
        _LOGGER.info("Lambda Heatpump Test: using pymodbus %s, word_order=%s", pymodbus_version, word_order)

    def connect(self):
        self.client.connect()

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass

    def read_u16_block(self, start_register: int, count: int):
        rr = self.client.read_holding_registers(start_register, count, unit=1)
        if getattr(rr, "isError", lambda: False)():
            raise UpdateFailed(f"Modbus error reading {{start_register}}+{{count}}: {{rr}}")
        return rr.registers

    def read_spec(self, spec: Dict[str, Any]) -> Any:
        reg = spec.get("register")
        dtype = (spec.get("data_type") or "int16").lower()
        # handle two-word values
        if isinstance(reg, list) and len(reg) == 2:
            regs = self.read_u16_block(min(reg), 2)
            # assume consecutive order; map accordingly
            r0 = regs[0] if reg[0] <= reg[1] else regs[1]
            r1 = regs[1] if reg[0] <= reg[1] else regs[0]
            raw_u32 = combine_u32(r0, r1, self.word_order)
            val = to_signed_32(raw_u32) if "int32" in dtype else raw_u32
        elif isinstance(reg, int):
            regs = self.read_u16_block(reg, 1)
            raw16 = regs[0]
            if "uint16" in dtype:
                val = raw16 & 0xFFFF
            else:
                val = to_signed_16(raw16)
        else:
            raise UpdateFailed(f"Unsupported register spec: {{reg}}")

        # scale/precision
        scale = spec.get("scale", 1)
        precision = spec.get("precision", 0)
        try:
            if scale not in (None, 1):
                val = val * scale
        except Exception:
            pass
        try:
            if precision is not None:
                val = round(val, int(precision))
        except Exception:
            pass

        # optional description_map list (index -> text)
        desc = spec.get("description_map")
        if isinstance(desc, list):
            try:
                idx = int(val)
            except Exception:
                idx = None
            if idx is not None and 0 <= idx < len(desc):
                return desc[idx]
        return val

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    ip_address = entry.data["ip_address"]
    word_order = entry.data.get("word_order", "big")  # before 2025 -> big, after 2025 -> little
    update_interval = timedelta(seconds=entry.data.get("update_interval", 30))

    client = ModbusClientManager(ip_address, word_order)
    client.connect()

    async def async_update_data():
        try:
            data: Dict[str, Any] = {{}}
            for spec in SENSORS:
                name = spec.get("name", "sensor")
                try:
                    data[name] = client.read_spec(spec)
                except Exception as sensor_err:
                    _LOGGER.debug("Read failed for %s: %s", name, sensor_err)
                    data.setdefault(name, None)
            return data
        except Exception as e:
            raise UpdateFailed(str(e))

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Lambda Heatpump Test Coordinator",
        update_method=async_update_data,
        update_interval=update_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    device_info = DeviceInfo(
        identifiers={{(DOMAIN, ip_address)}},
        name=f"Lambda Heatpump Test ({{ip_address}})",
        manufacturer="Lambda",
        model="Heatpump",
    )

    entities = [GenericLambdaSensor(coordinator, s, device_info) for s in SENSORS]
    async_add_entities(entities)

class GenericLambdaSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, spec: Dict[str, Any], device_info: DeviceInfo):
        self._coordinator = coordinator
        self._spec = spec
        base_uid = spec.get("unique_id") or spec.get("name", "lambda_sensor").lower().replace(" ", "_")
        self._attr_unique_id = f"lambda_heatpump_test_{{base_uid}}"
        self._attr_name = spec.get("name", "Lambda Sensor")
        self._attr_native_unit_of_measurement = spec.get("unit")
        self._attr_device_class = spec.get("device_class")
        self._attr_state_class = spec.get("state_class")
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def native_value(self):
        name = self._spec.get("name")
        return (self._coordinator.data or {{}}).get(name)

    async def async_update(self):
        await self._coordinator.async_request_refresh()
