# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///

import json
from base64 import b64encode
from collections.abc import Generator
from typing import Any

import requests


def main() -> None:
    print(json.dumps(list(wiki_gg_data(input("wiki.gg api authorization header: ")))))


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


if __name__ == "__main__":
    main()
