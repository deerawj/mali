from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import pymongo
import wikipedia
from time import time
from random import randint
from hashlib import sha256

from fastapi import FastAPI, HTTPException, responses, Response
from os import listdir
from markdown import markdown
from random import shuffle
from fastapi.middleware.cors import CORSMiddleware
from json import load
from pydantic import BaseModel

client = pymongo.MongoClient('localhost', 2000)
db = client['test']

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

        images = listdir(f"imgs/")
        gallery = []
        for i in images:
            if i.endswith(".jpg") and i.startswith(self.slug):
                gallery.append(f"/imgs/{i}")
        # should work now

        self.gallery = gallery

        if self.type == "news":
            self.tags = [i.strip().title() for i in meta["tags"].split(",") if i]
            self.auth = meta["auth"]
        if self.type == "ancs":
            self._for = meta["for"]
            self._from = meta["from"]
        
    def __dict__(self):
        if self.type == "news":
            return {
                "id":   self.slug,
                "banner": f"/imgs/{self.slug}.jpg",
                "title": self.name,
                "date": self.date,
                "author": self.auth,
                "description": self.desc,
                "tags": self.tags,
                "gallery": {
                    "available": len(self.gallery) > 0,
                    "photos": [{"src": i} for i in self.gallery]
                },
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
    global TEXT, NEWS, ANCS, SPORTS, CLUBS
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
            "description": v # truncate for testing purposes
        })

    CLUBS = []
    data = load(open("clubs.json"))
    for k, v in data.items():
        CLUBS.append({
            "name": k.lower(),
            "description": v[:400] # truncate for testing purposes
        })


    
setup() # planning to replace this

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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

@app.get("/imgs/{code}.jpg")
def news(code: str):
    return responses.FileResponse(f"imgs/{code}.jpg")

    
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
    

@app.get("/home")
def featured():
    return {
        "principal": {
            "name": "Mr. P.V.S.K.Ajith Ponnewila",
            "image": "/principal.jpg",
            "message": TEXT["principal"],
        },
        "featured":{
            "news": [i.__dict__() for i in list(NEWS.values())],
            "announcements": [i.__dict__() for i in list(ANCS.values())],
            "events": [

            ]
        }
    }

@app.get("/principal.jpg")
def principal():
    return responses.FileResponse("imgs/principal.jpg")

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
    return {
        "sports":SPORTS,
        "descriptions": [
            {"description": TEXT["sports1"]},
            {"description": TEXT["sports2"]},
        ]
    }

@app.get("/clubs")
def clubs():
    return {
        "clubs":CLUBS,
        "descriptions": [
            {"description": TEXT["clubs1"]},
            {"description": TEXT["clubs2"]},
        ]
    }

@app.get("/oba")
def oba():
    return {
        "description": TEXT["oba"],
        "committee": [
            {"name": "Mr. Luxmen Wendaruwa", "position": "President"},
            {"name": "Mr. Tisara Perera", "position": "Secretary"},
            {"name": "Mr. R M S R Rathnayaka", "position": "Treasurer"},
        ],
        "contributions": [
            {"contribution":"Infastructure Development"},
            {"contribution":"Children's Welfare Initiatives"},
            {"contribution":"Educational Support"},
            {"contribution":"Fundarsing and Finanacial Support"},
            {"contribution":"Preserving Traditions and Heritage"},
            {"contribution":"Collaborative Partnership"},
        ],
        "contact": {
            "website": "www.maliyadeva.com",
            "email": "info@maliyadevaoba.lk",
            "phone": "+94-372220185",
        }
    }

@app.get("/sections")
def sections():
    return [
        {"name":"Primary", "description": TEXT["primary"], "grades": "1-5"},
        {"name":"Junior", "description": TEXT["junior"], "grades": "6-7"},
        {"name":"Junior Secondary", "description": TEXT["juniorSec"], "grades": "8-9"},
        {"name":"Middle", "description": TEXT["middle"], "grades": "10-11"},
        {"name":"Advanced Level", "description": TEXT["advanced"], "grades": "12-13"},
    ]

class Login(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(resp: Response, login: Login):
    if login.username == "root" and login.password == "root":
        resp.set_cookie(key="token", value="root")
        return {"status": "success"}
    
@app.get("/limited")
def limited(resp: Response, token: str = None):
    if token == "root":
        return {"status": "success"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
class Contact(BaseModel):
    name: str
    email: str
    phone: str
    message: str

@app.post("/contact")
def contact(contact: Contact):
    print(contact)
    return {"status": "success"}

class Subscribe(BaseModel):
    email: str

@app.post("/subscribe")
def subscribe(subscribe: Subscribe):
    print(subscribe)
    return {"status": "success"}

class Search(BaseModel):
    query: str

@app.post("/search")
def search(search: Search):
    results = []
    for k, v in NEWS.items():
        if search.query in v.text.lower():
            results.append(v.__dict__())
    for k, v in ANCS.items():
        if search.query in v.text.lower():
            results.append(v.__dict__())
    return results

@app.route("/", methods=["GET", "POST"])
async def main(request: Request):
    # check users cookies to see if they are logged in
    # if they are, then show them the main page
    # if they are not, then show them the login page
    if request.method == "POST":
        form = await request.form()
        username = form.get('username')
        password = sha256(form.get('password').encode()).hexdigest()
        user = db['user'].find_one({
            'username': username,
            'password': password,
        })
        if user is None:
            return templates.TemplateResponse("logn.html", {"request": request})
        else:
            token = sha256(str(randint(0, 10000000000)).encode()).hexdigest()
            db['sessions'].insert_one({
                'username': username,
                'token': token,
            })
            response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="token", value=token)
            return response

    if request.cookies.get('token') is None:
        return templates.TemplateResponse("logn.html", {"request": request})
    else:
        # check if the token is valid
        token = request.cookies.get('token')
        user = db['sessions'].find_one({
            'token': token,
        })
        if user is None:
            return templates.TemplateResponse("logn.html", {"request": request})


    username = db['sessions'].find_one({
        'token': request.cookies.get('token'),
    })
    userdata = db['user'].find_one({
        'username': username['username'],
    })

    perms = []
    for perm in ['/wikis', '/todos', '/texts', '/blogs', '/clubs', '/queue', '/perms', '/users']:
        for i in userdata['perms']:
            if i in perm:
                perms.append(perm)
                break


    users = list(db['user'].find())
    wikis = db['wiki'].find()
    todos = db['todo'].find()
    texts = db['text'].find()
    clubs = db['club'].find()
    blogs = db['blog'].find()
    queue = db['queue'].find()
    return templates.TemplateResponse("main.html", {
        "username": userdata['username'],
        "request": request, 
        "perms": perms,
        "users": users,
        "wikis": wikis,
        "todos": todos,
        "texts": texts,
        "blogs": blogs,
        "queue": queue,
        "clubs": clubs,
    })

@app.post("/user/add")
async def add_user(request: Request):
    form = await request.form()
    username = form.get('username')
    password = form.get('password')
    db['user'].insert_one({
        'username': username,
        'password': password,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/user/del")
async def del_user(request: Request):
    form = await request.form()
    username = form.get('username')
    db['user'].delete_one({
        'username': username,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/wiki/add")
async def add_wiki(request: Request):
    form = await request.form()
    title = form.get('title')
    content = wikipedia.page(title).content
    print(content)
    db['wiki'].insert_one({
        'title': title,
        'content': content,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/wiki/del")
async def del_wiki(request: Request):
    form = await request.form()
    title = form.get('title')
    db['wiki'].delete_one({
        'title': title,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/todo/add")
async def add_todo(request: Request):
    form = await request.form()
    title = form.get('title')
    db['todo'].insert_one({
        'title': title,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/todo/del")
async def del_todo(request: Request):
    form = await request.form()
    title = form.get('title')
    db['todo'].delete_one({
        'title': title,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/text/add")
async def add_text(request: Request):
    form = await request.form()
    title = form.get('title')
    content = form.get('content')
    db['text'].insert_one({
        'title': title,
        'content': content,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/text/del")
async def del_text(request: Request):
    form = await request.form()
    title = form.get('title')
    db['text'].delete_one({
        'title': title,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/text/edit")
async def edit_text(request: Request):
    form = await request.form()
    title = form.get('title')
    content = form.get('content')
    db['text'].update_one({
        'title': title,
    }, {
        '$set': {
            'content': content,
        }
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/blog/add")
async def add_blog(request: Request):
    form = await request.form()
    title = form.get('title')
    tags = form.get('tags')
    content = form.get('content')
    photo = form.get('photo')
    db['queue'].insert_one({
        'title': title,
        'tags': tags,
        'content': content,
        'photo': photo,
        'time': time(),
    })

    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/blog/edit")
async def edit_blog(request: Request):
    form = await request.form()
    title = form.get('title')
    tags = form.get('tags')
    content = form.get('content')
    photo = form.get('photo')
    
    db['queue'].insert_one({
        'title': title,
        'tags': tags,
        'content': content,
        'photo': photo,
        'time': time(),
    })

    '''
    db['queue'].update_one({
        'title': title,
    }, {
        '$set': {
            'tags': tags,
            'content': content,
            'photo': photo,
            'time': time(),
        }
    })
    '''
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/queue/accept")
async def accept_queue(request: Request):
    form = await request.form()
    title = form.get('title')
    tags = form.get('tags')
    content = form.get('content')
    photo = form.get('photo')
    db['blog'].insert_one({
        'title': title,
        'tags': tags,
        'photo': photo,
        'content': content,
    })
    db['queue'].delete_one({
        'title': title,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/queue/reject")
async def reject_queue(request: Request):
    form = await request.form()
    title = form.get('title')
    db['queue'].delete_one({
        'title': title,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.post("/club/add")
async def add_club(request: Request):
    form = await request.form()
    title = form.get('title')
    description = form.get('description')
    photo = form.get('photo')
    is_sport = form.get('sport') == 'sport'
    db['club'].insert_one({
        'title': title,
        'description': description,
        'photo': photo,
        'is_sport': is_sport,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/club/del")
async def del_club(request: Request):
    form = await request.form()
    title = form.get('title')
    db['club'].delete_one({
        'title': title,
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/club/edit")
async def edit_club(request: Request):
    form = await request.form()
    title = form.get('title')
    description = form.get('description')
    photo = form.get('photo')
    is_sport = form.get('sport') == 'sport'
    db['club'].update_one({
        'title': title,
    }, {
        '$set': {
            'description': description,
            'photo': photo,
            'is_sport': is_sport,
        }
    })
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/perm/add")
async def add_perm(request: Request):
    form = await request.form()
    username = form.get('username')
    perm = form.get('perm')
    if perm and not perm.startswith("/"):
        perm = "/" + perm

    db['user'].update_one({
        'username': username,
    }, {
        '$push': {
            'perms': perm,
        }
    })

    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/perm/del")
async def del_perm(request: Request):
    form = await request.form()
    username = form.get('username')
    perm = form.get('perm')
    if perm and not perm.startswith("/"):
        perm = "/" + perm
    
    db['user'].update_one({
        'username': username,
    }, {
        '$pull': {
            'perms': perm,
        }
    })

    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)