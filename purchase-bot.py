#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Purchase Bot.
Usage: This bot records the spendings in the database and makes monthly and weekly reports.
Press Ctrl-C on the command line to stop the bot.
"""
import psycopg2
import logging
import re
import datetime
import random
import argparse

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

db_user = ""
db_pass = ""
db_host = ""
db_port = ""
db_name = ""

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

invalid_currency = ["Don't be hasty", "Next time", "Your hands are shaking", "No, I can't take this crap"]

def add_purchase(price, desc = None, p_id = 6):
    try:
        connection = psycopg2.connect(user = db_user,
                                    password = db_pass,
                                    host = db_host,
                                    port = db_port,
                                    database = db_name)

        cursor = connection.cursor()
        # Print PostgreSQL Connection properties

        d = datetime.date.today()
        

        # Print PostgreSQL version
        cursor.execute("""INSERT INTO purchase (purchase_amount,
                                                date_of_purchase,
                                                purchase_description,
                                                purchase_id) values ({}, '{}', '{}', {});""".format(price, d, desc, p_id))
        connection.commit()

    except (Exception, psycopg2.Error) as error:
        logger.error("Error while connecting to PostgreSQL: %s", error)
    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            logger.debug('PostgreSQL connection is closed')


def get_data_for_time(days):
  
    record = []
    try:
        connection = psycopg2.connect(user = db_user,
                                    password = db_pass,
                                    host = db_host,
                                    port = db_port,
                                    database = db_name)

        cursor = connection.cursor()

        d = datetime.date.today()
        week_ago = d - datetime.timedelta(days=days)

        # Print PostgreSQL version
        cursor.execute("""select p.purchase_amount, p.date_of_purchase, 
                            t.type_of_spending from purchase p, types t 
                            where p.purchase_id = t.id and date_of_purchase 
                            >= '{}';""".format(week_ago))
        connection.commit()
        record = cursor.fetchall()
    except (Exception, psycopg2.Error) as error:
        logger.error("Error while connecting to PostgreSQL: %s", error)
    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            logger.debug('PostgreSQL connection is closed')

    return record

def r_week(update, context):
    record = get_data_for_time(7)
    query = update.callback_query
    s = ""
    for r in record:
        s = s + "{} : {} € : {}\n".format(r[1], r[0], r[2])
    query.edit_message_text(text='This is your week 💶 report: \n {}'.format(s))

def r_month(update, context):
    try:
        connection = psycopg2.connect(user = db_user,
                                    password = db_pass,
                                    host = db_host,
                                    port = db_port,
                                    database = db_name)

        cursor = connection.cursor()

        today = datetime.date.today()
        m = (today.month) - 1
        m_now = today.month
        y = today.year
        month_ago = '{}-{}-01'.format(y,m)
        month_now = '{}-{}-01'.format(y,m_now)

        # Get the date of prev month
        first = today.replace(day=1)
        lastMonth = first - datetime.timedelta(days=1)

        # Print PostgreSQL version
        cursor.execute("""select distinct t.type_of_spending, sum(p.purchase_amount) 
                        from purchase p, 
                        types t where p.purchase_id = t.id and 
                        date_of_purchase >= '{}' and date_of_purchase < '{}' group by 
                        t.type_of_spending;""".format(month_ago, month_now))
        connection.commit()
        record = cursor.fetchall()
        query = update.callback_query
        s = ""
        for r in record:
            s = s + "{} : {} €\n".format(r[0], r[1])
        query.edit_message_text(text='This is your {0:%B} report: \n {1}'.format(lastMonth,s))

    except (psycopg2.Error) as error:
        logger.error("Error while db interaction: %s", error)
    except (Exception) as error:
        logger.error("Unexpected error: %s", error)
    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            logger.debug('PostgreSQL connection is closed')


STATE_WAIT_CURRENCY = 1
STATE_WAIT_TYPE = 2
STATE_WAIT_APPROVE = 3

state = None
price = 0
p_type_id = 0

def start_fn(update, context):

    update.message.reply_text(
        'Hi! My name is purchase Bot. I will hold all your spends here. '
        'Send /cancel to stop talking to me.\n\n')

    keyboard = [[InlineKeyboardButton("Add new...", callback_data='1')],
                 [InlineKeyboardButton("Report week", callback_data='2')],
                [InlineKeyboardButton("Report month", callback_data='3')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)

def cancel_fn(update, context):
    global state
    update.message.reply_text(
        'Ok, it was nice to see you. Bye! 👋\n\n')
    state = None


def button(update, context):

    query = update.callback_query
    global state
    global p_type_id

    if int(query.data) == 1:
        state = STATE_WAIT_CURRENCY
        query.edit_message_text(text="Please enter the amount...")
        return
    elif int(query.data) == 2:
        r_week(update, context) 
    elif int(query.data) == 3:
        r_month(update, context)

    elif int(query.data) == 20:
        add_purchase(price, p_id = p_type_id)
        query.edit_message_text(text="Yey! Done!")
        state = None
        return

    elif int(query.data) == 21:
        query.edit_message_text(text="Ok, see you next time!")
        state = None
        return

    elif int(query.data) == 10:
        # Type Grossery
        p_type_id = 1
        state = STATE_WAIT_APPROVE
        keyboard2 = [[InlineKeyboardButton("YES", callback_data='20')],
                    [InlineKeyboardButton("NO", callback_data='21')]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        query.edit_message_text(text="Are you sure?")
        query.edit_message_reply_markup(reply_markup=reply_markup2)
        return
    elif int(query.data) == 11:
        # Type Entertainment
        p_type_id = 2
        state = STATE_WAIT_APPROVE
        keyboard2 = [[InlineKeyboardButton("YES", callback_data='20')],
                    [InlineKeyboardButton("NO", callback_data='21')]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        query.edit_message_text(text="Are you sure?")
        query.edit_message_reply_markup(reply_markup=reply_markup2)
        return
    elif int(query.data) == 12:
        # Type Clothes
        p_type_id = 3
        state = STATE_WAIT_APPROVE
        keyboard2 = [[InlineKeyboardButton("YES", callback_data='20')],
                    [InlineKeyboardButton("NO", callback_data='21')]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        query.edit_message_text(text="Are you sure?")
        query.edit_message_reply_markup(reply_markup=reply_markup2)
        return
    elif int(query.data) == 13:
        # Type Home
        p_type_id = 4
        state = STATE_WAIT_APPROVE
        keyboard2 = [[InlineKeyboardButton("YES", callback_data='20')],
                    [InlineKeyboardButton("NO", callback_data='21')]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        query.edit_message_text(text="Are you sure?")
        query.edit_message_reply_markup(reply_markup=reply_markup2)
        return
    elif int(query.data) == 14:
        # Type Lunch
        p_type_id = 5
        state = STATE_WAIT_APPROVE
        keyboard2 = [[InlineKeyboardButton("YES", callback_data='20')],
                    [InlineKeyboardButton("NO", callback_data='21')]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        query.edit_message_text(text="Are you sure?")
        query.edit_message_reply_markup(reply_markup=reply_markup2)
        return
    elif int(query.data) == 15:
        # Type Others
        p_type_id = 6
        state = STATE_WAIT_APPROVE
        keyboard2 = [[InlineKeyboardButton("YES", callback_data='20')],
                    [InlineKeyboardButton("NO", callback_data='21')]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        query.edit_message_text(text="Are you sure?")
        query.edit_message_reply_markup(reply_markup=reply_markup2)
        return
    else:
        logger.error("unknown callback {}".format(query.data))
        # in case of any error - reset the state
        state = None

def process(update, context):
    """process the user message."""
    
    global price
    global state

    if state == STATE_WAIT_CURRENCY:
        logger.debug("handling request data in STATE ADD")
        # parse here the number is correct
        match = re.match(r"^\s*[0-9]{1,3}((\,|\.)\d{1,2})?\s*$", update.message.text)
        if match:
            logger.info("Received currency: %s", update.message.text)
            keyboard1 = [[InlineKeyboardButton("Grossery", callback_data='10')],
                [InlineKeyboardButton("Entertainment", callback_data='11')],
                [InlineKeyboardButton("Clothes", callback_data='12')],
                [InlineKeyboardButton("Home", callback_data='13')],
                [InlineKeyboardButton("Lunch", callback_data='14')],
                [InlineKeyboardButton("Others", callback_data='15')]]
 
            reply_markup1 = InlineKeyboardMarkup(keyboard1)
            update.message.reply_text('Sounds good! Please chose:', reply_markup=reply_markup1) 
            price = float(update.message.text.replace(",", "."))
            state = STATE_WAIT_TYPE
        else:
            logger.error("Invalid currency format: %s", update.message.text)
            update.message.reply_text(invalid_currency[random.randrange(0, len(invalid_currency)-1)] + ". Let's try it again...")
    else:
        logger.error("handling request data in the STATE which is not STATE_WAIT_CURRENCY")
        update.message.reply_text("Ops, something wrong!")
        state = None

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():

    global db_user
    global db_pass
    global db_host
    global db_port
    global db_name

    parser = argparse.ArgumentParser(
        description="""Create update file for bootloader. Example: python3 ./purchase-bot.py
                                                                        --host=localhost
                                                                        --port=5432
                                                                        --user=postgre
                                                                        --password=123456
                                                                        --database=testdb
                                                                        --token=<telegram token>""")
    parser.add_argument('--host', help='Host', required=True)
    parser.add_argument('-P', '--port', help='Port', required=True)
    parser.add_argument('-u', '--user', help='User', required=True)
    parser.add_argument('-p', '--password', help='Password', required=False)
    parser.add_argument('--database', help='Database name', required=True)
    parser.add_argument('-t', '--token', help='Token', required=True)

    args = parser.parse_args()

    db_user = args.user

    if args.password:
        db_pass = args.password
    else:
        db_pass = ""

    db_host = args.host
    db_port = args.port
    db_name = args.database

    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(args.token, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start_fn))
    dp.add_handler(CommandHandler("cancel", cancel_fn))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CallbackQueryHandler(r_week))
    dp.add_handler(CallbackQueryHandler(r_month))

    # on noncommand i.e message - process the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, process))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
