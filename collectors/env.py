from pathlib import Path
import sys

project_dir = Path(__file__).parent.absolute()
functions_dir = project_dir / 'functions'
l10n_dir = project_dir / 'l10n'
plugins_dir = project_dir / 'plugins'
scrapers_dir = project_dir / 'scrapers'
utypes_dir = project_dir / 'utypes'

all_dirs = project_dir, functions_dir, l10n_dir, plugins_dir, scrapers_dir, utypes_dir

for i, path in enumerate(all_dirs):
    sys.path.insert(i + 1, str(path))