import json
import re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


BASE = "https://www.shl.com"
CATALOG_URL = "https://www.shl.com/products/product-catalog/"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "catalog.json"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def is_individual_solution(text: str) -> bool:
    text_l = text.lower()
    return "individual test solution" in text_l or "individual test" in text_l


def guess_test_type(text: str) -> str:
    text_l = text.lower()
    if "personality" in text_l or "opq" in text_l:
        return "P"
    if "ability" in text_l or "reasoning" in text_l or "gsa" in text_l:
        return "A"
    if "simulation" in text_l or "situational" in text_l:
        return "S"
    if "knowledge" in text_l or "skills" in text_l or "coding" in text_l or "java" in text_l:
        return "K"
    return ""


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: set[str] = set()
    text_seen_individual = False
    for element in soup.find_all(["h2", "h3", "table", "a"]):
        element_text = clean(element.get_text(" "))
        if "Pre-packaged Job Solutions" in element_text:
            text_seen_individual = False
        if "Individual Test Solutions" in element_text:
            text_seen_individual = True

        if element.name != "a" or not text_seen_individual:
            continue

        href = element.get("href", "")
        label = clean(element.get_text(" "))
        full = urljoin(BASE, href)
        if "/solutions/products/product-catalog/view/" in full and label:
            urls.add(full.split("#")[0])
    return sorted(urls)


def extract_table_rows(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []
    for tr in soup.select("tr"):
        cells = [clean(td.get_text(" ")) for td in tr.find_all(["td", "th"])]
        link = tr.find("a", href=True)
        if not link or len(cells) < 2:
            continue
        href = urljoin(BASE, link["href"]).split("#")[0]
        if "/product-catalog/view/" not in href:
            continue
        name = clean(link.get_text(" "))
        test_type = cells[-1].replace(" ", "")
        if not name or "Solution" in name:
            continue
        rows.append(
            {
                "name": name,
                "url": href,
                "test_type": test_type or guess_test_type(name),
                "description": name,
                "job_levels": [],
                "languages": [],
                "raw_text": f"{name} {test_type}",
            }
        )
    return rows


def parse_detail(url: str, html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    text = clean(soup.get_text(" "))
    if "pre-packaged job solution" in text.lower():
        return None

    h1 = soup.find("h1")
    name = clean(h1.get_text(" ")) if h1 else ""
    if not name:
        title = soup.find("title")
        name = clean(title.get_text(" ")).split("|")[0].strip() if title else ""
    if not name:
        return None

    meta = soup.find("meta", attrs={"name": "description"})
    description = clean(meta.get("content", "")) if meta else ""
    if not description:
        first_p = soup.find("p")
        description = clean(first_p.get_text(" ")) if first_p else ""

    return {
        "name": name,
        "url": url,
        "test_type": guess_test_type(text),
        "description": description,
        "job_levels": [],
        "languages": [],
        "raw_text": text[:5000],
    }


def main() -> None:
    rows = []
    seen_urls: set[str] = set()

    # Type 1 pages are Individual Test Solutions. Table data is enough for reliable
    # catalog-only recommendations and avoids slow detail-page crawling.
    for start in range(0, 500, 12):
        page_url = f"{CATALOG_URL}?start={start}&type=1"
        try:
            page_rows = extract_table_rows(fetch(page_url))
            new_rows = [row for row in page_rows if row["url"] not in seen_urls]
            if start > 0 and not new_rows:
                break
            for row in new_rows:
                seen_urls.add(row["url"])
                rows.append(row)
                print(f"OK {row['name']}")
        except Exception as exc:
            print(f"SKIP {page_url}: {exc}")

    dedup = {}
    for row in rows:
        if row["url"] not in dedup:
            dedup[row["url"]] = row

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(list(dedup.values()), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(dedup)} assessments to {OUT}")


if __name__ == "__main__":
    main()
