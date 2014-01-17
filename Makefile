PYDOCTOR=pydoctor

docs:
	$(PYDOCTOR) --make-html --html-output apidoc --add-package tint --project-name=tint --project-url=http://github.com/bmuller/tint --html-use-sorttable --html-use-splitlinks --html-shorten-lists 

lint:
	pep8 --ignore=E303,E251,E201,E202 ./tint --max-line-length=140
	find ./tint -name '*.py' | xargs pyflakes

install:
	python setup.py install
