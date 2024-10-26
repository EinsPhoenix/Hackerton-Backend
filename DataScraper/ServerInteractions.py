from requests import post
from time import sleep
from os import system
from multiprocessing import Process

def StartServer(path):
    system(f"Py {path} runserver")

def InitServer(path):
    serverProcess = Process(target=StartServer, args=(path,), daemon=True)
    serverProcess.start()
    return serverProcess

def Login(gateway):
    url = f"{gateway}api/CreateOrLoginUserWithMail"
    formData = {
        "username": "Jan",
        "email": "jan.thomas0506@gmail.com",
        "password": "Kacke11!"
    }
    headers = {}
    response = post(url, data=formData, headers=headers)
    return response.json()["token"]

def GetSummaryAndTags(gateway, titel, content, token):
    url = f"{gateway}api/Ai/SummarizeAndTag/de"
    jsonData = {
        "titel": titel,
        "content": content
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = post(url, json=jsonData, headers=headers)
    if response.status_code == 200:
        summary = response.json()["content_summary"]
        mainTag = response.json()["MainTag"]["MainTag"]
        subTags = []
        subTags.append(response.json()["SubTags"][0]["SubTag1"])
        subTags.append(response.json()["SubTags"][1]["SubTag2"])
        subTags.append(response.json()["SubTags"][2]["SubTag3"])
        return summary, mainTag, subTags
    else:
        raise Exception(response.status_code, response.text)

def AddNewText(titel, content, summary, mainTag, subTags, token):
    url = "http://127.0.0.1:8000/api/AddNewText"
    formData = {
        "titel": titel,
        "content": content,
        "content_summary": summary,
        "main_tag": mainTag,
        "subtags": subTags
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = post(url, data=formData, headers=headers)
    return response