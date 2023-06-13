prod-install-requirements:
	ssh pdaf 'conda activate myawsconsole && cd myawsconsole && pip install -r requirements.txt'