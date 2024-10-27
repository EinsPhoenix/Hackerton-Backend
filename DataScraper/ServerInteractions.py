from requests import post
from os import system
from multiprocessing import Process

def StartServer(path):
    system(f"Py {path} runserver")

def InitServer(path):
    serverProcess = Process(target=StartServer, args=(path,), daemon=True)
    serverProcess.start()
    return serverProcess

def Login(gateway, username):
    url = f"{gateway}api/CreateOrLoginUserWithMail"
    formData = {
        "username": username,
        "email": f"{username}@gmail.com",
        "password": "Password123"
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
        try:
            summary = response.json()["data"]["content_summary"]
            mainTag = response.json()["data"]["MainTag"]["MainTag"]
            subTags = []
        except:
            return "", "", ""
        try:
            subTags.append(response.json()["data"]["SubTags"][0]["SubTag1"])
            subTags.append(response.json()["data"]["SubTags"][1]["SubTag2"])
            subTags.append(response.json()["data"]["SubTags"][2]["SubTag3"])
        except:
            pass
        return summary, mainTag, subTags
    else:
        raise Exception(response.status_code, response.text)

def AddNewText(gateway, titel, content, summary, mainTag, subTags, token):
    url = f"{gateway}/api/AddNewText"
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