"""Cliente API para EMASESA."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from .const import API_TOKEN_URL, API_CONSUMOS_URL

_LOGGER = logging.getLogger(__name__)


class EmasesaAuthError(Exception):
    """Error de autenticación con EMASESA."""


class EmasesaApiError(Exception):
    """Error general de la API de EMASESA."""


class EmasesaApiClient:
    """Cliente para la API REST de EMASESA."""

    def __init__(self, username: str, password: str, contrato: str) -> None:
        self._username = username
        self._password = password
        self._contrato = contrato
        self._token: str | None = None
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def authenticate(self) -> None:
        """Obtener token de autenticación de EMASESA."""
        _LOGGER.debug("Autenticando con EMASESA API...")
        try:
            resp = self._session.post(
                API_TOKEN_URL,
                data={"username": self._username, "password": self._password},
                timeout=30,
            )
            if resp.status_code == 401:
                raise EmasesaAuthError("Credenciales incorrectas")
            resp.raise_for_status()

            data = resp.json()
            token = None
            for key in ("token", "access_token", "Bearer", "bearer", "jwt", "accessToken"):
                if key in data:
                    token = data[key]
                    break

            if not token:
                _LOGGER.error("Respuesta de token inesperada: %s", data)
                raise EmasesaAuthError("No se encontró token en la respuesta")

            self._token = token
            self._session.headers.update({"Authorization": f"Bearer {self._token}"})
            _LOGGER.debug("Autenticación exitosa.")

        except requests.exceptions.ConnectionError as err:
            raise EmasesaApiError(f"Error de conexión: {err}") from err
        except requests.exceptions.Timeout as err:
            raise EmasesaApiError(f"Timeout: {err}") from err
        except requests.exceptions.HTTPError as err:
            raise EmasesaApiError(f"Error HTTP: {err}") from err

    def get_consumos(self) -> dict:
        """Obtener y parsear datos de consumo del contrato."""
        if not self._token:
            self.authenticate()

        url = f"{API_CONSUMOS_URL}/{self._contrato}"
        _LOGGER.debug("Consultando: %s", url)

        try:
            resp = self._session.get(url, timeout=30)

            if resp.status_code == 401:
                _LOGGER.debug("Token expirado, renovando...")
                self._token = None
                self.authenticate()
                resp = self._session.get(url, timeout=30)

            resp.raise_for_status()
            return self._parse(resp.json())

        except requests.exceptions.ConnectionError as err:
            raise EmasesaApiError(f"Error de conexión: {err}") from err
        except requests.exceptions.Timeout as err:
            raise EmasesaApiError(f"Timeout: {err}") from err
        except requests.exceptions.HTTPError as err:
            raise EmasesaApiError(f"Error HTTP: {err}") from err

    def _parse(self, data: list) -> dict:
        """Parsear respuesta real de EMASESA. Consumo en LITROS."""
        result = {
            "contrato": self._contrato,
            "ultima_actualizacion": datetime.now(timezone.utc).isoformat(),
            "consumo_hoy_l": None,
            "consumo_hoy_m3": None,
            "consumo_ayer_l": None,
            "consumo_ayer_m3": None,
            "lectura_contador_l": None,
            "lectura_contador_m3": None,
            "consumo_total_mes_l": None,
            "consumo_total_mes_m3": None,
            "consumo_medio_diario_l": None,
            "consumo_medio_diario_m3": None,
            "consumo_maximo_dia_l": None,
            "consumo_maximo_dia_m3": None,
            "fecha_ultima_lectura": None,
            "estado_ultima_lectura": None,
            "dias_disponibles": 0,
            "dias_raw": data,  # <-- datos crudos completos para inyectar en recorder
        }

        if not isinstance(data, list) or not data:
            return result

        result["dias_disponibles"] = len(data)

        dias_ok = [
            d for d in data
            if d.get("estado") in ("OK", "PARCIAL") and d.get("indice") is not None
        ]

        if dias_ok:
            ultimo = dias_ok[-1]
            result["fecha_ultima_lectura"] = ultimo.get("fecha")
            result["estado_ultima_lectura"] = ultimo.get("estado")

            indice = ultimo.get("indice")
            if indice is not None:
                result["lectura_contador_l"] = indice
                result["lectura_contador_m3"] = round(indice / 1000, 3)

            consumo_hoy = ultimo.get("consumo", 0)
            result["consumo_hoy_l"] = consumo_hoy
            result["consumo_hoy_m3"] = round(consumo_hoy / 1000, 3)

            if len(dias_ok) >= 2:
                consumo_ayer = dias_ok[-2].get("consumo", 0)
                result["consumo_ayer_l"] = consumo_ayer
                result["consumo_ayer_m3"] = round(consumo_ayer / 1000, 3)

        dias_completos = [d for d in data if d.get("estado") == "OK"]
        if dias_completos:
            consumos = [d.get("consumo", 0) for d in dias_completos]
            total = sum(consumos)
            result["consumo_total_mes_l"] = total
            result["consumo_total_mes_m3"] = round(total / 1000, 3)
            result["consumo_medio_diario_l"] = round(total / len(consumos), 1)
            result["consumo_medio_diario_m3"] = round(total / len(consumos) / 1000, 3)
            result["consumo_maximo_dia_l"] = max(consumos)
            result["consumo_maximo_dia_m3"] = round(max(consumos) / 1000, 3)

        return result
