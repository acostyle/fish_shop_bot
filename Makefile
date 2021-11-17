.PHONY: win_install
win_install:
		python -m venv venv
		venv\Scripts\activate.bat
		pip install -r requirements.txt

.PHONY: linux_install
linux_install:
		python -m venv venv
		source venv/bin/activate
		pip install -r requirements.txt
		