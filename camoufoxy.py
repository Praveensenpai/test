from contextlib import asynccontextmanager
from typing import AsyncIterator

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import BrowserContext


# <class 'playwright.async_api._generated.BrowserContext'>
@asynccontextmanager
async def Camoufoxy() -> AsyncIterator[BrowserContext]:
    """
    Camoufoxy is a context manager that yields a AsyncCamoufox instance.
    """
    async with AsyncCamoufox(
        headless="virtual",
        # config={"forceScopeAccess": True},
        # disable_coop=True,
        # i_know_what_im_doing=True,
        # persistent_context=True,
        # user_data_dir="./.user-data",
        # enable_cache=True,
        # geoip=True if config.USE_PROXY else False,
        # proxy=proxy_manager.proxy if config.USE_PROXY else None,
        locale="en-US",
        # firefox_user_prefs={
        # "permissions.default.image": 2,  # 1=Allow, 2=Block all images
        # "media.autoplay.default": 5,  # Block video autoplay
        # "media.preload": 0,  # Don't buffer videos in the background
        # "media.volume_scale": "0.0",  # Mute any audio just in case
        # },
    ) as browser:
        yield browser  # type: ignore
