import os
import shutil
import time
import sys
from unittest.mock import MagicMock

# Mock undetected_chromedriver before importing BaseSession
sys.modules["undetected_chromedriver"] = MagicMock()

from tinderbotz.base_session import BaseSession
from tinderbotz.helpers.storage_helper import StorageHelper
from tinderbotz.helpers.match_data import MatchData

class TestSession(BaseSession):
    app_name = "test_app"
    def __init__(self):
        # Skip BaseSession.__init__ to avoid overhead, just set what we need
        self.session_data = {}

    # Implement abstract methods to avoid instantiation errors if any
    @property
    def app_url(self) -> str:
        return "http://test"
    def _is_logged_in(self):
        return True
    def get_geomatch(self):
        pass
    def get_chat_ids(self, new=True, messaged=True):
        pass
    def get_new_matches(self, amount=100000):
        pass
    def get_messaged_matches(self, amount=100000):
        pass
    def send_message(self, chatid, message):
        pass
    def unmatch(self, chatid):
        pass
    def _handle_potential_popups(self):
        pass

def test_generic_storage_refactor():
    session = TestSession()
    directory = os.path.join("data", session.app_name)
    
    # Clean up
    if os.path.exists(directory):
        shutil.rmtree(directory)
        
    print("Testing is_ambush_allowed (fresh)...")
    assert session.is_ambush_allowed("user_1") == True
    print("Pass")
    
    print("Testing log_ambush_sent...")
    match_data = session.get_match_data("user_1")
    match_data.log_ambush_sent()
    session.save_match_data(match_data)
    
    # Verify file created
    assert os.path.exists(os.path.join(directory, "matches_data.json"))
    
    # Verify stats updated
    data = StorageHelper.load_matches_data(session.app_name)
    assert data["user_1"].ambush_count == 1
    print("Pass")
    
    print("Testing generic data storage...")
    match_data = session.get_match_data("user_1")
    match_data.name = "Alice"
    match_data.other_data["custom_field"] = "custom_value"
    session.save_match_data(match_data)
    
    # Reload and verify
    reloaded_data = StorageHelper.load_matches_data(session.app_name)
    user_1 = reloaded_data["user_1"]
    assert user_1.name == "Alice"
    assert user_1.other_data["custom_field"] == "custom_value"
    assert user_1.ambush_count == 1
    print("Pass")

    print("Testing is_ambush_allowed (after sending)...")
    assert session.is_ambush_allowed("user_1") == False
    print("Pass")
    
    # Cleanup
    if os.path.exists(directory):
        shutil.rmtree(directory)
    print("All tests passed!")

if __name__ == "__main__":
    test_generic_storage_refactor()
