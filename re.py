import sys
this_dir = sys.path.pop(0)
sys.modules.pop(__name__)
import re
sys.path.insert(0, this_dir)

import bash_importer
bash_importer.install_importer()
