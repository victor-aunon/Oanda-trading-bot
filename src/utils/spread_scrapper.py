# Libraries
import asyncio

# Packages
from bs4 import BeautifulSoup
from pyppeteer import launch

fx_url = "https://www.oanda.com/us-en/trading/instruments/"
crypto_url = "https://www.oanda.com/eu-en/trading/cfds/cryptocurrencies/"

# Crypto dict symbol: (Name in url, default spread)
cryptocurrencies = {
    "BTC": "Bitcoin",
    "BCH": "Bitcoin Cash",
    "ETH": "Ether",
    "LTC": "Litecoin"
}


class SpreadScrapper:

    @staticmethod
    def get_spread(pair: str) -> float:
        loop = asyncio.get_event_loop()
        try:
            task = asyncio.ensure_future(
                SpreadScrapper._get_page_content(pair)
            )
            loop.run_until_complete(task)
        except KeyboardInterrupt:
            task.cancel()
            loop.stop()
            loop.close()
        finally:
            spread = task.result()
            return spread

    @staticmethod
    async def _get_page_content(pair: str) -> float:
        # Using pyppeteer since Oanda does not work with simple requests
        # Headless set to True to avoid opening a Chrome window
        browser = await launch(headless=True)
        page = await browser.newPage()

        # Determine the url (forex or crypto)
        if pair[0:3] in cryptocurrencies and pair[3:] == "USD":
            pair_text = cryptocurrencies[pair[0:3]]
            url = crypto_url
        else:
            pair_text = f"{pair[0:3]}/{pair[3:]}"
            url = fx_url

        await page.goto(url)

        # Using waitForSelector to wait for the tbody to be visible
        tbody = await page.waitForSelector(
            ".live-rates__table tbody",
            visible=False
        )
        # Create a soup from the queryselector
        soup = BeautifulSoup(
            await page.evaluate('(tbody) => tbody.innerHTML', tbody),
            "html.parser"
        )
        await page.close()
        await browser.close()

        # Get the rows of the table and return the spread
        pairs = soup.findAll("tr")
        spread = 0.0
        for p in pairs:
            for child in p.contents:
                if child.string == pair_text:
                    spread = float(p.contents[3].string)
        return spread
