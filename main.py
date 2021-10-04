import collections
import datetime
import json
import pathlib
import re
from typing import List, Dict

import gspread

SHEET_KEY = "1RAIQGe5ViTwV8T4wy-4ZNiAz1HtpG4jPDwijgQ7j4OY"
DATA_DIR = pathlib.Path("data")
POST_DIR = pathlib.Path("content/posts")
META_TEMPLATE = """---
{}
---"""


def load_twint_json(path: pathlib.Path):
    for file in path.glob("**/*.json"):
        with file.open() as fp:
            for line in fp:
                yield json.loads(line)


def group_by_conversation(tweets):
    groups = collections.defaultdict(list)
    for tweet in tweets:
        groups[tweet["conversation_id"]].append(tweet)
    return groups


def filter_group(tweets: List[Dict]) -> List[Dict]:
    # Note: tweets may not be unique due to limitations in twint
    filtered = []
    seen = set()
    for tweet in tweets:
        if len(tweet["reply_to"]) == 0 and tweet["id"] not in seen:
            filtered.append(tweet)
            seen.add(tweet["id"])
    return sorted(
        filtered,
        key=lambda tweet: datetime.datetime.strptime(
            tweet["created_at"], "%Y-%m-%d %H:%M:%S %Z"
        ),
    )


if __name__ == "__main__":
    sheets_client = gspread.service_account()
    sheet = sheets_client.open_by_key(SHEET_KEY)
    worksheet = sheet.get_worksheet(0)
    records = worksheet.get_all_records()

    tweets = load_twint_json(pathlib.Path("twint/socialistdogmom"))
    tweets_grouped = group_by_conversation(tweets)

    for record in records:
        thread = record["thread"]
        match = re.search(r"status/(\d+)", thread)
        if match is not None:
            (tweet_id,) = match.groups()
            post_path = POST_DIR.joinpath(f"{tweet_id}.md")
            post_meta = {
                "title": record["meeting"],
                "date": record["date"],
                "tweet_id": tweet_id,
                "meetings": [record["meeting"]],
                "groups": [group.strip() for group in record["groups"].split(",")],
                "agenda": record["agenda"],
                "packet": record["packet"],
                "recording": record["recording"],
                "minutes": record["minutes"],
            }
            with post_path.open("w") as fp:
                fp.write(META_TEMPLATE.format(json.dumps(post_meta, indent=2)))
            thread_path = DATA_DIR.joinpath(f"{tweet_id}.json")
            tweets_thread = filter_group(tweets_grouped[tweet_id])
            with thread_path.open("w") as fp:
                json.dump(tweets_thread, fp, indent=2)
