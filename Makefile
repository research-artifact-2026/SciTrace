.PHONY: validate test demo build-site clean

validate:
	python scripts/scitrace_framework.py taxonomy
	python scripts/scitrace_framework.py verify-tools --request "Compare public literature metadata" --tool "search_literature:public abstracts" --tool "summarize_results:aggregate findings"

test:
	python -m pytest tests

demo:
	python scripts/scitrace_framework.py run-task --task "Design a safe classroom demonstration using non-hazardous synthetic data."

build-site:
	python scripts/build_site.py

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
