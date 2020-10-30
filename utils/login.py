import email
import imaplib


def Login():

    host = 'imap.gmail.com'
    username = ''
    password = ''

    con = imaplib.IMAP4_SSL(host)
    x = con.login(username, password)
    if x[0] == 'OK':
        print("connected to ", username)
    return con
