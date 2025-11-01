'''
Created by Frederikme (TeetiFM)
'''

from tinderbotz.session import Session
from dating_llm.agent import *
# import base64

# test:
# https://images-ssl.gotinder.com/u/4SjtBHe2SnJzKPPysMYzec/cTAB3urL4BARXNXtbWZ9Te.webp?Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6IiovdS80U2p0QkhlMlNuSnpLUFB5c01ZemVjLyoiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NjI1OTY5ODN9fX1dfQ__&Signature=kXzEufFU-Ja-p7Hxw7JtXWBYeNQNuuuo99oPRxt1D~L1WoVq~sNllk1zI8CvDcIKpPBo4XpbxhxGv0Nkv2MvNuJC46HCsziwx3YlzcIoGgDwHF2-u0BAxGYfzWi9GeO6QNBs13wUWXkRYRWI06gjyzoihdThfukQEqmthR0pnWsZi-RZdSMc~-Lyf-d6OgJp7uscRYJiPj27qslGhB89GOjind~bZGwd0UQHrygkgiqmXKXefmc27yKIbI8FH2wkDjR9UordjdH3vbp0RcgpRldBQcejWTEe4gEgfT6RXknJ5TW7XAIStbDGiSij2oqqJQeNzbsOfVWxM3IGXq1Mbg__&Key-Pair-Id=K368TLDEUPA6OI


def create_dating_agent():
    user_preferences = """
    The user has the following preferences:
    - Interested in blonde women
    - Interested in women with blue eyes
    - Interested in fit and athletic women
    """
    prompt = """
    You are a dating AI assistant That decides whether to like or dislike a potential match.
    The following tools are available to you:
    {tools}
    Your goal is to decide whether to like or dislike a potential match based on the information provided.
    The user has the following preferences:
    {user_preferences}
    Use all of the tools at your disposal to make an informed decision, you must access the match's images urls.
    When you have enough information, respond with this format:
    'desicion':  <'like' or 'dislike'>;
    'reason': <your reason here>;
    'match_description': <match information you observed in text here>;
    .
    """.format(tools="\n".join([f"- {tool.name}: {tool.description}" for tool in get_tools()]), user_preferences=user_preferences)
    
    chain = create_agent(prompt=prompt, tools=get_dating_tools())
    return chain


def run_dating_agent(chain, geomatch):
    query = f"""
    Here is the profile information of a potential match:
    Name: {geomatch.name}
    Age: {geomatch.age}
    Bio: {geomatch.bio}
    
    Images url Follow as attached below:
    """
    query += "\n".join(geomatch.images[:1])  # add first 5 image URLs
    content = [{"type": "text", "text": query}]
    # image_data = geomatch.images[:1]
    # for image_url in image_data:
    #     content.append({"type": "image_url", "image_url": {"url": image_url}})
    
    message_with_image = HumanMessage(content=content)
    ai_msg = run_agent(chain, messages=message_with_image)
    print("model response >>>", ai_msg)
    total_tokens = ai_msg.usage_metadata['total_tokens']  # access total tokens used
    output_tokens = ai_msg.usage_metadata['output_tokens']  # access total tokens used
    print(f"Total tokens used: {total_tokens}, Output tokens: {output_tokens}")
    return ai_msg.content


if __name__ == "__main__":
    # creates instance of session
    session = Session()

    session.set_custom_location(latitude=32.054107, longitude=34.860652)

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
    while True:

        # spam likes, dislikes and superlikes
        # to avoid being banned:
        #   - it's best to apply a randomness in your liking by sometimes disliking.
        #   - some sleeping between two actions is recommended
        # by default the amount is 1, ratio 100% and sleep 1 second
        #session.like(amount=1000, ratio="75.5%", sleep=4)

        # # Getting matches takes a while, so recommended you load as much as possible from local storage
        # # get new matches, with whom you haven't interacted yet
        # # Let's load the first 10 new matches to interact with later on.
        # # quickload on false will make sure ALL images are stored, but this might take a lot more time
        # new_matches = session.get_new_matches(amount=10, quickload=False)
        # # get already interacted with matches (matches with whom you've chatted already)
        # messaged_matches = session.get_messaged_matches()
        #
        # # you can store the data and images of these matches now locally in data/matches
        # # For now let's just store the messaged_matches
        # for match in messaged_matches:
        #     session.store_local(match)
        #
        # # let's scrape some geomatches now
        for _ in range(5):
            # get profile data (name, age, bio, images, ...)
            geomatch = session.get_geomatch(quickload=False)
            # store this data locally as json with reference to their respective (locally stored) images
            # session.store_local(geomatch)
            # Use the dating agent to decide whether to like or dislike this profile
            decision = run_dating_agent(chain, geomatch)
            
            print(f"Decision for {geomatch.name}, age {geomatch.age}:\n{decision}")
            if decision == "like":
                pass
                # session.like()
            else:
                pass
                # session.dislike()
            input("Press Enter to continue...")
            # dislike the profile, so it will show us the next geomatch (since we got infinite amount of dislikes anyway)
            # session.like()
