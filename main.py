from fastapi import FastAPI, HTTPException, responses
from os import listdir
from markdown import markdown
from random import shuffle
from fastapi.middleware.cors import CORSMiddleware

class ARTICLE:
    def __init__(self, slug: str, text: str):
        self.slug = slug
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
            "id":   self.slug,
            "banner": f"/news/{self.slug}.jpg",
            "title": self.name,
            "date": self.date,
            "author": self.auth,
            "description": self.desc,
            "tags": self.tags,
            #"text": self.text,
            "content": self.html,

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
            slug = file.split(".")[0]
            NEWS[slug] = ARTICLE(slug, f.read())

    
setup()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/")
def index():
    return {"text": "Hello World"}

@app.get("/api/setup")
def setup_route():
    setup()
    return {"text": "Setup Complete"}

@app.get("/api/text/{slug}")
def text(slug: str):
    if slug in TEXT:
        return {"text": TEXT[slug]}
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/api/news/random")
def news():
    item = list(NEWS.items())
    data = {}
    for k, v in item:
        data[k] = v.__dict__()
        if len(data) >= 3:
            break
    for k in data:
        del data[k]["content"]
    return data

@app.get("/api/news/tags/{tags}")
def news(tags: str):
    tags = [i.strip().title() for i in tags.split(",")]
    data = {}
    for k, v in NEWS.items():
        if any(i in tags for i in v.tags):
            data[k] = v.__dict__()
    return data

@app.get("/api/news/{code}.jpg")
def news(code: str):
    if code in NEWS:
        return responses.FileResponse(f"imgs/{code}.jpg")
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/api/news/{slug}")
def news(slug: str):
    if slug in NEWS:
        return NEWS[slug].__dict__()
    else:
        raise HTTPException(status_code=404, detail="Item not found")