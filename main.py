import telebot
from telebot import types
import sqlite3, re, requests, json, time

# Connect to the database
conn = sqlite3.connect(
  'newDB.db',
  check_same_thread=False)

# Create a cursor object to execute database queries
cursor = conn.cursor()

# Create a table with chatid as id and name, registration number, and campus columns
cursor.execute('''CREATE TABLE IF NOT EXISTS students
              (chatid TEXT PRIMARY KEY,
               name TEXT,
               registration_number TEXT UNIQUE,
               campus TEXT,
               currentstep TEXT);''')

# Commit the changes to the database
conn.commit()

API_KEY = '5843568454:AAHqj1oxLu84ijlWFETROnOUwlAbZVvRhj0'
bot = telebot.TeleBot(API_KEY)

# ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID') #553145791
ADMIN_CHAT_ID = '553145791'

# ensure all campus names are lowercase here
CAMPUS_LIST = ['sefere selam', '4 kilo', '5 kilo', '6 kilo', 'lideta']


@bot.message_handler(func=lambda m: m.content_type != 'text')
def msg_type_restriction(msg):
  res = f'Hey {msg.from_user.first_name}! Sorry I cant process this type of message. Please try again in plain text.'
  bot.send_message(msg.chat.id, res)


@bot.message_handler(commands=['start'])
def start(msg):
  cursor = conn.execute(
    "SELECT chatid, name, currentstep FROM students WHERE chatid = ?",
    (msg.chat.id, ))

  user = cursor.fetchone()
  next = None

  if user:
    if user[2] == 'name':
      res = "Welcome back!! Lets get started off with your Ztudent profile. What is your name (legal name)?"
      next = process_name_step

    elif user[2] == 'reg':
      res = f"""Welcome back, {user[1].split(' ')[0].capitalize()}! Lets continue where we left off. What is your registration number? It is something like UGR/0000/15."""
      next = process_ugr_step

    elif user[2] == 'campus':
      markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
      for c in CAMPUS_LIST:
        item = types.KeyboardButton(c.capitalize())
        markup.add(item)

      res = f"""Welcome back, {user[1].split(' ')[0].capitalize()}! Lets continue where we left off. Which campus are you in?"""
      next = process_campus_step

    elif user[2] == 'finish':
      res = f"""Hey, {user[1].split(' ')[0].capitalize()}. You have already finished setting up your profile. We are processing the data you have already sent. We will send you your login code. Please wait."""

    bot.send_message(msg.chat.id, res)
    if next != None:
        bot.register_next_step_handler(msg, next)

  else:
    conn.execute("INSERT INTO students (chatid, currentstep) VALUES (?, ?)",
                 (msg.chat.id, 'name'))
    conn.commit()
    res = f"""
    Hey there {msg.from_user.first_name}! Welcome, this is a customized bot for the Ztudent application. Ztudent aims to help you make informed decision to shape your future career.
    """
    bot.send_message(msg.chat.id, res)
    res = " Lets get started off with your Ztudent profile. What is your name (legal name)?"
    msg = bot.send_message(msg.chat.id, res)
    bot.register_next_step_handler(msg, process_name_step)


def process_name_step(msg):
  name = msg.text.strip()
  if re.match(r'^[a-zA-Z]+(\s[a-zA-Z]+)$', name):
    conn.execute(
      "UPDATE students SET name = ?, currentstep = ? WHERE chatid = ?",
      (name, 'reg', msg.chat.id))
    conn.commit()

    res = f"""Okay, {name.split(' ')[0].capitalize()}! What is your registration number? It is something like UGR/0000/15."""
    bot.send_message(msg.chat.id, res)
    bot.register_next_step_handler(msg, process_ugr_step)
  elif name.lower() == '/start_over':
    bot.send_message(
      msg.chat.id,
      'Starting over will erase the previous profile you made. Type yes to continue or cancel by typing anything else.'
    )
    bot.register_next_step_handler(msg, start_over)
  elif name.lower() == '/start':
    bot.send_message(
      msg.chat.id,
      'start command not effective here. Tap /start_over to start profile from the beginning or continue profile by providing your name.'
    )
    bot.register_next_step_handler(msg, process_name_step)
  elif name.lower() == '/help':
    help(msg)
  else:
    res = """Name invalid. It must consist first name and last name separated by a single space. Please check and try again."""
    bot.send_message(msg.chat.id, res)
    bot.register_next_step_handler(msg, process_name_step)


def process_ugr_step(msg):
  ugr = msg.text.upper()
  if re.match(r'^UGR/\d{4}/15$', ugr):
    try:
      conn.execute(
        "UPDATE students SET registration_number = ?, currentstep = ? WHERE chatid = ?",
        (ugr, 'campus', msg.chat.id))
      conn.commit()
    except sqlite3.IntegrityError:
      res = f'Registration number{ugr} already used. Report to @hhanizu if your registration number was used by someone else.'
      bot.send_message(msg.chat.id, res)
    finally:
      markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
      for c in CAMPUS_LIST:
        item = types.KeyboardButton(c.capitalize())
        markup.add(item)

      res = "Okay! Which campus are you in?"
      bot.send_message(msg.chat.id, res, reply_markup=markup)
      bot.register_next_step_handler(msg, process_campus_step)
  elif ugr.lower() == '/start_over':
    bot.send_message(
      msg.chat.id,
      'Starting over will erase the previous profile you made. Type yes to continue or cancel by typing anything else.'
    )
    bot.register_next_step_handler(msg, start_over)
  elif ugr.lower() == '/start':
    bot.send_message(
      msg.chat.id,
      'start command not effective here. Tap /start_over to start profile from the beginning or continue profile by provding your registration number.'
    )
    bot.register_next_step_handler(msg, process_ugr_step)
  elif ugr.lower() == '/help':
    help(msg)
  else:
    res = "Registration number invalid. It is something like UGR/--(4 digits)--/15. Please check and try again."
    bot.send_message(msg.chat.id, res)
    bot.register_next_step_handler(msg, process_ugr_step)


def process_campus_step(msg):
  campus = msg.text.lower()
  if campus in CAMPUS_LIST:
    conn.execute(
      "UPDATE students SET campus = ?, currentstep = ? WHERE chatid = ?",
      (campus, 'finish', msg.chat.id))
    conn.commit()

    markup = types.ReplyKeyboardRemove(selective=False)
    res = "Nice! We will send you a login code to activate your app. This usually take time please be patient. See you soon!!"
    bot.send_message(msg.chat.id, res, reply_markup=markup)
  elif campus == '/start_over':
    bot.send_message(
      msg.chat.id,
      'Starting over will erase the previous profile you made. Type yes to continue or cancel by typing anything else.'
    )
    bot.register_next_step_handler(msg, start_over)
  elif campus == '/start':
    bot.send_message(
      msg.chat.id,
      'start command not effective here. Tap /start_over to start profile from the beginning or continue profile by selecting your campus name.'
    )
    bot.register_next_step_handler(msg, process_campus_step)
  elif campus == '/help':
    help(msg)
  else:
    res = "Campus name invalid. Please select one of the AAU campuses listed on your keyboard."
    bot.send_message(msg.chat.id, res)
    bot.register_next_step_handler(msg, process_campus_step)


@bot.message_handler(commands=['start_over'])
def start_over(msg):
  if (msg.text != 'yes') & (msg.text != '/start_over'):
    bot.send_message(
      msg.chat.id,
      'Starting over canceled. Press /start to continue where you left off.')
    return
  try:
    conn.execute("UPDATE students SET currentstep = ? WHERE chatid = ?",
                 ('name', msg.chat.id))
    conn.commit()

    res = """Cleared your previous profile. Let's start again. What is your legal name?"""
    bot.send_message(msg.chat.id, res)
    bot.register_next_step_handler(msg, process_name_step)

  except sqlite3.IntegrityError:
    conn.execute("INSERT INTO students (chatid, currentstep) VALUES (?, ?)",
                 (msg.chat.id, 'name'))
    conn.commit()
    res = f"""
Hey there {msg.from_user.first_name}! Welcome, this is a customized bot for the Ztudent application. Ztudent aims to help you make informed decision to shape your future career.
"""
    bot.send_message(msg.chat.id, res)
    res = " Lets get started off with your Ztudent profile. What is your name (legal name)?"
    msg = bot.send_message(msg.chat.id, res)
    bot.register_next_step_handler(msg, process_name_step)


@bot.message_handler(commands=['help'])
def help(msg):
  res = f"""
    Welcome {msg.from_user.first_name}! This a simple customized bot for the Ztudent application.

What is Ztudent?
    Ztudent is an app that aims to help you make informed decision to shape your future career. It does so by gathering student grades and their desired departments. Finally you, the registered student, are able to:
      - view the how many students are interested in any particular department
      - compare your grades with all students interested in that same department
      - see the average grades of the total students in any particular department

Using these information any student can predict whether he/she is likely to join their department of interest. Accordingly, unlike any other time students take the chance to make a better informed decision regarding their academic career.

What does this bot do?
    This bot in particular helps you register for the Ztudent app. You are required to provide your name, registration number and the campus in which you are currently enrolled. Finally, it will send you an activation code to begin using the app.

Common Problems:
- I made an error so I want to edit my profile. (/start_over and set up your profile fresh from the beginning)
- Most problems can be fixed by /start_over

Contact the creator(@hhanizu) for further information.
Ztudent Bot is a simple bot that assists registration for the Ztudent application. Ztudent is only for AAU students.
Supported commands:
    /start - to begin or continue setting up your profile.
    /help - show detailed help message.
    /start_over - discard current progress and start from the beginning.

    """
  bot.send_message(msg.chat.id, res)


@bot.message_handler(func=lambda m: True)
def unrecognized_command(msg):
  res = """
Command not recognized. Here are the supported list of commands.\n
    /start - to begin or continue setting up your profile.
    /help - show detailed help message.
    /start_over - discard current profile progress and start from the beginning
    """
  bot.send_message(msg.chat.id, res)


def _init_bot(data):
  id_set = {u['message']['chat']['id'] for u in data['result']}
  update_list = sorted(data['result'], key=lambda i: i['update_id'], reverse=True)
  cmd_list = ['/help', '/start', '/start_over']
  for u in update_list:
    chat_id = u['message']['chat']['id']
    if chat_id in id_set:
      id_set.remove(chat_id)
      try:
        if u['message']['text'] in cmd_list:
          res = 'You got me! ZtudentBot was offline for a moment. Please repeat your command.'
          bot.send_message(chat_id, res)
      except KeyError:
        # this runs only if other file types were sent to the bot
        res = 'The type of your previous message is not supported. Please try again in plain text.'
        bot.send_message(chat_id, res)

  print('Bot running...')
  bot.infinity_polling(skip_pending=True)
  conn.close()


num_retries = 3
url = f'https://api.telegram.org/bot{API_KEY}/getUpdates'
while num_retries > 0:
  try:
    response = requests.get(url)
    if response.ok:
      data = json.loads(response.text)
      _init_bot(data) if data['ok'] else print(
        'Telegram old updates data is not ok')
    else:
      print(f"HTTP Error: {response.status_code}")
  except Exception as e:
    print(f"Error: {e}")
    time.sleep(1)

  num_retries -= 1
  print(f'Reinitailizing bot...{num_retries}')
