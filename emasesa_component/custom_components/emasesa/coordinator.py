"""DataUpdateCoordinator para EMASESA."""
from __future__ import annotations

import logging
from datetime import timedelta, datetime, timezone
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.const import UnitOfVolume

from .api import EmasesaApiClient, EmasesaApiError, EmasesaAuthError
from .const import CONF_CONTRATO, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

TZ_MADRID = ZoneInfo("Europe/Madrid")


class EmasesaDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordina las actualizaciones de datos de EMASESA."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._client = EmasesaApiClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            contrato=entry.data[CONF_CONTRATO],
        )
        self._contrato = entry.data[CONF_CONTRATO]
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)),
        )

    async def _async_update_data(self) -> dict:
        """Obtener datos y actualizar estadísticas históricas."""
        try:
            data = await self.hass.async_add_executor_job(self._client.get_consumos)
        except EmasesaAuthError as err:
            raise UpdateFailed(f"Error de autenticación EMASESA: {err}") from err
        except EmasesaApiError as err:
            raise UpdateFailed(f"Error API EMASESA: {err}") from err

        await self._inject_statistics(data.get("dias_raw", []))
        return data

    async def _inject_statistics(self, dias: list) -> None:
        """
        Inyectar consumo horario como estadística externa.
        Las horas de la API están en hora LOCAL de Madrid.
        Se convierten a UTC para almacenar en HA, que luego
        las muestra en la zona horaria local correctamente.
        """
        if not dias:
            return

        statistic_id = f"emasesa:agua_{self._contrato}"
        registros: list[tuple[datetime, float]] = []

        for dia in dias:
            if dia.get("estado") == "SIN_DATOS":
                continue

            fecha_str = dia.get("fecha")
            detalle = dia.get("detalle", [])

            for lectura in detalle:
                hora = int(lectura.get("hora", 0))
                consumo_l = lectura.get("consumo", 0) or 0
                consumo_m3 = round(consumo_l / 1000, 6)

                try:
                    # Hora local Madrid → convertir a UTC para almacenar
                    dt_local = datetime.strptime(
                        f"{fecha_str} {hora:02d}:00:00", "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=TZ_MADRID)
                    dt_utc = dt_local.astimezone(timezone.utc)
                except ValueError:
                    continue

                registros.append((dt_utc, consumo_m3))

        if not registros:
            _LOGGER.debug("No hay registros válidos que inyectar.")
            return

        registros.sort(key=lambda x: x[0])

        statistics: list[StatisticData] = []
        running_sum = 0.0

        for dt, consumo_m3 in registros:
            running_sum = round(running_sum + consumo_m3, 6)
            statistics.append(
                StatisticData(
                    start=dt,
                    state=consumo_m3,
                    sum=running_sum,
                    mean=None,
                    min=None,
                    max=None,
                )
            )

        metadata = StatisticMetaData(
            has_mean=False,
            has_sum=True,
            name=f"EMASESA Agua {self._contrato}",
            source="emasesa",
            statistic_id=statistic_id,
            unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        )

        _LOGGER.info(
            "Inyectando %d registros en %s (0 → %.3f m³)",
            len(statistics),
            statistic_id,
            running_sum,
        )
        async_add_external_statistics(self.hass, metadata, statistics)
