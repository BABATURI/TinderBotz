'''
Created by Frederikme (TeetiFM)
'''

from tinderbotz.session import Session, Geomatch
from dating_llm.agent import *


def create_dating_agent():
	user_pref = "I like fit and slim, blonde / hazel haired women with bright eyes who enjoy outdoor activities and have a good sense of humor."
	dllm = DatingLLM(user_pref)
	return dllm


def run_dating_agent(dllm: DatingLLM, geomatch: Geomatch):
	query = f"""
    Name: {geomatch.name}
    Age: {geomatch.age}
    Looking For: {geomatch.looking_for}
    Bio: {geomatch.bio}
    """
	image_data = geomatch.images[:3]

	ai_msg, total_tokens = dllm.run_llm(query, image_data)
	print(f"Total tokens used: {total_tokens}")
	return ai_msg


if __name__ == "__main__":
	# creates instance of session
	session = Session()
	location = (32.15792931573261, 34.84213125060156)
	session.set_custom_location(latitude=location[0], longitude=location[1])

	session.wait_for_login()

	# adjust allowed distance for geomatches
	# Note: PARAMETER IS IN KILOMETERS!
	# session.set_distance_range(km=50)

	# set range of prefered age
	# session.set_age_range(19, 23)

	# set interested in gender(s) -> options are: WOMEN, MEN, EVERYONE
	# session.set_sexuality(Sexuality.WOMEN)

	# Allow profiles from all over the world to appear
	# session.set_global(False)

	# ROUNDS = 10
	chain = create_dating_agent()

	auto_swipe_count = 9
	for _ in range(auto_swipe_count):
		# get profile data (name, age, bio, images, ...)
		geomatch = session.get_geomatch(quickload=False)
		# store this data locally as json with reference to their respective (locally stored) images
		# session.store_local(geomatch)
		# Use the dating agent to decide whether to like or dislike this profile
		print("running dating LLM query...")
		decision_json = run_dating_agent(chain, geomatch)

		print(f"Decision for {geomatch.name}, age {geomatch.age}:\n{decision_json}")
		if decision_json["decision"] == "like":
			session.like()
		else:
			session.dislike()
		input("Press Enter to continue...")
