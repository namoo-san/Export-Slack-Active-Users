# -*- coding: utf-8 -*-

import os
import re
import requests
import json
import pandas as pd

# Incomming webhooks for error message post
WEBHOOK_URL = "WEBHOOK_URL"
# OAuth bot token here
AUTH_TOKEN = "BOT_TOKEN"
# Slack files upload URL
UPLOAD_URL = "https://slack.com/api/files.upload"
# Post channel for result, attachment csv
POST_CHANNEL = "CHANNEL_NAME"

# Slack API token
BOT_TOKEN = "BOT_TOKEN"
# Slack API URL
URL = "https://slack.com/api/users.list"

# Filter text
FILTER_TEXT = "FILTER_TEXT"


def create_user_lists():
    # Create empty list
    users_result = []
    # Request API
    users = api_request(None)

    # Create user lists
    for user in users["members"]:
        deactivated = user["deleted"]
        profile_contents = user["profile"]

        # Filter active users
        if deactivated == False:
            if "email" in profile_contents:
                email = profile_contents["email"]
                if re.search(FILTER_TEXT, email):
                    users_result.append(email)

    if users["response_metadata"]:
        metadata = users["response_metadata"]
        cursor = metadata["next_cursor"]
        users = api_request(cursor)

        # Create user lists
        for user in users["members"]:
            deactivated = user["deleted"]
            profile_contents = user["profile"]

            if deactivated == False:
                if "email" in profile_contents:
                    email = profile_contents["email"]
                    if re.search(FILTER_TEXT, email):
                        users_result.append(email)

    return users_result


def api_request(cursor):
    # API request headers
    content_type = "application/x-www-form-urlencoded"
    payload = {'token': BOT_TOKEN}
    headers = {'content-type': content_type}
    response = requests.post(URL, payload, headers=headers)
    result = json.loads(response.text)

    # If "cursor" found, add cursor to request & get request
    if cursor:
        cursor_payload = {'token': BOT_TOKEN, 'cursor': cursor}
        response = requests.post(URL, cursor_payload, headers=headers)
        result = json.loads(response.text)
        return result

    # Return cursor
    return result


def slackPost(attachment):
    if attachment:
        # Post contents
        text = ":slack: {} を含むSlackのアクティブユーザーです:eyes:".format(FILTER_TEXT)
        # Attachment file path
        attachment_file = attachment
        # Attachment file title
        attachment_title = 'Slack active users'

        files = {'file': open(attachment_file, 'rb')}
        payload = {
            "token": AUTH_TOKEN,
            "channels": POST_CHANNEL,
            "filename": attachment_title,
            "filetype": "csv",
            "title": attachment_title,
            "initial_comment": text
        }

        requests.post(UPLOAD_URL, data=payload, files=files)

    else:
        text = "Slackからユーザー情報取れんかった・・・ :cry:"
        payload = {
            "text": text
        }

        data = json.dumps(payload)
        requests.post(WEBHOOK_URL, data)


def exportCSV(data):
    dataframe = pd.DataFrame(data, columns=["email"])
    # Export Lambda container /tmp/
    export_filename = "/tmp/SlackActiveUsers.csv"

    dataframe.to_csv(export_filename, index=False)
    return export_filename


def lambda_handler(event, context):
    user_info = create_user_lists()
    if user_info:
        # CSV export
        filepath = exportCSV(user_info)
        # Post to slack with attachment
        slackPost(filepath)
        # Remove file
        os.remove(filepath)
    else:
        print("No users info")
        slackPost(None)


def main():
    user_info = create_user_lists()
    print(user_info)

    print(exportCSV(user_info))


def error_handler(event):
    print(event)


if __name__ == "__main__":
    lambda_handler(None, None)
