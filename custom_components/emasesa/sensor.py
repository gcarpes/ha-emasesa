"""Sensores de consumo de agua EMASESA."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EmasesaDataUpdateCoordinator


@dataclass
class EmasesaSensorEntityDescription(SensorEntityDescription):
    """Descripción extendida para sensores EMASESA."""
    data_key: str = ""
    extra_attrs: list = field(default_factory=list)


SENSORS: tuple[EmasesaSensorEntityDescription, ...] = (
    EmasesaSensorEntityDescription(
        key="consumo_hoy_m3",
        data_key="consumo_hoy_m3",
        name="EMASESA Consumo Hoy",
        icon="mdi:water",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        extra_attrs=["fecha_ultima_lectura", "contrato", "ultima_actualizacion", "dias_disponibles"],
    ),
    EmasesaSensorEntityDescription(
        key="consumo_medio_diario_m3",
        data_key="consumo_medio_diario_m3",
        name="EMASESA Consumo Medio Diario",
        icon="mdi:chart-bar",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
        extra_attrs=["dias_disponibles", "contrato", "ultima_actualizacion"],
    ),
    EmasesaSensorEntityDescription(
        key="estado_contador",
        data_key="estado_contador",
        name="EMASESA Estado Contador",
        icon="mdi:counter",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=None,
        extra_attrs=["fecha_ultima_lectura", "contrato", "ultima_actualizacion"],
    ),
    EmasesaSensorEntityDescription(
        key="error_contador",
        data_key="error_contador",
        name="EMASESA Error Contador",
        icon="mdi:alert-circle",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.ENUM,
        state_class=None,
        extra_attrs=["fecha_ultima_lectura", "contrato", "ultima_actualizacion"],
    ),
    EmasesaSensorEntityDescription(
        key="consumo_nocturno",
        data_key="consumo_nocturno",
        name="EMASESA Consumo Nocturno",
        icon="mdi:pipe-leak",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.ENUM,
        state_class=None,
        extra_attrs=["fecha_ultima_lectura", "contrato", "ultima_actualizacion"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EmasesaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        EmasesaSensor(coordinator, entry, description)
        for description in SENSORS
    )


class EmasesaSensor(CoordinatorEntity[EmasesaDataUpdateCoordinator], SensorEntity):
    """Sensor de consumo de agua EMASESA."""

    entity_description: EmasesaSensorEntityDescription

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"emasesa_{entry.data['contrato']}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data["contrato"])},
            name=f"EMASESA Contrato {entry.data['contrato']}",
            manufacturer="EMASESA",
            model="Telecontaje Ciudadanos",
            configuration_url="https://datosabiertos.emasesa.com",
        )

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.data_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.data is None:
            return {}
        return {
            key: self.coordinator.data.get(key)
            for key in self.entity_description.extra_attrs
            if self.coordinator.data.get(key) is not None
        }

    @property
    def available(self) -> bool:
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.get(self.entity_description.data_key) is not None
        )
