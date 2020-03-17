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
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
import scipy.optimize
import requests

from bokeh.plotting import figure, output_file, show
from bokeh.layouts import column, layout
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

    modified = False
    if location_name.lower() == "germany":
        df, modified = germany_try_to_get_todays_value_from_zeit_de(df)

    now = datetime.utcnow()
    zeit_de_source = 'and <a href="https://zeit.de">zeit.de</a>' if modified else ""

    preamble_text = f"""
    Analysis based on confirmed COVID-19 cases for {location_name.upper()}.

    Data source: <a href="https://github.com/CSSEGISandData/COVID-19">github.com/CSSEGISandData/COVID-19</a> {zeit_de_source}

    Author: <a href="https://gehrcke.de">Dr. Jan-Philip Gehrcke</a>

    Code: <a href="https://github.com/jgehrcke/covid-19-analysis">github.com/jgehrcke/covid-19-analysis</a>

    Data points from before February 28 are ignored.

    Generated at {now .strftime('%Y-%m-%d %H:%M UTC')}
    """

    preamble_text = dedent(preamble_text.replace("\n\n", "<br />"))
    create_bokeh_html(df, location_name, preamble_text)


def create_bokeh_html(df, location_name, preamble_text):

    # upper-case for display purposes
    location_name = location_name.upper()

    # lower-case for lookup in DataFrame, and for filename generation.
    loc = location_name.lower()

    output_file(f"plot-{loc}.html")

    preamble = Div(text=preamble_text, height=120)

    cases_total = df

    cases_new = df[loc].diff()
    cases_new.name = "diff"
    cases_new = cases_new.to_frame()

    # cleaning step: a change of 0 implies that data wasn't updated on
    # that day. Set to NaN.
    cases_new["diff"].replace(0, np.NaN)

    cases_total_fit = expfit(cases_total, loc)

    # cases_new_fit['expfit'] =

    # sys.exit()

    # ticker = DatetimeTickFormatter(interval=5, num_minor_ticks=10)
    # xaxis = DatetimeAxis(ticker=ticker)

    # print(daily_cases_new)

    f1 = figure(
        title="evolution of total case count (half-logarithmic)",
        x_axis_type="datetime",
        y_axis_type="log",
        toolbar_location=None,
        background_fill_color="#F2F2F7",
    )
    f1.scatter(
        "date",
        loc,
        marker="x",
        size=8,
        line_width=3,
        legend_label="raw data",
        source=ColumnDataSource(data=cases_total),
    )
    f1.y_range.start = 1
    f1.y_range.end = cases_total[loc].max() * 10
    f1.xaxis.axis_label = "Date"
    f1.yaxis.axis_label = "total number of confirmed cases"
    f1.xaxis.ticker.desired_num_ticks = 15
    f1.outline_line_width = 4
    f1.outline_line_alpha = 0.3
    f1.outline_line_color = "#aec6cf"
    f1.line(
        "date",
        "expfit",
        legend_label="exponential fit",
        source=ColumnDataSource(data=cases_total_fit),
    )

    # f1.legend.title = "Legend"
    f1.legend.location = "top_left"

    flin = figure(
        title="evolution of total case count (linear)",
        x_axis_type="datetime",
        toolbar_location=None,
        background_fill_color="#F2F2F7",
    )
    flin.scatter(
        "date",
        loc,
        marker="x",
        size=8,
        line_width=3,
        legend_label="raw data",
        source=ColumnDataSource(data=cases_total),
    )
    flin.y_range.start = 1
    flin.y_range.end = cases_total[loc].max() * 1.3
    flin.xaxis.axis_label = "Date"
    flin.yaxis.axis_label = "total number of confirmed cases"
    flin.xaxis.ticker.desired_num_ticks = 15
    flin.outline_line_width = 4
    flin.outline_line_alpha = 0.3
    flin.outline_line_color = "#aec6cf"
    flin.line(
        "date",
        "expfit",
        legend_label="exponential fit",
        source=ColumnDataSource(data=cases_total_fit),
    )
    flin.legend.location = "top_left"

    f2 = figure(
        title="evolution of newly confirmed cases per day",
        x_axis_type="datetime",
        y_axis_type="log",
        toolbar_location=None,
        background_fill_color="#F2F2F7",
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

    f2.outline_line_width = 4
    f2.outline_line_alpha = 0.3
    f2.outline_line_color = "#aec6cf"

    show(
        column(preamble, f1, flin, f2, sizing_mode="stretch_both", max_width=700),
        browser="firefox",
    )


def expfit(df, loc):

    # Parameterize a simple linear function.
    def linfunc(x, a, b):
        return a + x * b

    # Get date-representing x values as numpy array containing float data type.
    x = np.array(df.index.to_pydatetime(), dtype=np.datetime64).astype("float")

    minx = x.min()

    # For the fit don't deal with crazy large x values, transform to time
    # deltas (by substracting mininum), and also transform from nanoseconds
    # seconds.
    fitx = (x - minx) / 10 ** 9

    # Get natural logarithm of data values
    y = np.log(df[loc].to_numpy())
    # log.info(fitx)
    # log.info(y)
    # log.info(", ".join("{%s, %s}" % (x, y) for x, y in zip(fitx, y)))

    # Choose starting parameters for iterative fit.
    p0 = [minx, 3]

    popt, pcov = scipy.optimize.curve_fit(linfunc, fitx, y, p0=p0)
    log.info("fit paramters: %s, %s", popt, pcov)

    # Get data values from fit for the time values corresponding to the time
    # values in the original time series used for fitting.
    fit_ys_log = linfunc(fitx, *popt)

    # Generate corresponding fit values by inverting logarithm.
    fit_ys = np.exp(fit_ys_log)

    # Create a data frame with the original time values as index, and the
    # values from the fit as a series named `expfit`
    df_fit = df.copy()
    df_fit["expfit"] = fit_ys
    return df_fit


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
        "_".join(c.lower().split()) if c != "nan" else ""
        for c in list(df["Country/Region"].astype("str"))
    ]
    provinces = [
        "_".join(p.lower().split()) if p != "nan" else ""
        for p in list(df["Province/State"].astype("str"))
    ]

    countries = [c.replace(",", "").replace(".", "") for c in countries]
    provinces = [p.replace(",", "").replace(".", "") for p in provinces]

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
        find_similar_locations(df, loc)
        sys.exit(1)

    # Ignore early data in subsequent processing.
    return df[loc].to_frame()["2020-02-28":]


def find_similar_locations(df, query):
    valid_locs = list(df.columns.values)

    for vl in valid_locs:
        if vl.startswith(query) or vl.endswith(query):
            log.info("candidate by suffix/prefix: %s", vl)

    # lds = {vl: jellyfish.levenshtein_distance(vl, query) for vl in valid_locs}
    # lds_sorted = {loc: ld for loc, ld in sorted(lds.items(), key=lambda item: item[1])}
    lds = {vl: SequenceMatcher(None, vl, query).ratio() for vl in valid_locs}
    lds_sorted = {
        loc: ld
        for loc, ld in sorted(lds.items(), key=lambda item: item[1], reverse=True)
    }

    for loc, ld in list(lds_sorted.items())[:6]:
        log.info("candidate by similarity: %s (similarity %.2f)", loc, ld)


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
        return df, False

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

    modified = False
    if zeit_count_today:
        log.info("use that data point")
        df = df.append(pd.DataFrame({"germany": [sample["count"]]}, index=[pd_today]))
        df.index.name = "date"
        modified = True

    return df, modified


if __name__ == "__main__":
    main()
