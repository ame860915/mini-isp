PY      ?= python3
INPUT   ?= data/synth
CONFIG  ?= configs/default.yaml
export PYTHONPATH := python_ref

.PHONY: all synth py c verify preview test clean

all: test verify

synth:            ## generate synthetic RAW with ground truth
	$(PY) tools/make_synthetic.py --out $(INPUT)

py: synth         ## run Python float reference, dump every stage
	$(PY) -m mini_isp.pipeline --input $(INPUT) --config $(CONFIG) --out out/py

c:                ## build fixed-point C model
	$(MAKE) -C c_model

verify: py c      ## run C model with same params and diff stage by stage
	$(PY) verify/run_c.py --input $(INPUT) --py out/py --out out/c
	$(PY) verify/compare.py --py out/py --c out/c --config $(CONFIG)

preview: py       ## half-res quick look of each stage
	$(PY) tools/preview.py out/py/01_blc out/py/02_awb --out out/preview.png

test:
	$(PY) -m pytest -q

clean:
	rm -rf out data/*.raw data/*.json
	$(MAKE) -C c_model clean
