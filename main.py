import json
from dataclasses import asdict
from pathlib import Path

from tinderbotz.session import Session, Geomatch
from dating_llm.agent import *


def create_dating_agent() -> DatingLLM:
	config_file: Path = Path("configuration", "user_pref")

	user_pref: str = "I like fit and slim, blonde / hazel haired women with bright eyes who enjoy outdoor activities and have a good sense of humor."
	if config_file.exists():
		with open("configuration/user_pref", "r") as f:
			user_pref = f.read()

	return DatingLLM(user_pref)


def get_response_from_dating_agent(dllm: DatingLLM, geomatch: Geomatch) -> Dict[str, Any]:
	# Note: to save tokens we don't save everything - only what matters
	minimized_duplicate_geomatch: Geomatch = Geomatch(name=geomatch.name,
	                                         age=geomatch.age,
	                                         work=geomatch.work,
	                                         study=geomatch.study,
	                                         bio=geomatch.bio,
	                                         lifestyle=geomatch.lifestyle,
	                                         passions=geomatch.passions,
	                                         looking_for=geomatch.looking_for)


	query: str = (f"Full profile info:\n"
	              f"{json.dumps({x: y for x, y in asdict(minimized_duplicate_geomatch).items() if y not in (None, '', [])}, indent=4)}")
	image_urls: List[str] = geomatch.image_urls[:3]

	ai_json_response, total_tokens = dllm.run_llm(query, image_urls)
	print(f"Total tokens used: {total_tokens}")
	return ai_json_response


def main() -> None:
	# creates instance of session
	session = Session()
	location = (32.15792931573261, 34.84213125060156)
	session.set_custom_location(latitude=location[0], longitude=location[1])

	session.wait_for_login()

	dating_agent: DatingLLM = create_dating_agent()

	for _ in range(10):
		# get profile data (name, age, bio, images, ...)
		geomatch: Geomatch = session.get_geomatch(quickload=False)
		# store this data locally as json with reference to their respective (locally stored) images
		session.store_local(geomatch)
		# Use the dating agent to decide whether to like or dislike this profile
		print("running dating LLM query...")
		decision_json: Dict[str, Any] = get_response_from_dating_agent(dating_agent, geomatch)

		print(f"Decision for {geomatch.name}, age {geomatch.age}:\n{decision_json}")
		if decision_json["decision"] == "like":
			session.like()
		else:
			session.dislike()
		input("Press Enter to continue...")


if __name__ == "__main__":
	main()
