migrage:
	ssh pdaf 'cd maoxd/myawsconsole && conda run -n myawsconsole python manage.py migrate'

install-requirements:
	ssh pdaf 'cd maoxd/myawsconsole && conda run -n myawsconsole pip install -r requirements.txt'
