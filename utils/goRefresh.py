import email
import imaplib
import re
# from imap_tools import MailBox, AND
from utils import s3_transfer
from termcolor import colored

def BelongTo_OpnBokOnbRecDly(headers):
    opn = "OPN" in headers['subject'] or "opn" in headers['subject']
    bok = "BOK" in headers['subject'] or "bok" in headers['subject']
    onb = "ONB" in headers['subject'] or "onb" in headers['subject']
    rec = "REC" in headers['subject'] or "rec" in headers['subject']
    dly = "DLY" in headers['subject'] or "dly" in headers['subject']

    return opn + bok + onb + rec + dly, opn, bok, onb, rec, dly


def BelongTo_PreNotice(headers, msg_Body2):
    pre = "PRE" in headers['subject'] or "pre" in headers['subject'] or "Pre Alert" in headers['subject']
    notice = "NOTICE OF" in headers['subject'] or "notice of" in headers['subject']

    return pre + notice, pre, notice


def getHeaders(email_msg2_forHeaders):
    headers = {'subject': "", 'to': "", 'from': "", 'date': ""}
    for header in ['subject', 'to', 'from', 'date']:
        headers[header] = email_msg2_forHeaders[header]

    return headers


def checkForLink(email_msg):
    pattern1_link = 'Link\sto\sShipment\sDocuments\s*<(.*)>'

    linkHelper = re.findall(pattern1_link, email_msg.as_string())
    if len(linkHelper) > 0:
        link = linkHelper[0]
        msg = 'this is link' + link
        return True, link

    else:
        return False, '-1'


def BelongTo_DrishaHatara(headers, email_msg):
    LinkExist, link = checkForLink(email_msg)
    return LinkExist, link


def classifyMaiL(email_msg, email_msg2_forHeaders):
    headers = getHeaders(email_msg2_forHeaders)  # {'subject': "", 'to': "", 'from': "", 'date': ""}
    # print(colored("entered classifyMaiL this is headers.. :)", "blue"), headers)

    part1 = BelongTo_OpnBokOnbRecDly(headers)  # (number, opn, bok, onb, rec, dly) as booleans
    part2 = BelongTo_PreNotice(headers, email_msg)  # (number, Pre, Notice)
    part3 = BelongTo_DrishaHatara(headers, email_msg)    # (boolean, link/'-1')

    classifiedMail = None
    if part1[0] + part2[0] + part3[0] == 1:
        if part1[0] == 1:
            sho = getSHO_Part1(email_msg, headers)
            if sho:
                classifiedMail = {"part": 'PART1', 'action': part1, 'sho': sho}
        elif part2[0] == 1:
            classifiedMail = {"part": 'PART2', 'action': part2}
        elif part3[0] == 1:
            classifiedMail = {"part": 'PART3', 'action': part3}
    else:
        print("action isnt 1.. -> ")

    return classifiedMail


# simple login, return connection
def Login():
    host = 'imap.gmail.com'
    username = 'autologisr@gmail.com'
    password = 'NANAbanana123'

    con = imaplib.IMAP4_SSL(host)
    x = con.login(username, password)
    if x[0] == 'OK':
        # print("connected to ", username)
        return con
    return "NO_GOOD"


def getSHO_Part1(msg_Body, headers):
    # print(colored('entered getSHO', 'yellow'))
    # print("this is msg_Body ->", msg_Body.as_string())

    pattern1 = '\(SHO\)\: AVI-(\d\d\d\d\d)'
    pattern2 = 'AVI-(\d\d\d\d\d)'
    pattern3 = 'REF# AVI-(\d\d\d\d\d)'

    m1 = re.findall(pattern1, msg_Body.as_string())
    m2 = re.findall(pattern2, msg_Body.as_string())
    m3 = re.findall(pattern3, headers['subject'])

    shoHelper = (m1, m2, m3)
    sho = None

    ok = True
    if len(m1) > 0 or len(m2) > 0 or len(m3) > 0:
        if len(m1) > 0:
            sho = m1[0]
        elif len(m2) > 0:
            sho = m2[0]
        elif len(m3) > 0:
            sho = m3[0]

        # in this for loop we make sure we fetched same number.. all of them should be SAME SHO
        for m in shoHelper:
            for number in m:
                if number != sho:
                    ok = False
        if ok:
            return sho

    return sho


def removeBlanks(myStr):
    index = 0
    for char in myStr:
        if char == ' ':
            index += 1
        else:
            break
    return myStr[index: len(myStr)].rstrip()


# in this function we make sure - Subject: Ocean  : Open order confirmation .
def get_SupplierLoadingDestinationTerms(msg_Body, headers):
    # print(msg_Body)

    pattern1_supplier = 'Supplier\:\s*(.*)'
    pattern2_loading = 'Port of Loading\:\s*(.*)'
    pattern3_destination = 'Port of Destination\:\s*(.*)'
    pattern4_terms = 'Delivery Terms\:\s*(.*)'

    # confirmed = False
    supplier = None
    portLoading = None
    portDestination = None
    terms = None
    remarks = None
    msg_Body_string = walkNow(msg_Body)

    # print(msg_Body_string)

    supplierHelper = re.findall(pattern1_supplier, msg_Body_string)
    portLoadingHelper = re.findall(pattern2_loading, msg_Body_string)
    portDestinationHelper = re.findall(pattern3_destination, msg_Body_string)
    termsHelper = re.findall(pattern4_terms, msg_Body_string)

    supplier = supplierHelper[0] if len(supplierHelper) > 0 else "-1"
    portLoading = portLoadingHelper[0] if len(portLoadingHelper) > 0 else "-1"
    portDestination = portDestinationHelper[0] if len(portDestinationHelper) > 0 else "-1"
    terms = termsHelper[0] if len(termsHelper) > 0 else "-1"

    # print("supplier -> ", supplier)
    # print('portLoading -> ', portLoading)
    # print('portDestination -> ', portDestination)
    # print('terms -> ', terms)

    supplier = removeBlanks(supplier)
    portLoading = removeBlanks(portLoading)
    portDestination = removeBlanks(portDestination)
    terms = removeBlanks(terms)

    return supplier, portLoading, portDestination, terms


def OPN_MAIL(email_msg, headers):
    supplier, portLoading, portDestination, terms = get_SupplierLoadingDestinationTerms(email_msg, headers)
    pattern1_confirmation = 'Subject\: (.*)\.'
    # pattern6_remarks = '\*Remarks\: \*.*\*(.*)\*'
    msg_Body_string = email_msg.as_string()

    m1 = re.findall(pattern1_confirmation, msg_Body_string)
    confirmed = "confirmation" in m1[0]
    return confirmed, supplier, portLoading, portDestination, terms


def BOK_MAIL(email_msg, headers):
    # print(colored('entered BOK...', 'red'), msg_Body)
    supplier, portLoading, portDestination, terms = get_SupplierLoadingDestinationTerms(email_msg, headers)

    pattern1_status = 'Current status of your order is \s*(\w*)\s'
    pattern2_BookingDetails = 'V/V:(.*)\s'
    pattern3_eta = 'ETA\s\w+\s(.*)\s'  #
    pattern4_etd = 'ETD\s\w+\s(.*)\s'  #

    msg_Body_string = email_msg.as_string()

    statusHelper = re.findall(pattern1_status, msg_Body_string)
    status = statusHelper[0] if len(statusHelper) > 0 else "-1"

    bookingDetails = re.findall(pattern2_BookingDetails, msg_Body_string)
    flight = bookingDetails[0] if len(bookingDetails) > 0 else "-1"

    etaHelper = re.findall(pattern3_eta, msg_Body_string)
    etdHelper = re.findall(pattern4_etd, msg_Body_string)

    eta = etaHelper[0] if len(etaHelper) > 0 else "-1"
    etd = etdHelper[0] if len(etaHelper) > 0 else "-1"

    return status, supplier, portLoading, portDestination, terms, eta, etd, flight


def ONB_MAIL(email_msg, headers):
    supplier, portLoading, portDestination, terms = get_SupplierLoadingDestinationTerms(email_msg, headers)

    pattern1_status = 'Current status of your order is\s*(.*)'

    msg_Body_string = email_msg.as_string()

    statusHelper = re.findall(pattern1_status, msg_Body_string)

    status = statusHelper[0] if len(statusHelper) > 0 else "-1"
    status = removeBlanks(status)

    return status, supplier, portLoading, portDestination, terms


# REC -> BOOKING ... OPEN ... ?
def REC_MAIL(email_msg, headers):
    supplier, portLoading, portDestination, terms = get_SupplierLoadingDestinationTerms(email_msg, headers)

    pattern1_status = 'Current status of your order is\s*(.*)'

    msg_Body_string = email_msg.as_string()

    statusHelper = re.findall(pattern1_status, msg_Body_string)
    status = statusHelper[0] if len(statusHelper) > 0 else "-1"
    status = status.rstrip()

    return status, supplier, portLoading, portDestination, terms


def DLY_MAIL(email_msg, headers):
    supplier, portLoading, portDestination, terms = get_SupplierLoadingDestinationTerms(email_msg, headers)

    pattern1_status = 'Current status of your order is\s*(.*)'

    msg_Body_string = email_msg.as_string()
    statusHelper = re.findall(pattern1_status, msg_Body_string)

    status = statusHelper[0] if len(statusHelper) > 0 else "-1"
    if "DELAY" in status:
        status = 'DELAY'
    return status, supplier, portLoading, portDestination, terms


def getAction_Part1(email_msg, headers, classifiedMaiL):
    action = None
    if classifiedMaiL['action'][1]:
        action = OPN_MAIL(email_msg, headers)
    elif classifiedMaiL['action'][2]:
        action = BOK_MAIL(email_msg, headers)
    elif classifiedMaiL['action'][3]:
        action = ONB_MAIL(email_msg, headers)
    elif classifiedMaiL['action'][4]:
        action = REC_MAIL(email_msg, headers)
    elif classifiedMaiL['action'][5]:
        action = DLY_MAIL(email_msg, headers)

    return action


def getSho_Pre(email_msg):
    pattern1_sho = '\:\s*(\d\d\d\d\d)\s*\d\d\.\d\d\.\d\d'

    shoHelper = re.findall(pattern1_sho, email_msg.as_string())
    sho = shoHelper[0] if len(shoHelper) > 0 else "-1"

    return sho


def getShoAmilut_Notice(email_msg):
    pattern1_amilut = '\:\s*(\d\d\d\d\d\d\d\d\d)\s*'
    pattern1_sho = '\:\s*\:\s*(\d\d\d\d\d)\s*'

    shoHelper = re.findall(pattern1_sho, email_msg.as_string())
    sho = shoHelper[0] if len(shoHelper) > 0 else "-1"

    amilutHelper = re.findall(pattern1_amilut, email_msg.as_string())
    amilut = amilutHelper[0] if len(amilutHelper) > 0 else "-1"

    return sho, amilut


def Pre_MAIL(email_msg, headers):
    sho = getSho_Pre(email_msg)
    return sho


def NOTICE_MAIL(email_msg, headers):

    sho, amilut = getShoAmilut_Notice(email_msg)
    return sho, amilut


def getAction_Part2(email_msg, headers, classifiedMaiL):
    action = None
    if classifiedMaiL['action'][1]:  # classifiedMaiL['action'] = (number, Pre, Notice)
        action = Pre_MAIL(email_msg, headers)
    elif classifiedMaiL['action'][2]:
        action = NOTICE_MAIL(email_msg, headers)

    return action


def checkIfDrisha(email_msg):
    pattern1_amir = 'amir@aviram'

    amirHelper = re.findall(pattern1_amir, email_msg.as_string())
    amir = amirHelper[0] if len(amirHelper) > 0 else "-1"

    return amir


def Drisha_Mail(email_msg):

    pattern1_amilut = '\:\s*(\d\d\d\d\d\d\d\d\d)\s*.*Link'

    amilutHelper = re.findall(pattern1_amilut, email_msg.as_string())
    amilut = amilutHelper[0] if len(amilutHelper) > 0 else "-1"

    _, link = checkForLink(email_msg)

    return amilut, link


def Hatara_Mail(email_msg):
    email_msgHelper = walkNow(email_msg)

    pattern1_amilut = 'Subject.*(\d\d\d\d\d\d\d\d\d)'

    amilutHelper = re.findall(pattern1_amilut, email_msgHelper)
    amilut = amilutHelper[0] if len(amilutHelper) > 0 else "-1"

    _, link = checkForLink(email_msg)
    # myPrinter('Hatara_Mail', 'blue')
    # myPrinter(amilut, 'blue')

    return amilut, link


def checkIfHatara(email_msg, headers):
    pattern1_hatara = 'www\.aviram\.co\.il'

    ataraHelper = re.findall(pattern1_hatara, email_msg.as_string())
    hatara = ataraHelper[0] if len(ataraHelper) > 0 else "-1"

    return hatara


def getAction_Part3(email_msg, headers, classifiedMaiL):

    drisha = checkIfDrisha(email_msg)
    hatara = checkIfHatara(email_msg, headers)

    action = None
    if drisha != '-1' and hatara == '-1':
        action = Drisha_Mail(email_msg)
        return action, 'DRISHA'

    if drisha == '-1' and hatara != '-1':
        action = Hatara_Mail(email_msg)
        return action, 'HATARA'

    return None


def getAction(email_msg, email_msg2_forHeaders, classifiedMaiL):
    headers = getHeaders(email_msg2_forHeaders)
    action = None
    if classifiedMaiL['part'] == 'PART1':
        helper = getAction_Part1(email_msg, headers, classifiedMaiL)
        action = {'details': helper, 'classifiedMaiL': classifiedMaiL}
    elif classifiedMaiL['part'] == 'PART2':
        helper = getAction_Part2(email_msg, headers, classifiedMaiL)
        action = {'details': helper, 'classifiedMaiL': classifiedMaiL}
    elif classifiedMaiL['part'] == 'PART3':
        helper = getAction_Part3(email_msg, headers, classifiedMaiL)
        action = {'details': helper, 'classifiedMaiL': classifiedMaiL}
    return action


def get_body(msg):
    if msg.is_multipart():
        return get_body(msg.get_payload(0))
    else:
        return email.message_from_bytes(msg.get_payload(None, True))


def parse_uid(data):
    pattern_uid = re.compile('\d+ \(UID (?P<uid>\d+)\)')
    match = pattern_uid.match(data)
    return match.group('uid')


def copyGrxFolder(con):
    typ, items = con.search(None, 'ALL')
    email_ids = items[0].split()

    for mailID in email_ids:
        _, data = con.fetch(mailID, "(UID)")
        msg_uid = parse_uid(data[0].decode('utf-8'))
        con.uid('COPY', msg_uid, 'GRX_processed')


def emptyGrxFolder(con):
    typ, items = con.search(None, 'ALL')
    ok = items != [b'']

    while ok:
        email_ids = items[0].split()
        mailID = email_ids[0]
        _, data = con.fetch(mailID, "(UID)")
        msg_uid = parse_uid(data[0].decode('utf-8'))
        con.uid('STORE', msg_uid, '+FLAGS', '(\\Deleted)')
        con.expunge()

        typ, items = con.search(None, 'ALL')
        ok = items != [b'']


def GoRefresh():
    con = Login()
    con.select('GRX')

    transferHelper = []
    actions = []
    unKnownActions = []

    typ, items = con.search(None, 'ALL')
    email_ids = items[0].split()

    # print(":) ", email_ids )
    for mailID in email_ids:
        # returns to data the uid
        # resp, data = con.fetch(mailID, "(UID)")

        # if data[0]:
        # msg_uid = parse_uid(data[0].decode('utf-8'))

        result, email_data = con.fetch(mailID, '(RFC822)')

        if result == 'OK':

            raw = email.message_from_bytes(email_data[0][1])
            email_msg = get_body(raw)  # good for all kinds
            # print(email_msg)

            raw_email_Helper = email_data[0][1].decode('utf-8')
            email_msg2_forHeaders = email.message_from_string(raw_email_Helper)  # good for fetching headers
            # print(email_msg2_forHeaders['subject'])

            classifiedMaiL = classifyMaiL(email_msg,
                                          email_msg2_forHeaders)  # (classified(bool), action, email_msg, headers)

            if classifiedMaiL is None:
                print("classifiedMaiL is None.. this is email_msg -> ")
            else:

                action = getAction(email_msg, email_msg2_forHeaders, classifiedMaiL)

                if action is not None:
                    print("action is -> ", action)
                    actions.append(action)
                    transferHelper.append({'action': action, 'email': email_data})
                else:
                    helper = {'classifiedMaiL': classifiedMaiL, 'email': email_msg.as_string()}
                    unKnownActions.append(helper)

    copyGrxFolder(con)
    copy_MSG = 'done copy'
    myPrinter(copy_MSG, 'blue')



    # transferTos3()

    emptyGrxFolder(con)
    copy_MSG = 'done delete'
    myPrinter(copy_MSG, 'red')

    con.expunge()
    con.close()
    return actions, unKnownActions


def walkNow(email_msg):
    msg_Body = None
    for part in email_msg.walk():
        if part.get_content_type() == "text/plain":
            # msg_Body now is in str..
            msg_Body = part.get_payload()
    return msg_Body


# def search(key, value, con):
#     result, data = con.search(None, key, '"{}"'.format(value))
#     print("this is data -> ", data)
#     return data


def myPrinter(msg, color):
    message = colored(msg, color)
    print(message)

