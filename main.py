from fastapi import FastAPI
from os import listdir
from markdown import markdown
from random import shuffle

class ARTICLE:
    def __init__(self, text: str):
        text = text.split("\n")
        meta = {}
        if text.pop(0) != "---":
            raise Exception("Invalid article: Missing MetaData")
        else:
            while True:
                line = text.pop(0)
                if line == "---":
                    break
                else:
                    key, value = line.split(":")
                    meta[key.strip()] = value.strip()
        self.text = "\n".join(text)
        self.html = markdown(self.text)

        self.tags = [i.strip().title() for i in meta["tags"].split(",")]
        self.name = meta["name"]
        self.date = meta["date"]
        self.auth = meta["auth"]
        self.desc = meta["desc"]
        
    def __dict__(self):
        return {
            "name": self.name,
            "date": self.date,
            "auth": self.auth,
            "desc": self.desc,
            "tags": self.tags,
            #"text": self.text,
            "html": self.html

        }


def setup():
    global TEXT, NEWS
    TEXT = {}
    for file in listdir("text"):
        with open(f"text/{file}") as f:
            TEXT[file.split(".")[0]] = markdown(f.read())

    NEWS = {}
    for file in listdir("news"):
        with open(f"news/{file}") as f:
            NEWS[file.split(".")[0]] = ARTICLE(f.read())

    
setup()
app = FastAPI()

@app.get("/")
def index():
    return {"text": "Hello World"}

@app.get("/setup")
def _setup():
    setup()
    return {"text": "Setup Complete"}

@app.get("/text/{slug}")
def text(slug: str):
    if slug in TEXT:
        return {"text": TEXT[slug]}
    else:
        return {"text": "Not found"}

@app.get("/news/random")
def news():
    item = list(NEWS.items())
    data = {}
    for k, v in item:
        data[k] = v.__dict__()
        if len(data) >= 3:
            break
    return data

@app.get("/news/tags/{tags}")
def news(tags: str):
    tags = [i.strip().title() for i in tags.split(",")]
    data = {}
    for k, v in NEWS.items():
        if any(i in tags for i in v.tags):
            data[k] = v.__dict__()
    return data
    

@app.get("/news/{slug}")
def news(slug: str):
    print(NEWS)
    if slug in NEWS:
        return NEWS[slug].__dict__()
    else:
        return {"news": "Not found"}