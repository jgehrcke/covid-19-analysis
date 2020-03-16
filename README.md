# covid-19-analysis

playground repo for analysis based on covid-19 infection data

### How to use

First, fetch or update data (this reads from the
[CSSEGISandData/COVID-19](https://github.com/CSSEGISandData/COVID-19) repository):

```
$ make fetch-data
```

Then invoke the analysis for a specific location, for example:

```
$ make plot-germany
```
