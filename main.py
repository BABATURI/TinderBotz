'''
Created by Frederikme (TeetiFM)
'''
from typing import Dict, Any

from tinderbotz.session import Session, Geomatch
from dating_llm.agent import *


def create_dating_agent() -> DatingLLM:
	user_pref = "I like fit and slim, blonde / hazel haired women with bright eyes who enjoy outdoor activities and have a good sense of humor."
	return DatingLLM(user_pref)


def get_response_from_dating_agent(dllm: DatingLLM, geomatch: Geomatch) -> Dict[str, Any]:
	query = f"""
    Name: {geomatch.name}
    Age: {geomatch.age}
    Looking For: {geomatch.looking_for}
    Bio: {geomatch.bio}
    """
	image_data = geomatch.images[:3]

	ai_json_response, total_tokens = dllm.run_llm(query, image_data)
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
		geomatch = session.get_geomatch(quickload=False)
		# store this data locally as json with reference to their respective (locally stored) images
		# session.store_local(geomatch)
		# Use the dating agent to decide whether to like or dislike this profile
		print("running dating LLM query...")
		decision_json = get_response_from_dating_agent(dating_agent, geomatch)

		print(f"Decision for {geomatch.name}, age {geomatch.age}:\n{decision_json}")
		if decision_json["decision"] == "like":
			session.like()
		else:
			session.dislike()
		input("Press Enter to continue...")


if __name__ == "__main__":
	main()
