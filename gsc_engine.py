import os
import pandas as pd

from io import BytesIO
from collections import defaultdict

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly"
]

ROW_LIMIT = 25000


# --------------------------------------------------
# Authentication
# --------------------------------------------------

def auth_gsc():

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build(
        "searchconsole",
        "v1",
        credentials=creds,
        cache_discovery=False
    )

    return service


# --------------------------------------------------
# Get Properties
# --------------------------------------------------

def get_sites(service):

    sites = service.sites().list().execute()

    return sites.get("siteEntry", [])


# --------------------------------------------------
# Fetch Search Console Data
# --------------------------------------------------

def fetch_search_analytics(
    service,
    site,
    start,
    end,
    dimensions
):

    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": dimensions,
        "rowLimit": ROW_LIMIT,
        "dataState": "final"
    }

    response = service.searchanalytics().query(
        siteUrl=site,
        body=body
    ).execute()

    return response.get("rows", [])


# --------------------------------------------------
# Cannibalization Summary
# --------------------------------------------------

def build_summary(rows):

    by_query = defaultdict(list)

    for r in rows:

        keys = r.get("keys", [])

        if len(keys) < 2:
            continue

        query = keys[0]
        page = keys[1]

        by_query[query].append({
            "query": query,
            "page": page,
            "clicks": r.get("clicks", 0),
            "impressions": r.get("impressions", 0),
            "ctr": r.get("ctr", 0),
            "position": r.get("position", 0)
        })

    output = []

    for query, urls in by_query.items():

        if len(urls) < 2:
            continue

        urls.sort(
            key=lambda x: x["clicks"],
            reverse=True
        )

        primary = urls[0]
        secondary = urls[1:]

        secondary_clicks = sum(
            x["clicks"]
            for x in secondary
        )

        secondary_impr = sum(
            x["impressions"]
            for x in secondary
        )

        secondary_ctr = (
            sum(
                x["ctr"] * x["impressions"]
                for x in secondary
            ) / secondary_impr
        ) if secondary_impr > 0 else 0

        secondary_pos = (
            sum(
                x["position"] * x["impressions"]
                for x in secondary
            ) / secondary_impr
        ) if secondary_impr > 0 else 0

        total_clicks = (
            primary["clicks"] +
            secondary_clicks
        )

        click_share = (
            primary["clicks"] /
            total_clicks
        ) if total_clicks > 0 else 0

        ctr_split = (
            primary["ctr"] -
            secondary_ctr
        )

        output.append({
            "Query": query,
            "Num URLs": len(urls),

            "Primary URL": primary["page"],
            "Primary Clicks": primary["clicks"],
            "Primary Impr": primary["impressions"],
            "Primary CTR": primary["ctr"],
            "Primary Pos": primary["position"],

            "Secondary URL(s)": " | ".join(
                x["page"]
                for x in secondary
            ),

            "Secondary Clicks (sum)": secondary_clicks,
            "Secondary Impr (sum)": secondary_impr,
            "Secondary CTR (weighted)": secondary_ctr,
            "Secondary Pos (weighted)": secondary_pos,

            "Click Share (Primary %)": click_share,
            "CTR Split (Primary - Secondary)": ctr_split
        })

    return pd.DataFrame(output)


# --------------------------------------------------
# Daily Swapping Analysis
# --------------------------------------------------

def build_daily_swapping(rows):

    by_date_query = defaultdict(list)

    for r in rows:

        keys = r.get("keys", [])

        if len(keys) < 3:
            continue

        date = keys[0]
        query = keys[1]
        page = keys[2]

        by_date_query[(date, query)].append({
            "page": page,
            "clicks": r.get("clicks", 0),
            "impressions": r.get("impressions", 0)
        })

    leaders = defaultdict(list)

    for (date, query), pages in by_date_query.items():

        pages.sort(
            key=lambda x: (
                x["clicks"],
                x["impressions"]
            ),
            reverse=True
        )

        leaders[query].append(
            pages[0]["page"]
        )

    output = []

    for query, pages in leaders.items():

        unique_pages = list(
            dict.fromkeys(pages)
        )

        unique_count = len(unique_pages)

        swapping_pct = (
            (unique_count - 1)
            / unique_count
        ) if unique_count > 0 else 0

        output.append({
            "Query": query,
            "Days Observed": len(pages),
            "Unique Leaders": unique_count,
            "Swapping %": swapping_pct,
            "Leaders (sample)": " | ".join(
                unique_pages[:6]
            )
        })

    return pd.DataFrame(output)


# --------------------------------------------------
# Main Analysis Function
# --------------------------------------------------

def run_analysis(
    service,
    site_url,
    start_date,
    end_date
):

    agg_rows = fetch_search_analytics(
        service,
        site_url,
        str(start_date),
        str(end_date),
        ["query", "page"]
    )

    daily_rows = fetch_search_analytics(
        service,
        site_url,
        str(start_date),
        str(end_date),
        ["date", "query", "page"]
    )

    df_summary = build_summary(
        agg_rows
    )

    df_swap = build_daily_swapping(
        daily_rows
    )

    return df_summary, df_swap


# --------------------------------------------------
# Excel Export
# --------------------------------------------------

def generate_excel_report(
    df_summary,
    df_swap
):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        if not df_summary.empty:
            df_summary.to_excel(
                writer,
                sheet_name="Cannibalization Summary",
                index=False
            )

        if not df_swap.empty:
            df_swap.to_excel(
                writer,
                sheet_name="Daily Swapping",
                index=False
            )

    output.seek(0)

    return output