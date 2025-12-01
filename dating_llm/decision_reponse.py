from dataclasses import dataclass


@dataclass
class DecisionResponse:
    decision: str
    like_message: str
    reason: str

    def __post__init__(self):
        assert self.decision in ("like", "dislike")

    @property
    def is_like(self) -> bool:
        return self.decision == 'like'

