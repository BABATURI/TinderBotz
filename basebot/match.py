from typing import Any, Dict, Optional, List

from basebot.geomatch import Geomatch


class Match(Geomatch):
	def __init__(self, name: str, chatid: str, age: Optional[int], work: Optional[str], study: Optional[str], home: Optional[str], gender: str, bio: Optional[str], distance: Optional[float], passions: Optional[List[str]]):
		self.chatid: str = chatid
		super().__init__(self, name, age, work, study, home, gender, bio, None, None, None, None, distance, passions)

	def get_chat_id(self) -> str:
		return self.chatid

	def get_dictionary(self) -> Dict[str, Any]:
		data: Dict[str, Any] = super().get_dictionary()
		data["chatid"] = self.get_chat_id()
		return data
