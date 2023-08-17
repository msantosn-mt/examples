#!/usr/bin/python -d

import os, sys, pymysql, smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email import Encoders

if len(sys.argv) != 3:
  print "\nThis commands needs 2 arguments.\n"
  print "Examples " + str(sys.argv[0]) + " <Ticket ID> <E-mail>\n"
  sys.exit(1)

ticketID = str(sys.argv[1])
dstEmail = str(sys.argv[2])

# Connecting to the DB.
DBConn = pymysql.connect(host='localhost', port=3306, user='tickets_usr', passwd='', db='tickets_db')
DBShell = DBConn.cursor()

SQLQuery = "SELECT email, name, subject, created, ticket_id FROM ticket_ticket WHERE status='open' AND ticketID ='" + ticketID + "'"
DBShell.execute(SQLQuery)

if DBShell.rowcount != 1:
  print "I didn't find the ticket you are referring to, perhaps it is already closed."
  print "Or perhaps there is something wrong with me!\n"
  print "I asked the MySQL this: " + SQLQuery
  print "\nI got " + str(DBShell.rowcount) + " results."
  sys.exit(2)

DBRow = DBShell.fetchone()
if DBRow is None:
  sys.exit(2)

srcEmail = DBRow[0]
srcName = DBRow[1]
srcSubject = DBRow[2]
srcDate = str(DBRow[3])
realticketID = str(DBRow[4])

srcSummary = 'On ' + srcDate + ', ' + srcName + ' <' + srcEmail + '>:\n'
print srcSubject
print srcSummary

SQLQuery = "SELECT headers, message FROM ticket_ticket_message WHERE ticket_id = " + realticketID
DBShell.execute(SQLQuery)

DBRow = DBShell.fetchone()
if DBRow is None:
  print "Could not get the content of the ticket.. Exiting..."
  sys.exit(3)

srcEmailHdrs = DBRow[0]
srcEmailContent = DBRow[1]
srcAttachments = []

SQLQuery = "SELECT file_name, file_key FROM ticket_ticket_attachment WHERE ticket_id = " + realticketID
DBShell.execute(SQLQuery)
if DBShell.rowcount > 0:
  print str(DBShell.rowcount) + " attachment(s) were found for this ticket."
  for row in DBShell.fetchall():
    filename = str(row[1]) + '_' + str(row[0])
    filekey = row[1]
    for path, dirs, files in os.walk('/var/www/ticket/files/'):
      for file in files:
        if filename in file:
          srcAttachments.append(os.path.join(path, file))

EmailBody = """
Hello,

We have received the following message which we are forwarding to you as
we have you listed as technical contact for the IP(s)/network in the
message.

Please let us know if you might need our help to fix the issue reported.

If you need more information in regards to this report, you can contact
the original sender.

Thank you.

=== Forwarded message ===
"""
EmailBody = EmailBody + srcSummary + srcEmailContent

EmailMsg = MIMEMultipart()
EmailMsg['Date'] = formatdate(localtime=True)
EmailMsg['Subject'] = 'Fwd: ' + srcSubject
EmailMsg['To'] = dstEmail
EmailMsg.attach( MIMEText(EmailBody) )

for attachment in srcAttachments:
  part = MIMEBase('application', "octet-stream")
  part.set_payload( open(attachment,"rb").read() )
  Encoders.encode_base64(part)
  part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attachment))
  EmailMsg.attach(part)


SendEmail = smtplib.SMTP('192.168.199.254','25')
#SendEmail.set_debuglevel(5)
SendEmail.starttls()
SendEmail.login('usr@emailserver','Password')
SendEmail.sendmail(EmailMsg['From'], [EmailMsg['To']], EmailMsg.as_string())

DBShell.close()
DBConn.close()
