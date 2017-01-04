"""
Support for the MQTT themostats.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate.mqtt/
"""
from homeassistant.components.mqtt import CONF_STATE_TOPIC, CONF_COMMAND_TOPIC, CONF_QOS, CONF_RETAIN
from homeassistant.components.climate import (
    ClimateDevice, ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW)
from homeassistant.const import CONF_NAME, TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_TEMPERATURE
import homeassistant.components.mqtt as mqtt

DEPENDENCIES = ['mqtt']

CONF_MODE_TOPIC = 'mode_topic'

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Demo climate devices."""
    add_devices([
        MqttClimate(hass, config.get(CONF_NAME), config.get(CONF_STATE_TOPIC), config.get(CONF_COMMAND_TOPIC), config.get(CONF_RETAIN), None, TEMP_CELSIUS, config.get(CONF_MODE_TOPIC), False, 18, 22, "On High", None, None, "Auto", None, None),
    ])


# pylint: disable=too-many-arguments, too-many-public-methods
class MqttClimate(ClimateDevice):
    """Representation of a mqtt climate device."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, hass, name, state_topic, command_topic, retain, target_temperature, unit_of_measurement, operation_topic,
                 away, away_temperature, current_temperature, current_fan_mode,
                 target_humidity, current_humidity,
                 current_operation, target_temp_high, target_temp_low):
        """Initialize the climate device."""
        self._hass = hass
        self._name = name
        self._state_topic = state_topic
        self._command_topic = command_topic
        self._retain = retain
        self._target_temperature = target_temperature
        self._target_humidity = target_humidity
        self._unit_of_measurement = unit_of_measurement
        self._away = away
        self._away_temperature = away_temperature
        self._current_temperature = current_temperature
        self._current_humidity = current_humidity
        self._current_fan_mode = current_fan_mode
        self._operation_topic = operation_topic
        self._current_operation = current_operation
        self._operation_list = ["Off", "On", "Auto", "Frost"]
        self._swing_list = ["Auto", "1", "2", "3", "Off"]
        self._target_temperature_high = target_temp_high
        self._target_temperature_low = target_temp_low

        def state_message_received(topic, payload, qos):
            """A new MQTT message has been received."""
            self._current_temperature = payload
            self.update_ha_state()

        def command_message_received(topic, payload, qos):
            """A new MQTT message has been received."""
            self._target_temperature = payload
            self._saved_target_temperature = self._target_temperature
            self.update_ha_state()

        def mode_message_received(topic, payload, qos):
            """A new MQTT message has been received."""
            self._current_operation = self._operation_list[int(payload, 10)]
            self.update_ha_state()

        mqtt.subscribe(hass, self._state_topic, state_message_received, 0)
        mqtt.subscribe(hass, self._command_topic, command_message_received, 0)
        mqtt.subscribe(hass, self._operation_topic, mode_message_received, 0)

    @property
    def should_poll(self):
        """Polling not needed for a demo climate device."""
        return False

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return self._target_temperature_high

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        return self._target_temperature_low

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._current_humidity

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return self._target_humidity

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._current_operation

    @property
    def operation_list(self):
        """List of available operation modes."""
        return self._operation_list

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self._away

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
            mqtt.publish(self.hass, self._command_topic+"/set", self._target_temperature, 0, self._retain)
        if kwargs.get(ATTR_TARGET_TEMP_HIGH) is not None and \
           kwargs.get(ATTR_TARGET_TEMP_LOW) is not None:
            self._target_temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
            self._target_temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        self.update_ha_state()

    def set_humidity(self, humidity):
        """Set new target temperature."""
        self._target_humidity = humidity
        self.update_ha_state()

    def set_swing_mode(self, swing_mode):
        """Set new target temperature."""
        self._current_swing_mode = swing_mode
        self.update_ha_state()

    def set_fan_mode(self, fan):
        """Set new target temperature."""
        self._current_fan_mode = fan
        self.update_ha_state()

    def set_operation_mode(self, operation_mode):
        """Set new target temperature."""
        self._current_operation = operation_mode
        mqtt.publish(self.hass, self._operation_topic+"/set", self._operation_list.index(self._current_operation), 0, self._retain)
        self.update_ha_state()

    def turn_away_mode_on(self):
        """Turn away mode on."""
        self._away = True
        self._saved_target_temperature = self._target_temperature
        self._target_temperature = self._away_temperature
        mqtt.publish(self.hass, self._command_topic+"/set", self._target_temperature, 0, self._retain)
        self.update_ha_state()

    def turn_away_mode_off(self):
        """Turn away mode off."""
        self._away = False
        self._target_temperature = self._saved_target_temperature
        mqtt.publish(self.hass, self._command_topic+"/set", self._target_temperature, 0, self._retain)
        self.update_ha_state()
