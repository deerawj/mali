import pymongo
import faker
from random import choice
from tqdm import tqdm
from hashlib import sha256
from sys import argv
 
if len(argv) != 2:
    print("Wrong arguments")

no_users = int(argv[1])


client = pymongo.MongoClient('localhost', 2000)

# clean the entire database
def clean_db():
    client.drop_database('test')

# add user sudo with password password
def add_admins():
    db = client['test']
    collection = db['user']
    collection.insert_one({
        "username": "sudo",
        "password": sha256("password123".encode()).hexdigest(),
        "perms": ["/"]
    })
    collection.insert_one({
        "username": "someone",
        "password": sha256("password".encode()).hexdigest(),
        "perms": ["/"]
    })

# add fake user data
def add_fake_user():
    db = client['test']
    collection = db['user']
    fake = faker.Faker()
    for i in tqdm(range(no_users)):
        user = {
            "username": fake.name(),
            "password": fake.password(),
            "perms": [choice(['/wikis', '/todos', '/texts', '/blogs', '/clubs', '/queue', '/perms', '/users']) for i in range(3)]
        }
        collection.insert_one(user)

clean_db()
# add_fake_user()
add_admins()