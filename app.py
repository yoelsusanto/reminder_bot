# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
import re
import json
import requests
import datetime
import os
import sys
import psycopg2
import db
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, AudioMessage, ImageMessage, FollowEvent, UnfollowEvent
)

app = Flask(__name__)
# Competitive programming schedule return
def gmt7now():
    utc = datetime.datetime.utcnow()
    return (utc + datetime.timedelta(hours=7))

# get channel_secret and channel_access_token from your environment variable
my_id = os.getenv('MY_LINE_ID', None)
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
db_url = os.getenv('DATABASE_URL', None)

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/pushmessage")
def pushmessage():
    conn = psycopg2.connect(db_url, sslmode='require')
    cur = conn.cursor()
    cur.execute('select * from listSchedules ;')
    
    results = cur.fetchall()
    for result in results:
        pesan = result[2]
        uId = result[1]
        date = result[3]
        time = result[4]
        deadline = datetime.datetime.combine(date,time)
        if deadline > gmt7now():
            remainTime = deadline - gmt7now()
            remainTimeText = ''
            if remainTime.days >= 1:
                remainTimeText = 'Hanya ada ' + str(remainTime.days) + ' hari'
            elif remainTime.seconds >= 3600:
                remainTimeText = 'Hanya ada ' + str(remainTime.seconds//3600) + ' jam'
            else:
                remainTimeText = 'Sudah kurang dari satu jam'
            pesan = 'Halo, ingat untuk ' + pesan + ' ya! ' + remainTimeText + ' lho sebelum deadline. Semangatt'
            pm(uId,pesan)
    return 'Data pushed!'

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'
# @handler.add(PostbackEvent)
# def balasPesanan(event):
@handler.add(UnfollowEvent)
def leaving(event):
    uId = event.source.user_id
    conn = psycopg2.connect(db_url, sslmode='require')
    cur = conn.cursor()
    cur.execute("delete from listSchedules where uid = '%s';" % (uId))
    cur.execute("delete from subscribers where uid = '%s';" % (uId))
    conn.commit()
    conn.close()

@handler.add(FollowEvent)
def followReply(event):
    uId = event.source.user_id
    uIdText = "'" + uId + "'"
    conn = psycopg2.connect(db_url, sslmode='require')
    print('Successfully connected')
    cur = conn.cursor()
    cur.execute("SELECT EXISTS (SELECT 1 FROM subscribers WHERE uid = " + uIdText +");")
    exists = cur.fetchone()[0]
    profile = line_bot_api.get_profile(uId)
    if exists:
        pm(uId,'Halo ' + profile.display_name + '! Kita berjumpa kembali!')
    else:
        pm(uId,'Halo ' + profile.display_name + '!')
        row = db.countRow('subscribers',cur)
        db.insertDataSubscriber(row+1,uId,event.source.type,cur)
    conn.commit()
    conn.close()

@handler.add(MessageEvent, message=TextMessage)
def replyText(event):
    input = event.message.text
    if '/delete' in input:
        uId = event.source.user_id
        id = input.split(' ')[1]
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute("SELECT uid FROM listSchedules where id = '%s';" % (id))
        resUid = cur.fetchone()[0]
        if resUid == uId:
            cur.execute("delete from listSchedules where id = '%s';" % (id))
            reply(event,'Delete successful!')
        else:
            reply(event,'Unable to delete!')
        conn.commit()
        conn.close()

    elif '/showall' == input:
        uId = event.source.user_id
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute("SELECT * FROM listSchedules where uid = '%s';" % (uId))
        results = cur.fetchall()
        if len(results)>0:
            isi = 'Dibawah ini adalah list jadwal anda: \n'
            for i in range(len(results)):
                date = results[i][3]
                time = results[i][4]
                deadline = datetime.datetime.combine(date,time)
                text = ''
                if i!=(len(results)-1):
                    text = ("%s. %s. Deadline: %s. id = %s\n" % (i+1, results[i][2], deadline.strftime("%d-%m-%Y %H:%M"), results[i][0]))
                else:
                    text = ("%s. %s. Deadline: %s. id = %s" % (i+1, results[i][2], deadline.strftime("%d-%m-%Y %H:%M"), results[i][0]))
                isi += text
            reply(event, isi)
        else:
            reply(event, 'Anda tidak mempunyai schedule!')
        conn.close()

    elif '/add' in input:
        uId = str(event.source.user_id)
        textPart = re.findall(r'"(.*?)"', input)
        deadline = datetime.datetime.strptime(textPart[1],'%d %m %Y %H:%M')
        message = textPart[0]
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute("SELECT count (*) FROM listSchedules where uid = '%s';" % (uId))
        count = cur.fetchone()[0]
        deadlineDate = datetime.datetime.strftime(deadline,'%Y-%m-%d')
        deadlineTime = datetime.datetime.strftime(deadline,'%H:%M')
        cur.execute("INSERT INTO listSchedules (id, uid, pesan, deadlineDate, deadlineTime) values (%s,'%s','%s','%s','%s');" % (count+1,uId,message,deadlineDate,deadlineTime))
        reply(event,'Schedule berhasil ditambahkan!')
        conn.commit()
        conn.close()
    else:
        reply(event,'Sorry, your message was not understood')

# shortening
def reply(event, isi): #reply message
    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=isi))
def pm(target_id, isi): #push message
    line_bot_api.push_message(target_id,TextSendMessage(text=isi))
def putQuotation(target):
    return "'" + target + "'"
if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
