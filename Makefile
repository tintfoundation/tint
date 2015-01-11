lint:
	pep8 --ignore=E303,E251,E201,E202 ./tint --max-line-length=140
	find ./tint -name '*.py' | xargs pyflakes

test:
	trial tint

run:
	pip install -r requirements.txt
	twistd -noy tint.tac
