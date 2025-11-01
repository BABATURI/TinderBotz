'''
Created by Frederikme (TeetiFM)
'''
import time

from tinderbotz.session import Session
from tinderbotz.helpers.constants_helper import *

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

    while True:

        # spam likes, dislikes and superlikes
        # to avoid being banned:
        #   - it's best to apply a randomness in your liking by sometimes disliking.
        #   - some sleeping between two actions is recommended
        # by default the amount is 1, ratio 100% and sleep 1 second
        session.like(amount=2, ratio="75.5%", sleep=4)
        exit(0)

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
            session.store_local(geomatch)
            # dislike the profile, so it will show us the next geomatch (since we got infinite amount of dislikes anyway)
            session.like()
