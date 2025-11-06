'''
Created by Frederikme (TeetiFM)
'''

from tinderbotz.session import Session, Geomatch
from dating_llm.agent import *
# import base64

# test:
# https://images-ssl.gotinder.com/u/4SjtBHe2SnJzKPPysMYzec/cTAB3urL4BARXNXtbWZ9Te.webp?Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6IiovdS80U2p0QkhlMlNuSnpLUFB5c01ZemVjLyoiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NjI1OTY5ODN9fX1dfQ__&Signature=kXzEufFU-Ja-p7Hxw7JtXWBYeNQNuuuo99oPRxt1D~L1WoVq~sNllk1zI8CvDcIKpPBo4XpbxhxGv0Nkv2MvNuJC46HCsziwx3YlzcIoGgDwHF2-u0BAxGYfzWi9GeO6QNBs13wUWXkRYRWI06gjyzoihdThfukQEqmthR0pnWsZi-RZdSMc~-Lyf-d6OgJp7uscRYJiPj27qslGhB89GOjind~bZGwd0UQHrygkgiqmXKXefmc27yKIbI8FH2wkDjR9UordjdH3vbp0RcgpRldBQcejWTEe4gEgfT6RXknJ5TW7XAIStbDGiSij2oqqJQeNzbsOfVWxM3IGXq1Mbg__&Key-Pair-Id=K368TLDEUPA6OI


def create_dating_agent():
    # user_preferences = """
    # The user has the following preferences:
    # - Interested in blonde women
    # - Interested in women with blue eyes
    # - Interested in fit and athletic women
    # """
    # prompt = """
    # You are a dating AI assistant That decides whether to like or dislike a potential match.
    # The following tools are available to you:
    # {tools}
    # Your goal is to decide whether to like or dislike a potential match based on the information provided.
    # The user has the following preferences:
    # {user_preferences}
    # Use all of the tools at your disposal to make an informed decision, you must access the match's images urls.
    # When you have enough information, respond with this format:
    # 'desicion':  <'like' or 'dislike'>;
    # 'reason': <your reason here>;
    # 'match_description': <match information you observed in text here>;
    # .
    # """.format(tools="\n".join([f"- {tool.name}: {tool.description}" for tool in []]), user_preferences=user_preferences)
    
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

    # Alternatively, you can also use your phone number to login
    country = "Israel"
    phone_number = "0"
    session.login_using_sms(country, phone_number)

    # adjust allowed distance for geomatches
    # Note: PARAMETER IS IN KILOMETERS!
    #session.set_distance_range(km=50)

    # set range of prefered age
    #session.set_age_range(19, 23)

    # set interested in gender(s) -> options are: WOMEN, MEN, EVERYONE
    #session.set_sexuality(Sexuality.WOMEN)

    # Allow profiles from all over the world to appear
    #session.set_global(False)

    #ROUNDS = 10
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
        # dislike the profile, so it will show us the next geomatch (since we got infinite amount of dislikes anyway)
        # session.like()
