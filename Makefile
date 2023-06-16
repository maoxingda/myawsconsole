install-requirements:
	ssh pdaf 'conda activate myawsconsole && cd myawsconsole && pip install -r requirements.txt'

prod-collectstatic:
	ssh pdaf 'conda activate myawsconsole && cd myawsconsole && python manage.py collectstatic --settings myawsconsole.prod_settings --no-input'

sbox-collectstatic:
	python manage.py collectstatic --settings myawsconsole.sbox_settings --no-input
