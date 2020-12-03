
pyinstaller --one-file --clean -F --noupx --hidden-import "./DABI/__init__.py" DABI.py
:: pyinstaller --clean -F --noupx --add-data "./templates/;./templates/" --add-data "./config.py;." UWEB.py
:: --debug all
