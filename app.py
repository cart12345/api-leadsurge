from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from instagrapi import Client
import time
import random

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Instagram client instance
cl = None

# Delay functions


def delay_5_seconds():
    time.sleep(5)


def random_delay():
    delay = random.uniform(5, 10)
    time.sleep(delay)

# Pydantic models for request data


class LoginData(BaseModel):
    username: str
    password: str


class ScrapeData(BaseModel):
    target: str
    amount: int


class DMData(BaseModel):
    usernames: list[str]
    mesg: str
    cmt: str

# Login endpoint


@app.post("/login")
def login(data: LoginData):
    global cl
    try:
        cl = Client()
        cl.login(data.username, data.password)
        return {"message": "Login successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Scrape followers endpoint


@app.post("/scrape_followers")
def scrape_followers(data: ScrapeData):
    if cl is None:
        raise HTTPException(status_code=400, detail="You need to login first")

    try:
        user_info = cl.user_info_by_username(data.target)
        if user_info is None:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user_info.pk
        followers = cl.user_followers(user_id=user_id, amount=data.amount)

        scraped_usernames = [cl.user_info(
            follower_id).username for follower_id in followers if cl.user_info(follower_id)]
        return {"usernames": scraped_usernames}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Scrape following endpoint


@app.post("/scrape_following")
def scrape_following(data: ScrapeData):
    if cl is None:
        raise HTTPException(status_code=400, detail="You need to login first")

    try:
        user_info = cl.user_info_by_username(data.target)
        if user_info is None:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user_info.pk
        following = cl.user_following(user_id=user_id, amount=data.amount)

        scraped_usernames = [cl.user_info(
            following_id).username for following_id in following if cl.user_info(following_id)]
        return {"usernames": scraped_usernames}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Send DMs endpoint


@app.post("/send_dms")
def send_dms(data: DMData):
    if cl is None:
        raise HTTPException(status_code=400, detail="You need to login first")

    try:
        max_dms = 10
        dms_sent = 0
        sent_dms = []

        for username in data.usernames:
            user_id = None
            try:
                user_id = cl.user_id_from_username(username)
            except Exception:
                continue

            if user_id:
                try:
                    user_info = cl.user_info(user_id)
                    user_posts = cl.user_medias(user_id)
                    if user_posts:
                        post_id = user_posts[0].id
                        cl.media_comment(post_id, data.cmt)
                        delay_5_seconds()
                        cl.media_like(post_id)
                        delay_5_seconds()
                        cl.user_follow(user_id)
                        random_delay()
                        cl.direct_send(text=data.mesg, user_ids=[user_id])
                        dms_sent += 1
                        if dms_sent >= max_dms:
                            break
                        sent_dms.append(
                            {"username": username, "message": data.mesg})
                    random_delay()
                except Exception:
                    continue

        return {"message": "DMs sent successfully", "sent_dms": sent_dms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
