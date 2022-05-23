# -*- coding: utf-8 -*-
"""
Created on Sat Apr  2 00:48:06 2022

@author: anddy
"""
import requests, json
import numpy as np
from datetime import datetime
import sys
import calendar
import pandas as pd
from datetime import time as time_time
sys.path.append('C:\\NotionUpdate\\progress')
from secret import secret
from myPackage import organize_evaluation_data as oed
from Connect_NotionAPI import NotionUpdate_API as NAPI
from myPackage import NotionprocessMonth as pMon
from myPackage import NotionprocessReadData as NRD
import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)



class Connect_Notion:
    def __init__(self):
        pass    
    
    # Retrieve Database from Notion
    def read_Database(self, databaseId, headers):
        readUrl = f"https://api.notion.com/v1/databases/{databaseId}/query"
    
        res = requests.request("POST", readUrl, headers=headers)
        data = res.json()
        # print(res.text)
    
        with open('./db.json', 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        return data
    
    
    # Organize & Convert JSON format into dictionary
    def get_projects_titles(self,data_json):
        most_properties = [len(data_json['results'][i]['properties'])
                                for i in range(len(data_json["results"]))]
        
        project_keys = list(data_json["results"][np.argmax(most_properties)]["properties"].keys()) 
        
        # since we are using 2 different data sets for the same code
        if "Due Date" not in project_keys and "Meditation (%)" not in project_keys:
            return project_keys + ["Due Date","pageId"]
        else:
            return project_keys + ["pageId"]
    
    
    def get_projects_data(self, data, projects):
        proj_data = {}
        
        for p in projects:
            if p == "Due Date":
                # Each block's Due Dates
                due_temp = []
                for i in range(len(data["results"])):
                    try:
                        due_temp.append(data['results'][i]['properties']['Due Date']['date']['start'])
                    except:
                        due_temp.append(0)
                
                proj_data[p] = due_temp
                
            elif p == "Date":
                # Each block's Dates(Mon,Tue,...,Sun)
                date_temp = []
                for i in range(len(data["results"])):
                    block = data['results'][i]['properties']['Date']['multi_select']
                    temp_p = [block[date]["name"]
                              for date in range(len(block))]
                    date_temp.append(temp_p)
                proj_data[p] = date_temp
            
            elif p == "pageId":
                proj_data[p] = [data['results'][i]['id']
                                    for i in range(len(data["results"]))]
            
            elif p == "To do":
                proj_data[p] = [data['results'][i]['properties']['To do']['checkbox']
                                    for i in range(len(data["results"]))]
            
            elif p == "Name":
                names = []
                for i in range(len(data["results"])):
                    try:
                        names.append(data['results'][i]['properties']['Name']['title'][0]['text']['content'].split(': ')[1])
                    except:
                        names.append(data['results'][i]['properties']['Name']['title'][0]['text']['content'])
                proj_data["Name"] = names
                proj_data["Category"] = [data['results'][i]['properties']['Name']['title'][0]['text']['content'].split(': ')[0]
                                    for i in range(len(data["results"]))]
                proj_data["Category_current"] = [data['results'][i]['properties']['Status 1']['select']['name']
                                    for i in range(len(data["results"]))]
            else:
                pass
                

        return proj_data
    
    
    # Get Evaluation Data from a separate database 
    def get_evaluation_data(self, data, projects):
        projects.pop(-1)        
        eval_data = oed.get_evaluation_data(projects, data)
        return eval_data
    
    # Overwrite the existing excel file with an updated data
    def download_evaluationCSV(self, eval_data):
        date = eval_data['Date'][0].split('/')
        month = date[0]
        year = date[-1][-2:]
        file_name = month + year + '.csv'
        eval_data.to_csv("C:\\NotionUpdate\progress\Data\%s" % file_name, index=False)
        
        # Download to my D drive if plugged in 
        try:
            eval_data.to_csv("D:\Personal\progress\Data\%s" % file_name, index=False)
        except:
            pass
            
    def get_today(self, key):
        # Get today's date
        week_days = ['Mon','Tue','Wed','Thur','Fri','Sat','Sun']
        year = int(datetime.today().strftime('%Y'))
        month = int(datetime.today().strftime('%m'))
        day = int(datetime.today().strftime('%d'))
        week_day_num = calendar.weekday(year,month,day)
        today = week_days[week_day_num]
        
        now = datetime.today()
        dt_string = now.strftime("%Y-%m-%d")
        
        if key == "day":
            return today
        else:
            return dt_string
    
    # Update a block(task) to today's column
    def updateTask_to_today(self, pageId, headers):
        updateUrl_to_next = f"https://api.notion.com/v1/pages/{pageId}"
    
        updateData_to_next = {
            "properties": {
                "Status 1": {
                    "select": 
                        {
                                "name": "Today"
                        }
                }        
            }
        }
        
        
        response = requests.request("PATCH", updateUrl_to_next, 
                                    headers=headers, data=json.dumps(updateData_to_next))
    
    # Update a block(task) from today's column to corresponding columns
    def updateTask_to_others(self, pageId, headers, category):
        updateUrl_to_waitlist = f"https://api.notion.com/v1/pages/{pageId}"
    
        updateData_to_waitlist = {
            "properties": {
                "Status 1": {
                    "select": 
                        {
                                "name": category
                        }
                }        
            }
        }
        
        
        response = requests.request("PATCH", updateUrl_to_waitlist, 
                                    headers=headers, data=json.dumps(updateData_to_waitlist))
        
    # Update Schedule
    def update_Schedule(self, proj_data):
        today = CNotion.get_today("day")
        today_date = CNotion.get_today("date")
        
        print("Updating Today's Schedule...\n")
        for block in range(len(proj_data['Name'])):
            
            # If it's past 1:00 pm, don't reschedule it again
                # Since I may have made some modifications, which needs to be fixed
            #if CNotion.is_time_between(time_time(13,00),time_time(21,59)) == True:
            #    return proj_data['Category_current'].count("Today")
            
            
            # Check if today(Mon,Tue,...,Sun) matches the block's day
                # 2 CASES that requires adjustment
                    # CASE 1: the block is NOT in Today column when it should be (Days)
                    # CASE 2: the block is in Today column wht it should NOT be  (Days)
                    # CASE 3: the block is NOT in Today column when it should be (Date)
                    
            # Check CASE 1
            if today in proj_data["Date"][block]:
                if proj_data["Category_current"][block] != "Today":
                    CNotion.updateTask_to_today(proj_data["pageId"][block], headers)
                    print("[%s] Block Updated" % proj_data["Name"][block])

            # Check CASE 2
            # If the block is incorrectly in Today's column send it back to its category(column)
            else:
                # disposable blocks(Used for one day: popped up meeting or laundry etc.)
                if proj_data['Date'][block] == [] and proj_data['Due Date'][block] == 0:
                    pass
                
                elif proj_data["Category_current"][block] == "Today":
                    CNotion.updateTask_to_others(proj_data["pageId"][block], headers,
                                                 proj_data["Category"][block])
                    print("[%s] Block Updated" % proj_data["Name"][block])
            
            # Check CASE 3
            if today_date == proj_data["Due Date"][block]:
                if proj_data["Category_current"] != "Today":
                    CNotion.updateTask_to_today(proj_data["pageId"][block], headers)
                    print("[%s] Block Updated" % proj_data["Name"][block])
        
        print("\nUpdate Complete\n\n\n")
        
        # Return the total number of today's todo lists
        return proj_data['Category_current'].count("Today")
    
    def update_evaluationJPG(self):
        print("Uploading evaluation.jpg file...")
        data_eval = NAPI.nsync.query_databases()
        projects_eval = NAPI.nsync.get_projects_titles(data_eval)
        projects_data_eval = pd.DataFrame(NAPI.nsync.get_projects_data(data_eval,projects_eval))
        projects_data_eval = projects_data_eval.rename(columns={'*Finished': 'Finished', '*Multiple (1~5)': 'Multiple','*Phone pickups':'Phone pickups',
                                       '*Screen time':'Screen time','Drink (%)':'Drink %', 'Drink? (over 3 beer)':'Drink',
                                       'Meditation (%)':'Meditation %', 'Meditation (min)':'Meditation', 'Multiple (%)':'Multiple %',
                                       'Pick up (%)':'Pick up %', 'Reading (%)':'Reading %', 'Rise time (%)':'Rise time %',
                                       'Run (%)':'Run %', 'Run (km)':'Run', 'Screen Time (%)':'Screen Time %', 'Work done (%)': 'Work done %',
                                       'Overall Satisfaction':'Satisfaction','Personal Reading':'Reading','Tech Consumption':'Tech',
                                       'Total To-do List':'Tot To-do', 'Phone pickups':'Pickups'})

        # Monthly Evaluation Plot
        pMon.monthly_eval(projects_data_eval) # Replace it with projects_data_eval
        NAPI.uploadEvaluationJPG()
        print('Completed')
        print()
        
        # Save to D Drive (if plugged in) for further statistical analysis
        RDATA = NRD.read_data()
        all_dat = RDATA.all_data("include date")[0]
        RDATA.save_to_Ddrive(all_dat)


        
    
    def is_time_between(self, begin_time, end_time, check_time=None):
        # If check time is not given, default to current UTC time
        check_time = check_time or datetime.now().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else: # crosses midnight
            return check_time >= begin_time or check_time <= end_time
    
        
    
databaseId = secret.todo_db("DATABASE_ID")
token = secret.notion_API("token_key")
headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
    "Notion-Version": "2021-05-13"
}
    
# Schedule my tasks 
CNotion = Connect_Notion()
data = CNotion.read_Database(databaseId, headers)
projects = CNotion.get_projects_titles(data)
proj_data = CNotion.get_projects_data(data, projects)

# Update Schedule
CNotion.update_Schedule(proj_data)

# Read Evaluation Database in Notion using different database ID
databaseId = secret.evaluation_db("DATABASE_ID")
CNotion = Connect_Notion()
data = CNotion.read_Database(databaseId, headers)
projects = CNotion.get_projects_titles(data)
eval_data = CNotion.get_evaluation_data(data, projects)


# Download the evaluation data
CNotion.download_evaluationCSV(eval_data)

# Upload Evaluation Visualization 
CNotion.update_evaluationJPG()









        
        
        
        