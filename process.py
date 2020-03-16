#!/usr/bin/env python
#
# MIT License

# Copyright (c) 2020 Dr. Jan-Philip Gehrcke

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
This program is part of https://github.com/jgehrcke/covid-19-analysis
"""
import logging
import sys
import re
import time
from datetime import datetime
from textwrap import dedent

import numpy as np
import pandas as pd
import requests

from bokeh.plotting import figure, output_file, show
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Div


log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


def main():
    data_file_path = sys.argv[1]
    location_name = sys.argv[2]

    df = jhu_csse_csv_to_dataframe(data_file_path, location_name)
    df = germany_try_to_get_todays_value_from_zeit_de(df)
    create_bokeh_html(df, location_name)


def create_bokeh_html(df, location_name):

    # upper-case for display purposes
    location_name = location_name.upper()

    # lower-case for lookup in DataFrame, and for filename generation.
    loc = location_name.lower()

    output_file(f"plot-{loc}.html")

    preamble_text = f"""
    Analysis based on confirmed COVID-19 cases for {location_name}.

    Data source: <a href="https://github.com/CSSEGISandData/COVID-19">github.com/CSSEGISandData/COVID-19</a>

    Author: <a href="https://gehrcke.de">Dr. Jan-Philip Gehrcke</a>

    Code: <a href="https://github.com/jgehrcke/covid-19-analysis">github.com/jgehrcke/covid19</a>

    Data points from before February 28 are ignored.
    """

    preamble = Div(
        text=dedent(preamble_text.replace("\n\n", "<br />")), width=600, height=120,
    )

    cases_total = df

    cases_new = df[loc].diff()
    cases_new.name = "diff"
    cases_new = cases_new.to_frame()

    # cleaning step: a change of 0 implies that data wasn't updated on
    # that day. Set to NaN.
    cases_new["diff"].replace(0, np.NaN)

    # ticker = DatetimeTickFormatter(interval=5, num_minor_ticks=10)
    # xaxis = DatetimeAxis(ticker=ticker)

    # print(daily_cases_new)

    f1 = figure(
        title="evolution of total case count",
        x_axis_type="datetime",
        y_axis_type="log",
        plot_width=1000,
        plot_height=450,
        toolbar_location=None,
    )
    f1.scatter(
        "date",
        loc,
        marker="x",
        size=8,
        line_width=3,
        source=ColumnDataSource(data=cases_total),
    )
    f1.y_range.start = 1
    f1.y_range.end = cases_total[loc].max() * 10
    f1.xaxis.axis_label = "Date"
    f1.yaxis.axis_label = "number of confirmed cases"
    f1.xaxis.ticker.desired_num_ticks = 15

    f2 = figure(
        title="evolution of newly confirmed cases per day",
        x_axis_type="datetime",
        y_axis_type="log",
        plot_width=1000,
        plot_height=450,
        toolbar_location=None,
    )

    f2.scatter(
        "date",
        "diff",
        marker="x",
        size=8,
        line_width=3,
        source=ColumnDataSource(data=cases_new),
    )
    f2.y_range.start = 1
    f2.y_range.end = cases_new["diff"].max() * 10
    f2.xaxis.axis_label = "Date"
    f2.yaxis.axis_label = "newly registered cases, per day"
    f2.xaxis.ticker.desired_num_ticks = 15

    show(column(preamble, f1, f2), browser="firefox")


def jhu_csse_csv_to_dataframe(data_file_path, location_name):
    """
    data_file_path: expect an instance of `time_series_19-covid-Confirmed.csv`
    from https://github.com/CSSEGISandData/COVID-19/

    location_name: the lower-cased version of this must be a column in the
    processed data set.
    """
    log.info("parse data file")
    df = pd.read_csv(data_file_path)

    log.info("process data file")
    # Merge location names into somewhat more managable identifiers.
    countries = [
        c.lower() if c != "nan" else ""
        for c in list(df["Country/Region"].astype("str"))
    ]
    provinces = [
        p.lower() if p != "nan" else ""
        for p in list(df["Province/State"].astype("str"))
    ]
    df["where"] = [f"{c}_{p}" if p else c for c, p in zip(countries, provinces)]

    # Make each column represent a location, and each row represent a day
    # (date).

    df.drop(["Lat", "Long", "Country/Region", "Province/State"], axis=1, inplace=True)

    df = df.set_index("where")
    df = df.transpose()

    # Parse date strings into pandas DateTime objects, set proper
    # DateTimeIndex.
    normalized_date_strings = [
        "/".join(t.zfill(2) for t in os.split("/")) for os in list(df.index)
    ]
    df.index = normalized_date_strings
    df.index = pd.to_datetime(df.index, format="%m/%d/%y")

    df.index.name = "date"
    # df.sort_index(inplace=True)

    # Only return series for specific location

    loc = location_name.lower()
    if loc not in df:
        log.error("location string `%s` not found in data set", loc)
        sys.exit(1)

    # Ignore early data in subsequent processing.
    return df[loc].to_frame()["2020-02-28":]


def germany_try_to_get_todays_value_from_zeit_de(df):
    url = f"https://interactive.zeit.de/cronjobs/2020/corona/data.json?time={int(time.time())}"
    log.info("try to get current case count from zeit.de")

    today = datetime.utcnow().strftime("%Y-%m-%d")

    data = None
    try:
        resp = requests.get(url, timeout=(3.05, 10))
        resp.raise_for_status()
        data = resp.json()

    except Exception as exc:
        log.warning("bail out: %s", str(exc))
        return df

    pd_today = pd.to_datetime(today, format="%Y-%m-%d")

    if pd_today not in df["germany"]:
        log.info("no sample for today in the original data set")

    zeit_count_today = None
    if data:
        # log.info(json.dumps(data, indent=2))
        if "chronology" in data:
            for sample in data["chronology"]:
                if "date" in sample:
                    if sample["date"] == today:
                        log.info("sample from zeit.de for today: %s", sample["count"])
                        zeit_count_today = sample["count"]

    if zeit_count_today:
        log.info("use that data point")
        df = df.append(pd.DataFrame({"germany": [sample["count"]]}, index=[pd_today]))
        df.index.name = "date"

    return df


if __name__ == "__main__":
    main()
