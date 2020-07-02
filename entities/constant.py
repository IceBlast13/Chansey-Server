import datetime
firebaseConfig = {
    "apiKey": "AIzaSyB9vkTP5BPzlhxhosSiH_XaklrKidfPGbQ",
    "authDomain": "wcked-28b7c.firebaseapp.com",
    "databaseURL": "https://wcked-28b7c.firebaseio.com",
    "projectId": "wcked-28b7c",
    "storageBucket": "wcked-28b7c.appspot.com",
    "messagingSenderId": "603152069527",
    "appId": "1:603152069527:web:76cf907c4a4b9a06"
  }


FIREBASE_ROOT = "https://wcked-28b7c.firebaseio.com/"
USERS = "/Users"
MESSAGE = "message"
DUPLICATE_USER = "A user with email '{}' already exists"
NOT_FOUND_USER = "A user with email '{}' does not exists"
SOMETHING_WRONG = "Something went wrong"
#USER DATA
MALE = "Male"
FEMALE = "Female"
NEW_USER = {"first_name": "",
            "last_name": "",
            "phone_number": "",
            "gender": MALE,
            "languages": "",

            "birth_date": datetime.datetime(1990, 1, 1).timestamp(),
            "location": ""
            }