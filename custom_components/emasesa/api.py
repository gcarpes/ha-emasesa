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
        """
        Parsear respuesta de EMASESA.

        Devuelve:
        - Datos para sensores HA
        - dias_raw: JSON completo para inyectar estadísticas horarias
        - ultimo_dia: datos del último día válido para sensores de estado
        """
        result = {
            "contrato": self._contrato,
            "ultima_actualizacion": datetime.now(timezone.utc).isoformat(),
            # Sensor consumo hoy
            "consumo_hoy_m3": None,
            # Sensor media diaria
            "consumo_medio_diario_m3": None,
            # Sensor estado contador
            "estado_contador": None,
            # Sensor error contador
            "error_contador": None,
            # Sensor consumo nocturno (posible fuga)
            "consumo_nocturno": None,
            # Metadatos
            "fecha_ultima_lectura": None,
            "dias_disponibles": 0,
            # Raw para estadísticas horarias
            "dias_raw": data,
        }

        if not isinstance(data, list) or not data:
            return result

        result["dias_disponibles"] = len(data)

        # Días con datos completos OK
        dias_ok = [d for d in data if d.get("estado") == "OK"]

        # Último día con datos válidos (OK o PARCIAL con índice)
        dias_validos = [
            d for d in data
            if d.get("estado") in ("OK", "PARCIAL") and d.get("indice") is not None
        ]

        if dias_validos:
            ultimo = dias_validos[-1]
            result["fecha_ultima_lectura"] = ultimo.get("fecha")

            # Consumo hoy en m³
            consumo_hoy = ultimo.get("consumo", 0) or 0
            result["consumo_hoy_m3"] = round(consumo_hoy / 1000, 3)

            # Estado del contador del último día
            result["estado_contador"] = ultimo.get("estado")

            # Error en la lectura
            result["error_contador"] = bool(ultimo.get("erroneo", False))

            # Consumo nocturno — true si alguna hora tiene nocturno=true
            detalle = ultimo.get("detalle", [])
            result["consumo_nocturno"] = any(
                h.get("nocturno", False) for h in detalle
            )

        # Media diaria sobre días OK completos
        if dias_ok:
            consumos = [d.get("consumo", 0) or 0 for d in dias_ok]
            total = sum(consumos)
            result["consumo_medio_diario_m3"] = round(
                total / len(consumos) / 1000, 3
            )

        return result
