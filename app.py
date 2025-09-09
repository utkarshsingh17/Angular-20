#!/usr/bin/env python3
"""
utils/parser.py
Parsing and normalization helpers for weather sensor text fields.
Standard units used by functions:
 - temperature => Celsius (°C)
 - wind_speed  => kilometers per hour (km/h)
 - precipitation => millimeters per hour (mm/h)
 - humidity => percent (0-100)
 - pressure => hectopascals (hPa)
"""
import re
from typing import Optional

_NUM_RE = r"([-+]?\d+(?:\.\d+)?)"

def _extract_number_and_unit(value: str):
    if value is None:
        return None, None
    s = str(value).strip()
    if s == "":
        return None, None
    # remove redundant whitespace around degree symbol
    s = s.replace("°", "")
    # common separators cleaned
    s = re.sub(r"\s+", " ", s)
    # try to find a number first
    m = re.search(_NUM_RE, s)
    if not m:
        return None, None
    number = float(m.group(1))
    # unit: anything non-numeric after number
    rest = s[m.end():].strip()
    # normalize typical units to lowercase compact form
    rest = rest.replace("per", "/").lower()
    rest = rest.replace("meters", "m").replace("metres", "m")
    rest = rest.replace("kilometers", "km").replace("kilometres", "km")
    rest = rest.replace("hours", "h").replace("hour", "h")
    rest = rest.replace("hours", "h")
    return number, rest

def parse_temperature(value: str) -> Optional[float]:
    """Return temperature in Celsius (float) or None."""
    if value is None:
        return None
    val = str(value).strip()
    # accept forms: "32 C", "32°C", "90 F", "287.2 K", "30.1 C"
    num, unit = _extract_number_and_unit(val)
    if num is None:
        return None
    # determine unit
    if unit is None or unit == "" or unit.startswith("c"):
        return float(num)
    if unit.startswith("f"):
        # Fahrenheit -> Celsius
        return (num - 32.0) * 5.0 / 9.0
    if unit.startswith("k"):
        # Kelvin -> Celsius
        return float(num) - 273.15
    # if numeric but no recognized unit, assume Celsius
    return float(num)

def parse_wind_speed(value: str) -> Optional[float]:
    """Return wind speed in km/h (float) or None.
    Handles: km/h, kmh, mph, m/s, m/s, m/h (meters per hour) etc.
    """
    if value is None:
        return None
    num, unit = _extract_number_and_unit(str(value))
    if num is None:
        return None
    u = (unit or "").strip()
    # variations: "km/h", "kmh", "km / h"
    if u.startswith("km"):
        return float(num)
    if u.startswith("mph"):
        # miles per hour -> km/h
        return float(num) * 1.60934
    if u.startswith("m/s") or u == "m/s":
        # meters per second -> km/h
        return float(num) * 3.6
    if u.startswith("m/h") or u == "m/h":
        # meters per hour -> km/h (1 m = 0.001 km)
        return float(num) * 0.001
    # if no unit, assume km/h
    return float(num)

def parse_precipitation(value: str) -> Optional[float]:
    """Return precipitation intensity in mm/h or None.
    Handles mm/h, mmh, in/h (inches per hour), inph, etc.
    """
    if value is None:
        return None
    num, unit = _extract_number_and_unit(str(value))
    if num is None:
        return None
    u = (unit or "").strip()
    if u.startswith("mm"):
        return float(num)
    if u.startswith("in"):
        # inches per hour -> mm/h
        return float(num) * 25.4
    # if unitless, assume mm/h
    return float(num)

def parse_humidity(value: str) -> Optional[float]:
    """Return humidity in percent (0-100) as float, or None."""
    if value is None:
        return None
    num, unit = _extract_number_and_unit(str(value))
    if num is None:
        return None
    # ensure within 0-100
    val = float(num)
    return max(0.0, min(100.0, val))

def parse_pressure(value: str) -> Optional[float]:
    """Return pressure in hPa (float) or None. Accepts hPa only."""
    if value is None:
        return None
    num, unit = _extract_number_and_unit(str(value))
    if num is None:
        return None
    # if unit indicates hpa, return as-is
    u = (unit or "").strip()
    if u.startswith("hpa") or u.startswith("hp"):
        return float(num)
    # sometimes reported in Pa (unlikely) - if 'pa' convert /100
    if u.startswith("pa") and float(num) > 1000:
        # e.g., 101325 Pa -> 1013.25 hPa
        return float(num) / 100.0
    # otherwise assume hPa
    return float(num)
