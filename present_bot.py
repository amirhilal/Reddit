import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import re

'''USER CONFIGURATION'''

USERNAME  = "XXXXX"
#This is the bot's Username. (In order to send mail, he must have some amount of Karma)
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = "XXXXXX"
#This is a short description of what the bot does.
SUBREDDIT = "XXXXX"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
REPLYSTRING = "Free presents from Santa"
BOTSTRING = "\n \n I am a bot, if you have any questions or concenrs please send a message to /u/Santa_fat"
#What to say
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
P_AMOUNT = 0

'''All done!'''
WAITS = str(WAIT)

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS presents(NAME TEXT, AMOUNT INT)')
cur.execute('CREATE TABLE IF NOT EXISTS presents_give(NAME TEXT, USER TEXT, AMOUNT INT)')
print('Loaded Completed table')

r = praw.Reddit(USERAGENT) #Default
r.login(USERNAME, PASSWORD) #Login

def freePresents():
        REPLYSTRING = "Free presents from Santa"
        print('Searching top submissions in '+ SUBREDDIT + '.')
        SUB = r.get_subreddit(SUBREDDIT) #Posts in sub
        TOP = SUB.get_hot(limit=3) #Get top 3 submissions
        for TOPS in TOP:
            pid = TOPS.id
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])

            try:
                pauthor = TOPS.author.name
            except AttributeError:
                pauthor = '[DELETED]'

            if not cur.fetchone():
                print('Up voting...')
                TOPS.upvote() #upvote all TOP submissions
                cur.execute('INSERT INTO oldposts (ID) VALUES(?)', [pid])
                cur.execute('SELECT * FROM presents WHERE NAME=?', [pauthor])
                if not cur.fetchone():
                    cur.execute('INSERT INTO presents VALUES(?,?)', [pauthor, "1"])
                    REPLYSTRING = REPLYSTRING+ " to " +pauthor
                else:
                    DATAS = cur.fetchone()[1]
                    if DATAS:
                        P_AMOUNT = DATAS + 1
                        cur.execute('UPDATE presents SET AMOUNT = AMOUNT + "1" WHERE NAME=?', [pauthor])
                        P_AMOUNT = str(P_AMOUNT)
                        REPLYSTRING = "Welcome back " +pauthor+", \n \n Free present from Santa \n \n You now have " +P_AMOUNT +" presents."
                    else:
                        cur.execute('INSERT INTO presents VALUES(?,?)', [pauthor, "1"])
                        REPLYSTRING = REPLYSTRING+ " to " +pauthor

                print ('Commenting...')
                TOPS.add_comment(REPLYSTRING+""+BOTSTRING)

        sql.commit()

def scanSub():
    REPLYSTRING = ""
    PARENTSTRING = ["presentbot give"]
    print('Searching '+ SUBREDDIT + ' for comments.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    for post in posts:
        pid = post.id
        try:
            pauthor = post.author.name
        except AttributeError:
            pauthor = '[DELETED]'
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            #cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
            pbody = post.body.lower()
            if any(key.lower() in pbody for key in PARENTSTRING):
                AMOUNTS = int(re.findall(r'\b\d+\b', pbody)[0])
                #WHEREUSER = WHEREUSER.find(" ")
                #print(WHEREUSER)
                USER = str(pbody.split(" "))
                WHEREUSER = str(USER.split("/u/"))
                print(WHEREUSER)
                cur.execute('SELECT * FROM presents WHERE NAME=?', [pauthor])
                DATA = cur.fetchone()
                if not DATA:
                    REPLYSTRING  = pauthor+", Sorry but you do not have any presents to give."
                else:
                    DATA = DATA[1]
                    try:
                        if DATA:
                            DATA = int(DATA)
                            if DATA >= AMOUNTS:
                                AMOUNTS = (str(AMOUNTS))
                                P_AMOUNT = DATA - 1
                                P_AMOUNT = str(P_AMOUNT)
                                cur.execute('UPDATE presents SET AMOUNT = AMOUNT - ? WHERE NAME=?', [AMOUNTS, pauthor])
                                cur.execute('SELECT * FROM presents WHERE NAME=?', [USER])
                                if cur.fetchone():
                                    cur.execute('UPDATE presents SET AMOUNT = AMOUNT + ? WHERE NAME=?', [AMOUNTS, USER])
                                else:
                                    cur.execute('INSERT INTO presents VALUES(?,?)', [USER, "1"])
                                    cur.execute('INSERT INTO presents_give VALUES(?,?,?)', [pauthor, USER, AMOUNTS])
                                    REPLYSTRING  = pauthor+", You just gave "+USER+" " +AMOUNTS+ " presents."
                            else:
                                REPLYSTRING  = pauthor+", Sorry but you do not have any presents to give."
                        else:
                            REPLYSTRING  = pauthor+", Sorry but you do not have any presents to give."
                    except Exception as e:
                        print('An error has occured:', e)
                #post.reply(REPLYSTRING+""+BOTSTRING)
            #sql.commit()


while True:
    try:
        scanSub()
        #freePresents()
    except Exception as e:
    	print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    time.sleep(WAIT)
