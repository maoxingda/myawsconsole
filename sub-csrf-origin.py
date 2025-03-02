import re
import sys

if __name__ == "__main__":
    origin = sys.argv[1]

    with open("myawsconsole/settings.py") as f:
        settings = f.read()

    csrf_origin_pattern = re.compile(r"'https://\w+\.\w+\.cpolar\.top'")

    settings = csrf_origin_pattern.sub(f"'{origin}'", settings)

    with open("myawsconsole/settings.py", "w") as f:
        f.write(settings)
