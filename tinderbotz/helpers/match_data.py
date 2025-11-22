import time
from dataclasses import dataclass, field, asdict, fields
from typing import Optional, Dict, Any, List

# TODO: move to config
MAX_AMBUSH_COUNT = 1


@dataclass
class MatchData:
    user_id: str
    name: Optional[str] = None
    ambush_count: int = 0
    last_messaged: Optional[str] = None
    msg_texts: List[str] = field(default_factory=list)
    other_data: Dict[str, Any] = field(default_factory=dict)

    def is_ambush_allowed(self) -> bool:
        return self.ambush_count < MAX_AMBUSH_COUNT
    
    def log_ambush_sent(self) -> None:
        self.ambush_count += 1
        self.last_messaged = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MatchData':
        known_fields = {f.name for f in fields(MatchData)}
        
        constructor_kwargs = {}
        # Start with existing other_data if present, or empty dict
        extras = data.get('other_data', {}).copy()
        
        for key, value in data.items():
            if key in known_fields:
                if key != 'other_data':
                    constructor_kwargs[key] = value
            else:
                extras[key] = value
        
        if 'user_id' not in constructor_kwargs:
            raise ValueError("user_id is required")

        return MatchData(other_data=extras, **constructor_kwargs)
