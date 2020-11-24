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
    logger.info(user.full_name + " has a message")
    update.message.reply_text(user.first_name + "vızqırt.")
    return True


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook(os.environ.get('WEBHOOK_URL'))
    if s:
        logger.info("Webhook set up success")
    else:
        logger.error("Webhook set up failure")


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
