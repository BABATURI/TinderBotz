import json
from dataclasses import asdict, dataclass, field
from typing import Tuple, List


@dataclass
class BotSettings:
    max_likes_per_session: int = 10
    max_swipes_per_session: int = 20
    active_hours_start: int = 10      # 10:00
    active_hours_end: int = 24        # 00:00
    sleep_time: int = 60 * 60
    location: Tuple[float, float] = (32.15792931573261, 34.84213125060156)
    bypass_active_hours: bool = False
    sessions: List[str] = field(default_factory=list)

    def __str__(self):
        return f"{json.dumps({x: y for x, y in asdict(self).items() if y not in (None, '', [])}, indent=4)}"
