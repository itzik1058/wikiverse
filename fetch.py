# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
#     "tqdm",
# ]
# ///

import json
import time
from base64 import b64encode
from collections.abc import Generator
from pathlib import Path
from typing import Any

import requests
from tqdm import tqdm


def main() -> None:
    wiki_gg = list(wiki_gg_data(input("wiki.gg api authorization header: ")))
    print(f"processing {len(wiki_gg)} wikis from wiki.gg/wikis")
    wiki_gg_pages = Path("src/assets/wiki.gg")
    wiki_gg_pages.mkdir(parents=True, exist_ok=True)
    with Path("src/assets/wiki.gg.json").open("w") as fp:
        json.dump(wiki_gg, fp)
    wiki_gg_public = Path("public/wiki.gg")
    wiki_gg_public.mkdir(parents=True, exist_ok=True)
    for wiki in wiki_gg:
        host = wiki["host"]
        logo_url = wiki["logo"]
        if logo_url is None:
            continue
        logo_path = (wiki_gg_public / wiki["id"]).with_suffix(".png")
        if logo_path.is_file():
            continue
        pages = list(wiki_pages(host))
        with (wiki_gg_pages / wiki["id"]).with_suffix(".json").open("w") as fp:
            json.dump({**wiki, "pages": pages}, fp)
        logo = requests.get(logo_url, stream=True)
        with logo_path.open("wb") as fp:
            fp.write(logo.content)


def wiki_gg_data(auth: str) -> Generator[dict[str, str]]:
    next = True
    offset = 0
    while next:
        response = wiki_gg_query(auth, offset)
        next = response["pagingMetadata"]["hasNext"]
        offset += 1000
        for item in response["dataItems"]:
            data = item["data"]
            yield (
                {
                    "id": item["id"],
                    "name": data["name"],
                    "host": data["host"],
                    "logo": data.get("logo"),
                }
            )


def wiki_gg_query(auth: str, offset: int, limit: int = 1000) -> dict[str, Any]:
    return requests.get(
        "https://www.wiki.gg/_api/cloud-data/v2/items/query",
        params={
            ".r": b64encode(
                json.dumps(
                    {
                        "dataCollectionId": "SyncedWikis",
                        "query": {
                            "filter": {},
                            "sort": [{"fieldName": "name", "order": "ASC"}],
                            "paging": {"offset": offset, "limit": limit},
                            "fields": [],
                        },
                        "referencedItemOptions": [],
                        "returnTotalCount": True,
                        "environment": "LIVE",
                        "appId": "9da2fba0-30fd-4379-962b-335075512ce3",
                    }
                ).encode()
            )
        },
        headers={"authorization": auth},
    ).json()


def wiki_pages(host: str) -> Generator[dict[str, Any]]:
    progress = tqdm(host, total=0, desc=host)
    offset = None
    while True:
        params = {
            "action": "query",
            "format": "json",
            "list": "allpages",
            "aplimit": "max",
        }
        if offset:
            params["apcontinue"] = offset
        response = requests.get(
            f"{host}/api.php",
            params=params,
        ).json()
        offset = response.get("continue", {}).get("apcontinue")
        pages = response.get("query", {}).get("allpages", [])
        if response.get("error"):
            raise ValueError(response["error"])
        progress.total += len(pages)
        for page in pages:
            response = requests.get(
                f"{host}/api.php",
                params={
                    "action": "parse",
                    "format": "json",
                    "page": page["title"],
                },
            ).json()
            if response.get("error"):
                raise ValueError(response["error"])
            yield response
            progress.update()
            progress.refresh()
            time.sleep(0.5)
        if not offset:
            break


def wiki_graph(host: str) -> Generator[dict[str, Any]]:
    progress = tqdm(host)
    offset = None
    while True:
        params = {
            "action": "query",
            "format": "json",
            "list": "allpages",
            "aplimit": "max",
        }
        if offset:
            params["apcontinue"] = offset
        response = requests.get(
            f"{host}/api.php",
            params=params,
        ).json()
        offset = response.get("continue", {}).get("apcontinue")
        pages = response.get("query", {}).get("allpages", [])
        progress.total += len(pages)
        for page in pages:
            page_id = page["pageid"]
            title = page["title"]
            page_content = (
                requests.get(
                    f"{host}/api.php",
                    params={
                        "action": "query",
                        "format": "json",
                        "prop": "revisions",
                        "rvprop": "content",
                        "rvslots": "main",
                        "pageids": page_id,
                    },
                )
                .json()
                .get("query", {})
                .get("pages", {})
                .get(str(page_id), {})
                .get("revisions", [{}])[0]
                .get("slots", {})
                .get("main", {})
                .get("*")
            )
            yield {
                "page_id": page_id,
                "title": title,
                "page_content": page_content,
            }
            progress.update()
            progress.refresh()
            link_offset = None
            while True:
                params = {
                    "action": "query",
                    "format": "json",
                    "prop": "links",
                    "pllimit": "max",
                    "pageids": page_id,
                }
                if link_offset:
                    params["plcontinue"] = link_offset
                response = requests.get(f"{host}/api.php", params=params).json()
                link_offset = response.get("continue", {}).get("plcontinue")
                for link in (
                    response.get("query", {})
                    .get("pages", {})
                    .get(str(page_id), {})
                    .get("links", [])
                ):
                    yield {
                        "source": title,
                        "target": link["title"],
                    }
                if not link_offset:
                    break
        if not offset:
            break


if __name__ == "__main__":
    main()
