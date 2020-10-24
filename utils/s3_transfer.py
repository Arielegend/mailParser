import email
import os

import boto3
from botocore.client import ClientError
from utils import login

BASE_NAME = 'msg_no_'
BASE_DIR = 'C:\\Users\\user\\Desktop\\new'

s3 = boto3.resource('s3',
                    aws_access_key_id="AKIATBFOUJ25FSSF4BGG",
                    aws_secret_access_key="DHVfvB6O9oIeB0EJsU/KF0OLNGgcfybjodIf/Sze")


#
#
def writeTofile(mailDir, partOfName, msg):
    ## no need of dos backslash -- newDir = BASE_DIR + mailDir.replace('/', '\\')

    newDir = BASE_DIR + mailDir

    if not os.path.exists(newDir):
        os.makedirs(newDir)

    os.chdir(newDir)

    # print('Dir:' + os.getcwd() )

    file_name = BASE_NAME + partOfName + '.eml'

    # print('Write:' + file_name)

    # fw = open(newDir + '/' + file_name, 'w', encoding="utf-8")
    # fw.write(msg)
    # fw.close()

    s3 = boto3.resource('s3',
                            aws_access_key_id="AKIATBFOUJ25FSSF4BGG",
                            aws_secret_access_key="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")

    object = s3.Object('mailsclientproccessed2', 'Garox/opn/sho1/filename.eml')
    object.put(Body=msg)

    print("done")

    return


def transfer():
    con = login.Login()
    con.select('GRX')

    typ, items = con.search(None, 'ALL')
    email_ids = items[0].split()

    for num in email_ids:
        typ, data = con.fetch(num, '(RFC822)')
        msg = email.message_from_bytes(data[0][1])

        # smsg = msg.as_bytes().decode(encoding='ISO-8859-1')
        smsg = msg.as_bytes()

        writeTofile('GRX', num.decode(), smsg)

    con.close()


def bucketExist():
    try:
        s3.meta.client.head_bucket(Bucket="mailsclientproccessed2")
        return True
    except ClientError:
        return False
