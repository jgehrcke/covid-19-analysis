# covid-19-analysis

A tiny analysis toolkit based on the COVID-19 infection data published in the
[CSSEGISandData/COVID-19](https://github.com/CSSEGISandData/COVID-19)
repository.

This pipeline looks at the _confirmed infection count_, as it evolves over time
for individual countries.

### Usage

1. Set up a Python environment with dependencies.

2. Fetch or update raw data:

   ```
   $ make fetch-data
   ```

3. Generate plots for a specific location, for example:

   ```
   $ make plot-germany
   ```

This will generate `plot-germany.html` and try to automatically open it. That
HTML document contains plots generated with
[Bokeh](https://docs.bokeh.org/en/latest/index.html). These plots responsively
adapt to the browser window width.

Example screenshot:
![covid-19-analysis example screenshot](https://raw.githubusercontent.com/jgehrcke/covid-19-analysis/master/screenshot.png "covid-19-analysis")

### Notes

`make plot-germany` attempts to fetch today's current confirmed infection count
from [zeit.de](https://www.zeit.de/) (at the time of writing this the official
numbers from German authorities lack behind, and zeit.de seems to do a decent
job at getting current numbers from individual federal ministries.)
