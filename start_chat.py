#!/home/smoose/projects/twitch-chatbot/venv/bin/python
import os
import asyncio
import json
from websockets.asyncio.client import connect
import logging
import requests
from dotenv import load_dotenv
import argparse

parser = argparse.ArgumentParser(description='This script does something.')
parser.add_argument('-d', '--debug', help='Debug Level: (ex: 10)',
                    required=False, default=logging.WARN)
args = parser.parse_args()

level = args.debug
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(message)s", level=int(level))

load_dotenv()  # Load environment variables from .env file

client_id = os.environ['client_id']
access_token = os.environ['access_token']


def authorize_device():
    params = {
        'client_id': client_id,
        'scope': 'user:bot user:read:chat user:write:chat',
        'response_type': 'token',
        'redirect_uri': 'http://localhost:3000/oauth',
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    authorization_grant = requests.get(
        'https://id.twitch.tv/oauth2/authorize', params=params, headers=headers)
    print('Paste this URL into your browser:', authorization_grant.url)
    print('Then, you\'ll grab the access_token in the url parameters.')
    print('Put that access_token into the .env file under access_token.')


def get_bot_user_id():
    url = 'https://api.twitch.tv/helix/users'
    params = {
        # 'login': 'SmooseJuice'
    }
    headers = {
        'Authorization': f"Bearer {access_token}",
        'Client-ID': client_id,
    }

    try:
        response = requests.get(url=url, headers=headers, params=params)
        print(response.text)
    except Exception as err:
        print(err)


def get_auth():
    headers = {
        'Authorization': f"OAuth {access_token}"
    }
    response = requests.get(
        'https://id.twitch.tv/oauth2/validate', headers=headers)

    return response.json()


async def websocket_event_handler():
    uri = "wss://eventsub.wss.twitch.tv/ws"
    async with connect(uri) as websocket:
        async for message in websocket:
            message = json.loads(message)
            metadata = message['metadata']
            payload = message['payload']
            logger.debug(f"message: {json.dumps(message)}")
            logger.debug(f"metadata: {json.dumps(metadata)}")
            logger.debug(
                f"message type: {json.dumps(metadata['message_type'])}")

            if metadata['message_type'] == 'session_welcome':
                # Subscribe to event
                body = {
                    'type': 'channel.chat.message',
                    'version': '1',
                    'condition': {
                        'broadcaster_user_id': '252026571',
                        'user_id': '252026571',
                    },
                    'transport': {
                        'method': 'websocket',
                        'session_id': payload['session']['id'],
                    },
                }
                headers = {
                    'Client-Id': client_id,
                    'Authorization': f"Bearer {access_token}",
                    'Content-Type': 'application/json',
                }

                try:
                    logger.debug(
                        f"Subscribing to {body['type']} event type(s)")
                    subscription = requests.post(
                        url="https://api.twitch.tv/helix/eventsub/subscriptions", json=body, headers=headers)

                except requests.exceptions.HTTPError as err:
                    logger.error(err)
            elif metadata['message_type'] == 'notification':
                logger.debug(payload)
                print(
                    f"{payload['event']['chatter_user_name']}: {payload['event']['message']['text']}")

                if "the sims" in payload['event']['message']['text'].lower():
                    print('You owe jennapii $50k. I don\'t make the rules. :shrug:')


if __name__ == "__main__":
    auth = get_auth()

    if auth['scopes'] is not None:
        asyncio.run(websocket_event_handler())
    else:
        print("Something is up, scopes is empty. Try a new access_token")
        get_bot_user_id()
        authorize_device()
