import telegram
from flask import Flask, request
from flask_pymongo import PyMongo
import logging
import os

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

    cursor = collection.aggregate([
        {
            "$search": {
                "index": "textSearch",
                "text": {
                    "query": update.message.text,
                    "path": ["Body", "Title"],
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "Id": 1,
                "Title": 1,
                "Body": 0,
                "score": {"$meta": "searchScore"}
            }
        },
        {
            "$limit": 4
        }
    ])
    results = list(cursor)
    if len(results) > 0:
        update.message.reply_text("Sorry :( No similar question was found.")
    else:
        update.message.reply_text("Look what I found! These are 4 most similar questions to yours: ")
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


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
