from __future__ import annotations

import logging
import asyncio
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant
from homeassistant.backports.enum import StrEnum
from homeassistant.components.sensor import (PLATFORM_SCHEMA, PLATFORM_SCHEMA_BASE, SensorEntity)
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation as DecimalInvalidOperation

from math import ceil, floor, log10
import re
from typing import Any, Final, cast, final, Literal



from typing_extensions import Self

from homeassistant.config_entries import ConfigEntry

# pylint: disable=[hass-deprecated-import]
from homeassistant.const import (  # noqa: F401
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
)
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.config_validation import (
    PLATFORM_SCHEMA,
    PLATFORM_SCHEMA_BASE,
)
from homeassistant.const import CONF_NAME
from pprint import pformat
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers. entity import  EntityDescription
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity_platform import EntityPlatform
from homeassistant.helpers.restore_state import ExtraStoredData, RestoreEntity
from homeassistant.helpers.typing import UNDEFINED, ConfigType, StateType, UndefinedType
from homeassistant.util import dt as dt_util
from homeassistant.util.enum import try_parse_enum

from datetime import timedelta


from homeassistant.components.sensor import *
from homeassistant.components.sensor import DOMAIN
from homeassistant.loader import bind_hass

#from .const import CONF_SERIAL
from .const import (  # noqa: F401
    ATTR_LAST_RESET,
    ATTR_OPTIONS,
    ATTR_STATE_CLASS,
    CONF_STATE_CLASS,
    DEVICE_CLASS_STATE_CLASSES,
    DEVICE_CLASS_UNITS,
    DEVICE_CLASSES,
    DEVICE_CLASSES_SCHEMA,
    DOMAIN,
    NON_NUMERIC_DEVICE_CLASSES,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL,
    STATE_CLASS_TOTAL_INCREASING,
    STATE_CLASSES,
    STATE_CLASSES_SCHEMA,
    UNIT_CONVERTERS,
    SensorDeviceClass,
    SensorStateClass,
)

from .pokeys import pokeys_instance
from .pokeys_interface import pokeys_interface

from .websocket_api import async_setup as async_setup_ws_api
#import websocket_api
pk = pokeys_interface()

_LOGGER = logging.getLogger("pokeys")
DOMAIN = "PoKeys57E"
CONF_SERIAL = "serial"

ENTITY_ID_FORMAT = DOMAIN + ".{}"

NEGATIVE_ZERO_PATTERN = re.compile(r"^-(0\.?0*)$")

#SCAN_INTERVAL: Final = timedelta(seconds=30)
SCAN_INTERVAL = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_SERIAL): cv.string,
})

__all__ = [
    "ATTR_LAST_RESET",
    "ATTR_OPTIONS",
    "ATTR_STATE_CLASS",
    "CONF_STATE_CLASS",
    "DEVICE_CLASS_STATE_CLASSES",
    "DOMAIN",
    "PLATFORM_SCHEMA_BASE",
    "PLATFORM_SCHEMA", 
    "RestoreSensor",
    "SensorDeviceClass",
    "SensorEntity",
    "SensorEntityDescription",
    "SensorExtraStoredData",
    "SensorStateClass",
]

# mypy: disallow-any-generics


async def async_setup_platform(hass: HomeAssistant, config: ConfigType, add_entities: AddEntitiesCallBack, discovery_info=None) -> bool: # -> bool
    """Track states and offer events for sensors."""
    component = hass.data[DOMAIN] = EntityComponent[SensorEntity](
        logging.getLogger("pokeys"), DOMAIN, hass, SCAN_INTERVAL
    )
    sensor = {
        "name": config[CONF_NAME],
        "serial": config[CONF_SERIAL]
    }
    add_entities([
        PoKeys57E(
            hass,
            config.get(CONF_NAME),
            config.get(CONF_SERIAL),
        )
    ])

    async_setup_ws_api(hass)
    _LOGGER.info(pformat(config))
    await component.async_setup(config)
    #await async_add_entities(sensor)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, config: ConfigType, add_entities: AddEntitiesCallBack, discovery_info=None) -> bool:
    """Set up a config entry."""
    component: EntityComponent[SensorEntity] = hass.data[DOMAIN]
    return await component.async_setup_entry(entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    component: EntityComponent[SensorEntity] = hass.data[DOMAIN]
    return await component.async_unload_entry(entry)
    #await self.hass.config_entries.async_forward_entry_unload(self.config_entry, "sensor")


@dataclass
class SensorEntityDescription(EntityDescription):
    """A class that describes sensor entities."""

    device_class: SensorDeviceClass | None = None
    last_reset: datetime | None = None
    native_unit_of_measurement: str | None = None
    options: list[str] | None = None
    state_class: SensorStateClass | str | None = None
    suggested_display_precision: int | None = None
    suggested_unit_of_measurement: str | None = None
    unit_of_measurement: None = None  # Type override, use native_unit_of_measurement

#DEVICE_CLASSES_SCHEMA = vol.All(vol.Lower, vol.Coerce(SensorDeviceClass))
class PoKeys57E(SensorEntity):
    """sensor entity"""

    entity_description: SensorEntityDescription
    _attr_device_class: SensorDeviceClass | None
    _attr_last_reset: datetime | None
    _attr_native_unit_of_measurement: str | None
    _attr_native_value: StateType | date | datetime | Decimal = None
    _attr_options: list[str] | None
    _attr_state_class: SensorStateClass | str | None
    _attr_state: None = None  # Subclasses of SensorEntity should not set this
    _attr_suggested_display_precision: int | None
    _attr_suggested_unit_of_measurement: str | None
    _attr_unit_of_measurement: None = (
        None  # Subclasses of SensorEntity should not set this
    )

    def __init__(self, hass, name, serial):
        self._serial = serial
        host = pk.device_discovery(serial)
        self._sensor = pokeys_instance(host)
        self._hass = hass
        
        self._name = name
        self._state = None
        pk.connect(host)

        
    @callback
    def add_to_platform_start(
        self,
        hass: HomeAssistant,
        platform: EntityPlatform,
        parallel_updates: asyncio.Semaphore | None,
    ) -> None:
        """Start adding an entity to a platform.

        Allows integrations to remove legacy custom unit conversion which is no longer
        needed without breaking existing sensors. Only works for sensors which are in
        the entity registry.

        This can be removed once core integrations have dropped unneeded custom unit
        conversion.
        """
        super().add_to_platform_start(hass, platform, parallel_updates)

        # Bail out if the sensor doesn't have a unique_id or a device class
        #if self.unique_id is None or self.device_class is None:
        #    return
        registry = er.async_get(self.hass)

        # Bail out if the entity is not yet registered
        if not (
            entity_id := registry.async_get_entity_id(
                platform.domain, platform.platform_name, self.unique_id
            )
        ):
            # Prime _sensor_option_unit_of_measurement to ensure the correct unit
            # is stored in the entity registry.
            self._sensor_option_unit_of_measurement = self._get_initial_suggested_unit()
            return

        registry_entry = registry.async_get(entity_id)
        assert registry_entry

        # Prime _sensor_option_unit_of_measurement to ensure the correct unit
        # is stored in the entity registry.
        self.registry_entry = registry_entry
        self._async_read_entity_options()

        # If the sensor has 'unit_of_measurement' in its sensor options, the user has
        # overridden the unit.
        # If the sensor has 'sensor.private' in its entity options, it already has a
        # suggested_unit.
        registry_unit = registry_entry.unit_of_measurement
        if (
            (
                (sensor_options := registry_entry.options.get(DOMAIN))
                and CONF_UNIT_OF_MEASUREMENT in sensor_options
            )
            or f"{DOMAIN}.private" in registry_entry.options
            or self.unit_of_measurement == registry_unit
        ):
            return

        # Make sure we can convert the units
        if (
            (unit_converter := UNIT_CONVERTERS.get(self.device_class)) is None
            or registry_unit not in unit_converter.VALID_UNITS
            or self.unit_of_measurement not in unit_converter.VALID_UNITS
        ):
            return

        # Set suggested_unit_of_measurement to the old unit to enable automatic
        # conversion
        self.registry_entry = registry.async_update_entity_options(
            entity_id,
            f"{DOMAIN}.private",
            {"suggested_unit_of_measurement": registry_unit},
        )
        # Update _sensor_option_unit_of_measurement to ensure the correct unit
        # is stored in the entity registry.
        self._async_read_entity_options()

    @property
    def name(self):
        return self._name

    async def async_update(self):
        """Update the sensor value."""
        # Implement your logic to retrieve or calculate the sensor value
        self._state = 42
        return self._state


    

    async def async_internal_added_to_hass(self) -> None:
        """Call when the sensor entity is added to hass."""
        await super().async_internal_added_to_hass()
        if not self.registry_entry:
            return
        self._async_read_entity_options()
        #self._update_suggested_precision()

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the class of this entity."""
        if hasattr(self, "_attr_device_class"):
            return self._attr_device_class
        if hasattr(self, "entity_description"):
            return self.entity_description.device_class
        return None

    @final
    @property
    def _numeric_state_expected(self) -> bool:
        """Return true if the sensor must be numeric."""
        # Note: the order of the checks needs to be kept aligned
        # with the checks in `state` property.
        device_class = try_parse_enum(SensorDeviceClass, self.device_class)
        if device_class in NON_NUMERIC_DEVICE_CLASSES:
            return False
        if (
            self.state_class is not None
            or self.native_unit_of_measurement is not None
            or self.suggested_display_precision is not None
        ):
            return True
        # Sensors with custom device classes will have the device class
        # converted to None and are not considered numeric
        return device_class is not None

    @property
    def options(self) -> list[str] | None:
        """Return a set of possible options."""
        if hasattr(self, "_attr_options"):
            return self._attr_options
        if hasattr(self, "entity_description"):
            return self.entity_description.options
        return None

    @final
    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the entity, after unit conversion."""
        # Highest priority, for registered entities: unit set by user,with fallback to
        # unit suggested by integration or secondary fallback to unit conversion rules
        if self._sensor_option_unit_of_measurement is not UNDEFINED:
            return self._sensor_option_unit_of_measurement

        # Second priority, for non registered entities: unit suggested by integration
        if not self.unique_id and self.suggested_unit_of_measurement:
            return self.suggested_unit_of_measurement

        # Third priority: Legacy temperature conversion, which applies
        # to both registered and non registered entities
        native_unit_of_measurement = self.native_unit_of_measurement

        if (
            self.device_class == SensorDeviceClass.TEMPERATURE
            and native_unit_of_measurement
            in {UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT}
        ):
            return self.hass.config.units.temperature_unit

        # Fourth priority: Native unit
        return native_unit_of_measurement

    @final
    @property
    def state(self) -> Any:
        """Return the state of the sensor and perform unit conversions, if needed."""
        native_unit_of_measurement = self.native_unit_of_measurement
        unit_of_measurement = self.unit_of_measurement
        value = self.native_value
        # For the sake of validation, we can ignore custom device classes
        # (customization and legacy style translations)
        device_class = try_parse_enum(SensorDeviceClass, self.device_class)
        state_class = self.state_class

        # Sensors with device classes indicating a non-numeric value
        # should not have a unit of measurement
        if device_class in NON_NUMERIC_DEVICE_CLASSES and unit_of_measurement:
            raise ValueError(
                f"Sensor {self.entity_id} has a unit of measurement and thus "
                "indicating it has a numeric value; however, it has the "
                f"non-numeric device class: {device_class}"
            )

        # Validate state class for sensors with a device class
        if (
            state_class
            and not self._invalid_state_class_reported
            and device_class
            and (classes := DEVICE_CLASS_STATE_CLASSES.get(device_class)) is not None
            and state_class not in classes
        ):
            self._invalid_state_class_reported = True
            report_issue = self._suggest_report_issue()

            # This should raise in Home Assistant Core 2023.6
            _LOGGER.warning(
                "Entity %s (%s) is using state class '%s' which "
                "is impossible considering device class ('%s') it is using; "
                "expected %s%s; "
                "Please update your configuration if your entity is manually "
                "configured, otherwise %s",
                self.entity_id,
                type(self),
                state_class,
                device_class,
                "None or one of " if classes else "None",
                ", ".join(f"'{value.value}'" for value in classes),
                report_issue,
            )

        # Checks below only apply if there is a value
        if value is None:
            return None

        # Received a datetime
        if device_class == SensorDeviceClass.TIMESTAMP:
            try:
                # We cast the value, to avoid using isinstance, but satisfy
                # typechecking. The errors are guarded in this try.
                value = cast(datetime, value)
                if value.tzinfo is None:
                    raise ValueError(
                        f"Invalid datetime: {self.entity_id} provides state '{value}', "
                        "which is missing timezone information"
                    )

                if value.tzinfo != timezone.utc:
                    value = value.astimezone(timezone.utc)

                return value.isoformat(timespec="seconds")
            except (AttributeError, OverflowError, TypeError) as err:
                raise ValueError(
                    f"Invalid datetime: {self.entity_id} has timestamp device class "
                    f"but provides state {value}:{type(value)} resulting in '{err}'"
                ) from err

        # Received a date value
        if device_class == SensorDeviceClass.DATE:
            try:
                # We cast the value, to avoid using isinstance, but satisfy
                # typechecking. The errors are guarded in this try.
                value = cast(date, value)
                return value.isoformat()
            except (AttributeError, TypeError) as err:
                raise ValueError(
                    f"Invalid date: {self.entity_id} has date device class "
                    f"but provides state {value}:{type(value)} resulting in '{err}'"
                ) from err

        # Enum checks
        if (
            options := self.options
        ) is not None or device_class == SensorDeviceClass.ENUM:
            if device_class != SensorDeviceClass.ENUM:
                reason = "is missing the enum device class"
                if device_class is not None:
                    reason = f"has device class '{device_class}' instead of 'enum'"
                raise ValueError(
                    f"Sensor {self.entity_id} is providing enum options, but {reason}"
                )

            if options and value not in options:
                raise ValueError(
                    f"Sensor {self.entity_id} provides state value '{value}', "
                    "which is not in the list of options provided"
                )
            return value

        suggested_precision = self.suggested_display_precision

        # If the sensor has neither a device class, a state class, a unit of measurement
        # nor a precision then there are no further checks or conversions
        if not self._numeric_state_expected:
            return value

        # From here on a numerical value is expected
        numerical_value: int | float | Decimal
        if not isinstance(value, (int, float, Decimal)):
            try:
                if isinstance(value, str) and "." not in value and "e" not in value:
                    numerical_value = int(value)
                else:
                    numerical_value = float(value)  # type:ignore[arg-type]
            except (TypeError, ValueError) as err:
                raise ValueError(
                    f"Sensor {self.entity_id} has device class '{device_class}', "
                    f"state class '{state_class}' unit '{unit_of_measurement}' and "
                    f"suggested precision '{suggested_precision}' thus indicating it "
                    f"has a numeric value; however, it has the non-numeric value: "
                    f"'{value}' ({type(value)})"
                ) from err
        else:
            numerical_value = value

        if (
            native_unit_of_measurement != unit_of_measurement
            and device_class in UNIT_CONVERTERS
        ):
            # Unit conversion needed
            converter = UNIT_CONVERTERS[device_class]

            converted_numerical_value = UNIT_CONVERTERS[device_class].convert(
                float(numerical_value),
                native_unit_of_measurement,
                unit_of_measurement,
            )

            # If unit conversion is happening, and there's no rounding for display,
            # do a best effort rounding here.
            if (
                suggested_precision is None
                and self._sensor_option_display_precision is None
            ):
                # Deduce the precision by finding the decimal point, if any
                value_s = str(value)
                precision = (
                    len(value_s) - value_s.index(".") - 1 if "." in value_s else 0
                )

                # Scale the precision when converting to a larger unit
                # For example 1.1 Wh should be rendered as 0.0011 kWh, not 0.0 kWh
                ratio_log = max(
                    0,
                    log10(
                        converter.get_unit_ratio(
                            native_unit_of_measurement, unit_of_measurement
                        )
                    ),
                )
                precision = precision + floor(ratio_log)

                value = f"{converted_numerical_value:.{precision}f}"
                # This can be replaced with adding the z option when we drop support for
                # Python 3.10
                value = NEGATIVE_ZERO_PATTERN.sub(r"\1", value)
            else:
                value = converted_numerical_value

        # Validate unit of measurement used for sensors with a device class
        if (
            not self._invalid_unit_of_measurement_reported
            and device_class
            and (units := DEVICE_CLASS_UNITS.get(device_class)) is not None
            and native_unit_of_measurement not in units
        ):
            self._invalid_unit_of_measurement_reported = True
            report_issue = self._suggest_report_issue()

            # This should raise in Home Assistant Core 2023.6
            _LOGGER.warning(
                (
                    "Entity %s (%s) is using native unit of measurement '%s' which "
                    "is not a valid unit for the device class ('%s') it is using; "
                    "expected one of %s; "
                    "Please update your configuration if your entity is manually "
                    "configured, otherwise %s"
                ),
                self.entity_id,
                type(self),
                native_unit_of_measurement,
                device_class,
                [str(unit) if unit else "no unit of measurement" for unit in units],
                report_issue,
            )

        return value

    def __repr__(self) -> str:
        """Return the representation.

        Entity.__repr__ includes the state in the generated string, this fails if we're
        called before self.hass is set.
        """
        if not self.hass:
            return f"<Entity {self.name}>"

        return super().__repr__()

    @callback
    def async_registry_entry_updated(self) -> None:
        """Run when the entity registry entry has been updated."""
        self._async_read_entity_options()
        #self._update_suggested_precision()

    @callback
    def _async_read_entity_options(self) -> None:
        """Read entity options from entity registry.

        Called when the entity registry entry has been updated and before the sensor is
        added to the state machine.
        """
        self._sensor_option_display_precision = self._suggested_precision_or_none()
        assert self.registry_entry
        if (
            sensor_options := self.registry_entry.options.get(f"{DOMAIN}.private")
        ) and "refresh_initial_entity_options" in sensor_options:
            registry = er.async_get(self.hass)
            initial_options = self.get_initial_entity_options() or {}
            registry.async_update_entity_options(
                self.entity_id,
                f"{DOMAIN}.private",
                initial_options.get(f"{DOMAIN}.private"),
            )
        self._sensor_option_unit_of_measurement = self._custom_unit_or_undef(
            DOMAIN, CONF_UNIT_OF_MEASUREMENT
        )
        if self._sensor_option_unit_of_measurement is UNDEFINED:
            self._sensor_option_unit_of_measurement = self._custom_unit_or_undef(
                f"{DOMAIN}.private", "suggested_unit_of_measurement"
            )




