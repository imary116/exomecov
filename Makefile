.PHONY: mosdepth

mosdepth:
	docker build -t gcr.io/daly-neale-sczmeta/mosdepth images/mosdepth
	docker push gcr.io/daly-neale-sczmeta/mosdepth
	