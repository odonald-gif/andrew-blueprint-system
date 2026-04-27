import logging
import asyncio
from typing import List, Dict, Any
from bs4 import BeautifulSoup

# Try importing playwright, fallback gracefully if not installed yet
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)

class DigitalScout:
    """
    The Advanced Internet Scout.
    Uses Playwright and BeautifulSoup to autonomously navigate JavaScript-heavy pages
    like Upwork to pull real-time remote jobs.
    """
    
    def __init__(self, target_keywords: List[str] = None):
        # Targeting high-paying, fast-turnaround, high-accuracy task keywords
        self.target_keywords = target_keywords or ["python automation", "api integration", "web scraping", "flutter bug"]

    def perform_routine_scan(self) -> Dict[str, List[Dict[str, Any]]]:
        """Runs all configured scout operations and returns intelligence."""
        # Because we're in a sync function inside nervous_system, 
        # we run the async playwright loop explicitly
        jobs = asyncio.run(self.scan_jobs_live())
        
        # Scholarship logic
        scholarships = self.scan_scholarships_live()
        
        return {
            "new_jobs": jobs,
            "new_scholarships": scholarships
        }

    async def scan_jobs_live(self) -> List[Dict[str, Any]]:
        """Scrapes jobs directly using a Headless Chromium browser instances."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not installed. Run 'pip install playwright' and 'playwright install'. Andrew, use Developer Bridge to fix this.")

        logger.info(f"Initiating Stealth Scout for fast-turnaround gigs searching: {self.target_keywords[0]}...")
        # Upwork formats spaces as %20 in search URL
        search_query = self.target_keywords[0].replace(' ', '%20')
        url = f"https://www.upwork.com/nx/search/jobs/?q={search_query}&sort=recency"
        
        scraped_jobs = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # Setting an extended timeout as SPA pages take time
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for job tiles to populate
                await page.wait_for_selector('section.up-card-section', timeout=15000)
                
                html_content = await page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                job_sections = soup.find_all('section', class_='up-card-section')
                
                for section in job_sections[:3]: # grab top 3
                    title_elem = section.find(['h2', 'h3'])
                    desc_elem = section.find('span', class_='up-text-break')
                    link_elem = section.find('a', href=True)
                    
                    if title_elem and link_elem:
                        scraped_jobs.append({
                            "platform": "Upwork (Playwright)",
                            "title": title_elem.get_text(separator=" ", strip=True),
                            "url": f"https://www.upwork.com{link_elem['href']}",
                            "description_snippet": desc_elem.get_text(strip=True)[:200] if desc_elem else "No description available"
                        })
                
                await browser.close()
                return scraped_jobs
                
        except Exception as e:
            logger.error(f"Playwright Scraping Error: {e}")
            raise RuntimeError(f"Playwright Scraping Error: {e}")

    def scan_scholarships_live(self) -> List[Dict[str, Any]]:
        """Scrapes real scholarships from an open directory"""
        import requests
        logger.info("Scanning for Master's programs and scholarships...")
        try:
            url = "https://www.scholars4dev.com/category/level-of-study/masters-scholarships/"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise RuntimeError(f"Failed to fetch scholarships, status code: {response.status_code}")
                
            soup = BeautifulSoup(response.text, 'html.parser')
            posts = soup.find_all('div', class_='post')
            results = []
            
            for post in posts[:3]:
                title_elem = post.find('h2')
                link_elem = title_elem.find('a') if title_elem else None
                details = post.find('div', class_='entry')
                
                if title_elem and link_elem:
                    results.append({
                        "program": title_elem.text.strip(),
                        "url": link_elem['href'],
                        "status": "Applications Open",
                        "description": details.text.strip()[:200] if details else "No description"
                    })
            
            if not results:
                 raise RuntimeError("Scraped scholarship page, but found no results.")
            return results
        except Exception as e:
            logger.error(f"Scholarship Scrape Error: {e}")
            raise RuntimeError(f"Scholarship Scrape Error: {e}")
