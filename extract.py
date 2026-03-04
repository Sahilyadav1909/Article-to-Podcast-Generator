import requests
import trafilatura


class ExtractError(Exception):
    """Raised when we can't fetch or extract blog text in a usable way."""


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}


def extract_blog(url: str, timeout: int = 25) -> dict:
    if not url or not url.startswith(("http://", "https://")):
        raise ExtractError("Please provide a valid http(s) URL.")

    # 1) Try trafilatura fetch first
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
            meta = trafilatura.extract_metadata(downloaded)
            title = meta.title if meta and meta.title else "Untitled Blog"
            if text and len(text.strip()) > 200:
                return {"title": title.strip(), "text": text.strip()}
    except Exception:
        pass

    # 2) Fallback: requests
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)

        if resp.status_code == 403:
            raise ExtractError(
                "This website blocked automated access (403 Forbidden). "
                "Try a different URL (Wikipedia/simple blogs work best)."
            )
        if resp.status_code == 404:
            raise ExtractError("This URL was not found (404). Please check the link and try again.")

        resp.raise_for_status()

        html = resp.text
        text = trafilatura.extract(html, include_comments=False, include_tables=True)
        meta = trafilatura.extract_metadata(html)
        title = meta.title if meta and meta.title else "Untitled Blog"

        if not text or len(text.strip()) < 200:
            raise ExtractError(
                "I fetched the page but could not extract enough readable article text. "
                "Try a different URL or a simpler blog page."
            )

        return {"title": title.strip(), "text": text.strip()}

    except requests.exceptions.RequestException as e:
        raise ExtractError(f"Network error while fetching the blog: {e}") from e