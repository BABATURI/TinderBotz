import json
import os
import random
import string


class StorageHelper:

    @staticmethod
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    # Returns hash value of the image saved by the url given
    @staticmethod
    def store_image_as(image: bytes, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

        temp_name = "temporary"

        with open("{}/{}/{}.png".format(os.getcwd(), directory, temp_name), 'wb') as f:
            f.write(image)

    @staticmethod
    def store_match(match, directory, filename):

        if not os.path.exists(directory):
            os.makedirs(directory)

        filepath = directory + "/{}.json".format(filename)

        try:
            with open(filepath, "r", encoding='utf-8') as fp:
                data = json.load(fp)
        except IOError:
            print("Could not read file, starting from scratch")
            data = {}

        data[match.get_id()] = match.get_dictionary()

        with open(filepath, 'w+', encoding="utf-8") as file:
            json.dump(data, file)
