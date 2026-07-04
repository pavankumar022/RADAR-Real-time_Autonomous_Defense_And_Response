"""
RADAR — Geolocation Service
Uses ip-api.com (free, no key required, 45 req/min).
In-memory + SQLite cache to avoid re-querying the same IP.
"""
import asyncio
import logging
import httpx
from typing import Optional
from backend import database as db

log = logging.getLogger(__name__)

# In-memory L1 cache (process lifetime, O(1) lookup)
_mem_cache: dict[str, dict] = {}

# Fallback table for known/private IP ranges (offline safety net)
_PRIVATE_FALLBACK = {
    "10.": {"lat": 37.7749, "lon": -122.4194, "country": "US", "city": "San Francisco"},
    "192.168.": {"lat": 37.7749, "lon": -122.4194, "country": "US", "city": "Local Network"},
    "172.16.": {"lat": 37.7749, "lon": -122.4194, "country": "US", "city": "Local Network"},
    "127.": {"lat": 37.7749, "lon": -122.4194, "country": "US", "city": "Localhost"},
    "LOCAL_SRV": {"lat": 37.7749, "lon": -122.4194, "country": "US", "city": "Local Server"},
}

# A curated fallback for demo IPs that might hit rate limits
_DEMO_IP_FALLBACK: dict[str, dict] = {
    "185.22.45.10": {"lat": 55.7558, "lon": 37.6173, "country": "RU", "city": "Moscow"},
    "45.122.9.201": {"lat": 39.9042, "lon": 116.4074, "country": "CN", "city": "Beijing"},
    "103.45.11.2": {"lat": 28.6139, "lon": 77.2090, "country": "IN", "city": "New Delhi"},
    "92.45.1.221": {"lat": 48.8566, "lon": 2.3522, "country": "FR", "city": "Paris"},
    "10.0.4.112": {"lat": 37.7749, "lon": -122.4194, "country": "US", "city": "Internal"},
    "10.0.1.55": {"lat": 37.7749, "lon": -122.4194, "country": "US", "city": "Internal"},
}


def _private_fallback(ip: str) -> Optional[dict]:
    """Return fallback geo for private/local IPs."""
    for prefix, geo in _PRIVATE_FALLBACK.items():
        if ip.startswith(prefix):
            return geo
    if ip in _DEMO_IP_FALLBACK:
        return _DEMO_IP_FALLBACK[ip]
    return None


async def lookup(ip: str) -> dict:
    """
    Resolve an IP address to lat/lon/country/city.
    Priority: L1 mem cache → SQLite cache → ip-api.com → demo fallback.
    Never throws — always returns a dict (possibly zeroed for unknown IPs).
    """
    # L1: memory
    if ip in _mem_cache:
        return _mem_cache[ip]

    # Check private/local ranges first (no API call needed)
    priv = _private_fallback(ip)
    if priv:
        _mem_cache[ip] = priv
        return priv

    # L2: SQLite cache
    cached = await db.get_geo_cache(ip)
    if cached:
        result = {
            "lat": cached["lat"],
            "lon": cached["lon"],
            "country": cached["country"],
            "city": cached["city"],
        }
        _mem_cache[ip] = result
        return result

    # L3: ip-api.com (async HTTP, timeout 3s)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,lat,lon,country,countryCode,city"},
            )
            data = resp.json()
            if data.get("status") == "success":
                result = {
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "country": data.get("countryCode", data.get("country", "??")),
                    "city": data.get("city", "Unknown"),
                }
                _mem_cache[ip] = result
                # Persist to SQLite async (fire-and-forget)
                asyncio.create_task(
                    db.set_geo_cache(ip, result["lat"], result["lon"], result["country"], result["city"])
                )
                return result
    except Exception as e:
        log.debug(f"Geolocation lookup failed for {ip}: {e}")

    # Fallback: unknown → null island with unknown labels
    fallback = {"lat": 0.0, "lon": 0.0, "country": "??", "city": "Unknown"}
    _mem_cache[ip] = fallback
    return fallback
