import email
import imaplib
from flask import Flask, request, jsonify, make_response
from utils import login, goRefresh, s3_transfer
from termcolor import colored

app = Flask(__name__)


print(s3_transfer.bucketExist())
#
# def print_hi(name):
#     # Use a breakpoint in the code line below to debug your script.
#     print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.
#

@app.route('/api/v1/newMails')
def newMails():
    print(colored("Entered newMails", 'green'))
    con = login.Login()
    con.select('GRX')
    typ, data = con.search(None, 'ALL')

    # closing connection
    con.close()
    if data == [b'']:
        return "False"
    print("there are new masils -> ", data)
    return 'True'


@app.route('/api/v1/saveMails', methods=['POST'])
def saveMails():
    print("entered saveMails")
    s3_transfer.transfer()
    response = make_response(
        'sababa',
        200,
    )
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/api/v1/refresh')
def refresh():
    actions, unKnownActions = goRefresh.GoRefresh()
    body = {'actions': actions, 'unKnownActions': unKnownActions}
    response = make_response(
        jsonify(body),
        200,
    )
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/')
def index():
    return "Shalom :2)"


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run(debug=True)


