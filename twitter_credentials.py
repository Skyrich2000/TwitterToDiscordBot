from tweepy import OAuthHandler

ACCESS_TOKEN = "1232324660282327040-Ko5fcd4oVDxhBNPu7SmkIdvq0ysbct"
ACCESS_TOKEN_SECRET = "b9X1vUOUeWn5tUmsacVzKwrdWpI6apiNfAh1nwxTB0I0U"
CONSUMER_KEY = "zd2QK7TciW3GZmWb8Luveaf71"
CONSUMER_SECRET = "mpmUadflg3pa9QwV4m8umsp7cdHpYI4CGgbqlV3TKNXEalnve5"

def auth():
    a = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    a.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    return a