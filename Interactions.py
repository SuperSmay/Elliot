class Hug:
    def solo(userName, otherNames= None):
        return f"{userName} wants a hug..."

    def multi(userName, otherNames):
        return f"{userName} is hugging {otherNames.join(' ')}"