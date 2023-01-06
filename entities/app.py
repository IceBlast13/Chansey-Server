import random
import re
from flask import Flask, request
from flask_restful import Resource, Api
from flask_jwt import JWT, jwt_required
import entities.constant as constant
import pyrebase
from client.client import Client
from bot.bot import Bot
from names import *
import datetime
#Specialisation Map
specialisations = {
                       "General practice": 15,
                       "Internal medicine": 19,
                       "Gastroenterology": 14,
                       "Urology": 42,
                       "Gynecology": 18,
                       "Surgery": 39,
                       "Psychiatry": 36,
                       "Orthopedics": 31,
                       "Rheumatology": 41,
                       "Allergology": 5,
                       "Otolaryngology": 32,
                       "Cardiology": 1,
                       "Pulmonology": 35,
                       "Neurology": 27,
                       "Dentistry": 43,
                       "Ophthalmology": 30,
                       "Infectiology": 23,
                       "Endocrinology": 12,
                       "Nephrology": 26,
                       "Dermatology": 11,
                       }

#Flask Setup
app = Flask(__name__)
app.secret_key = 'Thisisasupersecretkey'
api = Api(app)

#Pyrebase Setup
firebase = pyrebase.initialize_app(constant.firebaseConfig)
auth = firebase.auth()
db = firebase.database()

#Chat Bot Setup
uri = "<uri>"
api_key = "<key>"
secret_key = "<key>"
healthServiceUrl = "<service_url>"
language = "en-gb"

Client = Client(api_key, secret_key, uri, language, healthServiceUrl)

Nurse_Joy = Bot(Client)

#DELETE ME
items = []


class Auth(Resource):
    def post(self):
        data = request.get_json()
        try:
            user = auth.sign_in_with_email_and_password(data['username'], data['password'])
        except Exception:
            return {'message': constant.NOT_FOUND_USER.format(data["username"])}, 404
        return user, 200


class Register(Resource):
    def post(self):
        data = request.get_json()
        try:
            user = auth.create_user_with_email_and_password(data['username'], data['password'])
        except Exception:
            return {'message': constant.DUPLICATE_USER.format(data["username"])}, 400
        user_data = constant.NEW_USER
        db.child("users").child(user["localId"]).set(user_data, token=user['idToken'])
        return user, 201


class User(Resource):
    def get(self, token):
        try:
            user = auth.get_account_info(token)
        except Exception:
            return {'message': Exception}, 500

        return db.child("users").child(user["users"][0]['localId']).get(token=token).val(), 200

    def put(self, token):
        user_data = request.get_json()
        user = auth.get_account_info(token)
        try:
            db.child("users").child(user["users"][0]['localId']).update(user_data, token=token)
        except Exception:
            return {'message' : constant.SOMETHING_WRONG}, 500

        return db.child("users").child(user["users"][0]['localId']).get(token=token).val(), 200

class Users(Resource):

        def get(self, name):
            list = db.child("users").get().val()
            for user in list.values():
                full_name = user.get("first_name") + user.get("last_name")
                reverse_name = user.get("last_name") + user.get("first_name")
                if (name.lower() == full_name.lower() or name.lower() == reverse_name.lower()):
                    return user
            return {'message': 'User not found'}, 404



class Post(Resource):

    def post(self, token):
        user_data = request.get_json()
        user = auth.get_account_info(token)
        display_name = db.child("users").child(user["users"][0]['localId']).get(token=token).val().get("first_name")
        if display_name == "":
            return {'message' : "Please update your info"}, 500
        data = {
            'message' : user_data['message'],
            'title' : user_data['title'],
            'category' : user_data['category'],
            'comments' : False,
            'user' : user["users"][0]['localId'],
            'display_name' : display_name,
            'votes' : str(1)
        }
        try:
            db.child("posts").push(data)
        except Exception:
            return {'message' : constant.SOMETHING_WRONG}, 500

        return {'message' : "Post added"}


class PostList(Resource):

    def get(self):
        try:
            return db.child("posts").get().val()
        except Exception:
            return {'message': constant.SOMETHING_WRONG}, 500


class Comment(Resource):

    def post(self, token):
        user_data = request.get_json()
        user = auth.get_account_info(token)
        user_id = user["users"][0]['localId']
        display_name = db.child("users").child(user["users"][0]['localId']).get(token=token).val().get("first_name")
        if display_name == "":
            return {'message' : "Please update your info"}, 500
        data = {
            'message' : user_data['message'],
            'display_name': display_name,
            'votes': str(1),
            'user_id': user_id
        }
        try:
            db.child("posts").child(user_data['id']).child("comments").push(data)
        except Exception:
            return {'message': constant.SOMETHING_WRONG}, 500

        return {'message': "Comment added"}


class CommentList(Resource):

    def get(self, id):
        try:
            return db.child("posts").child(id).child("comments").get().val(), 200
        except Exception:
            return {'message': constant.SOMETHING_WRONG}, 500


class SymptomChecker(Resource):

    def get(self, text):
        return Nurse_Joy.talk_to_Bot(text)


class Diagnosis(Resource):

    def post(self, token):
        user_data = request.get_json()
        user = auth.get_account_info(token)
        gender = db.child("users").child(user["users"][0]['localId']).get(token=token).val().get("gender")
        year = db.child("users").child(user["users"][0]['localId']).get(token=token).val().get("birth_date")
        symptoms = []
        for item in user_data:
            symptoms.append(item['id'])
        return Client.loadDiagnosis(symptoms, gender, year.split("-")[0])


class Issue(Resource):

    def get(self, id):
        return Client.loadIssueInfo(id)


class Specialist(Resource):

    def get(self, token, id, time):
        filter = []
        user = auth.get_account_info(token)
        result = db.child("specialists").get().val()

        language = db.child("users").child(user["users"][0]['localId']).get(token=token).val().get("languages")
        location = db.child("users").child(user["users"][0]['localId']).get(token=token).val().get("location")
        first_name = db.child("users").child(user["users"][0]['localId']).get(token=token).val().get("first_name")
        last_name = db.child("users").child(user["users"][0]['localId']).get(token=token).val().get("last_name")

        patient_name = "{0} {1}".format(first_name, last_name)

        mylanguages = re.findall('[A-Z][^A-Z]*', language)


        for entry in result:

            hisLanguages = re.findall('[A-Z][^A-Z]*', entry.get("Language"))
            bool = self.match(mylanguages, hisLanguages)
            if bool and entry.get("Location") == location and str(entry.get("Specialisation")) == id:
                filter.append(entry)

        choice = random.choice(filter)
        index = choice.get("ID")
        consultation = {
            'patientName': patient_name,
            'patient': user["users"][0]['localId'],
            'time' : time,
            'specialistId' : index,
            'specialistName' : self.get_name(index),
            'specialisationName' : self.get_specialisation_name(index),
            'status' : 'Pending',
            'iconName' : 'clock'
        }
        db.child("specialists").child(index).child("Schedule").push(consultation)
        db.child("users").child(user["users"][0]['localId']).child("schedule").push(consultation, token=token)
        return choice

    def match(self, a, b):

        for element in a:
            for element1 in b:
                if element == element1:
                    return True
        return False

    def get_name(self, id):
        first_name = db.child("specialists").child(id).child("First Name").get().val()
        last_name = db.child("specialists").child(id).child("Last Name").get().val()
        full_name = first_name + " " + last_name
        return full_name

    def get_specialisation_name(self, id):
        index = db.child("specialists").child(id).child("Specialisation").get().val()
        for x, y in specialisations.items():
            if y == index:
                return x


class Specialists(Resource):

    def get(self, name):
        list = db.child("specialists").get().val()
        for doctor in list:
            full_name = doctor.get("First Name") + doctor.get("Last Name")
            reverse_name = doctor.get("Last Name") + doctor.get("First Name")
            if (name.lower() == full_name.lower() or name.lower() == reverse_name.lower()):
                return doctor
        return {'message': 'Specialist not found'}, 404

class Consultation(Resource):

    def get(self, token):
        user = auth.get_account_info(token)
        try:
            return db.child("users").child(user["users"][0]['localId']).child("schedule").get(token=token).val(), 200
        except Exception:
            return {'message': constant.SOMETHING_WRONG}, 500


class PostConsultation(Resource):

    def post(self, token):
        user = auth.get_account_info(token)
        user_data = request.get_json()
        first_name = db.child("users").child(user["users"][0]['localId']).get(token=token).val().get("first_name")
        last_name = db.child("users").child(user["users"][0]['localId']).get(token=token).val().get("last_name")
        display_name = "{0} {1}".format(first_name, last_name)

        consultation = {
            'patientName': display_name,
            'patient': user["users"][0]['localId'],
            'time': user_data["time"],
            'specialistId': user_data["id"],
            'specialistName': user_data["name"],
            'specialisationName': user_data["specialisation_name"],
            'status': 'Pending',
            'iconName': 'clock'
        }
        db.child("specialists").child(user_data["id"]).child("Schedule").push(consultation)
        db.child("users").child(user["users"][0]['localId']).child("schedule").push(consultation, token=token)

class Medic(Resource):

    def get(self, id):
        result = db.child("specialists").child(id).get().val()
        if(result != None):
            return result, 200
        else:
            return result, 404

    def post(self, id):
        medic = db.child("specialists").child(id).get().val()
        user_data = request.get_json()
        display_name = "Dr. {0} {1}".format(medic["First Name"], medic["Last Name"])
        data = {
            'message': user_data['message'],
            'display_name': display_name,
            'votes': str(1),
            'user_id': id
        }

        try:
            db.child("posts").child(user_data['id']).child("comments").push(data)
        except Exception:
            return {'message': constant.SOMETHING_WRONG}, 500

        return {'message': "Comment added"}

    def put(self, id):
        user_data = request.get_json()

        try:
            db.child("specialists").child(id).update(user_data)
        except Exception:
            return {'message': constant.SOMETHING_WRONG}, 500

        return db.child("specialists").child(id).get().val(), 200


class MedicConsultation(Resource):


    def get(self, id):
        try:
            return db.child("specialists").child(id).child("Schedule").get().val(), 200
        except Exception:
            return {'message': constant.SOMETHING_WRONG}, 500


    def put(self, id):
        user_data = request.get_json()

        patientId = db.child("specialists").child(id).child("Schedule").child(user_data["id"]).child("patient").get().val()
        patientName = db.child("specialists").child(id).child("Schedule").child(user_data["id"]).child("patientName").get().val()
        consultation = {
            'patientName': patientName,
            'patient': patientId,
            'time': user_data["time"],
            'specialistId': user_data["specialistId"],
            'specialistName': user_data["name"],
            'specialisationName': user_data["specialisation_name"],
            'status': user_data["status"],
            'iconName': user_data["iconName"]
        }

        try:
            c = db.child("specialists").child(id).child("Schedule").child(user_data["id"]).get().val()
            db.child("specialists").child(id).child("Schedule").child(user_data["id"]).update(consultation)
            l = db.child("users").child(patientId).child("schedule").get().val()
            for key, entry in l.items():
                if(c == entry):
                    db.child("users").child(patientId).child("schedule").child(key).update(consultation)
                    break
        except Exception:
            return {'message': constant.SOMETHING_WRONG}, 500








api.add_resource(Auth, '/auth')
api.add_resource(Register, '/register')
api.add_resource(User, '/user/<string:token>')
api.add_resource(Users, '/users/<string:name>')
api.add_resource(Post, '/post/<string:token>')
api.add_resource(PostList, '/posts')
api.add_resource(Comment, '/comment/<string:token>')
api.add_resource(CommentList, '/comments/<string:id>')
api.add_resource(SymptomChecker, '/symptom/<string:text>')
api.add_resource(Diagnosis, '/diagnosis/<string:token>')
api.add_resource(Issue, '/issue/<string:id>')
api.add_resource(Specialist, '/specialist/<string:token>/<string:id>/<string:time>')
api.add_resource(Specialists, '/specialists/<string:name>')
api.add_resource(Consultation, '/consultation/<string:token>')
api.add_resource(PostConsultation, '/postConsultation/<string:token>')
api.add_resource(Medic, '/medic/<string:id>')
api.add_resource(MedicConsultation, '/medicConsultation/<string:id>')

app.run(host='0.0.0.0', debug=True)






# for i in range(1000):
#     first_name = get_first_name()
#     last_name = get_last_name()
#     location = random.choice(("Bucharest", "Cluj-Napoca"))
#     data = {
#        "ID" : i,
#        "First Name" : first_name,
#        "Last Name" : last_name,
#        "Location" : location,
#        "Specialisation" : random.choice(list(specialisations.values())),
#        "Language" : random.choice(("English", "Deutsch", "EnglishDeutsch"))
#     }
#     result = db.child('specialists').child(str(i)).set(data)
#     print(result)
