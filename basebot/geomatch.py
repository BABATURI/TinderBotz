import random
import string
import json
import os

from typing import List


def _id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class Geomatch:

    def __init__(self, name, age, work, study, home, gender, bio, lifestyle, basics, anthem,
                    looking_for=None, distance=None, passions=None, instagram=None,
                    images: List[str] = []):
        self.name = name
        self.age = age
        self.work = work
        self.study = study
        self.home = home
        self.gender = gender
        self.passions = passions
        self.bio = bio
        self.lifestyle = lifestyle
        self.basics = basics
        self.anthem = anthem
        self.looking_for = looking_for
        self.distance = distance
        self.images: List[str] = images
        self.instagram = instagram
        self.prompts = []
        self.listening = []

        # create a unique id for this person
        self.id = "{}{}_{}".format(name, age, _id_generator(size=4))

    def get_name(self):
        return self.name

    def get_age(self):
        return self.age

    def get_work(self):
        return self.work

    def get_study(self):
        return self.study

    def get_home(self):
        return self.home

    def get_gender(self):
        return self.gender

    def get_passions(self):
        return self.passions

    def get_bio(self):
        return self.bio

    def get_lifestyle(self):
        return self.lifestyle

    def get_basics(self):
        return self.basics

    def get_anthem(self):
        return self.anthem

    def get_looking_for(self):
        return self.looking_for

    def get_distance(self):
        return self.distance

    def get_instagram(self):
        return self.instagram

    def get_id(self):
        return self.id

    def get_dictionary(self):
        data = {
            "name": self.get_name(),
            "age": self.get_age(),
            "work": self.get_work(),
            "study": self.get_study(),
            "home": self.get_home(),
            "gender": self.gender,
            "bio": self.get_bio(),
            "distance": self.get_distance(),
            "basics": self.get_basics(),
            "lifestyle": self.get_lifestyle(),
            "passions": self.get_passions(),
            "anthem": self.get_anthem(),
            "looking_for": self.get_looking_for(),
            "instagram": self.get_instagram(),
            "images": self.images,
        }
        return data

    def store_json(self, directory, filename):
        if not os.path.exists(directory):
            os.makedirs(directory)
		
        filepath = os.path.join(directory, "{}.json".format(filename))
        try:
            with open(filepath, "r", encoding='utf-8') as fp:
                data = json.load(fp)
        except IOError:
            print("Could not read file, starting from scratch")
            data = {}

        data[self.get_id()] = self.get_dictionary()
        with open(filepath, 'w+', encoding="utf-8") as file:
            json.dump(data, file)
