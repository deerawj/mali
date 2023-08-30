from fastapi import FastAPI, HTTPException, responses
from os import listdir
from markdown import markdown
from random import shuffle
from fastapi.middleware.cors import CORSMiddleware
from json import load

class ARTICLE:
    def __init__(self, slug: str, text: str, type: str):
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
        self.type = type

        
        self.name = meta["name"]
        self.date = meta["date"]
        self.desc = meta["desc"]

        if self.type == "news":
            self.tags = [i.strip().title() for i in meta["tags"].split(",")]
            self.auth = meta["auth"]
        if self.type == "ancs":
            self._for = meta["for"]
            self._from = meta["from"]
        
    def __dict__(self):
        if self.type == "news":
            return {
                "id":   self.slug,
                "banner": f"/{self.type}/{self.slug}.jpg",
                "title": self.name,
                "date": self.date,
                "author": self.auth,
                "description": self.desc,
                "tags": self.tags,
                #"text": self.text,
                "content": self.html
            }
        else:
            return {
                "id":   self.slug,
                "date": self.date,
                "title": self.name,
                "for": self._for,
                "from": self._from,
                "description": self.desc,
                "content": self.html
           }


def setup():
    global TEXT, NEWS, ANCS, SPORTS
    TEXT = {}
    for file in listdir("text"):
        with open(f"text/{file}") as f:
            TEXT[file.split(".")[0]] = f.read()
            #TEXT[file.split(".")[0]] = markdown(f.read())

    NEWS = {}
    for file in listdir("news"):
        if file.endswith(".md"):
            with open(f"news/{file}") as f:
                slug = file.split(".")[0]
                NEWS[slug] = ARTICLE(slug, f.read(), "news")

    ANCS = {}
    for file in listdir("ancs"):
        if file.endswith(".md"):
            with open(f"ancs/{file}") as f:
                slug = file.split(".")[0]
                ANCS[slug] = ARTICLE(slug, f.read(), "ancs")


    SPORTS = []
    data = load(open("sports.json"))
    for k, v in data.items():
        SPORTS.append({
            "name": k.lower(),
            "description": v[:400]+"..." # truncate for testing purposes
        })


    
setup()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return {"text": "Hello World"}

@app.get("/setup")
def setup_route():
    setup()
    return {"text": "Setup Complete"}

@app.get("/text/{slug}")
def text(slug: str):
    if slug in TEXT:
        return {"text": TEXT[slug]}
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/news/random")
def news():
    item = list(NEWS.items())
    data = {}
    for k, v in item:
        data[k] = v.__dict__()
        if len(data) >= 3:
            break
    for k in data:
        del data[k]["content"]
    return list(data.values())

@app.get("/news/all")
def news():
    data = {}
    for k, v in NEWS.items():
        data[k] = v.__dict__()
    for k in data:
        del data[k]["content"]
    return list(data.values())

@app.get("/news/tags/{tags}")
def news(tags: str):
    tags = [i.strip().title() for i in tags.split(",")]
    data = {}
    for k, v in NEWS.items():
        if any(i in tags for i in v.tags):
            data[k] = v.__dict__()
    return data

@app.get("/news/{code}.jpg")
def news(code: str):
    if code in NEWS:
        return responses.FileResponse(f"news/{code}.jpg")
    else:
        raise HTTPException(status_code=404, detail="Item not found")
    
@app.get("/news/{slug}")
def ancs(slug: str):
    if slug in NEWS:
        return NEWS[slug].__dict__()
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/ancs/random")
def ancs():
    item = list(ANCS.items())
    data = {}
    for k, v in item:
        data[k] = v.__dict__()
        if len(data) >= 3:
            break
    for k in data:
        del data[k]["content"]
    return list(data.values())

@app.get("/ancs/all")
def ancs():
    data = {}
    for k, v in ANCS.items():
        data[k] = v.__dict__()
    for k in data:
        del data[k]["content"]
    return list(data.values())

@app.get("/ancs/tags/{tags}")
def ancs(tags: str):
    tags = [i.strip().title() for i in tags.split(",")]
    data = {}
    for k, v in ANCS.items():
        if any(i in tags for i in v.tags):
            data[k] = v.__dict__()
    return data

@app.get("/ancs/{code}.jpg")
def ancs(code: str):
    if code in ANCS:
        return responses.FileResponse(f"ancs/{code}.jpg")
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/ancs/{slug}")
def ancs(slug: str):
    if slug in ANCS:
        return ANCS[slug].__dict__()
    else:
        raise HTTPException(status_code=404, detail="Item not found")
    

@app.get("/featured")
def featured():
    return {
        "news": [i.__dict__() for i in list(NEWS.values())],
        "ancs": [i.__dict__() for i in list(ANCS.values())],
        "events": []
    }

@app.get("/academics")
def academics():
    # have to fix it tomorrow
    return {
        "counts":[
            {"name":"teachers", "count": 200},
            {"name":"students", "count": 5000},
            {"name":"classes", "count": 130},
            {"name":"non-acedemic", "count": 64},
        ],
        "facilities":[
            {"item":"Modern Computer Labs"},
            {"item":"Fully Equiped Labotaries"},
            {"item":"Smart Class Rooms"},
            {"item":"Library"},
            {"item":"Auditorium"},
            {"item":"Play Ground"},
        ],
        "text_forces": TEXT["forces"],
        "text_facilities": TEXT["facilities"],
        "text_subjects": TEXT["subjects"],
    }



@app.get("/sports")
def sports():
    return SPORTS