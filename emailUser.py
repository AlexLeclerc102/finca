import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def sendErrorMail(sender, exception):
    # set up the SMTP server
    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login("alexandre.leclerc@gadz.org", "Zpsj76t3")

    email = "leclercalex10@gmail.com"

    msg = MIMEMultipart()       # create a message

    # add in the actual person name to the message template
    message = """Error:
    """ + str(exception) + """
    By: """ + str(sender)

    # setup the parameters of the message
    msg['From'] = "alexandre.leclerc@gadz.org"
    msg['To'] = email
    msg['Subject'] = "Error"

    # add in the message body
    msg.attach(MIMEText(message, 'plain'))

    # send the message via the server set up earlier.
    s.send_message(msg)
    print(msg)
    return None
