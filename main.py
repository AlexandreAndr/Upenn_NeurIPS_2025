import openreview
import csv
import os
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()  

OPEN_REVIEW_USERNAME = os.getenv("OPEN_REVIEW_USERNAME")
OPEN_REVIEW_PASSWORD = os.getenv("OPEN_REVIEW_PASSWORD")

def get_institutions_between(history, start_year, end_year=None):
    """
    Return all institutions where the experience overlaps with the given time range.
    If end_year is None, include experiences that extend beyond start_year or are ongoing.

    Example:
        get_institutions_between(history, 2020, 2025)
        get_institutions_between(history, 2020, None)
    """
    if not history:
        return ["N/A"]

    institutions = []
    positions = []
    for exp in history:
        position = exp.get("position")

        exp_start = exp.get("start")
        exp_end = exp.get("end")

        exp_end = float("inf") if exp_end is None else exp_end

        if end_year is None:
            if start_year <= exp_end:
                inst = exp.get("institution", {}).get("name")
                if inst:
                    institutions.append(inst)
                    positions.append(position)
        else:
            if exp_start <= end_year and exp_end >= start_year:
                inst = exp.get("institution", {}).get("name")
                if inst:
                    institutions.append(inst)
                    positions.append(position)

    institutions = [inst.replace(",", " || ") for inst in institutions]

    if len(institutions)==0:
        institutions = ["N/A"]
    if len(positions) == 0:
        positions = ["N/A"]
    
    return institutions, positions


def get_venue_info(submission):
    """Return the venue information from the submission."""
    return submission.content.get("venue", {}).get("value", "").split()[-1]


def fetch_neurips2025_accepted(
    baseurl="https://api2.openreview.net",
    batch_size=100,
    path="neurips2025_accepted.csv",
    username=OPEN_REVIEW_USERNAME,
    password=OPEN_REVIEW_PASSWORD,
):
    client = openreview.api.OpenReviewClient(
        baseurl=baseurl, username=username, password=password
    )

    # Fetch decision notes
    decisions = client.get_all_notes(
        invitation="NeurIPS.cc/2025/Conference/-/Submission",
        content={"venueid": "NeurIPS.cc/2025/Conference"},
    )

    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "PaperID",
                    "Title",
                    "Authors",
                    "Affiliations",
                    "Positions",
                    "Keywords",
                    "Venue",
                ]
            )

    buffer = []
    total_saved = 0

    for dec in tqdm(decisions):
        forum_id = dec.forum
        submission = client.get_note(forum_id)
        if not submission:
            continue

        title = submission.content.get("title", {}).get("value", "")
        authors = submission.content.get("authors", {}).get("value", [])
        author_ids = submission.content.get("authorids", {}).get("value", [])
        keywords = submission.content.get("keywords", {}).get("value", [])
        venue = get_venue_info(submission)

        affiliations = []
        positions = []
        for id in author_ids:
            aff = "N/A"
            pos = "N/A"
            try:
                profile = client.get_profile(id)
                history = profile.content.get("history", [])
                institutions , titles = get_institutions_between(history, 2025)

                aff = " && ".join(institutions)
                pos =" && ".join(titles)
            except Exception:
                pass
            affiliations.append(aff)
            positions.append(pos)

        buffer.append(
            [
                forum_id,
                title,
                "; ".join(authors),
                "; ".join(affiliations),
                "; ".join(positions),
                "; ".join(keywords),
                venue,
            ]
        )

        if len(buffer) >= batch_size:
            with open(path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(buffer)
            total_saved += len(buffer)
            buffer.clear()

    if buffer:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(buffer)
        total_saved += len(buffer)

    print(f"Saved {total_saved} records to {path}")


if __name__ == "__main__":
    fetch_neurips2025_accepted()
