class ValidationError(Exception):


    def __init__(self, messages):

        if isinstance(messages, str):
            messages = [messages]

        self.messages = messages


        Exception.__init__(self, " ".join(messages))


class DatabaseError(Exception):
    pass
