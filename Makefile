SHELL=/bin/bash -o pipefail -o errexit -o nounset
JHU_REPO_DIR?=jhu-csse-covid-19-data

.PHONY: update-dataset
fetch-data:
	@if [ -d "${JHU_REPO_DIR}" ]; then \
	    echo "updating ..." && \
		cd ${JHU_REPO_DIR} && git pull; \
	else \
		git clone https://github.com/CSSEGISandData/COVID-19 ${JHU_REPO_DIR}; \
	fi
	@ rm -f _current.csv && ln -s ${JHU_REPO_DIR}/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv _current.csv


plot-%:
	python process.py  _current.csv $*
