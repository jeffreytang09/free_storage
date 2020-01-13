source="free_storage"
pipenv run isort --apply --recursive $source
pipenv run black $source
pipenv run flake8 $source
pipenv run mypy $source
