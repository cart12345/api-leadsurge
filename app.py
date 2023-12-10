from flask import Flask, request, jsonify
from flask_cors import CORS
from instagrapi import Client
import time
import random

app = Flask(__name__)
CORS(app)

cl = None


def delay_5_seconds():
    time.sleep(5)


def random_delay():
    delay = random.uniform(5, 10)
    time.sleep(delay)


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        global cl
        cl = Client()
        cl.login(username, password)

        return jsonify({'message': 'Login successful'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/scrape_followers', methods=['POST'])
def scrape_followers():
    if cl is None:
        return jsonify({'error': 'You need to login first'}), 400

    try:
        data = request.get_json()
        target = data.get('target')
        amt = data.get('amount')

        user_info = cl.user_info_by_username(target)

        if user_info is None:
            return jsonify({'error': 'User not found'}), 404

        user_id = user_info.pk
        amt = int(amt)

        followers = cl.user_followers(user_id=user_id, amount=amt)

        scraped_usernames = []
        for follower_id in followers:
            follower_info = cl.user_info(follower_id)
            if follower_info:
                username = (follower_info.username)
                scraped_usernames.append(username)

        return jsonify({'usernames': scraped_usernames}), 200

    except Exception as e:
        print("Error in /scrape_followers:", str(e))
        return jsonify({'error': 'An error occurred'}), 500


@app.route('/scrape_following', methods=['POST'])
def scrape_following():
    if cl is None:
        return jsonify({'error': 'You need to login first'}), 400

    try:
        data = request.get_json()
        target = data.get('target')
        amt = data.get('amount')

        user_info = cl.user_info_by_username(target)

        if user_info is None:
            return jsonify({'error': 'User not found'}), 404

        user_id = user_info.pk
        amt = int(amt)

        following = cl.user_following(user_id=user_id, amount=amt)

        scraped_usernames = []
        for following_id in following:
            following_info = cl.user_info(following_id)
            if following_info:
                username = (following_info.username)
                scraped_usernames.append(username)

        return jsonify({'usernames': scraped_usernames}), 200

    except Exception as e:
        print("Error in /scrape_following:", str(e))
        return jsonify({'error': 'An error occurred'}), 500


@app.route('/send_dms', methods=['POST'])
def send_dms():
    if cl is None:
        return jsonify({'error': 'You need to login first'}), 400

    try:
        data = request.get_json()
        usernames = data.get("usernames", [])
        mesg = data.get("mesg", "")
        cmt = data.get("cmt", "")

        max_dms = 10
        dms_sent = 0
        sent_dms = []

        for username in usernames:
            user_id = None
            try:
                user_id = cl.user_id_from_username(username)
            except Exception as e:
                pass

            if user_id:
                try:
                    user_info = cl.user_info(user_id)
                    user_username = user_info.username

                    delay_5_seconds()

                    user_posts = cl.user_medias(user_id)
                    if user_posts:
                        post_id = user_posts[0].id
                        comment_text = cmt
                        cl.media_comment(post_id, comment_text)

                        delay_5_seconds()

                        cl.media_like(post_id)

                        delay_5_seconds()

                        cl.user_follow(user_id)

                        random_delay()

                        dm_text = mesg
                        cl.direct_send(text=dm_text, user_ids=[user_id])

                        dms_sent += 1

                        if dms_sent >= max_dms:
                            break

                        sent_dms.append(
                            {"username": username, "message": dm_text})
                    else:
                        pass

                    random_delay()
                except Exception as e:
                    pass
            else:
                pass

        return jsonify({"message": "DMs sent successfully", "sent_dms": sent_dms})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port='8080', debug=False, threaded=True)
