import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import warnings

# Disable pandas warnings
warnings.filterwarnings('ignore')

def generateTrip(start_date, end_date, endingpos):
  activities = []
  current_date = start_date
  num_activities = 10
  for i in range(num_activities):
    duration = timedelta(hours=random.randint(1, 6))
    startTime = current_date + timedelta(hours=random.randint(1, 8))
    endTime = startTime + duration
    current_date = endTime
    activity = {
        "ID": i + 1,
        "Type": "event",
        "StartTime": startTime,
        "EndTime": endTime,
        "Duration": duration,
        "Lat": random.uniform(0, 100),
        "Long": random.uniform(0, 100),
        "Scheduled" : random.random() < 0.3
    }
    activities.append(activity)

  df=pd.DataFrame(activities)

  df.loc[~df['Scheduled'], ['StartTime', 'EndTime']] = datetime(1999, 7, 1, 8, 0, 0)
  df = df.sort_values(by='Scheduled', ascending=False)

  return df

def getFreeTimes(df, pos, start_date, end_date):

  df_Scheduled=df[df["Scheduled"]==True]

  df_Scheduled = df_Scheduled.sort_values(by='StartTime')

  unoccupied_intervals = []
  previous_end   = start_date

  for _, row in df_Scheduled.iterrows():
      start = row['StartTime']
      end = row['EndTime']
      if start > previous_end:
        unoccupied_intervals.append((previous_end , start, row["Lat"], row["Long"]))
      previous_end = max(previous_end, end)
  unoccupied_intervals.append((previous_end , end_date, pos[0], pos[1]))
  freeTimes = pd.DataFrame(unoccupied_intervals, columns=["StartTime", "EndTime", "EndLat", "EndLong"])
  freeTimes["Duration"]=freeTimes["EndTime"]-freeTimes["StartTime"]
  freeTimes["StartLat"]=freeTimes["EndLat"].shift(1)
  freeTimes.loc[0, 'StartLat'] = freeTimes.iloc[-1]['EndLat']
  freeTimes["StartLong"]=freeTimes["EndLong"].shift(1)
  freeTimes.loc[0, 'StartLong'] = freeTimes.iloc[-1]['EndLong']
  freeTimes = freeTimes[["StartTime", "EndTime", "StartLat", "StartLong", "EndLat", "EndLong", "Duration"]]

  return freeTimes




def schedule(trip, endingpos, start_date, end_date):
  ftc = getFreeTimes(trip, endingpos, start_date, end_date)
  unscheduled = trip[trip["Scheduled"]==False]

  best = pd.DataFrame()

  #iterate through all of the free time chucks
  for index, tc in ftc.iterrows():
    #print("new loop")
    possible = unscheduled[unscheduled["Duration"]<tc["Duration"]]
    if len(possible)==0:
      continue
    startdist = (tc["StartLat"]-possible["Lat"])**2+(tc["StartLong"]-possible["Long"])**2
    enddist = (tc["EndLat"]-possible["Lat"])**2+(tc["EndLong"]-possible["Long"])**2
    #print("dist calculated")
    possible["StartDist"]=startdist
    possible["EndDist"]=enddist
    possible["ExcessTime"]=tc["Duration"]-possible["Duration"]
    #print("dur calculated")
    possible['ExcessTime'] = possible['ExcessTime'].dt.total_seconds() / 3600
    #print("excess time calculated")
    possible['MinDist'] = round(possible[['StartDist', 'EndDist']].min(axis=1), 10)
    possible['MinDistNorm']=normalize_column(possible['MinDist'])
    #print("mindist and norm calculated")
    possible['ExcessTimeNorm']=normalize_column(possible['ExcessTime'])
    #print("time norm calculated")
    possible['FTCIndex']=index
    #print("display")
    #display(possible)
    #print("display2")
    best = best.append(possible.loc[possible['MinDistNorm'].idxmin()])
    #print("iter done")
  #print("pos")
  #display(possible)
  possible.loc[possible['MinDistNorm'].idxmin()]
  result = best.nsmallest(1, 'MinDist', keep = "all")
  result = result.nsmallest(1, 'ExcessTime', keep = "last")
  result["InsertLoc"]=result["StartDist"] < result["EndDist"]
  insertEvent = result.to_dict(orient='records')[0]
  if insertEvent["InsertLoc"]:

    trip.loc[trip['ID'] == insertEvent["ID"], 'Scheduled'] = True  # Replace 'Scheduled' with the target column name
    trip.loc[trip['ID'] == insertEvent["ID"], 'StartTime'] = ftc.iloc[insertEvent["FTCIndex"]]["StartTime"]  # Replace 'Scheduled' with the target column name
    trip.loc[trip['ID'] == insertEvent["ID"], 'EndTime'] = ftc.iloc[insertEvent["FTCIndex"]]["StartTime"]+insertEvent["Duration"]  # Replace 'Scheduled' with the target column name

  else:
    trip.loc[trip['ID'] == insertEvent["ID"], 'Scheduled'] = True  # Replace 'Scheduled' with the target column name
    trip.loc[trip['ID'] == insertEvent["ID"], 'EndTime'] = ftc.iloc[insertEvent["FTCIndex"]]["EndTime"]  # Replace 'Scheduled' with the target column name
    trip.loc[trip['ID'] == insertEvent["ID"], 'StartTime'] = ftc.iloc[insertEvent["FTCIndex"]]["EndTime"]-insertEvent["Duration"]  # Replace 'Scheduled' with the target column name
        
  return trip

def normalize_column(column):
    if len(column) <= 1:
        return column.copy().fillna(0)
    normalized_column = (column - column.min()) / (column.max() - column.min())
    return normalized_column

start_date  = datetime(2023, 7, 1, 8, 0, 0)
end_date = datetime(2023, 7, 7, 20, 0, 0)
endingpos = [random.uniform(0, 100), random.uniform(0, 100)]

trip = generateTrip(start_date, end_date, endingpos)  
print("Original Trip")
display(trip)

trip=schedule(trip, endingpos, start_date, end_date)


while not trip['Scheduled'].all():
  trip=schedule(trip, endingpos, start_date, end_date)
print("Planned Trip")
display(trip)
