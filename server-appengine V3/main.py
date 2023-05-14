import io
from urllib import response
import uuid
from google.cloud import ndb
from flask import Flask, render_template, request, make_response
import json
from io import StringIO
from helpfunctions import *



app = Flask(__name__)

ds_client = ndb.Client()

class EntryModel(ndb.Model):
    #Logs automatically
    date = ndb.DateTimeProperty(auto_now_add=True)
    
    #Gets it in /matches
    answers = ndb.TextProperty(required=True)
    euclidean = ndb.TextProperty()
    manhattan = ndb.TextProperty()
    qda = ndb.TextProperty()
    random = ndb.TextProperty()

    #Gets it in /demo
    euclideanScore = ndb.TextProperty()
    manhattanScore = ndb.TextProperty()
    qdaScore = ndb.TextProperty()
    randomScore = ndb.TextProperty()

    #Gets it in /thankyou
    age = ndb.TextProperty()
    gender = ndb.TextProperty()
    voted = ndb.TextProperty()




@app.route('/')
def root():
    """
    Info and conset page
    """
    return render_template('Home page.html')

@app.route('/vaa', methods = ['POST'])
def GetVaa():
    """
    All 25 questions listed
    """
    listOfQ, valgkredse, partier = getData()
    session_id = str(uuid.uuid4())
    return render_template('VAA questions.html', sessionID = session_id, questions = listOfQ, partier = partier, valgkredse = valgkredse )


@app.route('/matches', methods = ['POST'])
def GetMatches():
    """
    Logs anwsers and the proposed matches for the user, sends the user to the match ranking page
    """
    answersString = ['{']
    forcal = []
    
    #Get what the person voted in 2022 (self.request.get finds element by name)
    #answersString.append("\"Stemte\":\"" + request.form.get('parti')+ "\", ")       

    #Get valgkreds
    #answersString.append("\"Valgkreds\":\"" + request.form.get('valgkredse') + "\", ")

    #Get all answers
    for i in range(25):
        temp = str(i+1)
        forcal.append(request.form.get('Q' + temp + ' Answer'))
        answersString.append("\"Q"+temp + '\": \"' + request.form.get('Q' + temp + ' Answer')+ '\", ')#-> "Qx" : "Enig",
    
    answersString = ''.join(answersString)
    answersString = answersString[:-2]
    answersString += '}'

    session_id = request.form.get('session_id')

    #Calculate all the different matches
    userinput = makeUserDF(forcal)
    matches = find_distances(userinput)
    
    with ds_client.context():
        entry_key = ndb.Key('EntryModel', session_id)
        em = EntryModel(key = entry_key)
        em.answers = answersString
        for i in matches:
            if "Euclidean" in i:
                em.euclidean = "{\"Euclidean\": \"" + i[1] + "\"}"
            elif "Manhattan" in i:
                em.manhattan = "{\"Manhattan\": \"" + i[1] + "\"}"
            elif "QDA" in i:
                em.qda = "{\"QDA\": \"" + i[1] + "\"}"
            elif "Random" in i:
                em.random = "{\"Random\": \"" + i[1] + "\"}"
        em.put()

    return render_template('Matches.html', Matches = matches, sessionID = session_id)

@app.route('/demo', methods = ['POST'])
def GetChoice():
    """
    Logs the scores and sends the user to the demographic questions
    """
    session_id = request.form.get('session_id')

    with ds_client.context():
        entity_key = ndb.Key('EntryModel', session_id)
        em = entity_key.get()
        em.euclideanScore = "{\"EuclideanScore\": \"" + request.form.get('Euclidean') + "\"}"
        em.manhattanScore = "{\"ManhattanScore\": \"" + request.form.get('Manhattan') + "\"}"
        em.qdaScore = "{\"QDAScore\": \"" + request.form.get('QDA') + "\"}"
        em.randomScore = "{\"RandomScore\": \"" + request.form.get('Random') + "\"}"
        em.put()
    listOfQ, valgkredse, partier = getData()
    agelist = [i for i in range(18, 101)]

    return render_template('Demographic questions.html', sessionID = session_id, partier = partier, ages = agelist)

@app.route('/thankyou', methods = ['POST'])
def GetThanks():
    """
    Logs the demographic questions and sends the user to the thank you page
    """
    session_id = request.form.get('session_id')

    #Log the age, gender and last voted
    with ds_client.context():
        entity_key = ndb.Key('EntryModel', session_id)
        em = entity_key.get()
        em.age = "{\"Age\": \"" + request.form.get('age') + "\"}"
        em.gender = "{\"Gender\": \"" + request.form.get('gender') + "\"}"
        em.voted = "{\"Voted\": \"" + request.form.get('parti') + "\"}"
        em.put()

    return render_template('Tak for din deltagelse.html', sessionID = session_id)


@app.route('/data')
def downloadData():
    users = []
    with ds_client.context():
        data = EntryModel.query()
        for d in data:
            answersDict = json.loads(d.answers) #Answers
            
            #Macthes
            euclideanDict = json.loads(d.euclidean) #Euclidean
            manhattanDict = json.loads(d.manhattan) #Manhattan
            qdaDict = json.loads(d.qda) #QDA
            randomDict = json.loads(d.random) #Random

            #Model scores
            euclideanScoreDict = json.loads(d.euclideanScore)
            manhattanScoreDict = json.loads(d.manhattanScore)
            qdaScoreDict = json.loads(d.qdaScore)
            randomScoreDict = json.loads(d.randomScore)

            #Demo info
            ageDict = json.loads(d.age)
            genderDict = json.loads(d.gender)
            votedDict = json.loads(d.voted)

            #Add demo info 
            ageDict.update(genderDict)
            ageDict.update(votedDict)
            ageDict.update(answersDict)

            #Add to dict
            ageDict.update(euclideanDict)
            ageDict.update(manhattanDict)
            ageDict.update(qdaDict)
            ageDict.update(randomDict)
            
            #Add model scores
            ageDict.update(euclideanScoreDict)
            ageDict.update(manhattanScoreDict)
            ageDict.update(qdaScoreDict)
            ageDict.update(randomScoreDict)

            #Add to JSON list
            users.append(ageDict)
    
    #Make into JSON format
    json_data = json.dumps(users, ensure_ascii=False)

    output = StringIO()
    output.write(json_data)
    output.seek(0)

    response = make_response(output.getvalue())
    response.headers.set('Content-Disposition', 'attachment', filename='data.json')
    response.headers.set('Content-Type', 'application/json')

    return response