import sys
import os

# Ajouter le répertoire de l'application au path Python
sys.path.insert(0, os.path.dirname(__file__))

from server import app as application
