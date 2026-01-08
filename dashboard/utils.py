import os
import sys
from pathlib import Path
import streamlit as st

# Add parent to path for imports if not already there
# This ensures we can import myllmtradingagents
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def get_config_path() -> str:
    """Get config path from environment or default."""
    return os.environ.get("MYLLM_CONFIG_PATH", "config/arena.yaml")


def get_storage():
    """Get storage instance."""
    from myllmtradingagents.settings import load_config
    from myllmtradingagents.storage import SQLiteStorage
    
    config_path = get_config_path()
    
    if not Path(config_path).exists():
        st.error(f"Config file not found: {config_path}")
        st.stop()
    
    config = load_config(config_path)
    storage = SQLiteStorage(config.db_path)
    storage.initialize()
    
    return storage, config
