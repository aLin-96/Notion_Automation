# -*- coding: utf-8 -*-
import requests, json
import numpy as np

def update_notion(content, pageId: str, headers):
    """_summary_

    Args:
        name (str): name of the column
        content (json): specified details in json format
            - Reference: https://developers.notion.com/reference/property-value-object
            - ex)
                - For date -> {"date": {"start": "2022-09-02"}}
                - For number -> {"number": 100}
        pageId (str): record pageId 
        headers (dictionary): headers with the token_key
    """
    update_url = f"https://api.notion.com/v1/pages/{pageId}"

    update_properties = {
        "properties": content
        }

    response = requests.request("PATCH", update_url,
                                headers=headers, data=json.dumps(update_properties))


    
def create_TodayTask(task_name:str, task_duration, task_databaseId:str, 
                    start_time:str, meeting_link:str, headers:dict):
    path = "https://api.notion.com/v1/pages"

    # Case 1: Includes the link
    newPageData_with_link = {
        "parent": {"database_id": task_databaseId},
        "properties": {
            "Name": {
                "title":[
                    {
                        "type": "text",
                        "text":{
                            "content": task_name
                        }
                    }
                ]
            },
            "Duration_EST": {"select": {"name": task_duration}},
            "Status": {"select": {"name": "Today"}},
            "web 1": {"url": meeting_link},
            "Time": {"rich_text": [{"type": "text", "text": {"content": start_time}}]}
        }
    }


        # Case 1: Includes the link
    newPageData_without_link = {
        "parent": {"database_id": task_databaseId},
        "properties": {
            "Name": {
                "title":[
                    {
                        "type": "text",
                        "text":{
                            "content": task_name
                        }
                    }
                ]
            },
            "Duration_EST": {"select": {"name": task_duration}},
            "Status": {"select": {"name": "Today"}},
            "Time": {"rich_text": [{"type": "text", "text": {"content": "Time: "}, "annotations":{"bold":True}},
                                   {"type": "text", "text": {"content": start_time}}]}
            }
    }

    if str(meeting_link) == str(np.nan):
        newPageData = newPageData_without_link
    else:
        newPageData = newPageData_with_link

    response = requests.post(path, json=newPageData, headers=headers)
    print(response)
    print()