import openreview
import csv
import os
import time
import json
from tqdm import tqdm
from dotenv import load_dotenv
from itertools import islice



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

#List of workshops
WORKSHOP_DISPLAY_NAMES = [
    ("NeurIPS 2025 Workshop A2EI",                "A2EI"),
    ("NeurIPS 2025 Workshop ACA",                 "ACA"),
    ("NeurIPS 2025 Workshop AI4D3",               "AI4D3"),
    ("NeurIPS 2025 Workshop AI4Mat",              "AI4Mat"),
    ("NeurIPS 2025 Workshop AI4Music",            "AI4Music"),
    ("NeurIPS 2025 Workshop AI4NextG",            "AI4NextG"),
    ("NeurIPS 2025 Workshop AI4Science",          "AI4Science"),
    ("NeurIPS 2025 Workshop AiForAnimalComms",    "AiForAnimalComms"),
    ("NeurIPS 2025 Workshop ARLET",               "ARLET"),
    ("NeurIPS 2025 Workshop BERT2S",              "BERT2S"),
    ("NeurIPS 2025 Workshop BioSafe GenAI",       "BioSafeGenAI"),
    ("NeurIPS 2025 Workshop BrainBodyFM",         "BrainBodyFM"),
    ("NeurIPS 2025 Workshop CauScien",            "CauScien"),
    ("NeurIPS 2025 Workshop CCFM",                "CCFM"),
    ("NeurIPS 2025 Workshop CogInterp",           "CogInterp"),
    ("NeurIPS 2025 Workshop COML",                "COML"),
    ("NeurIPS 2025 Workshop DBM",                 "DBM"),
    ("NeurIPS 2025 Workshop DiffCoALG",           "DiffCoALG"),
    ("NeurIPS 2025 Workshop DL4C",                "DL4C"),
    ("NeurIPS 2025 Workshop DynaFront",           "DynaFront"),
    ("NeurIPS 2025 Workshop ER",                  "ER"),
    ("NeurIPS 2025 Workshop EWM",                 "EWM"),
    ("NeurIPS 2025 Workshop FM4LS",               "FM4LS"),
    ("NeurIPS 2025 Workshop FMEA",                "FMEA"),
    ("NeurIPS 2025 Workshop FoRLM",               "FoRLM"),
    ("NeurIPS 2025 Workshop FPI",                 "FPI"),
    ("NeurIPS 2025 Workshop GenAI in Finance",    "GenAIinFinance"),
    ("NeurIPS 2025 Workshop GenAI4Health",        "GenAI4Health"),
    ("NeurIPS 2025 Workshop GenProCC",            "GenProCC"),
    ("NeurIPS 2025 Workshop Imageomics",          "Imageomics"),
    ("NeurIPS 2025 Workshop L2S",                 "L2S"),
    ("NeurIPS 2025 Workshop L2S Non-Proceedings Track", "L2S-Non-Proceedings-Track"),
    ("NeurIPS 2025 Workshop LAW",                 "LAW"),
    ("NeurIPS 2025 Workshop LiT",                 "LiT"),
    ("NeurIPS 2025 Workshop LLM Evaluation",      "LLM-Evaluation"),
    ("NeurIPS 2025 Workshop Lock-LLM",            "Lock-LLM"),
    ("NeurIPS 2025 Workshop LXAI",                "LXAI"),
    ("NeurIPS 2025 Workshop MATH-AI",             "MATH-AI"),
    ("NeurIPS 2025 Workshop MechInterp",          "MechInterp"),
    ("NeurIPS 2025 Workshop ML4PS",               "ML4PS"),
    ("NeurIPS 2025 Workshop MLForSys",            "MLForSys"),
    ("NeurIPS 2025 Workshop MLxOR",               "MLxOR"),
    ("NeurIPS 2025 Workshop MTI-LLM",             "MTI-LLM"),
    ("NeurIPS 2025 Workshop MusIML",              "MusIML"),
    ("NeurIPS 2025 Workshop NEGEL",               "NEGEL"),
    ("NeurIPS 2025 Workshop NeurReps",            "NeurReps"),
    ("NeurIPS 2025 Workshop NextVid",             "NextVid"),
    ("NeurIPS 2025 Workshop NPGML",               "NPGML"),
    ("NeurIPS 2025 Workshop OPT",                 "OPT"),
    ("NeurIPS 2025 Workshop QueerInAI",           "QueerInAI"),
    ("NeurIPS 2025 Workshop RegML",               "RegML"),
    ("NeurIPS 2025 Workshop Reliable ML",         "Reliable-ML"),
    ("NeurIPS 2025 Workshop ScaleOPT",            "ScaleOPT"),
    ("NeurIPS 2025 Workshop SEA",                 "SEA"),
    ("NeurIPS 2025 Workshop SpaVLE",              "SpaVLE"),
    ("NeurIPS 2025 Workshop SPIGM",               "SPIGM"),
    ("NeurIPS 2025 Workshop TS4H",                "TS4H"),
    ("NeurIPS 2025 Workshop UniReps",             "UniReps"),
    ("NeurIPS 2025 Workshop UrbanAI",             "UrbanAI"),
    ("NeurIPS 2025 Workshop VLM4RWD",             "VLM4RWD"),
    ("NeurIPS 2025 Workshop WCTD",                "WCTD"),
    ("NeurIPS 2025 Workshop WiML",                "WiML"),
]

def fetch_neurips2025_workshops_all(
    venue_index=None,   # set this if you want to just test 1 workshop venue
    baseurl="https://api2.openreview.net",
    batch_size=100,
    path="neurips2025_workshops_all.csv",
    username=OPEN_REVIEW_USERNAME,
    password=OPEN_REVIEW_PASSWORD,
):
    client = openreview.api.OpenReviewClient(
        baseurl=baseurl, username=username, password=password
    )

    # Create CSV once
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
                    "Workshop", #added workshop column 
                ]
            )
    # query individual workshops not all
    workshops = WORKSHOP_DISPLAY_NAMES
    if venue_index is not None:
        workshops = [WORKSHOP_DISPLAY_NAMES[venue_index]]

    total_saved = 0

    for display_name, venue_name in workshops:
        workshop_venueid = f"NeurIPS.cc/2025/Workshop/{venue_name}"
        print(f"\nGetting: {display_name}  ->  {workshop_venueid}")

        # Fetch decision notes
        decisions = client.get_all_notes(
            invitation=f"{workshop_venueid}/-/Submission",
            content={"venueid": workshop_venueid},
        )

        buffer = []

        for dec in tqdm(decisions, desc=venue_name):
            forum_id = dec.forum
            submission = client.get_note(forum_id)
            if not submission:
                continue

            title = submission.content.get("title", {}).get("value", "") or ""
            authors = submission.content.get("authors", {}).get("value", []) or []
            author_ids = submission.content.get("authorids", {}).get("value", []) or []
            keywords = submission.content.get("keywords", {}).get("value", []) or []
            venue = get_venue_info(submission)

            affiliations = []
            positions = []
            for aid in author_ids:
                aff = "N/A"
                pos = "N/A"
                try:
                    profile = client.get_profile(aid) 
                    history = (profile.content or {}).get("history", []) or []
                    institutions, titles = get_institutions_between(history, 2025)
                    aff = " && ".join(institutions)
                    pos = " && ".join(titles)
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
                    display_name, #workshop venue
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

    print(f"\nSaved {total_saved} records to {path}")

if __name__ == "__main__":
    fetch_neurips2025_workshops_all()
    # fetch_neurips2025_accepted()





