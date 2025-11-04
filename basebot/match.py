from basebot.geomatch import Geomatch

# A match has the same information as a geomatch, except that you have a chatroom with an id
class Match(Geomatch):

    def __init__(self, name, chatid, age, work, study, home, gender, bio, distance, passions):
        self.chatid = chatid
        # invoking the __init__ of the parent class
        super().__init__(self, name, age, work, study, home, gender, bio, distance, passions)

    def get_chat_id(self):
        return self.chatid

    def get_dictionary(self):
        data = super().get_dictionary()
        data["chatid"] = self.get_chat_id()
        return data
