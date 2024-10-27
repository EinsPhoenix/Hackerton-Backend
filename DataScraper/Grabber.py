from requests import get
from bs4 import BeautifulSoup
from re import sub, findall

def GetLinksFromCategory(category):
    nextUrl = f"https://de.wikipedia.org/wiki/Kategorie:{category}"
    links = []
    skipFirst = False
    while True:
        response = get(nextUrl).text
        soup = BeautifulSoup(response, "html.parser")
        div= soup.find_all("div", {"id": "mw-pages"})
        hrefs = findall(r"\"/wiki/[^\"]*\"", str(div))
        if hrefs:
            for href in hrefs:
                if skipFirst is False:
                    links.append(href[1:-1])
                else:
                    skipFirst = False
        if len(links) % 199 != 1 or len(links) == 1:
            return links
        lastSubject = findall(r"[^/]*$", links[-1])[0]
        nextUrl = f"https://de.wikipedia.org/w/index.php?title=Kategorie:{category}&pagefrom={lastSubject}#mw-pages"
        skipFirst = True

def GetPageContent(url):
    response = get(url).text
    soup = BeautifulSoup(response, "html.parser")
    content = ""
    buffer = ""
    usefullTags = soup.find_all(["h1", "h2", "p"])
    if url.startswith("https://de."):
        breakList = ["Weblinks", "Einzelnachweise", "Literatur", "Siehe auch"]
        ignoreList = ["Inhaltsverzeichnis"]
    elif url.startswith("https://en."):
        breakList = ["External links", "References", "Literature", "See also"]
        ignoreList = ["\n"]
    else:
        raise Exception("Language not supported!")
    for tag in usefullTags:
        if tag.text in breakList:
            break
        elif tag.text not in ignoreList:
            if str(tag)[1] == "p":
                buffer += f"{sub(r"\[\d*\]", "", tag.text)}\n"
            else:
                totalWordCount = len(content.split(" ")) + len(buffer.split(" "))
                if totalWordCount < 500:
                    content += buffer
                    buffer = f"{tag.text}\n"
                else:
                    break
    if totalWordCount < 600:
        content += buffer
    return usefullTags[0].text, content[:-2]