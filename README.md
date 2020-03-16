# covid-19-analysis

A tiny analysis toolkit based on the COVID-19 infeaction data published in the
[CSSEGISandData/COVID-19](https://github.com/CSSEGISandData/COVID-19).

This pipeline looks at the _confirmed infection count_.

### How to use this

1. Set up a Python environment with dependencies.

2. Fetch or update raw data (from the `CSSEGISandData/COVID-19` repository):

   ```
   $ make fetch-data
   ```

3. Invoke the analysis for a specific location, for example:

   ```
   $ make plot-germany
   ```

### Notes

`make plot-germany` attempts to fetch today's current confirmed infection count
from [zeit.de](https://www.zeit.de/) (at the time of writing this the official
numbers from German authorities lack behind, and zeit.de seems to do a decent
job at getting current numbers from individual federal ministries.)
