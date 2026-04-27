import logging
import asyncio
import os
from typing import Dict, Any

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)

class LinkedInAgent:
    """
    Playwright-based agent to organically interact with LinkedIn
    using Session Cookies to bypass login and avoid API bans.
    """
    def __init__(self):
        # The li_at cookie is the master session token for LinkedIn
        self.session_cookie = os.getenv("LINKEDIN_LI_AT_COOKIE")
        if not self.session_cookie:
            raise ValueError("MISSING LINKEDIN_LI_AT_COOKIE - Cannot authenticate with LinkedIn.")
        
    async def _simulate_human_typing(self, page, selector: str, text: str):
        """Simulates human typing delays."""
        await page.locator(selector).click()
        for char in text:
            await page.keyboard.press(char)
            await asyncio.sleep(0.05) # 50ms delay between keystrokes

    async def draft_and_post(self, content: str, auto_post: bool = False) -> Dict[str, Any]:
        """
        Navigates to LinkedIn, opens the post composer, types the content,
        and optionally posts it.
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed. Run 'pip install playwright' and 'playwright install'.")

        logger.info("Initializing LinkedIn Playwright Session...")
        try:
            async with async_playwright() as p:
                # Launch headful if we want to watch it, headless for background
                browser = await p.chromium.launch(headless=True)
                
                # Setup context with the session cookie
                context = await browser.new_context()
                await context.add_cookies([{
                    "name": "li_at",
                    "value": self.session_cookie,
                    "domain": ".linkedin.com",
                    "path": "/"
                }])
                
                page = await context.new_page()
                
                # Go to feed
                await page.goto("https://www.linkedin.com/feed/")
                
                # Wait for the "Start a post" button and click it
                await page.wait_for_selector("button.share-box-feed-entry__trigger")
                await page.click("button.share-box-feed-entry__trigger")
                
                # Wait for the editor to load
                editor_selector = "div.ql-editor"
                await page.wait_for_selector(editor_selector)
                
                # Type the content organically
                await self._simulate_human_typing(page, editor_selector, content)
                
                result_msg = "Drafted post successfully (did not click Post)."
                
                if auto_post:
                    # In a real scenario, this would find the final 'Post' button
                    post_btn_selector = "button.share-actions__primary-action"
                    await page.click(post_btn_selector)
                    result_msg = "Post published successfully."
                
                await browser.close()
                return {"status": "success", "output": result_msg}
                
        except Exception as e:
            logger.error(f"LinkedIn Playwright Error: {e}")
            return {"status": "error", "output": str(e)}

try:
    linkedin_agent = LinkedInAgent()
except ValueError as e:
    linkedin_agent = None
    logger.warning(f"LinkedIn Agent disabled: {e}")
