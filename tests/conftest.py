import sys
from pathlib import Path

# Permet d'importer les modules de src/ depuis les tests sans les installer
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
