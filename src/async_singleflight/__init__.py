"""async-singleflight: High-performance request coalescing engine for Python asyncio."""

from async_singleflight.coordinator import Result, SingleFlight

__version__ = "0.1.0"
__all__ = ["SingleFlight", "Result", "__version__"]
