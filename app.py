import telegram
import requests
from flask import Flask, request
from flask_pymongo import PyMongo
import logging
import os
from spacy_tokenizer import SpacyTokenizer
from neighboor_finder import NeighborFinder

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Flask(__name__)

app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

bot = telegram.Bot(token=os.environ.get('TELEGRAM_TOKEN'))
mongo = PyMongo(app)
collection = mongo.db.questions


@app.route('/')
def hello_world():
    cursor = collection.aggregate([{
        "$search": {
            "index": "textSearch",
            "text": {
                "query": "connection issue between Mysql and apache",
                "path": ["Body", "Title"],
            }
        }
    },
        {
            "$limit": 5
        }
    ])
    for operation in cursor:
        print(operation['Title'])
        print("Link: https://stackoverflow.com/questions/" + operation["Id"] + "\n============")
    return 'Welcome!'


@app.route('/new_query', methods=['POST'])
def new_query():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    user = update.message.from_user

    if update.message.text == "/start":
        update.message.reply_text("Welcome " + user.first_name + "! I am here to help you find out answers for your "
                                                                 "questions from StackOverflow. Please, type in "
                                                                 "your question...")
        logger.info(user.full_name + " has started a conversation")
        return "Done"

    if os.environ.get('SEND_GIF') == '1':
        gif = get_gif("searching")
        if gif is not None:
            update.message.reply_animation(gif, caption="Just a moment... I am trying to find out smth for you...")
        else:
            update.message.reply_text("Just a moment... I am trying to find out smth for you...")

    user_query = process_user_query(update.message.text)

    # if some empty message or only stop words are sent
    if not user_query or user_query.isspace():
        update.message.reply_text("Hello there! Ask me you question to find an answer :)")

    results = search(user_query)

    if len(results) == 0:
        update.message.reply_text("Sorry :( No similar question was found.")
    else:
        update.message.reply_text(
            "Look what I found! These are " + str(len(results)) + " most similar questions to yours: ")
        for operation in results:
            update.message.reply_text("https://stackoverflow.com/questions/" + operation["Id"])
    return "Done"


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook(os.environ.get('WEBHOOK_URL'))
    if s:
        logger.info("Webhook set up success")
    else:
        logger.error("Webhook set up failure")

    return "Done"


def get_gif(key):
    token = os.environ.get('GIPHY_TOKEN')
    url = "https://api.giphy.com/v1/gifs/random?api_key=" + \
          token + \
          "&tag=" + \
          key + "&rating=g"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()
    return data['data']['image_original_url']


def process_user_query(query):
    processing_type = os.environ.get('PROCESSING_TYPE')

    if processing_type == "SPACY_TOKENIZER":
        sentence_tokenizer = SpacyTokenizer()
        user_query = sentence_tokenizer.tokenize(query)
        return user_query
    else:
        return query


def search(query):
    processing_type = os.environ.get('SEARCH_TYPE')

    if processing_type == "NEIGHBOR_FINDER":
        finder = NeighborFinder()
        indexes = finder.get_indexes_of_neighbors(query)
        results = list()
        print(indexes)
        for index in indexes[0]:
            results.append(collection.find_one({"order": int(index)}))
        return results
    else:
        cursor = collection.aggregate([
            {
                "$search": {
                    "index": "textSearch",
                    "text": {
                        "query": query,
                        "path": ["Body", "Title"],
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "Id": 1,
                    "Title": 1,
                    "Body": 1,
                    "score": {"$meta": "searchScore"}
                }
            },
            {
                "$limit": int(os.environ.get('SEARCH_LIMIT'))
            }
        ])
        return list(cursor)


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
