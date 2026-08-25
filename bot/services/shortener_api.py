import aiohttp
from bot.utils.logger import logger


async def shorten_url(domain: str, api_key: str, long_url: str) -> str | None:
    """
    Calls a generic shortener API: https://<domain>/api?api=<key>&url=<url>
    Returns the shortened URL, or None on failure (caller should fall back
    to sending the unshortened link and log the failure).
    """
    if not domain or not api_key:
        return None

    endpoint = f"https://{domain}/api"
    params = {"api": api_key, "url": long_url, "format": "json"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json(content_type=None)
                shortened = data.get("shortenedUrl") or data.get("short_url") or data.get("shortlink")
                return shortened
    except Exception as e:
        logger.warning(f"Shortener API failed: {e}")
        return None
