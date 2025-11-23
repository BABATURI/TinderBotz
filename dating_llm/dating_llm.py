from typing import List, Dict, Any, Tuple


# todo: moved shared logic
class DatingLLM:
    def __init__(self) -> None:
        pass

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        raise NotImplementedError()

    def run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[Dict[str, Any], int]:
        raise NotImplementedError()
