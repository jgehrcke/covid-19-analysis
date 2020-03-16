# covid-19-analysis

A tiny analysis toolkit based on the COVID-19 infection data published in the
[CSSEGISandData/COVID-19](https://github.com/CSSEGISandData/COVID-19)
repository.

This pipeline looks at the _confirmed infection count_, as it evolves over time
for individual countries.

Prerequisite is a Python 3.6 environment with dependencies installed (`pip install -r requirements.txt`).

### Usage

1. Fetch raw data (can also be used to subsequently update the data):

   ```
   $ make fetch-data
   ```

2. Generate time evolution plots for a specific country or region, for example:

   ```
   $ make plot-germany
   ```

This generates `plot-germany.html`, and tries to automatically open it.

`make plot-italy`, `make plot-spain`, ... work correspondingly.

**Note**: `make plot-germany` attempts to fetch the current confirmed infection
count for Germany from [zeit.de](https://www.zeit.de/) (at the time of writing
this the official numbers from German authorities lack behind, and zeit.de
seems to do a decent job at getting current numbers from individual federal
ministries).

For a list of valid location names just do some trial and error. There should
be some helpful suggestion:

```
$ make plot-charleston
python process.py  _current.csv charleston
200316-19:02:40.440 INFO: parse data file
200316-19:02:40.448 INFO: process data file
200316-19:02:40.455 ERROR: location string `charleston` not found in data set
200316-19:02:40.473 INFO: candidate by similarity: us_charlton_ga (similarity 0.67)
200316-19:02:40.473 INFO: candidate by similarity: us_charleston_county_sc (similarity 0.61)
...
```

### Example screenshot

The HTML document contains plots generated with
[Bokeh](https://docs.bokeh.org/en/latest/index.html). The figures responsively
adapt to the browser window width.

![covid-19-analysis example screenshot](https://raw.githubusercontent.com/jgehrcke/covid-19-analysis/master/screenshot.png "covid-19-analysis")
