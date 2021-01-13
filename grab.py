import praw, threading, requests, os, json, shutil
from urllib.request import urlopen

r = praw.Reddit(user_agent = "ImageCore", client_id="T7Q06OKRC1STPA", client_secret="VlPXp5hjPOzo5M94HZEnc8TzuSuKLQ")
already_done = []
while True:
    subreddit = r.subreddit('weirdcore')
    for submission in subreddit.hot(limit=1000):
        if submission.id not in already_done:
            if not submission.stickied:
                try:
                    url = submission.url
                    if (isinstance(url, str)):
                        contents = urlopen(url).read()
                        try:
                            os.mkdir("realms/" + submission.id)
                        except FileExistsError:
                            pass
                        with open("realms/" + submission.id + "/image." + url.split(".")[-1], "wb") as f:
                            f.write(contents)
                        r = requests.post(
                            "https://api.deepai.org/api/densecap",
                            data={
                                'image': url,
                            },
                            headers={'api-key': '697944e3-1624-430c-bade-25d985f02b62'}
                        )
                        with open("realms/" + submission.id + "/densecap.json", "wb") as f:
                            f.write(json.dumps(r.json()).encode(encoding="UTF-8"))
                        with open("realms/" + submission.id + "/credits.json", "wb") as f:
                            dic = {
                                "username": submission.author.name,
                                "id": submission.author.id
                            }
                            f.write(json.dumps(dic).encode(encoding="UTF-8"))
                        already_done.append(submission.id)
                except:
                    shutil.rmtree("realms/" + submission.id, ignore_errors=True)
                    pass
