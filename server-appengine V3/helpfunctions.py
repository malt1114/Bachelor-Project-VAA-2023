import numpy as np
import pandas as pd
import random
import scipy.spatial as sps 
from pyparsing.helpers import List
import joblib

def getData():
    #Have to be in the loop - otherwise will not work
    listOfQ = []
    questions = pd.read_csv('data/Questions & Themes.csv')
    count = 1
    for index, row in questions.iterrows():
        que = row['Question']
        questionNum = row['Question Number']
        theme = row['Theme']
        idNum = "" #0X or XX
        if count < 10:
            idNum = str(0)+str(count)
        else:
            idNum = str(count)
        listOfQ.append((count, idNum, theme, que))
        count += 1
    data = pd.read_csv('data/Valgkredse.csv')
    data = data[data['Parti'] != ": Uden for partierne"] #remove uden for parti
    #data.replace({': Uden for partierne': "Uden for partierne"}, inplace=True)
    valgkredse = set([i for i in data["Valgkreds"]])
    valgkredse = sorted(valgkredse)
    partier = set([i for i in data["Parti"]])
    partier = sorted(partier)
    return listOfQ, valgkredse, partier

def makeUserDF(list):
    dic = {}
    dic["0"] = list
    df = pd.DataFrame.from_dict(dic, orient='index', columns = ["Q"+str(x+1) for x in range (25)])
    df.replace({"Lidt enig":1, "Enig":2, "Lidt uenig":-1, "Uenig":-2}, inplace= True)
    return df.values.flatten()


#For calculating the distances
def find_distances(user_input):
  """this is the only function that should be called directly, it takes the method string, user input list, and storkreds string
  and it returns the row in the candidate_data of the closest candidate for all methods except QDA which returns the predicted party"""

  #load candidate data and reduce to relevant subsection of data
  partyData = pd.read_csv("data/PartyConverted.csv")
  
  matches = []
  
  #Euclidean
  matches.append(euclidean_distance(partyData,user_input))

  #Manhattan
  matches.append(manhattan_distance(partyData,user_input))
  
  #QDA
  #qda_distance(user_input)
  matches.append(qda_distance(user_input))
  
  #Random
  matches.append(random_distance(partyData))
  random.shuffle(matches)
  return matches #[("Euclidean", "Option 1"), ("Manhattan", "Option 2"), ("QDA", "Option 3"), ("Random", "Option 4")]


def manhattan_distance(reducedpartyData,user_input):
  data = reducedpartyData.copy()
  data.loc[:,'Distance'] = data.apply(lambda row : sps.distance.cityblock(list(row.iloc[2:]), user_input), axis = 1)
  match = data.sort_values("Distance").iloc[0]
  return ('Manhattan', match['Party']) 

def euclidean_distance(reducedpartyData, user_input):
  data = reducedpartyData.copy()
  data.loc[:,'Distance'] = data.apply(lambda row : sps.distance.euclidean(list(row.iloc[2:]), user_input), axis = 1)
  match = data.sort_values("Distance").iloc[0]
  return ('Euclidean', match['Party'])

def random_distance(reducedpartyData):
  parties = list(reducedpartyData['Party'].unique())
  random_row_index = random.randint(0,len(parties)-1)
  return ('Random', parties[random_row_index])

def qda_distance(user_input):
  pipeline = joblib.load('model/QDA_Pipeline_All.pkl')
  num_user_input = user_input.reshape(1, -1)
  prediction =  pipeline.predict(num_user_input)[0]
  return ('QDA', prediction)