"""Thin async wrapper around Playwright — one Chromium page per agent run.

Playwright's own binary (chromium) is downloaded separately via
`playwright install chromium`; the Python package itself is pure Python +
a small native driver process, unaffected by the PyTorch/numba Smart App
Control issue seen elsewhere in this platform.
"""

from playwright.async_api import async_playwright


class BrowserSession:
    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._page = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._page = await self._browser.new_page()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def navigate(self, url: str) -> str:
        await self._page.goto(url, wait_until="domcontentloaded", timeout=20000)
        return f"Navigated to {self._page.url} (title: {await self._page.title()})"

    async def click(self, selector: str) -> str:
        await self._page.click(selector, timeout=8000)
        return f"Clicked '{selector}'"

    async def type_text(self, selector: str, text: str, submit: bool = False) -> str:
        await self._page.fill(selector, text, timeout=8000)
        if submit:
            await self._page.press(selector, "Enter")
        return f"Typed into '{selector}'" + (" and pressed Enter" if submit else "")

    async def extract_text(self, selector: str = "body", max_chars: int = 3000) -> str:
        elements = await self._page.query_selector_all(selector)
        texts = []
        for el in elements[:20]:
            t = await el.inner_text()
            if t.strip():
                texts.append(t.strip())
        combined = "\n".join(texts)
        return (combined[:max_chars] or "(no matching elements or empty text)").strip()

    async def get_title(self) -> str:
        return await self._page.title()

    async def current_url(self) -> str:
        return self._page.url
