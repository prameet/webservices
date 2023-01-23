from flask import Flask, request, jsonify, make_response, abort
from flask_restful import Resource, Api
import hashlib
from datetime import time, timedelta
import os
import logging
import pymysql.cursors
from datetime import datetime
from werkzeug.utils import secure_filename
import time
import re
import math, random
import urllib.request
import urllib.parse
import string
import base64
import face_recognition
import ast
import csv
import calendar
import xlsxwriter
import textwrap
from fpdf import FPDF, HTMLMixin
import cv2

# LOG CREATION
from flask_cors import CORS

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
app = Flask(__name__)
CORS(app)
api = Api(app, prefix="/api/v1")
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
# app.config['CORS_HEADERS'] = 'Content-Type'
# Upload file Path
ALLOWED_EXTENSIONS = {'csv', 'CSV'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Upload image type file Path
ALLOWED_IMAGE_EXT = {'JPEG', 'jpeg', 'jpg', 'png', 'PNG'}


def allowed_Img_Ext(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXT


def get_week_numbers_in_month(year, month):
    list_of_weeks = []
    initial_day = 1
    ending_day = calendar.monthrange(int(year), int(month))[1]  # get the last day of month
    initial_week = int(datetime(year, month, initial_day).isocalendar()[1])
    ending_week = int(datetime(year, month, ending_day).isocalendar()[1])
    counter = initial_week
    while (counter <= ending_week):
        list_of_weeks.append(counter)
        counter += 1
    return list_of_weeks


def sectohour(sec):
    ty_res = time.gmtime(sec)
    res = time.strftime("%H:%M:%S", ty_res)
    return res


def strhourtosec(time_str):
    t = time_str
    if 'days' in t:
        days, time = t.split(',')
        h, m, s = time.split(':')
        res = int(timedelta(hours=int(h), minutes=int(m), seconds=int(s)).total_seconds())
    else:
        h, m, s = t.split(':')
        res = int(timedelta(hours=int(h), minutes=int(m), seconds=int(s)).total_seconds())
    return res


def findDay(date):
    day, month, year = (int(i) for i in date.split('-'))
    dayNumber = calendar.weekday(year, month, day)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return (days[dayNumber])


# checkLicKey: for checking licence expired or not
def checkLicKey(OrganizationEmailId, OrganizationPassword):
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    ResponseData = DB.retrieveAllData("OrganizationDetails", "", "OrganizationEmailId='" + OrganizationEmailId + "'",
                                      "")
    length = int(len(ResponseData))
    is_expired = is_account_avail = 0
    if length > 0:
        is_account_avail = 1
        ExpiredDate = str(ResponseData[0]['ExpiredDate'])
        msg = 'Your license expired on (' + ExpiredDate + ')'
        if ExpiredDate < today:
            is_expired = 1
            msg = 'Your license has expired.  Please contact our support representative.'
        response = {'category': "1", 'is_expired': is_expired, 'is_account_avail': is_account_avail, 'message': msg}
    else:
        response = {'category': "0", 'is_expired': is_expired, 'is_account_avail': is_account_avail,
                    'message': "Account is not avail."}
    return response


# CLASS 'conf' IS FOR DATABASE CONNECTION
class conf():  # DB CONNECTION
    @staticmethod
    def connect():
        connection = pymysql.connect(host='localhost', user='root', password='', db='Api_v2',
                                     charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        return connection


# HERE CLASS DB IS DEFINED FOR  SQL CRUD OPERATION
class DB():  #
    @staticmethod
    # FUNCTION FOR RETRIVE ALL DATA WITH fields , wherecondition & ORDER_VALUE
    def retrieveAllData(tablename, fields, wherecondition, order):
        connection = conf.connect()
        cursor = connection.cursor()
        if fields:
            fields_value = fields
        else:
            fields_value = '*'
        sql_data = 'SELECT ' + fields_value + ' FROM ' + tablename
        if wherecondition:
            sql_data = sql_data + ' WHERE ' + wherecondition
        if order:
            sql_data = sql_data + ' ORDER BY ' + order
        try:
            cursor.execute(sql_data)
            rowcount = cursor.fetchall()
            connection.commit()
            cursor.close()
            connection.close()
            return rowcount
        except Exception as e:
            logger.exception('pymysql.Error, pymysql.Warning in retrive data')
            ResponseReturn = {"messageType": 'error', "messagetext": e}
            return ResponseReturn

    # FUNCTION FOR EXECUTION OF GROUP BY SQL QUERRY
    def selectAllData(allQuery):
        connection = conf.connect()
        cursor = connection.cursor()
        sql_data = allQuery
        try:
            cursor.execute(sql_data)
            rowcount = cursor.fetchall()
            connection.commit()
            cursor.close()
            connection.close()
            return rowcount
        except Exception as e:
            logger.exception('pymysql.Error, pymysql.Warning in retrive data')
            ResponseReturn = {"messageType": 'error', "messagetext": e}
            return ResponseReturn

    # FUNCTION FOR INSERTDATA
    def insertData(tablename, values):
        connection = conf.connect()
        cursor = connection.cursor()
        cols = values.keys()
        vals = values.values()
        strComma = "','"
        newVals = "'" + strComma.join(vals) + "'"
        sqlDataa = "INSERT INTO %s (%s) VALUES(%s)" % (tablename, ",".join(cols), "" + newVals)
        try:
            cursor.execute(sqlDataa)
            connection.commit()
            lastInsertId = cursor.lastrowid
            cursor.close()
            connection.close()
            message = "success"
            ResponseReturn = {"messageType": 'success', "messagetext": message, 'lastInsertId': lastInsertId}
            return ResponseReturn
        except (pymysql.Error, pymysql.Warning) as e:
            logger.exception('pymysql.Error, pymysql.Warning in fetching data')
            ResponseReturn = {"messageType": 'error', "messagetext": e, 'lastInsertId': '0'}
            return ResponseReturn

    # FUNCTION FOR DELETE SINGLE ROW
    def deleteSingleRow(tablename, wherecondition):
        connection = conf.connect()
        cursor = connection.cursor()
        sql_data = 'DELETE FROM ' + tablename
        if wherecondition:
            sql_data = sql_data + ' WHERE ' + wherecondition
        try:
            cursor.execute(sql_data)
            connection.commit()
            cursor.close()
            connection.close()
            message = "success"
            ResponseReturn = {"messageType": 'success', "messagetext": message}
            return ResponseReturn
        except (pymysql.Error, pymysql.Warning) as e:
            logger.exception('pymysql.Error, pymysql.Warning in deleteSingleRow data')
            ResponseReturn = {"messageType": 'error', "messagetext": e}
            return ResponseReturn

    # FUNCTION FOR UPDATE DATA
    def updateData(tablename, values, wherecondition):
        connection = conf.connect()
        cursor = connection.cursor()
        alldata = ''
        for key in values:
            if alldata:
                alldata = alldata + ", " + key + " = '" + values[key] + "'"
            else:
                alldata = alldata + key + " = '" + values[key] + "'"
        sqlDataa = "UPDATE " + tablename + " SET " + alldata + " WHERE " + wherecondition
        # print(sqlDataa)
        try:
            cursor.execute(sqlDataa)
            connection.commit()
            cursor.close()
            connection.close()
            message = "success"
            ResponseReturn = {"messageType": 'success', "messagetext": message}
            return ResponseReturn
        except (pymysql.Error, pymysql.Warning) as e:
            logger.exception('pymysql.Error, pymysql.Warning in updateData data')
            ResponseReturn = {"messageType": 'error', "messagetext": e}
            return ResponseReturn

    # FUNCTION FOR DIRECT INSERT DATA
    def directinsertData(insertqurrydata):
        connection = conf.connect()
        cursor = connection.cursor()
        sqlDataa = insertqurrydata
        try:
            cursor.execute(sqlDataa)
            connection.commit()
            lastInsertId = cursor.lastrowid
            cursor.close()
            connection.close()
            msg = "success"
            ResponseReturn = {"messageType": 'success', "messagetext": msg, 'lastInsertId': lastInsertId}
            return ResponseReturn
        except (pymysql.Error, pymysql.Warning) as e:
            logger.exception('pymysql.Error, pymysql.Warning in fetching data')
            ResponseReturn = {"messageType": 'error', "messagetext": e, 'lastInsertId': '0'}
            return ResponseReturn


# Get List of FCMToken By IN_ODI01/027
def FCMMessageSend(LicKey, UserType, Title, Message):
    now = datetime.now()
    CreatedDate = now.strftime('%Y-%m-%d %H:%M:%S')
    UserType, Title, Message = UserType.strip(), Title.strip(), Message.strip()
    if UserType == 'user' or UserType == 'admin':
        QsFCMTokenSession = "SELECT FCMTokenNo,EmpId,UserType FROM FCMTokenSession  WHERE LicKey ='" + LicKey + "' and UserType='" + UserType + "' and IsActive='1' and Isdelete='0'"
    else:
        QsFCMTokenSession = "SELECT FCMTokenNo,EmpId,UserType FROM FCMTokenSession  WHERE LicKey ='" + LicKey + "' and IsActive='1' and Isdelete='0'"
    RsFCMTokenSession = DB.selectAllData(QsFCMTokenSession)
    if len(RsFCMTokenSession) > 0:
        FCMTokens = []
        for i in range(len(RsFCMTokenSession)):
            SingleFCMToken = str(RsFCMTokenSession[i]['FCMTokenNo'])
            UserType = str(RsFCMTokenSession[i]['UserType'])
            EmpId = str(RsFCMTokenSession[i]['EmpId'])
            # Add Notification to DB
            values = {'LicKey': LicKey, 'EmpId': EmpId, 'UserType': UserType, 'Message': Message, 'IsActive': '1',
                      'IsDelete': '0', 'CreatedDate': CreatedDate, 'UpdatedDate': CreatedDate}
            insertResult = DB.insertData("Notifications", values)
            FCMTokens.append(SingleFCMToken)
        fcm.sendPush(Title, Message, FCMTokens)
    return True


class HTML2PDF(FPDF, HTMLMixin):
    pass


class CREATEPDF():
    # By IN/ODI01/027
    def employeesList(RsEmployeeList):
        pdf = HTML2PDF()
        LicKey = RsEmployeeList[1]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'Employee_List_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="100%">"""
        table += """<thead><tr><th colspan="5">Employee List</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="5%" style="text-weight:bold;">#</th>
            <th align="left" width="17%" style="text-weight:bold;">Employee Id</th>
            <th align="left" width="30%" style="text-weight:bold;">Name</th>
            <th align="left" width="33%" style="text-weight:bold;">Email ID</th>
            <th align="left" width="15%" style="text-weight:bold;">Mobile No</th>
            </tr>"""
        # <th width="20%" style="text-weight:bold;">Location</th>
        # <td width="10%">Created Date</td>
        table += """<tbody>"""
        for i in range(len(RsEmployeeList)):
            slNo = str(i + 1)
            EmpId = str(RsEmployeeList[i]['EmpId'])
            EmpName = str(RsEmployeeList[i]['EmpName'])
            LocationName = str(RsEmployeeList[i]['LocationName'])
            EmailId = str(RsEmployeeList[i]['EmailId'])
            MobileNo = str(RsEmployeeList[i]['MobileNo'])
            CreatedDate = RsEmployeeList[i]['CreatedDate2']
            table += """<tr><td width="5%">""" + str(slNo) + """</td>
                <td width="17%">""" + EmpId + """</td>
                <td width="30%">""" + EmpName + """</td>
                <td width="33%">""" + EmailId + """</td>
                <td width="15%">""" + MobileNo + """</td>
                </tr>"""
            # <td width="20%">"""+LocationName+"""</td>
            # <td width="10%">"""+CreatedDate+"""</td>
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName

    # By IN/ODI01/053
    def shiftList(RsShiftList):
        pdf = HTML2PDF()
        LicKey = RsShiftList[1]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'Shift_Setting_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="80%">"""
        table += """<thead><tr><th colspan="5">Shift Setting</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="5%" style="text-weight:bold;">#</th>
            <th align="left" width="17%" style="text-weight:bold;">Shift Name</th>
            <th align="left" width="20%" style="text-weight:bold;">Shift Start Time</th>
            <th align="left" width="20%" style="text-weight:bold;">Shift End Time</th>
            <th align="left" width="20%" style="text-weight:bold;">Shift Length</th>
            <th align="left" width="20%" style="text-weight:bold;">Shift Margin</th>
            <th align="left" width="20%" style="text-weight:bold;">Location</th>
            </tr>"""
        table += """<tbody>"""
        for i in range(len(RsShiftList)):
            slNo = str(i + 1)
            ShiftName = str(RsShiftList[i]['ShiftName'])
            StartTime = str(RsShiftList[i]['StartTime'])
            EndTime = str(RsShiftList[i]['EndTime'])
            ShiftLength = str(RsShiftList[i]['ShiftLength'])
            ShiftMargin = str(RsShiftList[i]['ShiftMargin'])
            LocationName = str(RsShiftList[i]['LocationName'])
            table += """<tr><td width="5%">""" + str(slNo) + """</td>
                <td width="17%">""" + ShiftName + """</td>
                <td width="20%">""" + StartTime + """</td>
                <td width="20%">""" + EndTime + """</td>
                <td width="20%">""" + ShiftLength + """</td>
                <td width="20%">""" + ShiftMargin + """</td>
                <td width="20%">""" + LocationName + """</td>
                </tr>"""
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName

    # By IN/ODI01/053
    def shiftMappingList(RsshiftMappingList):
        pdf = HTML2PDF()
        LicKey = RsshiftMappingList[1]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'Employee_Shift_Mapping_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="80%">"""
        table += """<thead><tr><th colspan="5">Employee Shift Mapping</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="6%" style="text-weight:bold;">#</th>
            <th align="left" width="17%" style="text-weight:bold;">Employee Id</th>
            <th align="left" width="20%" style="text-weight:bold;">Employee Name</th>
            <th align="left" width="20%" style="text-weight:bold;">Location</th>
            <th align="left" width="20%" style="text-weight:bold;">Shift Name</th>
            <th align="left" width="20%" style="text-weight:bold;">Start Time</th>
            <th align="left" width="20%" style="text-weight:bold;">End Time</th>
            </tr>"""
        table += """<tbody>"""
        for i in range(len(RsshiftMappingList)):
            slNo = str(i + 1)
            EmpId = str(RsshiftMappingList[i]['EmpId'])
            EmpName = str(RsshiftMappingList[i]['EmpName'])
            LocationName = str(RsshiftMappingList[i]['LocationName'])
            ShiftName = str(RsshiftMappingList[i]['ShiftName'])
            StartTime = str(RsshiftMappingList[i]['StartTime'])
            EndTime = str(RsshiftMappingList[i]['EndTime'])
            table += """<tr><td width="5%">""" + str(slNo) + """</td>
                <td width="17%">""" + EmpId + """</td>
                <td width="20%">""" + EmpName + """</td>
                <td width="20%">""" + LocationName + """</td>
                <td width="20%">""" + ShiftName + """</td>
                <td width="20%">""" + StartTime + """</td>
                <td width="20%">""" + EndTime + """</td>
                </tr>"""
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName

    # By IN/ODI01/053
    def userList(RsUserList):
        pdf = HTML2PDF()
        LicKey = RsUserList[1]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'User_Authentication_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="80%">"""
        table += """<thead><tr><th colspan="5">User Authentication</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="6%" style="text-weight:bold;">#</th>
            <th align="left" width="17%" style="text-weight:bold;">Location</th>
            <th align="left" width="20%" style="text-weight:bold;">Employee Id</th>
            <th align="left" width="40%" style="text-weight:bold;">User Name</th>
            <th align="left" width="20%" style="text-weight:bold;">Created Date</th>
            </tr>"""
        table += """<tbody>"""
        for i in range(len(RsUserList)):
            slNo = str(i + 1)
            LocationName = str(RsUserList[i]['LocationName'])
            EmpId = str(RsUserList[i]['EmpId'])
            UserName = str(RsUserList[i]['UserName'])
            CreatedDate = str(RsUserList[i]['CreatedDate'])
            table += """<tr><td width="5%">""" + str(slNo) + """</td>
                <td width="17%">""" + LocationName + """</td>
                <td width="20%">""" + EmpId + """</td>
                <td width="40%">""" + UserName + """</td>
                <td width="20%">""" + CreatedDate + """</td>
                </tr>"""
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName

    # By IN/ODI01/053
    def recentReport(recentActivityData):
        pdf = HTML2PDF()
        LicKey = recentActivityData[0]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'All_Activity_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="80%">"""
        table += """<thead><tr><th colspan="5">All Activity</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="6%" style="text-weight:bold;">#</th>
            <th align="left" width="20%" style="text-weight:bold;">Employee Id</th>
            <th align="left" width="25%" style="text-weight:bold;">Name</th>
            <th align="left" width="40%" style="text-weight:bold;">Seen Date</th>
            <th align="left" width="20%" style="text-weight:bold;">Camera Seen</th>
            </tr>"""
        table += """<tbody>"""
        for i in range(len(recentActivityData)):
            slNo = str(i + 1)
            EmpId = str(recentActivityData[i]['EmpId'])
            EmpName = str(recentActivityData[i]['EmpName'])
            ADTime = str(recentActivityData[i]['ADTime'])
            Source = str(recentActivityData[i]['Source'])
            table += """<tr><td width="5%">""" + str(slNo) + """</td>
                <td width="20%">""" + EmpId + """</td>
                <td width="25%">""" + EmpName + """</td>
                <td width="40%">""" + ADTime + """</td>
                <td width="20%">""" + Source + """</td>
                </tr>"""
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName

    # By IN/ODI01/053
    def dailyReport(DailyActivityData):
        pdf = HTML2PDF()
        LicKey = DailyActivityData[0]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'Daily_Activity_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="80%">"""
        table += """<thead><tr><th colspan="5">Daily Activity</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="5%" style="text-weight:bold;">#</th>
            <th align="left" width="18%" style="text-weight:bold;">Employee Id</th>
            <th align="left" width="10%" style="text-weight:bold;">Name</th>
            <th align="left" width="17%" style="text-weight:bold;">Location</th>
            <th align="left" width="23%" style="text-weight:bold;">First Seen</th>
            <th align="left" width="25%" style="text-weight:bold;">Last Seen</th>
            <th align="left" width="20%" style="text-weight:bold;">Shift</th>
            <th align="left" width="20%" style="text-weight:bold;">Status</th>
            </tr>"""
        table += """<tbody>"""
        for i in range(len(DailyActivityData)):
            slNo = str(i + 1)
            EmpId = str(DailyActivityData[i]['EmpId'])
            EmpName = str(DailyActivityData[i]['EmpName'])
            LocationName = str(DailyActivityData[i]['LocationName'])
            FirstSeen = str(DailyActivityData[i]['FirstSeen'])
            LastSeen = str(DailyActivityData[i]['LastSeen'])
            ShiftName = str(DailyActivityData[i]['ShiftName'])
            Status = str(DailyActivityData[i]['Status'])
            table += """<tr><td width="5%">""" + str(slNo) + """</td>
                <td width="18%">""" + EmpId + """</td>
                <td width="10%">""" + EmpName + """</td>
                <td width="17%">""" + LocationName + """</td>
                <td width="23%">""" + FirstSeen + """</td>
                <td width="25%">""" + LastSeen + """</td>
                <td width="20%">""" + ShiftName + """</td>
                <td width="20%">""" + Status + """</td>
                </tr>"""
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName

    # By IN/ODI01/052
    def locationList(RsLocationList):
        pdf = HTML2PDF()
        LicKey = RsLocationList[1]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'Location_Details_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="100%">"""
        table += """<thead><tr><th colspan="6">Location Details</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="10%" style="text-weight:bold;">Sl No.</th>
            <th align="left" width="25%" style="text-weight:bold;">Location Name</th>
            <th align="left" width="20%" style="text-weight:bold;">System Info</th>
            <th align="left" width="20%" style="text-weight:bold;">No Of Employees</th>
            <th align="left" width="15%" style="text-weight:bold;">Created Date </th>
            <th align="left" width="10%" style="text-weight:bold;">Status</th>
            </tr>"""
        table += """<tbody>"""
        for i in range(len(RsLocationList)):
            slNo = str(i + 1)
            LocationName = str(RsLocationList[i]['LocationName'])
            SystemInfo = str(RsLocationList[i]['SystemInfo'])
            NO_OF_EMPLOYEES = str(RsLocationList[i]['NO_OF_EMPLOYEES'])
            CreatedDate = str(RsLocationList[i]['CreatedDate'])
            Status = str(RsLocationList[i]['Status'])
            table += """<tr><td width="10%">""" + str(slNo) + """</td>
                <td width="25%">""" + LocationName + """</td>
                <td width="20%">""" + SystemInfo + """</td>
                <td width="20%">""" + NO_OF_EMPLOYEES + """</td>
                <td width="15%">""" + CreatedDate + """</td>
                <td width="10%">""" + Status + """</td>
                </tr>"""
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName

    # By IN/ODI01/052
    def compoffList(RsCompoffList):
        pdf = HTML2PDF()
        LicKey = RsCompoffList[1]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'Compoff_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="100%">"""
        table += """<thead><tr><th colspan="6">Off Management</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="10%" style="text-weight:bold;">Sl No.</th>
            <th align="left" width="20%" style="text-weight:bold;">Employee ID </th>
            <th align="left" width="30%" style="text-weight:bold;">Employee Name</th>
            <th align="left" width="15%" style="text-weight:bold;">Location</th>
            <th align="left" width="15%" style="text-weight:bold;">OffDate </th>
            <th align="left" width="10%" style="text-weight:bold;">Status</th>
            </tr>"""
        table += """<tbody>"""
        for i in range(len(RsCompoffList)):
            slNo = str(i + 1)
            EmpId = str(RsCompoffList[i]['EmpId'])
            EmpName = str(RsCompoffList[i]['EmpName'])
            LocationName = str(RsCompoffList[i]['LocationName'])
            OffDate = str(RsCompoffList[i]['OffDate'])
            Status = str(RsCompoffList[i]['Status'])
            table += """<tr><td width="10%">""" + str(slNo) + """</td>
                <td width="20%">""" + EmpId + """</td>
                <td width="30%" >""" + EmpName + """</td>
                <td width="15%">""" + LocationName + """</td>
                <td width="15%">""" + OffDate + """</td>
                <td width="10%">""" + Status + """</td>
                </tr>"""
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName

    # By IN/ODI01/052
    def leaveList(RsLeaveList):
        pdf = HTML2PDF()
        LicKey = RsLeaveList[1]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'Leave_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="100%">"""
        table += """<thead><tr><th colspan="6">Leave Management</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="5%" style="text-weight:bold;">#</th>
            <th align="left" width="25%" style="text-weight:bold;">Employee Name</th>
            <th align="left" width="15%" style="text-weight:bold;">Location</th>
            <th align="left" width="15%" style="text-weight:bold;">Leave Date</th>
            <th align="left" width="12%" style="text-weight:bold;">Leave Type </th>
            <th align="left" width="18%" style="text-weight:bold;">Leave Purpose </th>
            <th align="left" width="10%" style="text-weight:bold;">Status</th>
            </tr>"""
        table += """<tbody>"""
        for i in range(len(RsLeaveList)):
            slNo = str(i + 1)
            EmpName = str(RsLeaveList[i]['EmpName'])
            LocationName = str(RsLeaveList[i]['LocationName'])
            LeaveDate = str(RsLeaveList[i]['LeaveDate'])
            LeaveType = str(RsLeaveList[i]['LeaveType'])
            LeavePurpose = str(RsLeaveList[i]['LeavePurpose'])
            Status = str(RsLeaveList[i]['Status'])
            table += """<tr><td width="5%">""" + str(slNo) + """</td>
                <td width="25%">""" + EmpName + """</td>
                <td width="15%" >""" + LocationName + """</td>
                <td width="15%">""" + LeaveDate + """</td>
                <td width="12%">""" + LeaveType + """</td>
                <td width="18%">""" + LeavePurpose + """</td>
                <td width="10%">""" + Status + """</td>
                </tr>"""
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName

    # By IN/ODI01/052
    def holidayList(RsHolidayList):
        pdf = HTML2PDF()
        LicKey = RsHolidayList[1]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'Holiday_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="100%">"""
        table += """<thead><tr><th colspan="6">Holiday Setting</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="10%" style="text-weight:bold;">Sl No.</th>
            <th align="left" width="25%" style="text-weight:bold;">Location</th>
            <th align="left" width="20%" style="text-weight:bold;">Date</th>
            <th align="left" width="30%" style="text-weight:bold;">Holiday</th>
            <th align="left" width="15%" style="text-weight:bold;">Status</th>
            </tr>"""
        table += """<tbody>"""
        for i in range(len(RsHolidayList)):
            slNo = str(i + 1)
            LocationName = str(RsHolidayList[i]['LocationName'])
            SetDate = str(RsHolidayList[i]['SetDate'])
            Holiday = str(RsHolidayList[i]['Holiday'])
            Status = str(RsHolidayList[i]['Status'])
            table += """<tr><td width="10%">""" + str(slNo) + """</td>
                <td width="25%">""" + LocationName + """</td>
                <td width="20%" >""" + SetDate + """</td>
                <td width="30%">""" + Holiday + """</td>
                <td width="15%">""" + Status + """</td>
                </tr>"""
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName

    # By IN/ODI01/052
    def geofenceList(RsGeofenceList):
        pdf = HTML2PDF()
        LicKey = RsGeofenceList[1]['LicKey']
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
        fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/PDF"
        if not os.path.exists(fileFolderPath):
            os.makedirs(fileFolderPath)
        uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
        fileName = 'Geofence_' + tdayTimeStamp + '_' + uniqueid + '.pdf'
        fullFileDirName = fileFolderPath + '/' + fileName
        table = """<table border="0" align="center" width="100%">"""
        table += """<thead><tr><th colspan="5">Airface | Geofence</th></tr></thead>"""
        table += """<tbody>
            <tr><th align="left" width="10%" style="text-weight:bold;">Sl No.</th>
            <th align="left" width="20%" style="text-weight:bold;">Area Name</th>
            <th align="left" width="40%" style="text-weight:bold;">Latitude & Longitude</th>
            <th align="left" width="15%" style="text-weight:bold;">No Of Users</th>
            <th align="left" width="20%" style="text-weight:bold;">Created Date </th>
            </tr>"""
        table += """<tbody>"""
        for i in range(len(RsGeofenceList)):
            slNo = str(i + 1)
            AreaName = str(RsGeofenceList[i]['AreaName'])
            Latlang = str(RsGeofenceList[i]['Latlang'])
            NoOfUsers = str(RsGeofenceList[i]['NoOfUsers'])
            CreatedDate = str(RsGeofenceList[i]['CreatedDate'])
            wrapper = textwrap.TextWrapper(width=50)
            dedented_text = textwrap.dedent(text=Latlang)
            original = wrapper.fill(text=dedented_text)
            shortened = textwrap.shorten(text=original, width=50)
            short_Latlang = wrapper.fill(text=shortened)
            table += """<tr><td width="10%">""" + str(slNo) + """</td>
                <td width="20%">""" + AreaName + """</td>
                <td width="40%">""" + short_Latlang + """</td>
                <td width="15%">""" + NoOfUsers + """</td>
                <td width="20%">""" + CreatedDate + """</td>
                </tr>"""
        table += """</tbody>
        </table>"""
        pdf.add_page()
        pdf.write_html(table)
        pdf.output(fullFileDirName)
        return fullFileDirName
    # FUNCTION FOR CHECKING FOR  EMAIL VALIDATION


# regexemail = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
regexemail = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w'


def checkemail(email):
    if (re.search(regexemail, email)):
        return True
    else:
        return False


# MOBILE VALIDATION
def checkmobile(s):
    # 1) Begins with 0 or 91
    # 2) Then contains 7 or 8 or 9.
    # 3) Then contains 9 digits
    Pattern = re.compile("(0/91)?[1-9][0-9]{9}")
    return Pattern.match(s)


# Monthly Activity Clone
def monthlyactivityclone(LicKey, AttendanceMonth, AttendanceYear):
    curDate = datetime.today().date()
    QsEmployeeList = "SELECT EmpId FROM EmployeeRegistration WHERE IsDelete = 0 AND IsActive = 1 and LicKey='" + LicKey + "' "
    RsEmployeeList = DB.selectAllData(QsEmployeeList)
    for i in range(len(RsEmployeeList)):
        updatevalueArray = ""
        getEmpId = RsEmployeeList[i]['EmpId']
        QsActivityDetailscheck = "SELECT * from MonthlyActivity where EmpId='" + getEmpId + "' and  AttendanceMonth = '" + AttendanceMonth + "' and  AttendanceYear='" + AttendanceYear + "' AND LicKey = '" + LicKey + "' GROUP BY EmpId ORDER BY EmpId ASC "
        RsActivityDetailscheck = DB.selectAllData(QsActivityDetailscheck)
        QsActivityDetails = "SELECT Extract(Day from ADDate) As CurentDay, EmpId, MIN(ADTime) AS FIRSTSEEN,MAX(ADTime) AS LASTSEEN from ActivityDetails where EmpId = '" + getEmpId + "' AND  Extract(Month from ADDate)='" + AttendanceMonth + "' and Extract(Year from ADDate)='" + AttendanceYear + "' AND LicKey = '" + LicKey + "' GROUP BY ADDate ORDER BY ADDate ASC "
        RsActivityDetails = DB.selectAllData(QsActivityDetails)
        for j in range(len(RsActivityDetails)):
            FIRSTSEEN = RsActivityDetails[j]['FIRSTSEEN']
            LASTSEEN = RsActivityDetails[j]['LASTSEEN']
            FIRSTSEENTime = date_time_obj = datetime.strptime(str(FIRSTSEEN), '%Y-%m-%d %H:%M:%S')
            LASTSEENTime = date_time_obj = datetime.strptime(str(LASTSEEN), '%Y-%m-%d %H:%M:%S')
            firstAtttime = datetime.strftime(FIRSTSEENTime, "%H:%M:%S")
            lastAtttime = datetime.strftime(LASTSEENTime, "%H:%M:%S")
            if updatevalueArray == '':
                dayInValue = "'D" + str(RsActivityDetails[j]['CurentDay']) + "_IN' : '" + str(
                    firstAtttime) + "'," + "'D" + str(RsActivityDetails[j]['CurentDay']) + "_OUT' : '" + str(
                    lastAtttime) + "'"
            else:
                dayInValue = ",'D" + str(RsActivityDetails[j]['CurentDay']) + "_IN' : '" + str(
                    firstAtttime) + "'," + "'D" + str(RsActivityDetails[j]['CurentDay']) + "_OUT' : '" + str(
                    lastAtttime) + "'"
            updatevalueArray = updatevalueArray + dayInValue
        singleValueArray = "{" + "'EmpId': '" + getEmpId + "', 'LicKey': '" + LicKey + "', 'attendancemonth': '" + AttendanceMonth + "', 'attendanceyear': '" + AttendanceYear + "'," + updatevalueArray + "}"
        my_dict = ast.literal_eval(singleValueArray)
        DB.insertData('MonthlyActivity', my_dict)
        if len(RsActivityDetailscheck) > 0:
            DeleteMonthlyActivityId = RsActivityDetailscheck[0]['MonthlyActivityId']
            querry = "delete from  MonthlyActivity where MonthlyActivityId='" + str(
                DeleteMonthlyActivityId) + "' and LicKey='" + LicKey + "' and EmpId='" + getEmpId + "'"
            DB.selectAllData(querry)
    return "true"


def insertNewEmployee(LicKey, EmpId, EmpName, EmailId, MobileNo, BaseLocationId):
    IsEnrolled = IsDelete = IsAdmin = IsZohoEmp = "0"
    IsActive = "1"
    CreatedDate = datetime.now().strftime('%Y-%m-%d')
    error = 0
    messageCode, messageText = [], []
    ResponseDataForEmailId = DB.retrieveAllData("EmployeeRegistration", "",
                                                "`LicKey`='" + LicKey + "' AND `EmailId`='" + EmailId + "'", "")
    ResponseDataForEmpId = DB.retrieveAllData("EmployeeRegistration", "",
                                              "`LicKey`='" + LicKey + "' AND `EmpId`='" + EmpId + "'", "")
    validateemailcheck = checkemail(EmailId)
    if not validateemailcheck:
        error = error + 1
        messageCode.append(4)
        messageText.append('Invalid Email Id !')
    validatecheckmobile = checkmobile(MobileNo)
    if not validatecheckmobile:
        error = error + 1
        messageCode.append(3)
        messageText.append('Invalid Mobile No !')
    if len(ResponseDataForEmailId) > 0:
        error = error + 1
        messageCode.append(1)
        messageText.append('Email ID already exists !')
    if len(ResponseDataForEmpId) > 0:
        error = error + 1
        messageCode.append(2)
        messageText.append('Employee ID already exists !')
    message = messageText
    msgstatus = messageCode
    if error > 0:
        RequestData = {'category': "0", 'message': message, 'message-code': msgstatus, 'EmpId': EmpId,
                       'EmpName': EmpName, 'EmailId': EmailId, 'MobileNo': MobileNo, 'BaseLocationId': BaseLocationId}
        response = {'category': "0", 'message': message, 'RequestData': RequestData}
    else:
        values = {'LicKey': LicKey, 'BaseLocationId': BaseLocationId, 'EmpId': EmpId, 'EmpName': EmpName,
                  'EmailId': EmailId, 'MobileNo': MobileNo, 'IsEnrolled': IsEnrolled, 'IsActive': IsActive,
                  'IsDelete': IsDelete, 'IsAdmin': IsAdmin, 'IsZohoEmp': IsZohoEmp, 'CreatedDate': CreatedDate,
                  'UpdatedDate': CreatedDate}
        showmessage = DB.insertData("EmployeeRegistration", values)
        if showmessage['messageType'] == 'success':
            RequestData = {'category': "1", 'message': "Employee added successfully.", 'EmpId': EmpId,
                           'EmpName': EmpName, 'EmailId': EmailId, 'MobileNo': MobileNo,
                           'BaseLocationId': BaseLocationId}
            response = {'category': "1", 'message': "Employee added successfully.",
                        'ResponseData': showmessage['lastInsertId'], 'RequestData': RequestData}
        else:
            RequestData = {'category': "0", 'message': "Sorry ! something Error in DB. try it again.", 'EmpId': EmpId,
                           'EmpName': EmpName, 'EmailId': EmailId, 'MobileNo': MobileNo,
                           'BaseLocationId': BaseLocationId}
            response = {'category': category, 'message': "Sorry ! something Error in DB. try it again.",
                        'RequestData': RequestData}
    return response


# CLASS 'authVerifyUser' IS DEFINED HERE FOR  AUTHENTICATE VERIFICATION
class authVerifyUser():
    def authServices():
        LicKey = ''
        if 'LicKey' in request.headers:
            LicKey = request.headers['LicKey']
        if LicKey == '':
            response = {'category': "0", 'authenticate': "False", 'message': "Sorry! all credentials are mandatory."}
        else:
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')
            ResponseData = DB.retrieveAllData("OrganizationDetails", "", "LicKey='" + LicKey + "'", "")
            length = int(len(ResponseData))
            is_expired = is_account_avail = 0
            if length > 0:
                response = {'category': "1", 'authenticate': "True", 'is_expired': is_expired,
                            'message': "All credentials available", 'LicKey': LicKey}
                is_account_avail = 1
                ExpiredDate = str(ResponseData[0]['ExpiredDate'])
                msg = 'Your license expired on (' + ExpiredDate + ')'
                if ExpiredDate < today:
                    response = {'category': "0", 'authenticate': "False", 'is_expired': 1, 'LicKey': LicKey,
                                'message': "Your license has expired.  Please contact our support representative."}
            else:
                response = {'category': "0", 'authenticate': "False", 'is_expired': 1, 'LicKey': LicKey,
                            'message': "Please contact our support representative to verify your credential."}

        return response

    # FUNCTION 'authLogin' IS DEFINED HERE FOR  AUTHENTICATE VERIFICATION IN LOGIN API
    def authLogin():
        OrganizationEmailId = OrganizationPassword = UserType = ''
        if 'OrganizationEmailId' in request.headers and 'OrganizationPassword' in request.headers and 'UserType' in request.headers:
            OrganizationEmailId, OrganizationPassword, UserType = request.headers['OrganizationEmailId'], \
                                                                  request.headers['OrganizationPassword'], \
                                                                  request.headers['UserType']
        if OrganizationEmailId == '' and OrganizationPassword == '' and UserType == '':
            response = {'category': "0", 'authenticate': "False", 'message': "All credentials are mandatory"}
        else:
            if UserType == 'admin':
                varcheckLicKeyIsValidate = checkLicKey(OrganizationEmailId, OrganizationPassword)
                if varcheckLicKeyIsValidate['category'] == '1':
                    if varcheckLicKeyIsValidate['is_expired'] == 1:
                        response = {'category': "0", 'authenticate': "False",
                                    'message': "Your license has expired.  Please contact our support representative."}
                    else:
                        response = {'category': "1", 'authenticate': "True",
                                    'message': "All credentials are available."}
                else:
                    response = {'category': "0", 'authenticate': "False",
                                'message': "Please contact our support representative to verify your credential."}
            else:
                UserResponseData = DB.retrieveAllData("UserLogin", "", "UserName='" + OrganizationEmailId + "'", "")
                userlength = int(len(UserResponseData))
                if userlength > 0:
                    LicKey = UserResponseData[0]['LicKey']
                    now = datetime.now()
                    today = now.strftime('%Y-%m-%d')
                    ResponseData = DB.retrieveAllData("OrganizationDetails", "", "LicKey='" + LicKey + "'", "")
                    length = int(len(ResponseData))
                    is_expired = is_account_avail = 0
                    if length > 0:
                        response = {'category': "1", 'authenticate': "True", 'is_expired': is_expired,
                                    'message': "All credentials available", 'LicKey': LicKey}
                        is_account_avail = 1
                        ExpiredDate = str(ResponseData[0]['ExpiredDate'])
                        msg = 'Your license expired on (' + ExpiredDate + ')'
                        if ExpiredDate < today:
                            response = {'category': "0", 'authenticate': "False", 'is_expired': 1, 'LicKey': LicKey,
                                        'message': "Your license has expired.  Please contact our support representative."}
                    else:
                        response = {'category': "0", 'authenticate': "False", 'is_expired': 1, 'LicKey': LicKey,
                                    'message': "Please contact our support representative to verify your credential."}
                else:
                    response = {'category': "0", 'authenticate': "False",
                                'message': "Please contact our support representative to verify your credential."}  # 'is_expired': 1,
        return response

    # FUNCTION 'checkAuthenticate' IS DEFINED HERE FOR  AUTHENTICATE VERIFICATION AND CALLED IN EVERY API AFTER ONCE LOGIN IS DONE
    def checkAuthenticate():
        LicKey = ''
        AccessToken = ''
        if 'LicKey' in request.headers and 'AccessToken' in request.headers:
            LicKey = request.headers['LicKey']
            AccessToken = request.headers['AccessToken']
        if LicKey == '' and AccessToken == '':
            response = {'category': "0", 'authenticate': "False",
                        'message': "Sorry! all credential header are mandatory."}
        else:
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')
            ResponseData = DB.retrieveAllData("OrganizationDetails", "", "LicKey='" + LicKey + "'", "")
            length = int(len(ResponseData))
            is_expired = is_account_avail = 0
            if length > 0:
                response = {'category': "1", 'authenticate': "True", 'is_expired': is_expired,
                            'message': "All credentials available", 'LicKey': LicKey}
                is_account_avail = 1
                ExpiredDate = str(ResponseData[0]['ExpiredDate'])
                msg = 'Your license expired on (' + ExpiredDate + ')'
                if ExpiredDate < today:
                    response = {'category': "0", 'authenticate': "False", 'is_expired': 1, 'LicKey': LicKey,
                                'message': "Your license has expired.  Please contact our support representative."}
                else:
                    ResponseData = DB.retrieveAllData("ApiUserSession", "",
                                                      "`LicKey`= '" + LicKey + "' AND `AccessToken`= '" + AccessToken + "' and `IsExpire`= '0'",
                                                      "")
                    if len(ResponseData) > 0:
                        userdata = {'AccessToken': AccessToken, 'RequestType': ResponseData[0]['RequestType'],
                                    'UserType': ResponseData[0]['UserType']}
                        response = {'category': "1", 'LicKey': LicKey, 'authenticate': "True", 'userdata': userdata,
                                    'message': "Authorized Access Success."}
                    else:
                        response = {'category': "0", 'authenticate': "False", 'message': "This is not a valid user."}
            else:
                response = {'category': "0", 'authenticate': "False", 'is_expired': 1, 'LicKey': LicKey,
                            'message': "Please contact our support representative to verify your credential."}
        return response


# API STARTS HERE
class Welcomedash(Resource):
    def get(self):
        return {'message': 'Welcome to our API dashboard.'}

    def post(self):
        name = request.form['name']
        return {'Hi--': name + ' Welcome to our API dashboard.'}, 201


# API FOR LOGIN
# @cross_origin()
class RcAPILogin(Resource):
    def post(self):
        VURS = authVerifyUser.authLogin()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            OrganizationEmailId = ''
            OrganizationPassword = ''
            UserType = ''
            FCMTokenNo = ''
            AndroidId = ''
            if 'OrganizationEmailId' in request.headers and 'OrganizationPassword' in request.headers and 'UserType' in request.headers:  # 'LicKey' in request.headers
                OrganizationEmailId = request.headers['OrganizationEmailId']
                OrganizationPassword = request.headers['OrganizationPassword']
                UserType = request.headers['UserType']
            if 'FCMTokenNo' in request.headers:
                FCMTokenNo = request.headers['FCMTokenNo']
            if 'AndroidId' in request.headers:
                AndroidId = request.headers['AndroidId']
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')
            if (OrganizationEmailId.isspace() == True or OrganizationEmailId == '') or (
                    OrganizationPassword.isspace() == True or OrganizationPassword == '') or (
                    UserType.isspace() == True or UserType == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                if UserType == 'admin':
                    md5password = hashlib.md5()
                    md5password.update(OrganizationPassword.encode("utf-8"))
                    tablename = "OrganizationDetails"
                    order = 'OrganizationEmailId DESC'
                    wherecondition1 = " OrganizationEmailId='" + OrganizationEmailId + "'"
                    fields1 = "LicKey"
                    ResponseData = DB.retrieveAllData(tablename, fields1, wherecondition1, order)
                    if len(ResponseData):
                        LicKey = ResponseData[0]['LicKey']

                        wherecondition = "LicKey='" + LicKey + "' AND OrganizationEmailId='" + OrganizationEmailId + "' and IsActive=1 and IsDelete=0"
                        fields = ""
                        OrganizationDetails = DB.retrieveAllData(tablename, fields, wherecondition, order)
                        if len(OrganizationDetails) > 0:
                            encryptionHashpass = md5password.hexdigest()

                            if OrganizationDetails[0]['OrganizationPassword'] == encryptionHashpass:
                                tablename = "ApiUserSession"
                                wherecondition = "UserType = '" + UserType + "' and LicKey = '" + LicKey + "' and MasterID = '" + str(
                                    OrganizationDetails[0]['OrganizationDetailsId']) + "'"
                                fields = ""
                                order = ""
                                apiUserSessionData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                                now = datetime.now()
                                todaydatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                                RequestType = 'API'
                                MasterId = str(OrganizationDetails[0]['OrganizationDetailsId'])
                                UniqueId = ''.join(random.choice(string.ascii_lowercase) for i in range(12))
                                AccessToken = UniqueId
                                IsExpire = '0'
                                CreatedDate = todaydatetime
                                tablename = 'ApiUserSession'
                                if len(FCMTokenNo) > 0:
                                    CheckFCMQuerry1 = "select * from FCMTokenSession where AndroidId='" + str(
                                        AndroidId) + "'"
                                    FCMTokenData1 = DB.selectAllData(CheckFCMQuerry1)
                                    if len(FCMTokenData1) > 0:
                                        FCMTokenSessionId = FCMTokenData1[0]['FCMTokenSessionId']
                                        UpdateFCMTokenQuerry = "update FCMTokenSession set FCMTokenNo='" + FCMTokenNo + "',LicKey='" + LicKey + "' ,UserName='" + OrganizationEmailId + "',EmpId='Organization Admin',UserType='" + UserType + "',IsActive=1,IsDelete=0,UpdatedDate='" + CreatedDate + "' where AndroidId='" + str(
                                            AndroidId) + "'"
                                        DB.selectAllData(UpdateFCMTokenQuerry)
                                        FCMTokenData = FCMTokenNo
                                        AndroidId = AndroidId
                                    else:
                                        values = {'AndroidId': str(AndroidId), 'FCMTokenNo': str(FCMTokenNo),
                                                  'LicKey': LicKey,
                                                  'UserName': OrganizationEmailId, 'UserType': UserType,
                                                  'IsActive': '1', 'IsDelete': '0', 'CreatedDate': CreatedDate,
                                                  'UpdatedDate': CreatedDate, 'EmpId': 'Organization Admin'}
                                        lastinsertid = DB.insertData('FCMTokenSession', values)
                                        # CheckFCMQuerry = "select * from FCMTokenSession where  UserName='" + OrganizationEmailId + "' and LicKey='" + LicKey + "'"
                                        # FCMTokenData = DB.selectAllData(CheckFCMQuerry)
                                        FCMTokenData = FCMTokenNo
                                        AndroidId = AndroidId
                                else:
                                    FCMTokenData = 'NULL'
                                    AndroidId = 'NULL'
                                if len(apiUserSessionData):
                                    LicKey = OrganizationDetails[0]['LicKey']
                                    OrganizationName = OrganizationDetails[0]['OrganizationName']
                                    OrganizationEmailId = OrganizationDetails[0]['OrganizationEmailId']
                                    OrganizationMobileNo = OrganizationDetails[0]['OrganizationMobileNo']
                                    AccessToken = apiUserSessionData[0]['AccessToken']
                                    ProfileImg = OrganizationDetails[0]['ProfileImg']
                                    AdminImg = OrganizationDetails[0]['AdminImg']
                                    ResponseData = {'LicKey': LicKey, 'OrganizationName': OrganizationName,
                                                    'OrganizationEmailId': OrganizationEmailId,
                                                    'OrganizationMobileNo': OrganizationMobileNo,
                                                    'AccessToken': AccessToken, 'ProfileImg': ProfileImg,
                                                    'AdminImg': AdminImg, 'FCMTokenNo': FCMTokenData,
                                                    'AndroidId': AndroidId}
                                else:
                                    values = {'RequestType': str(RequestType), 'UserType': UserType,
                                              'MasterID': MasterId,
                                              'AccessToken': AccessToken, 'IsExpire': IsExpire,
                                              'CreatedDateTime': CreatedDate, 'LicKey': LicKey}
                                    lastinsertid = DB.insertData(tablename, values)
                                    LicKey = OrganizationDetails[0]['LicKey']
                                    OrganizationName = OrganizationDetails[0]['OrganizationName']
                                    OrganizationEmailId = OrganizationDetails[0]['OrganizationEmailId']
                                    OrganizationMobileNo = OrganizationDetails[0]['OrganizationMobileNo']
                                    ProfileImg = OrganizationDetails[0]['ProfileImg']
                                    AdminImg = OrganizationDetails[0]['AdminImg']
                                    AccessToken = apiUserSessionData[0]['AccessToken']
                                    ResponseData = {'LicKey': LicKey, 'OrganizationName': OrganizationName,
                                                    'OrganizationEmailId': OrganizationEmailId,
                                                    'OrganizationMobileNo': OrganizationMobileNo,
                                                    'AccessToken': AccessToken, 'ProfileImg': ProfileImg,
                                                    'AdminImg': AdminImg}
                                category = "1"
                                message = "Hi " + OrganizationDetails[0][
                                    'OrganizationName'] + ", your login successfull."
                                response = {'category': category, 'message': message, 'ResponseData': ResponseData}
                            else:
                                response = {'category': "0",
                                            'message': "Email ID Or Password Or User Type do not match ! Please try again."}
                        else:
                            response = {'category': "0",
                                        'message': "Email ID Or Password Or User Type do not match ! Please try again."}
                    else:
                        response = {'category': "0", 'message': "Sorry! this module not implement right now."}
                elif UserType == 'user':
                    md5password = hashlib.md5()
                    md5password.update(OrganizationPassword.encode("utf-8"))
                    tablename = "UserLogin"
                    order = 'Username DESC'
                    wherecondition1 = " `Username`='" + OrganizationEmailId + "'"
                    fields1 = "LicKey,BaseLocationId"
                    retriveData = DB.retrieveAllData(tablename, fields1, wherecondition1, order)
                    if len(retriveData):
                        licKey = retriveData[0]['LicKey']
                        BaseLocationId = ''
                        BaseLocationId = retriveData[0]['BaseLocationId']
                        wherecondition = "LicKey='" + licKey + "' AND UserName='" + OrganizationEmailId + "'"
                        fields = ""
                        userDetails = DB.retrieveAllData(tablename, fields, wherecondition, order)
                        if len(userDetails) > 0:
                            # qsEmpRes = "select EmpName,MobileNo,EmailId from EmployeeRegistration where EmailId='" + OrganizationEmailId + "' and EmpId='" + userDetails[0]['EmpId'] + "' and LicKey='"+licKey+"'"
                            qsEmpRes = "select EmpName,MobileNo,EmailId,(select ImagePath from DatasetEncodings where LicKey='" + licKey + "' and EmpId='" + \
                                       userDetails[0][
                                           'EmpId'] + "' and IsActive=1 group by EmpId) As UserProfileImage from EmployeeRegistration where EmailId='" + OrganizationEmailId + "' and EmpId='" + \
                                       userDetails[0]['EmpId'] + "' and LicKey='" + licKey + "'"
                            rsEmpRes = DB.selectAllData(qsEmpRes)
                            empName = rsEmpRes[0]['EmpName']
                            MobileNo = rsEmpRes[0]['MobileNo']
                            EmailId = rsEmpRes[0]['EmailId']
                            UserProfileImage = rsEmpRes[0]['UserProfileImage']
                            empName = str(empName)
                            splitEmpName = empName.split(' ')
                            employeeName = splitEmpName[0]
                            encryptionHashpass = md5password.hexdigest()
                            if userDetails[0]['Password'] == encryptionHashpass:
                                masterId = str(userDetails[0]['UserLoginId'])
                                userName = userDetails[0]['UserName']
                                MarkAttendance = userDetails[0]['MarkAttendance']
                                MarkAttendanceType = userDetails[0]['MarkAttendanceType']
                                querrySession = "select * from ApiUserSession where UserType = '" + UserType + "' and LicKey = '" + licKey + "' and MasterID = '" + str(
                                    userDetails[0]['UserLoginId']) + "' "
                                # print(querrySession)
                                apiUserSessionData = DB.selectAllData(querrySession)
                                now = datetime.now()
                                todaydatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                                # requestType = 'API'
                                createdDate = todaydatetime
                                tablename = 'ApiUserSession'
                                if len(apiUserSessionData) > 0:
                                    licKey = userDetails[0]['LicKey']
                                    accessToken = apiUserSessionData[0]['AccessToken']
                                    empId = str(userDetails[0]['EmpId'])
                                    qsOrgDetails = "select B.AccessToken as AccessToken, A.LicKey AS LicKey,A.OrganizationEmailId AS OrganizationEmailId ,A.OrganizationMobileNo as OrganizationMobileNo,A.OrganizationName as OrganizationName  from OrganizationDetails AS A ,ApiUserSession AS B where A.LicKey='" + licKey + "' and IsActive=1 and IsDelete=0 and B.EmpId='" + \
                                                   userDetails[0]['UserName'] + "'"
                                    rsOrgDetails = DB.selectAllData(qsOrgDetails)
                                    if len(FCMTokenNo) > 0:
                                        CheckFCMQuerry1 = "select * from FCMTokenSession where AndroidId='" + str(
                                            AndroidId) + "'"
                                        FCMTokenData1 = DB.selectAllData(CheckFCMQuerry1)
                                        if len(FCMTokenData1) > 0:
                                            FCMTokenSessionId = FCMTokenData1[0]['FCMTokenSessionId']
                                            UpdateFCMTokenQuerry = "update FCMTokenSession set FCMTokenNo='" + FCMTokenNo + "',EmpId='" + empId + "',LicKey='" + licKey + "' ,UserName='" + OrganizationEmailId + "',UserType='" + UserType + "',IsActive=1,IsDelete=0,UpdatedDate='" + createdDate + "' where AndroidId='" + str(
                                                AndroidId) + "'"
                                            DB.selectAllData(UpdateFCMTokenQuerry)
                                            FCMTokenData = FCMTokenNo
                                            AndroidId = AndroidId

                                        else:
                                            values = {'FCMTokenNo': FCMTokenNo, 'LicKey': licKey,
                                                      'UserName': OrganizationEmailId, 'UserType': UserType,
                                                      'IsActive': '1', 'IsDelete': '0', 'CreatedDate': createdDate,
                                                      'UpdatedDate': createdDate, 'EmpId': empId,
                                                      'AndroidId': str(AndroidId)}
                                            lastinsertid = DB.insertData('FCMTokenSession', values)
                                            # CheckFCMQuerry = "select * from FCMTokenSession where  UserName='" + OrganizationEmailId + "' and LicKey='" + licKey + "'"
                                            # FCMTokenData = DB.selectAllData(CheckFCMQuerry)
                                            FCMTokenData = FCMTokenNo
                                            AndroidId = AndroidId
                                    else:
                                        FCMTokenData = 'NULL'
                                        AndroidId = 'NULL'
                                    if len(rsOrgDetails) > 0:
                                        orglicKey = rsOrgDetails[0]['LicKey']
                                        orgAccessToken = rsOrgDetails[0]['AccessToken']
                                        orgOrganizationEmailId = rsOrgDetails[0]['OrganizationEmailId']
                                        orgOrganizationName = rsOrgDetails[0]['OrganizationName']
                                        OrganizationMobileNo = rsOrgDetails[0]['OrganizationMobileNo']
                                        responseData = {'LicKey': licKey, 'UserName': userName,
                                                        'EmpId': empId, 'MarkAttendance': MarkAttendance,
                                                        'UserAccessToken': accessToken,
                                                        'OrganizationEmailId': orgOrganizationEmailId,
                                                        'OrganizationName': orgOrganizationName,
                                                        'AccessToken': orgAccessToken,
                                                        'LicKey': orglicKey,
                                                        'OrganizationMobileNo': OrganizationMobileNo,
                                                        'EmployeeMobileNo': MobileNo, 'EmployeeEmailId': EmailId,
                                                        'EmployeeName': rsEmpRes[0]['EmpName'],
                                                        'UserProfileImage': UserProfileImage,
                                                        'MarkAttendanceType': MarkAttendanceType,
                                                        'FCMTokenNo': FCMTokenData, 'AndroidId': AndroidId,
                                                        'BaseLocationId': BaseLocationId}
                                    else:
                                        responseData = {'message': 'Data not added properly.'}
                                else:
                                    qsOrgDetails = "select  A.LicKey AS LicKey,A.OrganizationEmailId AS OrganizationEmailId ,A.OrganizationMobileNo as OrganizationMobileNo,A.OrganizationName as OrganizationName  from OrganizationDetails AS A  where A.LicKey='" + licKey + "' and A.IsDelete=0 and A.IsActive=1"
                                    rsOrgDetails = DB.selectAllData(qsOrgDetails)
                                    orglicKey = rsOrgDetails[0]['LicKey']
                                    querry = "select * from ApiUserSession where LicKey='" + orglicKey + "' and IsExpire=0 and UserType='admin'"
                                    sessionData = DB.selectAllData(querry)
                                    if len(sessionData) > 0:
                                        orgAccessToken = sessionData[0]['AccessToken']
                                        orgOrganizationEmailId = rsOrgDetails[0]['OrganizationEmailId']
                                        orgOrganizationName = rsOrgDetails[0]['OrganizationName']
                                        OrganizationMobileNo = rsOrgDetails[0]['OrganizationMobileNo']
                                        tablename = 'ApiUserSession'
                                        values = {'RequestType': 'API',
                                                  'UserType': UserType, 'EmpId': userName,
                                                  'AccessToken': orgAccessToken,
                                                  'MasterID': masterId, 'IsExpire': '0',
                                                  'CreatedDateTime': createdDate, 'LicKey': licKey}
                                        lastinsertid = DB.insertData(tablename, values)
                                        licKey = userDetails[0]['LicKey']
                                        username = userDetails[0]['UserName']
                                        empId = userDetails[0]['EmpId']
                                        MarkAttendance = userDetails[0]['MarkAttendance']
                                        MarkAttendanceType = userDetails[0]['MarkAttendanceType']
                                        accessToken = apiUserSessionData[0]['AccessToken']
                                        responseData = {'LicKey': licKey, 'UserName': userName,
                                                        'EmpId': empId, 'MarkAttendance': MarkAttendance,
                                                        'UserAccessToken': accessToken,
                                                        'OrganizationEmailId': orgOrganizationEmailId,
                                                        'OrganizationName': orgOrganizationName,
                                                        'AccessToken': orgAccessToken,
                                                        'LicKey': orglicKey,
                                                        'OrganizationMobileNo': OrganizationMobileNo,
                                                        'EmployeeMobileNo': MobileNo, 'EmployeeEmailId': EmailId,
                                                        'EmployeeName': empName, 'UserProfileImage': UserProfileImage,
                                                        'MarkAttendanceType': MarkAttendanceType,
                                                        'BaseLocationId': BaseLocationId}
                                    else:
                                        responseData = {'message': 'Data not Inserted properly.'}
                                category = "1"
                                message = "Hi " + str(employeeName) + ", your login successfull."
                                response = {'category': category, 'message': message, 'ResponseData': responseData}
                            else:
                                response = {'category': "0", 'message': "your credentials do not match!"}
                        else:
                            response = {'category': "0", 'message': "your credentials do not match!"}
                    else:
                        response = {'category': "0", 'message': "your credentials do not match!"}
                else:
                    response = {'category': "0", 'message': "Sorry! this module not implement right now."}
                response = make_response(jsonify(response))
                return response


# API FOR PRESENT EMPLOYEE INFO IN DASHBOARD
class RcAPIPresentEmployee(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            searchDate = ''
            if 'searchDate' in RequestData:
                searchDate = RequestData["searchDate"]
            # if LicKey == '' and searchDate == '':
            if (LicKey.isspace() == True or LicKey == '') or (searchDate.isspace() == True or searchDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                # Removing space from left and right side
                searchDate = searchDate.strip()
                # Removing space from left and right side
                currentMonth = datetime.strptime(searchDate, "%Y-%m-%d")
                month = currentMonth.month
                presentQuerry = "select A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName,C.BaseLocationId,D.ShiftMasterId from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + searchDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "'  group by A.EmployeeShiftHistoryId"
                presentInfo = DB.selectAllData(presentQuerry)
                response = {'category': "1", 'message': "Present Employee Info.", 'ResponseData': presentInfo}
            response = make_response(jsonify(response))
            return response


# API FOR ABSENT EMPLOYEE INFO IN DASHBOARD
class RcAPIAbsentEmployee(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            searchDate = ''
            if 'searchDate' in RequestData:
                searchDate = RequestData["searchDate"]
            if (LicKey.isspace() == True or LicKey == '') or (searchDate.isspace() == True or searchDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                searchDate = searchDate.strip()
                # searchDate = '2020-11-12'
                Querry = "Select F.EmpId,G.LocationName,F.EmpName,H.ShiftMasterId,I.ShiftName,J.ImagePath FROM BaseLocation AS G, EmployeeShiftHistory AS H, ShiftMaster AS I, EmployeeRegistration AS F left join DatasetEncodings AS J on (F.EmpId=J.EmpId and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0) where F.EmpId NOT IN (select A.EmpId from ActivityDetails as A,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + searchDate + "' and E.LicKey='" + LicKey + "') and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId) and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0 and G.BaseLocationId=F.BaseLocationId and H.StartDate='" + searchDate + "' and F.EmpId=H.EmpId and H.ShiftMasterId=I.ShiftMasterId GROUP BY F.EmpId"
                # print(Querry)
                absentEmp = DB.selectAllData(Querry)
                response = {'category': "1", 'message': "Absent Employee Information.", 'ResponseData': absentEmp}
            response = make_response(jsonify(response))
            return response


# API FOR LATECOMING EMPLOYEE INFO DASHBOARD
class RcAPILateComing(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            searchDate = ''
            if 'searchDate' in RequestData:
                searchDate = RequestData["searchDate"]
            # if LicKey == '' or searchDate == '':
            if (LicKey.isspace() == True or LicKey == '') or (searchDate.isspace() == True or searchDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                # Removing space from left and right side
                searchDate = searchDate.strip()
                # Removing space from left and right side
                currentMonth = datetime.strptime(searchDate, "%Y-%m-%d")
                Query = "select A.EmpId, A.EmpImage, B.EmpName, B.EmployeeRegistrationId, A.EmployeeShiftHistoryId, A.ShiftMasterId, convert(D.ShiftMargin,char) AS ShiftMargin, convert(min(A.ADTime),char) AS FirstSeen, convert(max(A.ADTime),char) AS LastSeen, convert(min(A.ADDate),char) AS ADDate, C.LocationName, D.ShiftName from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + searchDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
                ResponseData = DB.selectAllData(Query)
                response = {'category': "1", 'message': "Latecoming Employee Info.", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# API FOR MULTIPLE EMPLOYEE LISTING
class RcAPIActiveMultiEmployee(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                # querry1="select count(*) from BaseLocation as C,Employeeregistration AS A left join DatasetEncodings AS B ON (A.EmpId=B.EmpId and A.LicKey='"+LicKey+"') where A.LicKey='"+LicKey+"' and C.BaseLocationId=A.BaseLocationId and A.IsDelete=0 and (A.IsActive=1 OR A.IsActive=0) GROUP BY A.EmpId"
                querry = "select A.*,B.ImagePath,C.LocationName,CONVERT(A.CreatedDate,CHAR) AS CreatedDate from BaseLocation as C,EmployeeRegistration AS A left join DatasetEncodings AS B ON (A.EmpId=B.EmpId and A.LicKey='" + LicKey + "' and  B.LicKey='" + LicKey + "') where A.LicKey='" + LicKey + "' and A.IsDelete=0 and A.IsActive=1  and C.BaseLocationId=A.BaseLocationId GROUP BY A.EmpId ORDER BY A.EmployeeRegistrationId Desc"  # (A.IsActive=1 OR A.IsActive=0)
                data = DB.selectAllData(querry)
                if len(data) > 0:
                    response = {'category': "1", 'message': "List of all employees", 'ResponseData': data}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# API FOR MULTIPLE EMPLOYEE LISTING
class RcAPIMultiEmployee(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                # querry1="select count(*) from BaseLocation as C,Employeeregistration AS A left join DatasetEncodings AS B ON (A.EmpId=B.EmpId and A.LicKey='"+LicKey+"') where A.LicKey='"+LicKey+"' and C.BaseLocationId=A.BaseLocationId and A.IsDelete=0 and (A.IsActive=1 OR A.IsActive=0) GROUP BY A.EmpId"
                querry = "select A.*,B.ImagePath,C.LocationName,CONVERT(A.CreatedDate,CHAR) AS CreatedDate from BaseLocation as C,EmployeeRegistration AS A left join DatasetEncodings AS B ON (A.EmpId=B.EmpId and A.LicKey='" + LicKey + "' and  B.LicKey='" + LicKey + "') where A.LicKey='" + LicKey + "' and A.IsDelete=0  and C.BaseLocationId=A.BaseLocationId GROUP BY A.EmpId ORDER BY A.EmployeeRegistrationId Desc"  # (A.IsActive=1 OR A.IsActive=0)
                # print(querry)
                data = DB.selectAllData(querry)
                if len(data) > 0:
                    response = {'category': "1", 'message': "List of all employees", 'ResponseData': data}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# API FOR MULTIPLE EMPLOYEE Excel by IN/ODI01/027
class RcAPIMultiEmployeeExcel(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                excellink = ''
                QsEmployeeList = "select A.*,B.ImagePath,C.LocationName,CONVERT(A.CreatedDate,CHAR) AS CreatedDate2 from BaseLocation as C,EmployeeRegistration AS A left join DatasetEncodings AS B ON (A.EmpId=B.EmpId and A.LicKey='" + LicKey + "' and B.LicKey='" + LicKey + "') where A.LicKey='" + LicKey + "' and A.IsDelete=0 and (A.IsActive=1 OR A.IsActive=0) and C.BaseLocationId=A.BaseLocationId GROUP BY A.EmpId"
                RsEmployeeList = DB.selectAllData(QsEmployeeList)
                lenOfRsEmployeeList = len(RsEmployeeList)
                if lenOfRsEmployeeList > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'Employee_List_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("Employee List")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:G1', 'Employee List', bold)
                    worksheet.write('A2', 'Sl. No', bold)
                    worksheet.write('B2', 'Employee Id', bold)
                    worksheet.write('C2', 'Name', bold)
                    worksheet.write('D2', 'Location', bold)
                    worksheet.write('E2', 'Email ID', bold)
                    worksheet.write('F2', 'Mobile No', bold)
                    worksheet.write('G2', 'Created Date', bold)
                    row = 2
                    col = 0
                    for j in range(len(RsEmployeeList)):
                        EmpId = RsEmployeeList[j]['EmpId']
                        EmpName = RsEmployeeList[j]['EmpName']
                        LocationName = RsEmployeeList[j]['LocationName']
                        EmailId = RsEmployeeList[j]['EmailId']
                        MobileNo = str(RsEmployeeList[j]['MobileNo'])
                        CreatedDate = RsEmployeeList[j]['CreatedDate2']
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, EmpId)
                        worksheet.write(row, col + 2, EmpName)
                        worksheet.write(row, col + 3, LocationName)
                        worksheet.write(row, col + 4, EmailId)
                        worksheet.write(row, col + 5, str(MobileNo))
                        worksheet.write(row, col + 6, CreatedDate)
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "List of all employees", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response

        # API FOR MULTIPLE EMPLOYEE PDF


# API FOR MULTIPLE EMPLOYEE Pdf by IN/ODI01/027
class RcAPIMultiEmployeePdf(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                QsEmployeeList = "select A.*,B.ImagePath,C.LocationName,CONVERT(A.CreatedDate,CHAR) AS CreatedDate2 from BaseLocation as C,EmployeeRegistration AS A left join DatasetEncodings AS B ON (A.EmpId=B.EmpId and A.LicKey='" + LicKey + "' and B.LicKey='" + LicKey + "') where A.LicKey='" + LicKey + "' and A.IsDelete=0 and (A.IsActive=1 OR A.IsActive=0) and C.BaseLocationId=A.BaseLocationId GROUP BY A.EmpId"
                RsEmployeeList = DB.selectAllData(QsEmployeeList)
                lenOfRsEmployeeList = len(RsEmployeeList)
                pdflink = ''
                if lenOfRsEmployeeList > 0:
                    RsOfPDF = CREATEPDF.employeesList(RsEmployeeList)
                response = {'category': "1", 'message': "List of all employees", 'pdflink': RsOfPDF}
            response = make_response(jsonify(response))
            return response


# API FOR  SINGLE EMPLOYEE LIST,EMPLOYEE ADD AND EMPLOYEE DELETE
class RcAPIEmployee(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Master id as a unquie id of the table
            # if MasterId == '':
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                # Removing space from left and right side
                MasterId = MasterId.strip()
                # Removing space from left and right side
                querry = "select A.*,B.LocationName from EmployeeRegistration AS A,BaseLocation AS B where A.LicKey='" + LicKey + "' and A.EmployeeRegistrationId='" + MasterId + "' and A.BaseLocationId=B.BaseLocationId"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response

    # Add Employee
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            EmpName = ''
            EmpId = ''
            EmailId = ''
            MobileNo = ''
            BaseLocationId = ''
            IsEnrolled = '0'
            IsTrained = '0'
            IsActive = '1'
            IsDelete = '0'
            if 'EmpName' in RequestData and 'EmpId' in RequestData and 'EmailId' in RequestData and 'MobileNo' in RequestData and 'BaseLocationId' in RequestData:
                EmpName = RequestData['EmpName']
                EmpId = RequestData['EmpId']
                EmailId = RequestData['EmailId']
                MobileNo = RequestData['MobileNo']
                BaseLocationId = RequestData['BaseLocationId']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (EmpName.isspace() == True or EmpName == '') or (
                    EmpId.isspace() == True or EmpId == '') or (EmailId.isspace() == True or EmailId == '') or (
                    MobileNo.isspace() == True or MobileNo == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}  # , 'RequestData': RequestData
            else:
                EmpName = EmpName.strip()
                EmpId = EmpId.strip()
                EmailId = EmailId.strip()
                MobileNo = MobileNo.strip()
                BaseLocationId = BaseLocationId.strip()
                validateemailcheck = checkemail(EmailId)
                tablename = "EmployeeRegistration"
                order = ""
                wherecondition = "`LicKey`='" + LicKey + "' AND `EmailId`='" + EmailId + "'"
                fields = ''
                if validateemailcheck:
                    if (checkmobile(MobileNo)):
                        ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                        if len(ResponseData) > 0:
                            error = error + 1
                            message = 'Email ID already exists !'
                        else:
                            wherecondition = "`LicKey`='" + LicKey + "' AND `EmpId`='" + EmpId + "'"
                            ResponseData1 = DB.retrieveAllData(tablename, fields, wherecondition, order)
                            if len(ResponseData1) > 0:
                                error = error + 1
                                message = 'Employee ID already exists.'
                            else:
                                pass
                    else:
                        error = error + 1
                        message = 'Invalid Mobile No'
                else:
                    error = error + 1
                    message = 'Invalid Email Id'
                if error > 0:
                    response = {'category': "0", 'message': message}  # , 'RequestData': RequestData
                else:
                    # unique_id = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    # 'verification_id': unique_id,
                    # select BaseLocationId
                    values = {'LicKey': LicKey, 'BaseLocationId': BaseLocationId, 'EmpId': EmpId,
                              'EmpName': EmpName, 'EmailId': EmailId, 'MobileNo': MobileNo,
                              'IsEnrolled': IsEnrolled, 'IsActive': IsActive, 'IsDelete': IsDelete,
                              'CreatedDate': CreatedDate, 'UpdatedDate': CreatedDate}
                    showmessage = DB.insertData(tablename, values)
                    if showmessage['messageType'] == 'success':
                        response = {'category': "1",
                                    'message': "Record added successfully."}  # 'ResponseData': showmessage['lastInsertId']
                    else:
                        response = {'category': "0", 'message': "Sorry ! something Error in DB. try it again."}
            response = make_response(jsonify(response))
            return response

    # Update Employee
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            EmpName = ''
            EmpId = ''
            EmailId = ''
            MobileNo = ''
            BaseLocationId = ''
            IsEnrolled = '0'
            IsTrained = '0'
            # IsActive = ''
            IsDelete = '0'
            if 'EmpName' in RequestData and 'EmpId' in RequestData and 'EmailId' in RequestData and 'MobileNo' in RequestData and 'BaseLocationId' in RequestData:  # and 'IsActive' in RequestData
                EmpName = RequestData['EmpName']
                EmpId = RequestData['EmpId']
                EmailId = RequestData['EmailId']
                MobileNo = RequestData['MobileNo']
                BaseLocationId = RequestData['BaseLocationId']
                # IsActive = RequestData['IsActive']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == '') or (
                    EmpName.isspace() == True or EmpName == '') or (EmpId.isspace() == True or EmpId == '') or (
                    EmailId.isspace() == True or EmailId == '') or (MobileNo.isspace() == True or MobileNo == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == ''):
                # or IsActive == ''
                # if LicKey == '' or MasterId == '' or EmpName == '' or EmpId == '' or EmailId == '' or MobileNo == '' or BaseLocationId == '':  # or IsActive == ''
                response = {'category': "0", 'message': "All fields are mandatory"}  # , 'RequestData': RequestData
            else:
                MasterId = MasterId.strip()
                EmpName = EmpName.strip()
                EmpId = EmpId.strip()
                EmailId = EmailId.strip()
                MobileNo = MobileNo.strip()
                BaseLocationId = BaseLocationId.strip()
                validatemailcheck = checkemail(EmailId)
                tablename = "EmployeeRegistration"
                order = ""
                wherecondition = "`LicKey`='" + LicKey + "' AND `EmailId`='" + EmailId + "' AND `EmployeeRegistrationId` != '" + MasterId + "'"
                fields = ''
                if validatemailcheck:
                    if (checkmobile(MobileNo)):
                        ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                        if len(ResponseData) > 0:
                            error = error + 1
                            message = 'Email ID already exists.'
                        else:
                            wherecondition = "`LicKey`='" + LicKey + "' AND `EmpId`='" + EmpId + "' AND `EmployeeRegistrationId` != '" + MasterId + "'"
                            ResponseData1 = DB.retrieveAllData(tablename, fields, wherecondition, order)
                            if len(ResponseData1) > 0:
                                error = error + 1
                                message = 'Employee ID already exists !'
                            else:
                                pass
                    else:
                        error = error + 1
                        message = 'Invalid Mobile No.'
                else:
                    error = error + 1
                    message = 'Invalid Email Id.'
                if error > 0:
                    # message="Erorr Occured"
                    response = {'category': '0', 'message': message}
                else:
                    tablename = "EmployeeRegistration"
                    wherecondition = "`LicKey` = '" + LicKey + "' and `EmployeeRegistrationId` = '" + MasterId + "'"
                    values = {'LicKey': LicKey, 'BaseLocationId': BaseLocationId,
                              'EmpId': EmpId, 'EmpName': EmpName, 'EmailId': EmailId,
                              'MobileNo': MobileNo,
                              'UpdatedDate': CreatedDate}  # 'IsActive': IsActive,'CreatedDate': CreatedDate,
                    showmessage = DB.updateData(tablename, values, wherecondition)
                    order = ""
                    fields = ''
                    ResponseData2 = DB.retrieveAllData(tablename, fields, wherecondition, order)
                    if len(ResponseData2) > 0:
                        if showmessage['messageType'] == 'success':
                            response = {'category': "1", 'message': "Employee updated successfully."}
                        else:
                            response = {'category': "0", 'message': "Sorry ! something error in db. try it again."}
                    else:
                        response = {'category': "0", 'message': "Sorry ! Data not updated in db. try it again."}
            response = make_response(jsonify(response))
            return response


# Emloyee Info
class RcAPIEmployeeInfo(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Master id as the employeeid
            # if MasterId == '':
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                MasterId = MasterId.strip()
                querry = "select A.*,B.ImagePath,C.LocationName,CONVERT(A.CreatedDate,CHAR) AS CreatedDate from BaseLocation as C,EmployeeRegistration AS A left join DatasetEncodings AS B ON (A.EmpId=B.EmpId and A.LicKey='" + LicKey + "') where A.LicKey='" + LicKey + "' and A.EmpId='" + str(
                    MasterId) + "' and C.BaseLocationId=A.BaseLocationId GROUP BY A.EmpId"
                ResponseData = DB.selectAllData(querry)
                response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# Verify Employee
class RcAPIEmployeeVerify(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Master id as the employeeid
            # if MasterId == '':
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                MasterId = MasterId.strip()
                querry = "select * from EmployeeRegistration where LicKey='" + LicKey + "' and EmpId='" + MasterId + "'"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Employee ID  exists.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Employee ID is not exists."}
            response = make_response(jsonify(response))
            return response


# Temporarily Delete Employee
class RcAPIDeleteStatus(Resource):
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            now = datetime.now()
            UpdatedDate = now.strftime('%Y-%m-%d')
            LicKey = VURS['LicKey']
            if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                MasterId = MasterId.strip()
                querry = "select * from EmployeeRegistration where  EmployeeRegistrationId='" + MasterId + "' and LicKey='" + LicKey + "'"
                responseData = DB.selectAllData(querry)
                if len(responseData):
                    ResponseData1 = responseData[0]['IsDelete']
                    if ResponseData1 == 0:
                        tablename = 'EmployeeRegistration'
                        wherecondition = "`LicKey`= '" + LicKey + "' AND `EmployeeRegistrationId`= '" + MasterId + "'"
                        values = {"IsDelete": '1', 'UpdatedDate': UpdatedDate}
                        ResponseData1 = DB.updateData(tablename, values, wherecondition)
                        response = {'category': "1", 'message': "Employee deleted temporarily."}
                    else:
                        response = {'category': "0", 'message': "Please try again."}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
        response = make_response(jsonify(response))
        return response


#  Employee Status
class RcAPIEmployeeStatus(Resource):
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # if LicKey == '' or MasterId == '':
            if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                # Removing space from left and right side
                MasterId = MasterId.strip()
                # Removing space from left and right side
                Querry = "SELECT * FROM EmployeeRegistration WHERE EmployeeRegistrationId  ='" + MasterId + "' and Isdelete=0 LIMIT 1 "
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    ResponseData1 = ResponseData[0]['IsActive']
                    if ResponseData1 == 0:
                        tablename = 'EmployeeRegistration'
                        wherecondition = "`LicKey`= '" + LicKey + "' AND `EmployeeRegistrationId`= '" + MasterId + "'"
                        values = {"IsActive": '1'}
                        ResponseData1 = DB.updateData(tablename, values, wherecondition)
                        response = {'category': "1", 'message': "Employee activated successfully."}
                    elif ResponseData1 == 1:
                        tablename = 'EmployeeRegistration'
                        wherecondition = "`LicKey`= '" + LicKey + "' AND `EmployeeRegistrationId`= '" + MasterId + "'"
                        values = {"IsActive": '0'}
                        ResponseData1 = DB.updateData(tablename, values, wherecondition)
                        response = {'category': "1", 'message': "Employee deactivated successfully."}
                    else:
                        response = {'category': "0", 'message': "Data not found!"}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
        response = make_response(jsonify(response))
        return response


# MULTIPLE LOCATION LIST
class RcAPIMultiLocation(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                Querry = "SELECT A.BaseLocationId,A.LocationName,A.LicKey,A.SystemInfo ,A.IsActive,  CONVERT(A.CreatedDate,CHAR) As CreatedDate,count(B.EmpId) AS NO_OF_EMPLOYEES from BaseLocation AS A left join EmployeeRegistration AS B on (A.BaseLocationId=B.BaseLocationId and A.LicKey='" + LicKey + "' and B.IsActive=1 and B.IsDelete=0) GROUP BY A.BaseLocationId Having A.LicKey='" + LicKey + "' ORDER BY A.BaseLocationId DESC"
                ResponseData = DB.selectAllData(Querry)
                response = {'category': "1", 'message': "List of all location.", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# SINGLE LOCATION LIST,ADD LOCATION & DELETE LOCATION
class RcAPILocation(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Mastrer id as a unquie id of the table
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'BaseLocation'
                wherecondition = "`LicKey`= '" + LicKey + "' and `BaseLocationId`= '" + MasterId + "'"
                order = ""
                fields = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
            response = make_response(jsonify(response))
            return response

    # DELETE LOCATION
    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Mastrer id as a unquie id of the table
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                querry = "select * from EmployeeRegistration where BaseLocationId ='" + MasterId + "' and LicKey='" + LicKey + "'"
                data = DB.selectAllData(querry)
                if len(data) > 0:
                    response = {'category': "0", 'message': "Can't delete location!"}
                else:
                    tablename = 'BaseLocation'
                    wherecondition = "LicKey= '" + LicKey + "' AND `BaseLocationId`= '" + MasterId + "'"
                    querry = "select * from BaseLocation where LicKey='" + LicKey + "' AND `BaseLocationId`= '" + MasterId + "'"
                    Location = DB.selectAllData(querry)
                    if len(Location) > 0:
                        deletelocation = DB.deleteSingleRow(tablename, wherecondition)
                        response = {'category': '1', 'message': 'Location deleted successfully.'}
                    else:
                        response = {'category': "0", 'message': "Error.Location Doesn't Exist"}
            response = make_response(jsonify(response))
            return response

    # UPDATE LOCATION
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            LocationName = ''
            SystemInfo = ''
            IsActive = ''
            if 'LocationName' in RequestData and 'SystemInfo' in RequestData and 'IsActive' in RequestData:
                LocationName = RequestData['LocationName']
                SystemInfo = RequestData['SystemInfo']
                IsActive = RequestData['IsActive']
            # now = datetime.now()
            # CreatedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == '') or (
                    LocationName.isspace() == True or LocationName == '') or (
                    SystemInfo.isspace() == True or SystemInfo == '') or (IsActive.isspace() or IsActive == '') == True:
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                MasterId = MasterId.strip()
                LocationName = LocationName.strip()
                SystemInfo = SystemInfo.strip()
                SystemInfo = SystemInfo.strip()
                Qurry1 = "select * from BaseLocation where LicKey='" + LicKey + "' and `BaseLocationId` = '" + MasterId + "'"
                resultData = DB.selectAllData(Qurry1)
                if len(resultData):
                    tablename = "BaseLocation"
                    wherecondition = "`LicKey`='" + LicKey + "' AND `BaseLocationId` = '" + MasterId + "'"
                    values = {'LocationName': LocationName, 'SystemInfo': SystemInfo, 'IsActive': IsActive}
                    showmessage = DB.updateData(tablename, values, wherecondition)
                    if showmessage['messageType'] == 'success':
                        response = {'category': '1', 'message': 'Location updated successfully.'}
                    else:
                        response = {'category': '0', 'message': 'error occured'}
                else:
                    response = {'category': '0', 'message': 'Data not found'}
            response = make_response(jsonify(response))
            return response

    # ADD LOCATION
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            LocationName = ''
            SystemInfo = ''
            IsActive = ''
            if 'LocationName' in RequestData and 'SystemInfo' in RequestData and 'IsActive' in RequestData:
                LocationName = RequestData['LocationName']
                SystemInfo = RequestData['SystemInfo']
                IsActive = RequestData['IsActive']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            # if LicKey==''  or LocationName=='' or SystemInfo ==''  or IsActive=='':
            if (LicKey.isspace() == True or LicKey == '') or (
                    LocationName == [] or LocationName == [''] or LocationName == [' ']) or (
                    SystemInfo.isspace() == True or SystemInfo == '') or (IsActive.isspace() == True or IsActive == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                # if all('' == s or s.isspace() for s in LocationName):
                if not any(s.strip() for s in LocationName):
                    response = {'category': "0", 'message': "All fields are mandatory."}
                else:
                    # Removing space from left and right side
                    SystemInfo = SystemInfo.strip()
                    IsActive = IsActive.strip()
                    # Removing space from left and right side
                    for key in LocationName:
                        singleLocationName = key.strip()
                        # print(singleLocationName)
                        if singleLocationName and not singleLocationName.isspace():
                            Querry = "SELECT * FROM BaseLocation WHERE LicKey ='" + LicKey + "' AND LocationName= '" + singleLocationName + "'"
                            # print(Querry)
                            ResponseData = DB.selectAllData(Querry)
                            if len(ResponseData) == 0:
                                tablename = "BaseLocation"
                                values = {'LicKey': LicKey, 'LocationName': key.strip(), 'SystemInfo': SystemInfo,
                                          'IsActive': IsActive, 'CreatedDate': CreatedDate}
                                showmessage = DB.insertData(tablename, values)
                                if showmessage['messageType'] == 'success':
                                    response = {'category': '1', 'message': 'Location inserted successfully.'}
                                else:
                                    response = {'category': '0', 'message': 'Error Occured in Add Location.'}
                            else:
                                response = {'category': '0', 'message': 'This Location already exist.!'}
            response = make_response(jsonify(response))
            return response


# GET PROFILE,ADD PROFILE
class RcAPIProfile(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            tablename = "OrganizationDetails"
            order = 'OrganizationEmailId DESC'
            wherecondition = "LicKey='" + LicKey + "' and IsDelete=0 and IsActive=1"
            fields = "LicKey,OrganizationName,OrganizationEmailId,OrganizationMobileNo,CONVERT(IssuedDate,CHAR) AS IssuedDate,CONVERT(IssuedTime,CHAR) AS IssuedTime,CONVERT(ExpiredDate,CHAR) AS ExpiredDate,CONVERT(ExpiredTime,CHAR) AS ExpiredTime,ProfileImg,AdminImg"
            ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
            if ResponseData:
                response = {'category': "1", 'message': "Welcome to profile.", 'ResponseData': ResponseData}
            else:
                response = {'category': "0", 'message': "Sorry! invalid user."}
            response = make_response(jsonify(response))
            return response


# ADD ADMIN PROFILE
class RcAPIAdminProfile(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            # print(RequestData)
            AdminImg = ''
            adminName = ""
            if 'AdminImg' in RequestData:
                AdminImg = RequestData['AdminImg']
            if 'adminName' in RequestData:
                adminName = RequestData['adminName']
            if (LicKey.isspace() == True or LicKey == '') or (adminName.isspace() == True or adminName == '') and (
                    AdminImg.isspace() == True or AdminImg == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                AdminImg = AdminImg.strip()
                adminName = adminName.strip()
                now = datetime.now()
                file = now.strftime('%Y%m%d%H%M%S')
                profileImageName = str(LicKey) + str(file)
                if AdminImg != '':
                    encodeAdminImg = AdminImg.replace('data:image/png;base64,', '')
                    encodeImg = bytes(encodeAdminImg, 'utf-8')
                    decodeImg = base64.decodestring(encodeImg)
                    imgPath = "images/logoImg"
                    imgField = 'static/public/' + imgPath
                    # imgDir = imgField + "/" + str(file) + ".png"
                    imgDir = imgField + "/" + profileImageName + ".png"
                    if not os.path.exists(imgField):
                        os.makedirs(imgField)
                        if encodeImg:
                            resultImg = open(imgDir, 'wb')
                            resultImg.write(decodeImg)
                        else:
                            # pass
                            a = 1
                    else:
                        resultImg = open(imgDir, 'wb')
                        resultImg.write(decodeImg)
                else:
                    imgDir = ''
                tablename = "OrganizationDetails"
                wherecondition = "`LicKey` ='" + LicKey + "' and IsDelete=0 and IsActive=1"
                fields = ""
                order = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                # print(ResponseData)
                if len(ResponseData) > 0:
                    if imgDir != '' and adminName != '':
                        tablename = "OrganizationDetails"
                        wherecondition = "`LicKey` ='" + LicKey + "' and  `IsDelete`=0 and `IsActive`=1 "
                        values = {'AdminImg': imgDir, 'OrganizationName': adminName}
                        showmessage = DB.updateData(tablename, values, wherecondition)
                        if showmessage['messageType'] == 'success':
                            response = {'category': "1", 'message': "Organization logo and name updated successfully."}
                            response = make_response(jsonify(response))
                            return response
                        else:
                            response = {'category': "0", 'message': "Sorry! error occured. Please try again later."}
                            response = make_response(jsonify(response))
                            return response
                    elif imgDir != '' and adminName == '':
                        tablename = "OrganizationDetails"
                        wherecondition = "`LicKey` ='" + LicKey + "' and  `IsDelete`=0 and `IsActive`=1 "
                        values = {'AdminImg': imgDir}
                        showmessage = DB.updateData(tablename, values, wherecondition)
                        if showmessage['messageType'] == 'success':
                            response = {'category': "1", 'message': "Organization logo updated successfully."}
                            response = make_response(jsonify(response))
                            return response
                        else:
                            response = {'category': "0", 'message': "Sorry! error occured. Please try again later."}
                            response = make_response(jsonify(response))
                            return response
                    else:
                        values = {'OrganizationName': adminName}
                        showmessage = DB.updateData(tablename, values, wherecondition)
                        if showmessage['messageType'] == 'success':
                            response = {'category': "1", 'message': "Organization name updated successfully."}
                            response = make_response(jsonify(response))
                            return response
                        else:
                            response = {'category': "0", 'message': "Sorry! error occured. Please try again later."}
                            response = make_response(jsonify(response))
                            return response
                else:
                    response = {'category': '0', 'message': 'Something data base error.'}
            response = make_response(jsonify(response))
            return response


# ADD USER PROFILE
class RcAPIUserProfile(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            userImg = ''
            if 'userImg' in RequestData:
                userImg = RequestData['userImg']
            if (LicKey.isspace() == True or LicKey == '') or (userImg.isspace() == True or userImg == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                userImg = userImg.strip()
                now = datetime.now()
                file = now.strftime('%Y%m%d%H%M%S')
                if userImg != '':
                    encodeUserImg = userImg.replace('data:image/png;base64,', '')
                    encodeImg = bytes(encodeUserImg, 'utf-8')
                    decodeImg = base64.decodestring(encodeImg)
                    imgPath = "images/profile"
                    imgField = 'static/public/' + imgPath
                    imgDir = imgField + "/" + str(file) + ".png"
                    userImgName = str(file) + ".png"
                    if not os.path.exists(imgField):
                        os.makedirs(imgField)
                        if encodeImg:
                            resultImg = open(imgDir, 'wb')
                            resultImg.write(decodeImg)
                        else:
                            # pass
                            a = 1
                    else:
                        resultImg = open(imgDir, 'wb')
                        resultImg.write(decodeImg)
                else:
                    imgDir = ''
                tablename = "OrganizationDetails"
                wherecondition = "`LicKey` ='" + LicKey + "' and IsActive=1 and IsDelete=0"
                fields = ""
                order = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData):
                    if imgDir != '':
                        # tablename = "OrganizationDetails"
                        # wherecondition = "LicKey ='" + LicKey + "' and IsActive=1 and IsDelete=0"
                        # values = {'ProfileImg': imgDir}
                        # print('=============values====================')
                        # print(values)
                        # showmessage = DB.updateData(tablename, values, wherecondition)
                        querry1 = "update OrganizationDetails set ProfileImg='" + imgDir + "' where LicKey ='" + LicKey + "' and IsActive=1 and IsDelete=0"
                        showmessage = DB.selectAllData(querry1)
                        response = {'category': "1", 'message': "Profile image updated successfully."}
                        response = make_response(jsonify(response))
                        return response
                    else:
                        response = {'category': '0', 'message': "Not a valid account"}
                else:
                    response = {'category': '0', 'message': 'Something data base error.'}
            response = make_response(jsonify(response))
            return response


# UPDATE PROFILE
class RcAPIUpdateProfile(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            OrganizationEmailId = ''
            OrganizationMobileNo = ''
            OrganizationName = ''
            if 'OrganizationEmailId' in RequestData and 'OrganizationMobileNo' in RequestData:
                OrganizationEmailId = RequestData['OrganizationEmailId']
                OrganizationMobileNo = RequestData['OrganizationMobileNo']
            if (LicKey.isspace() == True or LicKey == '') or (
                    OrganizationEmailId.isspace() == True or OrganizationEmailId == '') or (
                    OrganizationMobileNo.isspace() == True or OrganizationMobileNo == ''):
                response = {'category': "0", 'message': 'All fields are mandatory.'}
            else:
                OrganizationEmailId = OrganizationEmailId.strip()
                OrganizationMobileNo = OrganizationMobileNo.strip()
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                tablename = "OrganizationDetails"
                wherecondition = "LicKey ='" + LicKey + "' and IsActive=1 and IsDelete=0'"
                fields = ""
                order = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    tablename = "OrganizationDetails"
                    wherecondition = "LicKey ='" + LicKey + "' and IsActive=1 and IsDelete=0"
                    values = {'OrganizationEmailId': OrganizationEmailId,
                              'OrganizationMobileNo': OrganizationMobileNo}
                    Update_profile = DB.updateData(tablename, values, wherecondition)
                    response = {'category': '1', 'message': 'Profile updated successfully.'}
                else:
                    response = {'category': '0', 'message': 'Some data base error.'}
            response = make_response(jsonify(response))
            return response


# CHANGE PASSWORD
class RcAPIChangePassword(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            oldPassword = newPassword = confirmPassword = ''
            RequestData = request.get_json()
            if 'oldPassword' in RequestData and 'newPassword' in RequestData and 'confirmPassword' in RequestData and 'emailId' in RequestData:
                oldPassword = RequestData['oldPassword']
                newPassword = RequestData['newPassword']
                confirmPassword = RequestData['confirmPassword']
                emailId = RequestData['emailId']
            if (LicKey.isspace() == True or LicKey == '') or (oldPassword.isspace() == True or oldPassword == '') or (
                    newPassword.isspace() == True or newPassword == '') or (
                    confirmPassword.isspace() == True or confirmPassword == '') or (
                    emailId.isspace() == True or emailId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
                response = make_response(jsonify(response))
                return response
            else:
                oldPassword = oldPassword.strip()
                newPassword = newPassword.strip()
                confirmPassword = confirmPassword.strip()
                if newPassword == confirmPassword:
                    md5oldpassword = hashlib.md5()
                    md5oldpassword.update(oldPassword.encode("utf-8"))
                    oldhashpass = md5oldpassword.hexdigest()
                    md5newpassword = hashlib.md5()
                    md5newpassword.update(newPassword.encode("utf-8"))
                    newhashpass = md5newpassword.hexdigest()
                    tablename = 'OrganizationDetails'
                    wherecondition = "`LicKey`= '" + LicKey + "' and OrganizationEmailId='" + emailId + "'"
                    order = ' OrganizationEmailId DESC'
                    fields = ""
                    dataRecords = DB.retrieveAllData(tablename, fields, wherecondition, order)
                    ResponseData = dataRecords
                    if len(ResponseData) > 0:
                        if ResponseData[0]['OrganizationPassword'] == oldhashpass:
                            values = {'OrganizationPassword': newhashpass}
                            showMsg = DB.updateData(tablename, values, wherecondition)
                            if showMsg['messageType'] == 'success':
                                response = {'category': "1", 'message': "Password updated successfully"}
                                response = make_response(jsonify(response))
                                return response
                            else:
                                response = {'category': "0", 'message': "Sorry! error occured. Please try again later."}
                                response = make_response(jsonify(response))
                                return response
                        else:
                            response = {'category': "0", 'message': "Sorry! Credential do not match (Old Password)."}
                            response = make_response(jsonify(response))
                            return response
                    else:
                        response = {'category': "0", 'message': "Sorry! your credential not valid."}
                        response = make_response(jsonify(response))
                        return response
                else:
                    response = {'category': "0", 'message': "Sorry! new password and confirm password do not match!"}
                    response = make_response(jsonify(response))
                    return response


# OLD PASSWORD VERIFICATION
class RcAPIOldPassword(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            oldPassword = ''
            emailId = ''
            RequestData = request.get_json()
            if 'oldPassword' in RequestData and 'emailId' in RequestData:
                oldPassword = RequestData['oldPassword']
                emailId = RequestData['emailId']
            if (LicKey.isspace() == True or LicKey == '') or (oldPassword.isspace() == True or oldPassword == '') or (
                    emailId.isspace() == True or emailId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                oldPassword = oldPassword.strip()
                emailId = emailId.strip()
                md5oldpassword = hashlib.md5()
                md5oldpassword.update(oldPassword.encode("utf-8"))
                oldhashpass = md5oldpassword.hexdigest()
                querry = "select OrganizationPassword from OrganizationDetails where `LicKey`='" + LicKey + "' and OrganizationEmailId='" + emailId + "'"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    password = ResponseData[0]['OrganizationPassword']
                    if password == oldhashpass:
                        response = {'category': "1", 'message': "Success"}
                    else:
                        response = {'category': "0", 'message': "Sorry! Invalid Password"}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
            response = make_response(jsonify(response))
            return response


# API FOR  MULTIPLE ENROLL LISTING
class RcAPIGetMultipleEnroll(Resource):
    def post(self):
        VURS = authVerifyUser.authServices()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are required."}
            else:
                tablename = 'DatasetEncodings'
                wherecondition = "`LicKey`= '" + LicKey + "'"
                order = "DatasetEncodingsId ASC"
                fields = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# API FOR GET SINGLE ENROLL LIST
class RcAPIEnroll(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # master id as a employee id
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'DatasetEncodings'
                wherecondition = "`LicKey`= '" + LicKey + "' and `EmpId`= '" + MasterId + "'"
                order = ""
                fields = "DatasetEncodingsId,ImagePath,EmpId,EmpName"
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response

    # DELETE EMPLOYEE ENROLLMENT
    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # masterid as a TABLE UNIQUE ID
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'DatasetEncodings'
                wherecondition = "`LicKey`= '" + LicKey + "' AND `DatasetEncodingsId`= '" + MasterId + "'"
                Querry = "select * from DatasetEncodings where LicKey= '" + LicKey + "' AND `DatasetEncodingsId`= '" + MasterId + "'"
                CountEncodings = DB.selectAllData(Querry)
                if len(CountEncodings) > 0:
                    delete1 = DB.deleteSingleRow(tablename, wherecondition)
                    response = {'category': "1", 'message': "Deletion of Enrolled Employee successfull."}
                else:
                    response = {'category': "0", 'message': "Error!The Enrollment Id Doesn't Exist."}
            response = make_response(jsonify(response))
            return response

    # EMPLOYEE ENROLLMENT
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID AS a Employee Id
            # File image as base64 encoded
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            EmpName = ''
            EmpId = ''
            BaseLocationId = ''
            ImagePath = ''
            if 'EmpName' in RequestData and 'EmpId' in RequestData and 'BaseLocationId' in RequestData and 'ImagePath' in RequestData:
                EmpName = RequestData['EmpName']
                EmpId = RequestData['EmpId']
                BaseLocationId = RequestData['BaseLocationId']
                ImagePath = RequestData['ImagePath']
            now = datetime.now()
            createdDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (EmpName.isspace() == True or EmpName == '') or (
                    EmpId.isspace() == True or EmpId == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    ImagePath == [] or ImagePath == [''] or ImagePath == [' ']):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpName = EmpName.strip()
                EmpId = EmpId.strip()
                BaseLocationId = BaseLocationId.strip()
                len(ImagePath)
                tablename = "EmployeeRegistration"
                order = ""
                fields = ""
                wherecondition = "`LicKey`='" + LicKey + "' AND `EmpId`='" + EmpId + "' AND `IsActive` = '1'"
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    photo = ''
                    prefixDir = 'static/'
                    directory = 'public/face-video/'
                    slass = str('/')
                    licDirectory = str(directory + LicKey)
                    licEmployeeDirectory = str(licDirectory + slass + EmpId)

                    if not os.path.exists(prefixDir + directory):
                        os.makedirs(prefixDir + directory)

                    if not os.path.exists(prefixDir + licDirectory):
                        os.makedirs(prefixDir + licDirectory)

                    if not os.path.exists(prefixDir + licEmployeeDirectory):
                        os.makedirs(prefixDir + licEmployeeDirectory)

                    for i in range(len(ImagePath)):
                        singleImageData = ImagePath[i]
                        imageBlobStr = singleImageData.replace("data:image/png;base64,", '')
                        imageBlobStr = bytes(imageBlobStr, 'ascii')
                        no = str(i)
                        fileNameAsTime = datetime.now().strftime("%Y%m%d%H%M%S")
                        imageName = str(fileNameAsTime + no + '.png')
                        shortImagePath = str(licEmployeeDirectory + slass + imageName)
                        image_path = str(prefixDir + licEmployeeDirectory + slass + imageName)
                        with open(image_path, "wb") as fh:
                            fh.write(base64.decodebytes(imageBlobStr))
                        knownFaceEncodings = []
                        knownFaceNames = []
                        name1 = EmpId + "_" + EmpName
                        emp_id_split = name1.split('_', 3)
                        c1 = name1 + "_image"
                        c2 = name1 + "_face_encoding"
                        c1 = face_recognition.load_image_file(image_path)
                        c2 = face_recognition.face_encodings(c1)
                        if len(c2) > 0:
                            c2 = c2[0]
                        knownFaceEncodings.append(c2)
                        knownFaceNames.append(name1)
                        IsActive = "1"
                        path = prefixDir + shortImagePath
                        strLoop = "NULL,'" + EmpId + "','" + EmpName + "'" + ",'" + IsActive + "','" + LicKey + "','" + path + "',"
                        n = len(c2)
                        j = 0
                        for j in range(len(c2)):
                            if j < 127:
                                strLoop += (str(c2[j])) + ","
                            else:
                                strLoop += str(c2[j])
                        if (n > 0):
                            tablename = "DatasetEncodings"
                            wherecondition = "`EmpId` = '" + EmpId + "' AND `LicKey` = '" + LicKey + "'"
                            order = ''
                            fields = ""
                            ResponseData1 = DB.retrieveAllData(tablename, fields, wherecondition, order)
                            countlen = len(ResponseData1)
                            countlen = int(countlen)
                            if countlen < 12:
                                # print(str(countlen) + "12 if")
                                sql_encoding = "INSERT INTO `DatasetEncodings`  VALUES (" + strLoop + "," + BaseLocationId + ")"
                                showmessage = DB.directinsertData(sql_encoding)
                                tablename = "EmployeeRegistration"
                                values = {'IsEnrolled': str(1)}
                                wherecondition = "EmpId='" + EmpId + "' and LicKey='" + LicKey + "'"
                                DB.updateData(tablename, values, wherecondition)
                                response = {'category': '1',
                                            'message': "Congratulation! your employee enroll successfully."}
                                ResponseData = make_response(jsonify(response))
                            elif countlen == 12:
                                # print(str(countlen) + "12 else")
                                response = {'category': 'error',
                                            'feedback': "Sorry! already you added maximum no of image for profile."}
                                ResponseData = make_response(jsonify(response))
                            else:
                                # print(str(countlen) + "12 else")
                                response = {'category': 'error',
                                            'feedback': "Sorry! already you added maximum no of image for profile."}
                                ResponseData = make_response(jsonify(response))
                        else:
                            response = {'category': "error",
                                        'feedback': "Enrollment of this employee not gone well! Please enroll again."}
                            ResponseData = make_response(jsonify(response))
                else:
                    response = {'category': "0", 'message': "Sorry! this account is invalid or inactive."}
            response = make_response(jsonify(response))
            return response


# API FOR GET ENROLLED EMPLOYEE DETILAS
class RcAPIEnrollEmployeeDetails(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # master id as a employee id
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                querry = "select A.ImagePath, A.EmpName,B.EmailId from DatasetEncodings AS A , EmployeeRegistration AS B where A.EmpId='" + MasterId + "' and B.EmpId='" + MasterId + "' and  A.LicKey='" + LicKey + "' "
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:

                    response = {'category': "1", 'message': "Details of Enrolled Employee",
                                'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found!"}

            response = make_response(jsonify(response))
            return response


class RcAPIDeleteEnrolldEmployee(Resource):
    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            imagePath = ''
            if 'imagePath' in RequestData:
                imagePath = RequestData['imagePath']
            # master id as a employee id
            if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == '') or (
                    imagePath.isspace() == True or imagePath == ''):
                response = {'category': "0", 'message': "All fields are manadatory."}
            else:
                imagePath = imagePath.strip()
                querry = "select * from DatasetEncodings where  EmpId='" + MasterId + "' and ImagePath='" + str(
                    imagePath) + "' and LicKey='" + LicKey + "'"
                responseData = DB.selectAllData(querry)
                if len(responseData):
                    tablename = "DatasetEncodings"
                    wherecondition = "EmpId='" + MasterId + "' and ImagePath='" + str(
                        imagePath) + "' and LicKey='" + LicKey + "'"
                    querry = "select * from DatasetEncodings where EmpId='" + MasterId + "' and ImagePath='" + str(
                        imagePath) + "' and LicKey='" + LicKey + "' "
                    countEncodings = DB.selectAllData(querry)
                    showmessage = DB.deleteSingleRow(tablename, wherecondition)
                    response = {'category': '1', 'message': 'Enrolled profile image deleted successfully.'}
                else:
                    response = {'category': '0', 'message': 'no data to delete'}
            response = make_response(jsonify(response))
            return response


# DAILY REPORT
class RcAPIDailyReport(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            StartDate = ''
            if 'StartDate' in RequestData:
                StartDate = RequestData['StartDate']
            if (LicKey.isspace() == True or LicKey == '') or (StartDate.isspace() == True or StartDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory.", 'RequestData': RequestData}
            else:
                StartDate = StartDate.strip()
                # querry = "select '1' as Status,A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + StartDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId"
                # ResponseData = DB.selectAllData(querry)

                # enterpriseDailyReport="select '1' as Status,A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName,(SELECT CameraName FROM Camera WHERE CameraId IN(select Source from ActivityDetails where ADTime IN (SELECT convert(max(ADTime),char) from ActivityDetails WHERE LicKey='"+LicKey+"' and EmpId=A.EmpId) and LicKey='"+LicKey+"') and LicKey='"+LicKey+"') AS LastSeenCamera,(SELECT CameraName FROM Camera WHERE CameraId IN(select Source from ActivityDetails where ADTime IN (SELECT convert(min(ADTime),char) from ActivityDetails WHERE LicKey='"+LicKey+"' and EmpId=A.EmpId) and LicKey='"+LicKey+"') and LicKey='"+LicKey+"') AS FirstSeenCamera from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='"+StartDate+"' and E.LicKey='"+LicKey+"') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='"+LicKey+"' group by A.EmployeeShiftHistoryId"

                enterpriseDailyReport = "select '1' as Status,A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName, CASE When CAST(min(A.ADTime) AS TIME) > D.ShiftMargin THEN CONVERT(TIMEDIFF (CAST(min(A.ADTime) AS TIME),D.ShiftMargin) ,CHAR) END AS LateDuration ,(SELECT CameraName FROM Camera WHERE CameraId IN(select Source from ActivityDetails where ADTime IN (SELECT convert(max(ADTime),char) from ActivityDetails WHERE LicKey='" + LicKey + "' and EmpId=A.EmpId) and LicKey='" + LicKey + "') and LicKey='" + LicKey + "') AS LastSeenCamera,(SELECT CameraName FROM Camera WHERE CameraId IN(select Source from ActivityDetails where ADTime IN (SELECT convert(min(ADTime),char) from ActivityDetails WHERE LicKey='" + LicKey + "' and EmpId=A.EmpId) and LicKey='" + LicKey + "') and LicKey='" + LicKey + "') AS FirstSeenCamera from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + StartDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by B.EmployeeRegistrationId"
                ResponseData = DB.selectAllData(enterpriseDailyReport)
                if ResponseData:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not Found."}
                response = make_response(jsonify(response))
                return response


class RcAPIUserReport(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            EmpId = SearchMonth = SearchYear = ''
            if 'EmpId' in RequestData and 'SearchMonth' in RequestData and 'SearchYear' in RequestData:
                EmpId, SearchMonth, SearchYear = RequestData['EmpId'], RequestData['SearchMonth'], RequestData[
                    'SearchYear']
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == '') or (
                    SearchMonth.isspace() == True or SearchMonth == '') or (
                    SearchYear.isspace() == True or SearchYear == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:

                EmpId = EmpId.strip()
                SearchMonth = SearchMonth.strip()
                SearchYear = SearchYear.strip()
                AttendanceMonth = SearchMonth
                AttendanceYear = SearchYear
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                currentYear = now.strftime('%Y')
                currentMonth = now.strftime('%m')
                currentMonthdate = now.strftime('%d')
                newreportlist = []
                isCurrentMonth = ''
                if AttendanceYear > currentYear:

                    response = {'category': "1", 'message': "User Report List", 'ResponseData': newreportlist}
                elif AttendanceYear == currentYear and currentMonth < AttendanceMonth:

                    response = {'category': "1", 'message': "User Report List", 'ResponseData': newreportlist}

                else:
                    Queryemployeedetails = "SELECT * FROM EmployeeRegistration WHERE EmpId='" + EmpId + "' AND LicKey='" + LicKey + "' LIMIT 1"
                    Queryforreport = "Select A.EmpId, B.EmpName, convert(A.ADDate,CHAR) AS ADDate, CONVERT(MIN(A.ADTime),CHAR) AS FirstSeen, CONVERT(MAX(A.ADTime),CHAR) AS LastSeen, CONVERT(TIMEDIFF(MAX(A.ADTime),MIN(A.ADTime)),CHAR) AS TotalHours, CONVERT(ADDTIME((TIMEDIFF(CONVERT(MAX(A.ADTime),TIME),C.EndTime)),(TIMEDIFF(C.ShiftMargin,CONVERT(min(A.ADTime),TIME)))),CHAR) AS TimeDifference, C.ShiftName, CONVERT(C.StartTime,CHAR) AS StartTime, CONVERT(C.EndTime,CHAR) AS EndTime FROM ActivityDetails AS A, EmployeeRegistration AS B, ShiftMaster AS C WHERE A.EmpId=B.EmpId and A.ShiftMasterId=C.ShiftMasterId AND A.EmpId='" + EmpId + "' AND EXTRACT(MONTH FROM ADDate)='" + SearchMonth + "' and EXTRACT(YEAR FROM ADDate)='" + SearchYear + "'  and A.LicKey='" + LicKey + "' GROUP BY A.EmpId,A.EmployeeShiftHistoryId"
                    # print(Queryforreport)
                    employeedetails = DB.selectAllData(Queryemployeedetails)
                    reportlist = DB.selectAllData(Queryforreport)
                    extraleave = []
                    # ShiftMasterId = reportlist[0]['ShiftMasterId']
                    monthdays_list = calendar.monthcalendar(int(AttendanceYear), int(AttendanceMonth))
                    allMonthdatesArray = []
                    multiWeekArray = []
                    for aryIndex in range(len(monthdays_list)):
                        weeklyDayDateAppendAry = []
                        weeklyDaynoArray = monthdays_list[aryIndex]
                        for weekaryIndex in range(len(weeklyDaynoArray)):
                            singleWeekArray = []
                            singleDayno = weeklyDaynoArray[weekaryIndex]
                            date = str(singleDayno) + "-" + str(AttendanceMonth) + "-" + str(AttendanceYear)
                            passdate = str(AttendanceYear) + "-" + str(AttendanceMonth) + "-" + str(singleDayno)
                            if singleDayno != 0:
                                DayName = findDay(date)
                                # For Get month all Date
                                AttendanceDate_str = str(singleDayno)
                                AttendanceMonth_str = str(AttendanceMonth)
                                AttendanceDate_str = AttendanceDate_str.zfill(2)
                                AttendanceMonth_str = AttendanceMonth_str.zfill(2)
                                assigndate = str(AttendanceYear) + "-" + str(AttendanceMonth_str) + "-" + str(
                                    AttendanceDate_str)
                                allMonthdatesArray.append(assigndate)
                                datewisesingleArray = {"DayName": DayName, "Date": assigndate}
                            else:
                                datewisesingleArray = ""
                            weeklyDayDateAppendAry.append(datewisesingleArray)
                        multiWeekArray.append(weeklyDayDateAppendAry)
                    mothfirstdate = allMonthdatesArray[0]
                    QsShiftList = "select ShiftMasterId from EmployeeShiftHistory where EmpId='" + EmpId + "' and ShiftMonth='" + str(
                        AttendanceMonth) + "' and ShiftYear='" + str(
                        AttendanceYear) + "' ORDER BY StartDate ASC LIMIT 1"
                    RsShiftList = DB.selectAllData(QsShiftList)
                    if len(RsShiftList) > 0:
                        ShiftMasterId = str(RsShiftList[0]['ShiftMasterId'])
                    else:
                        ShiftMasterId = '0'
                    if len(employeedetails) > 0:
                        EmpName = str(employeedetails[0]['EmpName'])
                    else:
                        EmpName = "N/A"
                    qsQuerryForWeekEndList = "SELECT WeekendDetailsId,BaseLocationId,ShiftMasterId,ShiftMonth,DayName,AllWeek,FirstWeek,SecondWeek,ThirdWeek,FourthWeek,FifthWeek FROM WeekendDetails WHERE LicKey = '" + LicKey + "' AND ShiftMasterId= '" + str(
                        ShiftMasterId) + "' AND ShiftMonth= '" + str(AttendanceMonth) + "' AND IsDelete = 0 "
                    rsQuerryForWeekEndList = DB.selectAllData(qsQuerryForWeekEndList)
                    WeekendDates = []
                    for countIndex in range(len(rsQuerryForWeekEndList)):
                        FirstWeekData = rsQuerryForWeekEndList[countIndex]['FirstWeek']
                        SecondWeekData = rsQuerryForWeekEndList[countIndex]['SecondWeek']
                        ThirdWeekData = rsQuerryForWeekEndList[countIndex]['ThirdWeek']
                        FourthWeekData = rsQuerryForWeekEndList[countIndex]['FourthWeek']
                        FifthWeekData = rsQuerryForWeekEndList[countIndex]['FifthWeek']
                        WeekEndDayName = rsQuerryForWeekEndList[countIndex]['DayName']
                        if FirstWeekData == "on":
                            if multiWeekArray[0] != "":
                                for j in range(len(multiWeekArray[0])):
                                    if multiWeekArray[0][j] != "":
                                        if multiWeekArray[0][j]['DayName'] == WeekEndDayName:
                                            WeekendDates.append(multiWeekArray[0][j]['Date'])

                        if SecondWeekData == "on":
                            if multiWeekArray[1] != "":
                                for j in range(len(multiWeekArray[1])):
                                    if multiWeekArray[1][j] != "":
                                        if multiWeekArray[1][j]['DayName'] == WeekEndDayName:
                                            WeekendDates.append(multiWeekArray[1][j]['Date'])

                        if ThirdWeekData == "on":
                            if multiWeekArray[2] != "":
                                for j in range(len(multiWeekArray[2])):
                                    if multiWeekArray[2][j] != "":
                                        if multiWeekArray[2][j]['DayName'] == WeekEndDayName:
                                            WeekendDates.append(multiWeekArray[2][j]['Date'])
                        if FifthWeekData == "on":
                            if multiWeekArray[3] != "":
                                for j in range(len(multiWeekArray[3])):
                                    if multiWeekArray[3][j] != "":
                                        if multiWeekArray[3][j]['DayName'] == WeekEndDayName:
                                            WeekendDates.append(multiWeekArray[3][j]['Date'])
                        if FifthWeekData == "on":
                            if multiWeekArray[4] != "":
                                for j in range(len(multiWeekArray[4])):
                                    if multiWeekArray[4][j] != "":
                                        if multiWeekArray[4][j]['DayName'] == WeekEndDayName:
                                            WeekendDates.append(multiWeekArray[4][j]['Date'])
                    allUserReportList = []
                    cntLeave = cntHoliday = cntCompOff = cntWeekend = 0
                    for dateIndex in range(len(allMonthdatesArray)):
                        IsLeave = IsHoliday = IsCompOff = IsWeekend = "No"
                        getActivityDetails = 0
                        CheckDate = str(allMonthdatesArray[dateIndex])
                        if CheckDate in WeekendDates:
                            IsWeekend = "Yes"
                            cntWeekend = cntWeekend + 1
                        # Check Holiday Is present or Not
                        qsQuerryHolidayList = "SELECT Convert(SetDate,CHAR) AS SetDate,Holiday FROM HolidayList WHERE LicKey = '" + LicKey + "' AND IsActive = 1  AND SetDate= '" + CheckDate + "'"
                        rsQuerryHolidayList = DB.selectAllData(qsQuerryHolidayList)
                        if len(rsQuerryHolidayList) > 0:
                            cntHoliday = cntHoliday + 1
                            IsHoliday = "Yes"

                        # Check Leave Is present or Not
                        qsQuerryLeaveList = "SELECT Convert(LeaveDate,CHAR) AS LeaveDate,LeavePurpose FROM EmployeeLeaveHistory WHERE LicKey = '" + LicKey + "' AND EmpId= '" + EmpId + "' AND LeaveDate= '" + CheckDate + "' AND Status = 1"
                        rsQuerryLeaveList = DB.selectAllData(qsQuerryLeaveList)
                        if len(rsQuerryLeaveList) > 0:
                            cntLeave = cntLeave + 1
                            IsLeave = "Yes"

                        # Check CompOff Is present or Not
                        qsQuerryCompOffList = "SELECT Convert(OffDate,CHAR) AS OffDate FROM CompOff WHERE LicKey = '" + LicKey + "' AND EmpId= '" + EmpId + "' AND Status = 1 AND OffDate= '" + CheckDate + "'"
                        rsQuerryCompOffList = DB.selectAllData(qsQuerryCompOffList)
                        if len(rsQuerryCompOffList) > 0:
                            cntCompOff = cntCompOff + 1
                            IsCompOff = "Yes"

                        if len(reportlist) > 0:
                            for reportIndex in range(len(reportlist)):
                                if CheckDate == reportlist[reportIndex]['ADDate']:
                                    singleDateReport = {}
                                    singleDateReport['EmpId'] = reportlist[reportIndex]['EmpId']
                                    singleDateReport['EmpName'] = reportlist[reportIndex]['EmpName']
                                    singleDateReport['ADDate'] = reportlist[reportIndex]['ADDate']
                                    singleDateReport['FirstSeen'] = reportlist[reportIndex]['FirstSeen']
                                    singleDateReport['LastSeen'] = reportlist[reportIndex]['LastSeen']
                                    singleDateReport['ShiftName'] = reportlist[reportIndex]['ShiftName']
                                    singleDateReport['TimeDifference'] = reportlist[reportIndex]['TimeDifference']
                                    singleDateReport['StartTime'] = reportlist[reportIndex]['StartTime']
                                    singleDateReport['EndTime'] = reportlist[reportIndex]['EndTime']
                                    singleDateReport['TotalHours'] = reportlist[reportIndex]['TotalHours']
                                    if IsHoliday == 'Yes':
                                        singleDateReport['Status'] = "Holiday/Present"
                                    elif IsWeekend == 'Yes':
                                        singleDateReport['Status'] = "Weekend/Present"
                                    else:
                                        singleDateReport['Status'] = "Present"
                                    singleDateReport['IsView'] = "1"
                                    getActivityDetails = getActivityDetails + 1
                                    newreportlist.append(singleDateReport)
                                    break
                        if getActivityDetails == 0:
                            lengthofnewactivity = len(newreportlist)
                            if lengthofnewactivity > 0:
                                arrayindex = lengthofnewactivity + 1
                            else:
                                arrayindex = 0
                            singleDateReport = {}
                            singleDateReport['EmpId'] = EmpId
                            singleDateReport['EmpName'] = EmpName
                            singleDateReport['ADDate'] = CheckDate
                            singleDateReport['FirstSeen'] = "N/A"
                            singleDateReport['LastSeen'] = "N/A"
                            singleDateReport['ShiftName'] = "N/A"
                            singleDateReport['TimeDifference'] = "00:00:00"
                            singleDateReport['StartTime'] = "N/A"
                            singleDateReport['EndTime'] = "N/A"
                            singleDateReport['TotalHours'] = "00:00:00"
                            status = ""
                            if IsHoliday == 'Yes':
                                if IsWeekend == 'Yes':
                                    status = "Holiday/Weekend"
                                else:
                                    status = "Holiday"
                            elif IsWeekend == 'Yes':
                                status = "Weekend"
                            elif IsLeave == 'Yes':
                                status = "Leave"
                            elif IsCompOff == 'Yes':
                                status = "CompOff Leave"
                            else:
                                status = "Absent"
                            singleDateReport['Status'] = status
                            singleDateReport['IsView'] = "0"
                            newreportlist.append(singleDateReport)
                        if today == CheckDate:
                            break
                    response = {'category': "1", 'message': "User Report List", 'ResponseData': newreportlist}
        response = make_response(jsonify(response))
        return response


class RcAPIDailyRecentImages(Resource):
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            ADDate = ''
            if 'ADDate' in RequestData:
                ADDate = RequestData['ADDate']
            if (LicKey.isspace() == True or LicKey == '') or (ADDate.isspace() == True or ADDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                ADDate = ADDate.strip()
                resultData = []
                # now = datetime.now()
                # ADDate = now.strftime('%Y-%m-%d')
                QUERY = "Select EmpId,FileLocation,EmpImage,convert(ADDate,char) AS ADDate from ActivityDetails where LicKey= '" + LicKey + "' AND EmpId='" + MasterId + "' and ADDate='" + ADDate + "'"
                ResponseData = DB.selectAllData(QUERY)
                QUERY1 = "Select EmpImage from ActivityDetails where LicKey= '" + LicKey + "' AND EmpId='" + MasterId + "' and ADDate='" + ADDate + "'"
                ResponseData1 = DB.selectAllData(QUERY1)
                response = {'category': "1", 'message': "List of daily recent images on a particular date",
                            'EmpImage': ResponseData}
        response = make_response(jsonify(response))
        return response


class RcAPISingleTimesheet(Resource):
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            StartDate = ''
            EndDate = ''
            if 'StartDate' in RequestData and 'EndDate' in RequestData:
                StartDate = RequestData['StartDate']
                EndDate = RequestData['EndDate']
            if (LicKey.isspace() == True or LicKey == '') or (StartDate.isspace() == True or StartDate == '') or (
                    EndDate.isspace() == True or EndDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                StartDate = StartDate.strip()
                EndDate = EndDate.strip()
                sql_fetch_data1 = "SELECT EmpImage FROM ActivityDetails WHERE EmpId = '" + MasterId + "'  AND LicKey='" + LicKey + "' Group BY EmpId "
                ResponseData1 = DB.selectAllData(sql_fetch_data1)
                sql_fetch_data = "SELECT ActivityDetailsId,convert(ADDate,char) AS ADDate,convert(ADTime,char) AS ADTime,EmpImage FROM ActivityDetails WHERE EmpId = '" + MasterId + "' AND ADDate <= '" + EndDate + "' AND ADDate >='" + StartDate + "' AND LicKey='" + LicKey + "' ORDER BY ActivityDetailsId DESC"
                ResponseData = DB.selectAllData(sql_fetch_data)
                response = {'category': "1", 'message': "List of daily recent images in a range",
                            'ResponseData': ResponseData, 'ResponseData1': ResponseData1}
        response = make_response(jsonify(response))
        return response


# ALL ACTIVITY LIST REPORT
class RcAPIAllActivityReport(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # RequestData = request.get_json()
            # if not RequestData:
            # abort(400)
            # StartDate = ''
            '''if 'StartDate' in RequestData:
                StartDate = RequestData['StartDate']'''
            if LicKey == '':  # or StartDate == ''
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                now = datetime.now()
                ADDate = now.strftime('%Y-%m-%d')
                # querry="Select A.EmpId,B.EmpName,convert(A.ADTime,char) AS  ADTime,A.Source,A.EmpImage,convert(A.ADDate,char) AS ADDate from ActivityDetails as A,EmployeeRegistration as B where A.EmpId=B.EmpId and A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + StartDate + "' and E.LicKey='" + LicKey + "') and A.LicKey='" + LicKey + "'  order by A.ADTime DESC Limit 50"#group by A.EmployeeShiftHistoryId
                querry = "Select A.EmpId,B.EmpName,convert(cast(A.ADTime as time(0)),char) AS ADTime,A.Source,C.CameraName,A.EmpImage,convert(A.ADDate,char) AS ADDate from EmployeeRegistration as B , ActivityDetails as A LEFT JOIN Camera AS C ON (C.CameraId=A.Source and C.LicKey='" + LicKey + "') where A.EmpId=B.EmpId and A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.LicKey='" + LicKey + "') and A.LicKey='" + LicKey + "' order by A.ADTime DESC Limit 50"  # group by A.EmployeeShiftHistoryId
                # print(querry)
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "List of recent report.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# All activity report
class RcAPIRecentReport(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if (LicKey.isspace() == True or LicKey == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                now = datetime.now()
                Today = now.strftime('%Y-%m-%d')
                # Today='2020-12-10'
                # querry="Select A.EmpId,B.EmpName,convert(A.ADTime,char) AS ADTime,A.Source,A.EmpImage,convert(A.ADDate,char) AS ADDate from ActivityDetails as A,EmployeeRegistration as B where A.EmpId=B.EmpId and A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='"+Today+"' and E.LicKey='"+LicKey+"') and A.LicKey='"+LicKey+"' group by A.EmployeeShiftHistoryId order by A.ADDate DESC"
                querry = "Select A.EmpId,B.EmpName,convert(A.ADTime,char) AS ADTime,A.Source,A.EmpImage,convert(A.ADDate,char) AS ADDate from ActivityDetails as A,EmployeeRegistration as B where A.EmpId=B.EmpId and A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + Today + "' and E.LicKey='" + LicKey + "') and A.LicKey='" + LicKey + "'  order by A.ADTime DESC"
                # print(querry)
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "List of recent report.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# to get the check in and check out time of each employee based on time
class RcAPIAttendanceInfo(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            ADDate = ''
            EmpId = ''
            if 'ADDate' in RequestData and 'EmpId' in RequestData:
                ADDate = RequestData['ADDate']
                EmpId = RequestData['EmpId']
            if (LicKey.isspace() == True or LicKey == '') or (ADDate.isspace() == True or ADDate == '') or (
                    EmpId.isspace() == True or EmpId == ''):
                response = {'category': "0", 'message': "All fields are mandatory.", 'RequestData': RequestData}
            else:
                ADDate = ADDate.strip()
                EmpId = EmpId.strip()
                QUERY1 = "SELECT A.Source,CONVERT(A.ADTime,char) AS ADTime,A.EmpImage,B.CameraName FROM `ActivityDetails` AS A Left Join Camera AS B ON(A.Source=B.CameraId and B.LicKey='" + LicKey + "') where A.EmpId='" + EmpId + "' and A.ADDate='" + ADDate + "' and A.LicKey='" + LicKey + "' ORDER BY A.ADTime ASC"
                QUERY2 = "Select A.EmpName,DAYNAME(B.ADDate) AS DayName,convert(B.ADDate,CHAR) AS ADDate,CONVERT(min(B.ADTime),CHAR) as FirstSeen,CONVERT(max(B.ADTime),CHAR) as LastSeen,CONVERT(TIMEDIFF(max(B.ADTime),min(B.ADTime)),CHAR) AS TotalHours from ActivityDetails AS B,EmployeeRegistration AS A where B.EmpId='" + EmpId + "' and B.ADDate='" + ADDate + "' and B.LicKey='" + LicKey + "' and A.EmpId=B.EmpId"
                ResponseData = DB.selectAllData(QUERY1)
                ResponseData1 = DB.selectAllData(QUERY2)
                allresponse = {'timesheetdetails': ResponseData1, 'activitylog': ResponseData}
                response = {'category': "1", 'message': "List of Attendance Info", 'ResponseData': allresponse}
        response = make_response(jsonify(response))
        return response


class RcAPICheckInOut(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            ADDate = ''
            EmpId = ''
            if 'ADDate' in RequestData and 'EmpId' in RequestData:
                ADDate = RequestData['ADDate']
                EmpId = RequestData['EmpId']
            if (LicKey.isspace() == True or LicKey == '') or (ADDate.isspace() == True or ADDate == '') or (
                    EmpId.isspace() == True or EmpId == ''):
                response = {'category': "0", 'message': "All fields are mandatory.", 'RequestData': RequestData}
            else:
                ADDate = ADDate.strip()
                EmpId = EmpId.strip()
                QUERY1 = "select A.ActivityDetailsId,B.EmpName,CONVERT(A.ADTime,CHAR) AS ADTime from ActivityDetails AS A,EmployeeRegistration AS B where A.EmployeeShiftHistoryId IN (select C.EmployeeShiftHistoryId from EmployeeShiftHistory AS C where C.StartDate='" + ADDate + "' and C.EmpId='" + EmpId + "' and C.LicKey='" + LicKey + "') and A.EmpId=B.EmpId ORDER BY A.ADTime ASC"
                # print(QUERY1)
                ResponseData = DB.selectAllData(QUERY1)
                if len(ResponseData) > 0:

                    response = {'category': "1", 'message': "List of Check In & Out", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
        response = make_response(jsonify(response))
        return response


class RcAPICheckInOutDetails(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            ADDate = ''
            EmpId = ''
            if 'ADDate' in RequestData and 'EmpId' in RequestData:
                ADDate = RequestData['ADDate']
                EmpId = RequestData['EmpId']
            if (LicKey.isspace() == True or LicKey == '') or (ADDate.isspace() == True or ADDate == '') or (
                    EmpId.isspace() == True or EmpId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                ADDate = ADDate.strip()
                EmpId = EmpId.strip()
                QUERY1 = "select A.ActivityDetailsId,CONVERT(A.ADTime,CHAR) AS ADTime from ActivityDetails AS A where A.EmployeeShiftHistoryId IN (select C.EmployeeShiftHistoryId from EmployeeShiftHistory AS C where C.StartDate='" + ADDate + "' and C.EmpId='" + EmpId + "' and C.LicKey='" + LicKey + "') ORDER BY A.ADTime ASC"
                ResponseData1 = DB.selectAllData(QUERY1)
                QUERY2 = "select A.EmpId,B.EmpName,CONVERT(min(A.ADDate),CHAR) AS ADDate,DAYNAME(min(A.ADDate)) AS WeekDayName,CONVERT(min(A.ADTime),CHAR) AS FirstSeen,CONVERT(max(A.ADTime),CHAR) AS LastSeen, CONVERT(TIMEDIFF(max(A.ADTime),min(A.ADTime)),CHAR) AS TimeDifference FROM ActivityDetails AS A,EmployeeRegistration AS B WHERE A.EmployeeShiftHistoryId IN (SELECT EmployeeShiftHistoryId FROM `EmployeeShiftHistory` where StartDate='" + ADDate + "' and LicKey='" + LicKey + "' and EmpId='" + EmpId + "') and A.EmpId=B.EmpId"
                ResponseData2 = DB.selectAllData(QUERY2)
                response = {'category': "1", 'message': "List of Check In & Out Details",
                            'ResponseData2': ResponseData2, 'ResponseData1': ResponseData1}
        response = make_response(jsonify(response))
        return response


# MULTIPLE CAMERALISTING
class RcAPIMultipleCameraList(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                querry = "select A.*,B.LocationName As BaseLocationName from SecretKey AS A,BaseLocation AS B where A.LicKey='" + LicKey + "' and A.BaseLocationId=B.BaseLocationId ORDER BY A.SecretKeyId DESC"
                ResponseData = DB.selectAllData(querry)
                # print(querry)
                if len(ResponseData) > 0:
                    response = {'category': '1', 'message': 'List of Cameras', 'ResponseData': ResponseData}
                else:
                    response = {'category': '0', 'message': 'Data not found'}
            response = make_response(jsonify(response))
            return response


# Organization Details
class RcAPIOrganizationDetails(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                querry = "select OrganizationDetailsId,ZohoAuthKey,IsGeofences,OrganizationName,OrganizationEmailId,OrganizationMobileNo,OrganizationPassword,OrgCountryCode,IssuedDate,CONVERT(IssuedTime,CHAR) AS IssuedTime ,ExpiredDate,CONVERT(ExpiredTime,CHAR)  AS ExpiredTime,LicenseType,LicenseValidInDays,NoOfCameras,ProfileImg,AdminImg,IsActive,IsDelete,CreatedDate,SecretKeyToConfirmProfile from OrganizationDetails where LicKey='" + LicKey + "'"
                ResponseData = DB.selectAllData(querry)
                response = {'category': '1', 'message': 'Organization Details', 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# Country Details
class RcAPICountryDetails(Resource):
    def get(self):
        querry = "select CountryId,CountryName,CountryCode,DialCode,CurrencyName,CurrencySymbol,CurrencyCode,CountryPrice,TaxPercent,CONVERT(CreatedDate,CHAR) AS CreatedDate ,CONVERT(UpdatedDate,CHAR) AS UpdatedDate From Country"
        ResponseData = DB.selectAllData(querry)
        response = {'category': '1', 'message': 'Country Details', 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# CAMERA ADD
class RcAPICameraDetails(Resource):
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            Status = "1"
            CameraType = ""
            CameraSerialNo = ""
            BaseLocationId = ""
            SystemInfo = ""
            # is_active="1"
            if 'CameraType' in RequestData and 'CameraSerialNo' in RequestData and 'BaseLocationId' in RequestData and 'SystemInfo' in RequestData:
                CameraType = RequestData['CameraType']
                CameraSerialNo = RequestData['CameraSerialNo']
                BaseLocationId = RequestData['BaseLocationId']
                SystemInfo = RequestData['SystemInfo']
            now = datetime.now()
            GeneratedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (CameraType.isspace() == True or CameraType == '') or (
                    CameraSerialNo.isspace() == True or CameraSerialNo == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    SystemInfo.isspace() == True or SystemInfo == ''):
                response = {'category': "0", 'message': "All fields are mandatory.", 'RequestData': RequestData}
            else:
                CameraType = CameraType.strip()
                CameraSerialNo = CameraSerialNo.strip()
                BaseLocationId = BaseLocationId.strip()
                SystemInfo = SystemInfo.strip()
                tablename1 = "OrganizationDetails"
                wherecondition1 = "`LicKey`= '" + LicKey + "'"
                fields1 = "NoOfCameras"
                order1 = ""
                ResponseData1 = DB.retrieveAllData(tablename1, fields1, wherecondition1, order1)
                tablename2 = "SecretKey"
                wherecondition2 = "`LicKey`='" + LicKey + "'"
                fields2 = "count(*)"
                order2 = ""
                ResponseData2 = DB.retrieveAllData(tablename2, fields2, wherecondition2, order2)
                NoOfCameras = ResponseData1[0]['NoOfCameras']
                NoOfSecretKey = ResponseData2[0]['count(*)']
                if NoOfCameras > NoOfSecretKey:
                    SecretKey = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    tablename = "SecretKey"
                    values = {'LicKey': LicKey, 'CameraType': CameraType, 'CameraSerialNo': CameraSerialNo,
                              'BaseLocationId': BaseLocationId, 'SecretKey': SecretKey, 'Status': Status,
                              'GeneratedDate': GeneratedDate}
                    showmessage = DB.insertData(tablename, values)
                    # Rs_Insert_secret_key = cursor.lastrowid #handle this
                    if showmessage['messageType'] == 'success':
                        response = {'category': '1', 'message': 'Camera Added Successfully'}
                    else:
                        response = {'category': '0', 'message': 'Database Error.'}
                else:
                    response = {'category': '0', 'message': 'Cannot Add More Camera'}
            response = make_response(jsonify(response))
            return response


# SHIFT LISTING
class RcAPIGetMultiShift(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                # querry = "select A.ShiftMasterId,A.BaseLocationId,A.LicKey, A.ShiftName,MINUTE(TIMEDIFF(A.ShiftMargin ,A.StartTime)) as ShiftMargin,CONVERT(A.StartTime,CHAR) AS StartTime, CONVERT(A.ShiftLength,CHAR) AS ShiftLength,CONVERT(A.EndTime,CHAR) AS EndTime,IsEditable, CONVERT(A.CreatedDate,CHAR) AS CreatedDate,B.LocationName, count(C.EmployeeShiftHistoryId) AS NoOfEmployees from ShiftMaster AS A ,BaseLocation AS B,EmployeeShiftHistory AS C where A.LicKey='"+LicKey+"' and A.BaseLocationId=B.BaseLocationId and A.ShiftMasterId=C.ShiftMasterId group by A.ShiftMasterId ORDER BY ShiftMasterId DESC"
                querry = "select A.ShiftMasterId,A.BaseLocationId,A.LicKey, A.ShiftName,MINUTE(TIMEDIFF(A.ShiftMargin ,A.StartTime)) as ShiftMargin,CONVERT(A.StartTime,CHAR) AS StartTime, CONVERT(A.ShiftLength,CHAR) AS ShiftLength,CONVERT(A.EndTime,CHAR) AS EndTime,IsEditable, CONVERT(A.CreatedDate,CHAR) AS CreatedDate,B.LocationName, count(C.EmployeeShiftHistoryId) AS NoOfEmployees from BaseLocation AS B ,ShiftMaster AS A Left Join EmployeeShiftHistory AS C ON ( A.LicKey='" + LicKey + "' and A.ShiftMasterId=C.ShiftMasterId) where A.BaseLocationId=B.BaseLocationId group by A.ShiftMasterId ORDER BY ShiftMasterId DESC"
                # print(querry)
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': '1', 'message': 'List of active shifts.', 'ResponseData': ResponseData}
                else:
                    response = {'category': '0', 'message': 'Data not found!'}
            response = make_response(jsonify(response))
            return response


# SINGLE SHIFT LIST,ADD SHIFT & DELETE SHIFT
class RcAPIShift(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'ShiftMaster'
                wherecondition = "`LicKey`= '" + LicKey + "' and `ShiftMasterId`= '" + MasterId + "'"
                order = ""
                fields = "ShiftMasterId,BaseLocationId,LicKey,ShiftName,CONVERT(ShiftMargin,CHAR) AS ShiftMargin,CONVERT(StartTime,CHAR) AS StartTime,CONVERT(EndTime,CHAR) AS EndTime,CONVERT(ShiftLength,CHAR) AS ShiftLength,IsNightShift,IsEditable,CONVERT(CreatedDate,CHAR) AS CreatedDate"
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    response = {'category': '1', 'message': 'List of Single Active shift.',
                                'ResponseData': ResponseData}
                else:
                    response = {'category': '0', 'message': 'Data not found!'}
            response = make_response(jsonify(response))
            return response

    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                ResponseData = DB.retrieveAllData('ShiftMaster', "",
                                                  "`LicKey`= '" + LicKey + "' and `ShiftMasterId`= '" + MasterId + "'",
                                                  "")
                if len(ResponseData):
                    ResponseData = DB.retrieveAllData('EmployeeShiftHistory', "",
                                                      "`LicKey`= '" + LicKey + "' and `ShiftMasterId`= '" + MasterId + "'",
                                                      "")
                    if len(ResponseData) > 0:
                        response = {'category': '0', 'message': 'Shift can not delete, already assign.'}
                    else:
                        DB.deleteSingleRow("ShiftMaster",
                                           "`LicKey`= '" + LicKey + "' and `ShiftMasterId`= '" + MasterId + "'")
                        response = {'category': '1', 'message': 'Shift deleted successfully.'}
                else:
                    response = {'category': '0', 'message': 'Data not found'}
            response = make_response(jsonify(response))
            return response

    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID CAN BE ANY THING BUT YOU HAVE TO SEND THERE ANY THING IN URL
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                BaseLocationId = ShiftName = ShiftMargin = StartTime = EndTime = IsNightShift = ''
                if 'BaseLocationId' in RequestData and 'ShiftName' in RequestData and 'ShiftMargin' in RequestData and 'StartTime' in RequestData and 'EndTime' in RequestData:
                    BaseLocationId, ShiftName, ShiftMargin, StartTime, EndTime = RequestData['BaseLocationId'], \
                                                                                 RequestData['ShiftName'], RequestData[
                                                                                     'ShiftMargin'], RequestData[
                                                                                     'StartTime'], RequestData[
                                                                                     'EndTime']
                now = datetime.now()
                created_date = now.strftime('%Y-%m-%d')
                if (StartTime > EndTime):
                    IsNightShift = '1'
                else:
                    IsNightShift = '0'
                if (BaseLocationId.isspace() == True or BaseLocationId == '') or (
                        ShiftName.isspace() == True or ShiftName == '') or (
                        ShiftMargin.isspace() == True or ShiftMargin == '') or (
                        StartTime.isspace() == True or StartTime == '') or (
                        EndTime.isspace() == True or EndTime == '') or (
                        IsNightShift.isspace() == True or IsNightShift == ''):
                    response = {'category': "0", 'message': "All fields are mandatory."}
                else:
                    # Removing space from left and right side
                    BaseLocationId = BaseLocationId.strip()
                    ShiftName = ShiftName.strip()
                    ShiftMargin = ShiftMargin.strip()
                    StartTime = StartTime.strip()
                    EndTime = EndTime.strip()
                    IsNightShift = IsNightShift.strip()
                    querry = "select * from ShiftMaster where ShiftName='" + ShiftName + "' and LicKey='" + LicKey + "' and BaseLocationId='" + BaseLocationId + "'"
                    ShiftResult = DB.selectAllData(querry)
                    # print(ShiftResult)
                    if len(ShiftResult) > 0:
                        response = {'category': "0", 'message': "Shift already exists"}
                    else:
                        if IsNightShift == '1':
                            starttimeshow = datetime.strptime("1900-01-01 " + StartTime, '%Y-%m-%d %H:%M:%S')
                            endtimeshow = datetime.strptime("1900-01-02 " + EndTime, '%Y-%m-%d %H:%M:%S')
                            TimeDifference = endtimeshow - starttimeshow
                            TimeDifferenceinsec = TimeDifference.total_seconds()
                            Intervaltime = int(TimeDifferenceinsec)
                            defaultInterval = ''
                            hour_str = str(Intervaltime // 3600)
                            minute_str = str((Intervaltime % 3600) // 60)
                            second_str = str((Intervaltime % 3600) % 60)
                            hour = hour_str.zfill(2)
                            minute = minute_str.zfill(2)
                            second = second_str.zfill(2)
                            defaultInterval = "{}:{}:{}".format(hour, minute, second)
                            ShiftLength = defaultInterval
                            # error = 0
                        if IsNightShift == '0':
                            FirstStartTime = datetime.strptime(StartTime, '%H:%M:%S')
                            LastEndTime = datetime.strptime(EndTime, '%H:%M:%S')
                            TimeDifference = LastEndTime - FirstStartTime
                            ShiftLength = str(TimeDifference)
                            ShiftLengthArray = ShiftLength.split(':')
                            hour = ShiftLengthArray[0].zfill(2)
                            minute = ShiftLengthArray[1].zfill(2)
                            second = ShiftLengthArray[2].zfill(2)
                            defaultInterval = "{}:{}:{}".format(hour, minute, second)
                            ShiftLength = defaultInterval
                        values = {'LicKey': LicKey, 'BaseLocationId': BaseLocationId, 'ShiftName': ShiftName,
                                  'ShiftMargin': ShiftMargin, 'StartTime': StartTime, 'EndTime': EndTime,
                                  'ShiftLength': ShiftLength, 'IsNightShift': IsNightShift, 'CreatedDate': created_date}
                        showmessage = DB.insertData("ShiftMaster", values)
                        if showmessage['messageType'] == 'success':
                            response = {'category': "1", 'message': "Shift Added Successfully"}
                        else:
                            response = {'category': "0", 'message': "Sorry ! something error in db. try it again."}
                response = make_response(jsonify(response))
                return response

    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID should be shift master id
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                BaseLocationId = ShiftName = ShiftMargin = StartTime = EndTime = IsNightShift = ''
                if 'BaseLocationId' in RequestData and 'ShiftName' in RequestData and 'ShiftMargin' in RequestData and 'StartTime' in RequestData and 'EndTime' in RequestData:
                    BaseLocationId, ShiftName, ShiftMargin, StartTime, EndTime = RequestData['BaseLocationId'], \
                                                                                 RequestData['ShiftName'], RequestData[
                                                                                     'ShiftMargin'], RequestData[
                                                                                     'StartTime'], RequestData[
                                                                                     'EndTime']
                now = datetime.now()
                created_date = now.strftime('%Y-%m-%d')
                if (StartTime > EndTime):
                    IsNightShift = '1'
                else:
                    IsNightShift = '0'
                if (BaseLocationId.isspace() == True or BaseLocationId == '') or (
                        ShiftName.isspace() == True or ShiftName == '') or (
                        ShiftMargin.isspace() == True or ShiftMargin == '') or (
                        StartTime.isspace() == True or StartTime == '') or (
                        EndTime.isspace() == True or EndTime == '') or (
                        IsNightShift.isspace() == True or IsNightShift == ''):
                    response = {'category': "0", 'message': "All fields are mandatory."}
                else:
                    BaseLocationId = BaseLocationId.strip()
                    ShiftName = ShiftName.strip()
                    ShiftMargin = ShiftMargin.strip()
                    StartTime = StartTime.strip()
                    EndTime = EndTime.strip()
                    IsNightShift = IsNightShift.strip()
                    if IsNightShift == '1':
                        starttimeshow = datetime.strptime("1900-01-01 " + StartTime, '%Y-%m-%d %H:%M:%S')
                        endtimeshow = datetime.strptime("1900-01-02 " + EndTime, '%Y-%m-%d %H:%M:%S')
                        TimeDifference = endtimeshow - starttimeshow
                        TimeDifferenceinsec = TimeDifference.total_seconds()
                        Intervaltime = int(TimeDifferenceinsec)
                        defaultInterval = ''
                        hour_str = str(Intervaltime // 3600)
                        minute_str = str((Intervaltime % 3600) // 60)
                        second_str = str((Intervaltime % 3600) % 60)
                        hour = hour_str.zfill(2)
                        minute = minute_str.zfill(2)
                        second = second_str.zfill(2)
                        defaultInterval = "{}:{}:{}".format(hour, minute, second)
                        ShiftLength = defaultInterval
                        # error = 0
                    if IsNightShift == '0':
                        FirstStartTime = datetime.strptime(StartTime, '%H:%M:%S')
                        LastEndTime = datetime.strptime(EndTime, '%H:%M:%S')
                        TimeDifference = LastEndTime - FirstStartTime
                        ShiftLength = str(TimeDifference)
                        ShiftLengthArray = ShiftLength.split(':')
                        hour = ShiftLengthArray[0].zfill(2)
                        minute = ShiftLengthArray[1].zfill(2)
                        second = ShiftLengthArray[2].zfill(2)
                        defaultInterval = "{}:{}:{}".format(hour, minute, second)
                        ShiftLength = defaultInterval
                    values = {'LicKey': LicKey, 'BaseLocationId': BaseLocationId, 'ShiftName': ShiftName,
                              'ShiftMargin': ShiftMargin, 'StartTime': StartTime, 'EndTime': EndTime,
                              'ShiftLength': ShiftLength, 'IsNightShift': IsNightShift, 'CreatedDate': created_date}
                    showmessage = DB.updateData("ShiftMaster", values,
                                                "`LicKey`='" + LicKey + "' and `ShiftMasterId`='" + MasterId + "'")

                    if showmessage['messageType'] == 'success':
                        response = {'category': "1", 'message': "Shift Updated Successfully"}
                    else:
                        response = {'category': "0", 'message': "Sorry ! something error in db. try it again."}
            response = make_response(jsonify(response))
            return response


# API FOR  MULTIPLE HOLIDAY LISTING
class RcAPIMultiHoliday(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                Querry = "select A.*,B.LocationName From HolidayList AS A ,BaseLocation AS B where A.Lickey='" + LicKey + "' and A.BaseLocationID=B.BaseLocationID ORDER BY HolidayListId DESC"
                ResponseData = DB.selectAllData(Querry)
                response = {'category': "1", 'message': "List of all Holidays.", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# SINGLE HOLIDAY LIST,ADD,UPDATE & DELETE HOLIDAY
class RcAPIHoliday(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'HolidayList'
                wherecondition = "`LicKey`= '" + LicKey + "' and `HolidayListId`= '" + MasterId + "' and IsActive=1"
                order = ""
                fields = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
            response = make_response(jsonify(response))
            return response

    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Mastrer id as a unquie id of the table
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                querry = "select CONVERT(SetDate, CHAR) As SetDate from HolidayList where LicKey ='" + LicKey + "' AND `HolidayListId`= '" + MasterId + "'"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    for i in ResponseData:
                        value = i.get("SetDate")
                        if value > today:
                            tablename = 'HolidayList'
                            wherecondition = "`LicKey`= '" + LicKey + "' AND `HolidayListId`= '" + MasterId + "'"
                            showmessage = DB.deleteSingleRow(tablename, wherecondition)
                            if showmessage['messageType'] == 'success':
                                response = {'category': "1", 'message': "Holiday deleted successfully."}
                            else:
                                response = {'category': "0", 'message': "Database Error."}
                        else:
                            response = {'category': "0", 'message': "You can not delete."}
                else:
                    response = {'category': "0", 'message': "Data not found."}
            response = make_response(jsonify(response))
            return response

    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            BaseLocationId = ''
            SetDate = ''
            Holiday = ''
            SetMonth = ''
            CreatedDate = ''
            if 'BaseLocationId' in RequestData and 'SetDate' in RequestData and 'Holiday' in RequestData and 'SetMonth' in RequestData:
                BaseLocationId = RequestData['BaseLocationId']
                SetDate = RequestData['SetDate']
                Holiday = RequestData['Holiday']
                SetMonth = RequestData['SetMonth']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            if (MasterId.isspace() == True or MasterId == '') or (LicKey.isspace() == True or LicKey == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    SetDate.isspace() == True or SetDate == '') or (Holiday.isspace() == True or Holiday == '') or (
                    SetMonth.isspace() == True or SetMonth == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                MasterId = MasterId.strip()
                BaseLocationId = BaseLocationId.strip()
                SetDate = SetDate.strip()
                Holiday = Holiday.strip()
                SetMonth = SetMonth.strip()
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                querry = "select CONVERT(SetDate, CHAR) As SetDate from HolidayList where LicKey ='" + LicKey + "' AND `HolidayListId`= '" + MasterId + "'"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    for i in ResponseData:
                        value = i.get("SetDate")
                        if value > today:
                            Querry = 'UPDATE HolidayList SET LicKey = "' + LicKey + '", BaseLocationId = "' + BaseLocationId + '", SetDate = "' + SetDate + '", Holiday = "' + Holiday + '", SetMonth = "' + SetMonth + '", UpdatedDate = "' + CreatedDate + '" WHERE LicKey="' + LicKey + '" AND HolidayListId = "' + MasterId + '"'
                            showmessage = DB.selectAllData(Querry)
                            response = {'category': '1', 'message': 'Holiday updated successfully.'}
                        else:
                            response = {'category': "0", 'message': "You can not Update."}
                else:
                    response = {'category': "0", 'message': "Data not found."}
            response = make_response(jsonify(response))
            return response

    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            BaseLocationId = ''
            SetDate = ''
            Holiday = ''
            SetMonth = ''
            IsActive = '1'
            CreatedDate = ''
            if 'BaseLocationId' in RequestData and 'SetDate' in RequestData and 'Holiday' in RequestData and 'SetMonth' in RequestData:
                BaseLocationId = RequestData['BaseLocationId']
                SetDate = RequestData['SetDate']
                Holiday = RequestData['Holiday']
                SetMonth = RequestData['SetMonth']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    SetDate.isspace() == True or SetDate == '') or (Holiday.isspace() == True or Holiday == '') or (
                    SetMonth.isspace() == True or SetMonth == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                BaseLocationId = BaseLocationId.strip()
                SetDate = SetDate.strip()
                Holiday = Holiday.strip()
                SetMonth = SetMonth.strip()
                if SetDate > CreatedDate:
                    Querry = 'INSERT INTO HolidayList (LicKey, BaseLocationId, SetDate, Holiday, SetMonth, IsActive,CreatedDate) VALUES ("' + LicKey + '","' + str(
                        BaseLocationId) + '", "' + SetDate + '", "' + Holiday + '", "' + str(
                        SetMonth) + '", "' + IsActive + '", "' + CreatedDate + '") '
                    showmessage = DB.selectAllData(Querry)
                    # if showmessage['messageType'] == 'success':
                    response = {'category': "1", 'message': "Holiday Added Successfully"}
                    # else:
                    # response = {'category': "0", 'message': "Database Error"}
                else:
                    response = {'category': "0", 'message': "You can not Update."}
            response = make_response(jsonify(response))
            return response


# API FOR  MULTIPLE LEAVE LISTING
class RcAPIMultiLeave(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                Querry = "select A.EmployeeLeaveHistoryId ,A.BaseLocationId ,A.EmpID,A.LicKey, A.LeaveDate,A.LeaveType," \
                         "A.LeavePurpose,A.Status,B.LocationName,C.EmpName From EmployeeLeaveHistory AS A,BaseLocation AS B," \
                         "EmployeeRegistration AS C Where A.BaseLocationId=B.BaseLocationId and A.EmpID=C.EmpID and A.Lickey='" + LicKey + "' and " \
                                                                                                                                           "A.LicKey='" + LicKey + "' and B.LicKey='" + LicKey + "' ORDER BY EmployeeLeaveHistoryId DESC "
                # print(Querry)
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "List of all leave.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found."}
            response = make_response(jsonify(response))
            return response


# SINGLE LEAVE LIST,ADD,UPDATE & DELETE LEAVE
class RcAPILeave(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Mastrer id as a unquie id of the table
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'EmployeeLeaveHistory'
                wherecondition = "`LicKey`= '" + LicKey + "' and `EmployeeLeaveHistoryId`= '" + MasterId + "'"
                order = ""
                fields = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:

                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response

    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Mastrer id as a unquie id of the table
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                querry = "select CONVERT(LeaveDate, CHAR) As LeaveDate from EmployeeLeaveHistory where LicKey ='" + LicKey + "' AND `EmployeeLeaveHistoryId`= '" + MasterId + "'"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    for i in ResponseData:
                        value = i.get("LeaveDate")
                        if value > today:
                            tablename = 'EmployeeLeaveHistory'
                            wherecondition = "`LicKey`= '" + LicKey + "' AND `EmployeeLeaveHistoryId`= '" + MasterId + "'"
                            deletelocation = DB.deleteSingleRow(tablename, wherecondition)
                            response = {'category': "1", 'message': "Leave deleted successfully."}
                        else:
                            response = {'category': "0", 'message': "You can not delete."}
                else:
                    response = {'category': "0", 'message': "Data not found."}
                response = make_response(jsonify(response))
                return response

    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            EmpId = ''
            BaseLocationId = ''
            OffDate = ''
            LeaveType = ''
            LeavePurpose = ''
            CreatedDate = ''
            if 'EmpId' in RequestData and 'BaseLocationId' in RequestData and 'OffDate' in RequestData and 'LeaveType' in RequestData and 'LeavePurpose' in RequestData:
                EmpId = RequestData['EmpId']
                BaseLocationId = RequestData['BaseLocationId']
                OffDate = RequestData['OffDate']
                LeaveType = RequestData['LeaveType']
                LeavePurpose = RequestData['LeavePurpose']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            if (MasterId.isspace() == True or MasterId == '') or (LicKey.isspace() == True or LicKey == '') or (
                    EmpId.isspace() == True or EmpId == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    OffDate.isspace() == True or OffDate == '') or (LeaveType.isspace() == True or LeaveType == '') or (
                    LeavePurpose.isspace() == True or LeavePurpose == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                MasterId = MasterId.strip()
                EmpId = EmpId.strip()
                BaseLocationId = BaseLocationId.strip()
                OffDate = OffDate.strip()
                LeaveType = LeaveType.strip()
                LeavePurpose = LeavePurpose.strip()
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                querry = "select CONVERT(LeaveDate, CHAR) As LeaveDate from EmployeeLeaveHistory where LicKey ='" + LicKey + "' AND `EmployeeLeaveHistoryId`= '" + MasterId + "'"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    for i in ResponseData:
                        value = i.get("LeaveDate")
                        if value > today:
                            tablename = 'EmployeeLeaveHistory'
                            wherecondition = "`LicKey`= '" + LicKey + "' AND `EmployeeLeaveHistoryId` ='" + MasterId + "'"
                            values = {'LicKey': LicKey, 'EmpId': EmpId, 'BaseLocationId': BaseLocationId,
                                      'LeaveDate': OffDate, 'LeaveType': LeaveType, 'LeavePurpose': LeavePurpose,
                                      'CreatedDate': CreatedDate}
                            showmessage = DB.updateData(tablename, values, wherecondition)
                            if showmessage['messageType'] == 'success':
                                response = {'category': '1', 'message': 'Leave updated successfully.'}
                            else:
                                response = {'category': '0', 'message': 'Something data base error.'}
                        else:
                            response = {'category': "0", 'message': "You can not update."}
                else:
                    response = {'category': "0", 'message': "Data not found."}
            response = make_response(jsonify(response))
            return response

    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            EmpId = ''
            BaseLocationId = ''
            OffDate = ''
            LeaveType = ''
            LeavePurpose = ''
            Status = '0'
            CreatedDate = ''
            if 'EmpId' in RequestData and 'BaseLocationId' in RequestData and 'OffDate' in RequestData and 'LeaveType' in RequestData and 'LeavePurpose' in RequestData:
                EmpId = RequestData['EmpId']
                BaseLocationId = RequestData['BaseLocationId']
                OffDate = RequestData['OffDate']
                LeaveType = RequestData['LeaveType']
                LeavePurpose = RequestData['LeavePurpose']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    OffDate.isspace() == True or OffDate == '') or (LeaveType.isspace() == True or LeaveType == '') or (
                    LeavePurpose.isspace() == True or LeavePurpose == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpId = EmpId.strip()
                BaseLocationId = BaseLocationId.strip()
                OffDate = OffDate.strip()
                LeaveType = LeaveType.strip()
                LeavePurpose = LeavePurpose.strip()
                tablename = "EmployeeLeaveHistory"
                values = {'LicKey': LicKey, 'EmpId': EmpId, 'BaseLocationId': BaseLocationId,
                          'LeaveDate': OffDate, 'LeaveType': LeaveType, 'LeavePurpose': LeavePurpose,
                          'CreatedDate': CreatedDate, 'Status': Status, 'UpdatedDate': CreatedDate}
                showmessage = DB.insertData(tablename, values)
                if showmessage['messageType'] == 'success':
                    response = {'category': '1', 'message': 'Leave Added successfully.'}
                else:
                    response = {'category': '0', 'message': 'Something data base error.'}
            response = make_response(jsonify(response))
            return response


# API FOR  MULTIPLE COMPOFF LEAVE LISTING
class RcAPIMultiCompoffleave(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                Querry = "select A.*,B.EmpName,C.LocationName From CompOff AS A,EmployeeRegistration AS B,BaseLocation AS C where A.LicKey='" + LicKey + "' and A.LicKey=B.LicKey and A.EmpId=B.EmpID and A.BaseLocationId=C.BaseLocationId ORDER BY A.CompOffId DESC"
                # print(Querry)
                ResponseData = DB.selectAllData(Querry)
                response = {'category': "1", 'message': "List of all Compensatory Leave.", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# SINGLE COMPOFF LEAVE LIST,ADD,UPDATE & DELETE COMPOFF LEAVE
class RcAPICompoffleave(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Mastrer id as a unquie id of the table
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'CompOff'
                wherecondition = "`LicKey`= '" + LicKey + "' and `CompOffId`= '" + MasterId + "'"
                order = ""
                fields = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response

    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Mastrer id as a unquie id of the table
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                querry = "select CONVERT(OffDate, CHAR) As OffDate from CompOff where LicKey ='" + LicKey + "' AND `CompOffId`= '" + MasterId + "'"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    for i in ResponseData:
                        value = i.get("OffDate")
                        if value > today:
                            tablename = 'CompOff'
                            wherecondition = "`LicKey`= '" + LicKey + "' AND `CompOffId`= '" + MasterId + "'"
                            ResponseData = DB.deleteSingleRow(tablename, wherecondition)
                            response = {'category': "1", 'message': "Compoff deleted successfully."}
                        else:
                            response = {'category': "0", 'message': "You can not delete."}
                else:
                    response = {'category': "0", 'message': "Data not found."}
            response = make_response(jsonify(response))
            return response

    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            MasterId = MasterId
            EmpId = ''
            BaseLocationId = ''
            OffDate = ''
            if 'EmpId' in RequestData and 'BaseLocationId' in RequestData and 'OffDate' in RequestData:
                EmpId = RequestData['EmpId']
                BaseLocationId = RequestData['BaseLocationId']
                OffDate = RequestData['OffDate']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d %H:%M:%S')
            if (MasterId.isspace() == True or MasterId == '') or (LicKey.isspace() == True or LicKey == '') or (
                    EmpId.isspace() == True or EmpId == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    OffDate.isspace() == True or OffDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                MasterId = MasterId.strip()
                BaseLocationId = BaseLocationId.strip()
                OffDate = OffDate.strip()
                EmpId = EmpId.strip()
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                querry = "select CONVERT(OffDate, CHAR) As OffDate from CompOff where LicKey ='" + LicKey + "' AND `CompOffId`= '" + MasterId + "'"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    for i in ResponseData:
                        value = i.get("OffDate")
                        if value > today:
                            tablename = "CompOff"
                            wherecondition = "`LicKey`='" + LicKey + "' AND `CompOffId` ='" + MasterId + "'"
                            values = {'EmpId': EmpId, 'BaseLocationId': BaseLocationId, 'OffDate': OffDate}
                            showmessage = DB.updateData(tablename, values, wherecondition)
                            if showmessage['messageType'] == 'success':
                                response = {'category': '1', 'message': 'Compoff updated successfully.'}
                            else:
                                response = {'category': '0', 'message': 'Something data base error.'}
                        else:
                            response = {'category': "0", 'message': "You can not update."}
                else:
                    response = {'category': "0", 'message': "Data not found."}
            response = make_response(jsonify(response))
            return response

    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID for validate URL
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            EmpId = ''
            BaseLocationId = ''
            OffDate = ''
            Status = '0'
            if 'EmpId' in RequestData and 'BaseLocationId' in RequestData and 'OffDate' in RequestData:
                EmpId = RequestData['EmpId']
                BaseLocationId = RequestData['BaseLocationId']
                OffDate = RequestData['OffDate']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    OffDate.isspace() == True or OffDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                # Removing space from left and right side
                BaseLocationId = BaseLocationId.strip()
                OffDate = OffDate.strip()
                EmpId = EmpId.strip()
                # Removing space from left and right side
                tablename = "CompOff"
                values = {'LicKey': LicKey, 'EmpId': EmpId, 'BaseLocationId': BaseLocationId, 'OffDate': OffDate,
                          'Status': Status}
                showmessage = DB.insertData(tablename, values)
                if showmessage['messageType'] == 'success':
                    response = {'category': '1', 'message': 'Compoff added successfully.'}
                else:
                    response = {'category': '0', 'message': 'Something data base error.'}
        response = make_response(jsonify(response))
        return response


# API FOR  USER DETAILS LISTING
class RcAPIGetMultiUserDetails(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']

            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                Querry = "Select A.UserLoginId,A.LicKey,CONVERT(A.CreatedDate,CHAR) AS CreatedDate,A.BaseLocationId,A.EmpId,A.UserName,A.UserProfileImg,A.MarkAttendance,A.MarkAttendanceType,A.IsAdmin,A.IsActive AS status,A.IsDelete,A.GeofenceAreaId,B.AreaName,B.Shape,B.Latlang,C.LocationName,D.EmployeeRegistrationId ,D.EmpName from EmployeeRegistration AS D,BaseLocation AS C,UserLogin AS A left join GeofenceArea AS B ON (A.GeofenceAreaId=B.GeofenceAreaId) where A.LicKey='" + LicKey + "' and A.BaseLocationId=C.BaseLocationId and A.EmpId=D.EmpId and A.LicKey=D.LicKey ORDER BY A.UserLoginId DESC"
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "List of all User Details.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# API FOR  USER DETAILS LISTING
class RcAPIGetLocationWiseMultiUserDetails(Resource):
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']

            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                Querry = "Select A.UserLoginId,A.LicKey,CONVERT(A.CreatedDate,CHAR) AS CreatedDate,A.BaseLocationId,A.EmpId,A.UserName,A.UserProfileImg,A.MarkAttendance,A.MarkAttendanceType,A.IsAdmin,A.IsActive AS status,A.IsDelete,A.GeofenceAreaId,B.AreaName,B.Shape,B.Latlang,C.LocationName,D.EmployeeRegistrationId ,D.EmpName from EmployeeRegistration AS D,BaseLocation AS C,UserLogin AS A left join GeofenceArea AS B ON (A.GeofenceAreaId=B.GeofenceAreaId) where A.LicKey='" + LicKey + "' and A.BaseLocationId='" + MasterId + "' and C.BaseLocationId='" + MasterId + "' and A.EmpId=D.EmpId and A.LicKey=D.LicKey ORDER BY A.UserLoginId DESC"
                # print(Querry)
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "List of all User Details.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# ADD,UPDATE,DELETE USER DETAILS
class RcAPIUserDetails(Resource):
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                error = 0
                EmailId = ""
                EmpId = ""
                EmpName = ""
                BaseLocationId = ""
                Password = ""
                ConfirmPassword = ""
                IsActive = '1'
                IsDelete = '0'
                # MarkAttendance=""
                # MarkAttendanceType = ""
                # GeofenceAreaId=""
                if 'EmailId' in RequestData and 'EmpId' in RequestData and 'EmpName' in RequestData and 'BaseLocationId' in RequestData and 'Password' in RequestData and 'ConfirmPassword' in RequestData:  # and 'MarkAttendance' in RequestData and 'GeofenceAreaId' in RequestData and 'MarkAttendanceType' in RequestData
                    EmailId = RequestData['EmailId']
                    EmpId = RequestData['EmpId']
                    EmpName = RequestData['EmpName']
                    BaseLocationId = RequestData['BaseLocationId']
                    Password = RequestData['Password']
                    ConfirmPassword = RequestData['ConfirmPassword']
                    # MarkAttendance = str(RequestData['MarkAttendance'])
                    # GeofenceAreaId = str(RequestData['GeofenceAreaId'])
                    # MarkAttendanceType = str(RequestData['MarkAttendanceType'])
                now = datetime.now()
                CreatedDate = now.strftime('%Y-%m-%d')
                if (LicKey.isspace() == True or LicKey == '') or (EmailId.isspace() == True or EmailId == '') or (
                        EmpId.isspace() == True or EmpId == '') or (EmpName.isspace() == True or EmpName == '') \
                        or (BaseLocationId.isspace() == True or BaseLocationId == '') or (
                        Password.isspace() == True or Password == '') or (
                        ConfirmPassword.isspace() == True or ConfirmPassword == ''):  # or (MarkAttendance.isspace() == True or MarkAttendance == '') or (GeofenceAreaId.isspace() == True) or (MarkAttendanceType.isspace() == True or MarkAttendanceType == '')
                    response = {'category': "0", 'message': "All fields are mandatory."}
                else:
                    EmailId = EmailId.strip()
                    EmpId = EmpId.strip()
                    EmpName = EmpName.strip()
                    BaseLocationId = BaseLocationId.strip()
                    Password = Password.strip()
                    ConfirmPassword = ConfirmPassword.strip()
                    # MarkAttendance = MarkAttendance.strip()
                    # MarkAttendanceType = MarkAttendanceType.strip()
                    # GeofenceAreaId = GeofenceAreaId.strip()
                    tablename = "EmployeeRegistration"
                    wherecondition = "`LicKey`='" + LicKey + "' AND  `EmailId`='" + EmailId + "' AND  `EmpId`='" + EmpId + "' AND  `EmpName`='" + EmpName + "' AND  `BaseLocationId`='" + BaseLocationId + "'"
                    fields = ""
                    order = ""
                    ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                    if len(ResponseData) == 0:
                        category = '0'
                        message = 'Data not found.'
                        response = {'category': category, 'message': message}
                    else:
                        tablename = "UserLogin"
                        wherecondition = "`LicKey`='" + LicKey + "' AND  `Username`='" + EmailId + "' AND  `EmpId`='" + EmpId + "'"
                        fields = ""
                        order = ""
                        ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                        if len(ResponseData) > 0:
                            response = {'category': '0', 'message': 'This user already exists.'}
                        else:
                            if ConfirmPassword == Password:
                                md5password = hashlib.md5()
                                md5password.update(ConfirmPassword.encode("utf-8"))
                                encryption_hashpass = md5password.hexdigest()
                                tablename = "UserLogin"
                                values = {'LicKey': LicKey, 'BaseLocationId': BaseLocationId,
                                          'Password': encryption_hashpass,
                                          'EmpId': EmpId, 'Username': EmailId, 'IsActive': IsActive,
                                          'IsDelete': IsDelete,
                                          'CreatedDate': CreatedDate}  # ,'GeofenceAreaId':GeofenceAreaId,'MarkAttendance':MarkAttendance,'MarkAttendanceType':MarkAttendanceType
                                showmessage = DB.insertData(tablename, values)
                                if showmessage['messageType'] == 'success':
                                    query11 = "Select MenuMasterId from MenuMaster where 1=1"
                                    ResponseData11 = DB.selectAllData(query11)
                                    for i in ResponseData11:
                                        MenuMasterId = (i.get('MenuMasterId'))
                                        query22 = "Select SubMenuMasterId from SubMenuMaster where MenuMasterId='" + str(
                                            MenuMasterId) + "'"
                                        ResponseData22 = DB.selectAllData(query22)
                                        if len(ResponseData22) == 0:
                                            tablename1 = "UserPrivilege"
                                            values1 = {'EmpId': EmpId, 'MenuMasterId': str(MenuMasterId),
                                                       'SubMenuMasterId': '0', 'FullControl': '0',
                                                       'EntryOnly': '0', 'ReadOnly': '0', 'UpdateOnly': '0',
                                                       'DeleteOnly': '0', 'NoControl': '1',
                                                       'LicKey': LicKey}
                                            showmessage = DB.insertData(tablename1, values1)
                                            if showmessage['messageType'] == 'success':
                                                response = {'category': "1", 'message': "User Added successfully."}
                                            else:
                                                response = {'category': "0", 'message': "Not inserted."}
                                        else:
                                            for j in range(len(ResponseData22)):
                                                SubMenuMasterId = ResponseData22[j]['SubMenuMasterId']
                                                tablename1 = "UserPrivilege"
                                                values1 = {'EmpId': EmpId, 'MenuMasterId': str(MenuMasterId),
                                                           'SubMenuMasterId': str(SubMenuMasterId), 'FullControl': '0',
                                                           'EntryOnly': '0', 'ReadOnly': '0', 'UpdateOnly': '0',
                                                           'DeleteOnly': '0', 'NoControl': '1',
                                                           'LicKey': LicKey}
                                                showmessage = DB.insertData(tablename1, values1)
                                                if showmessage['messageType'] == 'success':
                                                    response = {'category': "1", 'message': "User Added successfully."}
                                                else:
                                                    response = {'category': "0", 'message': "Not inserted."}
                                    # Send Notification to Admin for adding User.
                                    FCMMessageSend(LicKey, "admin", "Airface", EmailId + " added as an new user.")
                                else:
                                    response = {'category': '0', 'message': 'DB Error'}
                            else:
                                response = {'category': '0', 'message': 'Give correct password'}
                response = make_response(jsonify(response))
                return response

    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                error = 0
                EmailId = ""
                EmpId = ""
                EmpName = ""
                BaseLocationId = ""
                Password = ""
                ConfirmPassword = ""
                IsActive = '1'
                IsDelete = '0'
                # MarkAttendance=''
                # GeofenceAreaId=''
                # MarkAttendanceType = ""
                if 'EmailId' in RequestData and 'EmpId' in RequestData and 'EmpName' in RequestData and 'BaseLocationId' in RequestData and 'Password' in RequestData and 'ConfirmPassword' in RequestData:  # and 'MarkAttendance' in RequestData and 'GeofenceAreaId' in RequestData  and 'MarkAttendanceType' in RequestData
                    EmailId = RequestData['EmailId']
                    EmpId = RequestData['EmpId']
                    EmpName = RequestData['EmpName']
                    BaseLocationId = RequestData['BaseLocationId']
                    Password = RequestData['Password']
                    ConfirmPassword = RequestData['ConfirmPassword']
                    # GeofenceAreaId = str(RequestData['GeofenceAreaId'])
                    # MarkAttendance = str(RequestData['MarkAttendance'])
                    # MarkAttendanceType = str(RequestData['MarkAttendanceType'])
                now = datetime.now()
                CreatedDate = now.strftime('%Y-%m-%d')
                if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == '') or (
                        EmailId.isspace() == True or EmailId == '') or (
                        EmpId.isspace() == True or EmpId == '') or (EmpName.isspace() == True or EmpName == '') \
                        or (BaseLocationId.isspace() == True or BaseLocationId == '') or (
                        Password.isspace() == True or Password == '') or (
                        ConfirmPassword.isspace() == True or ConfirmPassword == ''):  # (GeofenceAreaId.isspace() == True or GeofenceAreaId == '') or
                    # or (MarkAttendance.isspace() == True or MarkAttendance == '') or ( MarkAttendanceType.isspace() == True or MarkAttendanceType == '')
                    response = {'category': "0", 'message': "All fields are mandatory."}
                else:
                    EmailId = EmailId.strip()
                    EmpId = EmpId.strip()
                    EmpName = EmpName.strip()
                    BaseLocationId = BaseLocationId.strip()
                    Password = Password.strip()
                    ConfirmPassword = ConfirmPassword.strip()
                    # MarkAttendance = MarkAttendance.strip()
                    # GeofenceAreaId = GeofenceAreaId.strip()
                    # MarkAttendanceType = MarkAttendanceType.strip()
                    querry = "select * from UserLogin where LicKey='" + LicKey + "' and UserLoginId='" + MasterId + "'"
                    responseData = DB.selectAllData(querry)
                    if len(responseData):
                        if ConfirmPassword == Password:
                            md5password = hashlib.md5()
                            md5password.update(ConfirmPassword.encode("utf-8"))
                            encryption_hashpass = md5password.hexdigest()
                            tablename = "UserLogin"
                            wherecondition = "`LicKey`='" + LicKey + "' AND `UserLoginId` ='" + MasterId + "' AND  `Username`='" + EmailId + "' AND  `EmpId`='" + EmpId + "'  AND  `BaseLocationId`='" + BaseLocationId + "'"
                            values = {'Password': encryption_hashpass, 'UpdatedDate': CreatedDate, 'IsDelete': IsDelete}
                            # , 'MarkAttendance': MarkAttendance, 'GeofenceAreaId': GeofenceAreaId,'MarkAttendanceType':MarkAttendanceType
                            showmessage = DB.updateData(tablename, values, wherecondition)
                            if showmessage['messageType'] == 'success':
                                response = {'category': '1', 'message': 'User updated Successfully .'}
                            else:
                                response = {'category': '0', 'message': 'DB Error Occured !'}
                        else:
                            response = {'category': '0', 'message': "Password and Confirmpassword Don't match"}
                    else:
                        response = {'category': '0', 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response

    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'UserLogin'
                wherecondition = "`LicKey`= '" + LicKey + "' and `UserLoginId`= '" + MasterId + "'"
                order = ""
                fields = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData):
                    DB.deleteSingleRow(tablename, wherecondition)
                    response = {'category': '1', 'message': 'User deleted successfully.'}
                else:
                    response = {'category': '0', 'message': 'Data not found'}
            response = make_response(jsonify(response))
            return response

    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'UserLogin'
                wherecondition = "`LicKey`= '" + LicKey + "' and `UserLoginId`= '" + MasterId + "'"
                order = ""
                fields = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                # querry="select A.UserLoginId,A.LicKey,A.BaseLocationId,A.MarkAttendance,A.MarkAttendanceType,A.GeofenceAreaId,(select A.AreaName from GeofenceArea AS A ,UserLogin AS B where   A.GeofenceAreaId=B.GeofenceAreaId and A.LicKey=B.LicKey and B.UserLoginId='"+MasterId+"' ) AS AreaName,A.EmpId,A.UserName,A.UserProfileImg,A.MarkAttendance,A.IsAdmin,CONVERT(A.CreatedDate,CHAR) AS CreatedDate,CONVERT(A.UpdatedDate,CHAR) AS UpdatedDate ,A.IsActive,A.IsDelete ,B.EmployeeRegistrationId From UserLogin AS A,EmployeeRegistration AS B Where A.LicKey='"+LicKey+"' and B.EmpId=A.EmpId and A.UserLoginId='"+MasterId+"'"
                querry = "select A.UserLoginId,A.LicKey,A.BaseLocationId,A.EmpId,A.UserName,A.UserProfileImg,A.IsAdmin,CONVERT(A.CreatedDate,CHAR) AS CreatedDate,CONVERT(A.UpdatedDate,CHAR) AS UpdatedDate ,A.IsActive,A.IsDelete ,B.EmployeeRegistrationId From UserLogin AS A,EmployeeRegistration AS B Where A.LicKey='" + LicKey + "' and B.EmpId=A.EmpId and A.UserLoginId='" + MasterId + "'"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': '1', 'message': 'List of Active User Details.',
                                'ResponseData': ResponseData}
                else:
                    response = {'category': '0', 'message': 'Data not found.'}
            response = make_response(jsonify(response))
            return response


# MENU
class RcAPIMenu(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                ResponseData = "select * from MenuMaster "
                ResponseData = DB.selectAllData(ResponseData)
                response = {'category': "1", 'message': "List of all Menus.", 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# SUBMENU
class RcAPISubmenu(Resource):
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '' and LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                if MasterId == '1':
                    ResponseData = {"CreatedDate": "",
                                    "MenuMasterId": 1,
                                    "SubMenuIcon": "",
                                    "SubMenuMasterId": '0',
                                    "SubMenuName": "",
                                    "SubMenuNameEn": "",
                                    "SubMenuNameSp": "",
                                    "SubMenuUrl": "",
                                    "UpdatedDate": ""}
                    response = {'category': "1", 'message': "List of all Submenus.", 'ResponseData': ResponseData}
                else:
                    ResponseData = "select SubMenuMasterId ,MenuMasterId,SubMenuName,SubMenuNameEn,SubMenuNameSp,SubMenuUrl,SubMenuIcon,convert(CreatedDate,char) as CreatedDate, convert(UpdatedDate,char) as UpdatedDate from SubMenuMaster where `MenuMasterId`='" + MasterId + "'"
                    ResponseData = DB.selectAllData(ResponseData)
                    response = {'category': "1", 'message': "List of all Submenus.", 'ResponseData': ResponseData}
                response = make_response(jsonify(response))
                return response


# USER ACCESS
class RcAPIUserAccess(Resource):
    def post(self, MasterId, MenuId, SubMenuId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            ControlType = ''
            if 'ControlType' in RequestData:
                ControlType = RequestData['ControlType']
            now = datetime.now()
            UpdatedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (ControlType.isspace() == True or ControlType == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                ControlType = ControlType.strip()
                if ControlType == "Full Control":
                    tablename = "UserPrivilege"
                    userAccessQuerry = "select * from UserPrivilege where LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                    userAccessData = DB.selectAllData(userAccessQuerry)
                    if len(userAccessData) > 0:
                        wherecondition = "LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                        values = {'FullControl': '1', 'EntryOnly': '1', 'ReadOnly': '1', 'UpdateOnly': '1',
                                  'DeleteOnly': '1', 'NoControl': '0', 'UpdatedDate': UpdatedDate, 'LicKey': LicKey}
                        showmessage = DB.updateData(tablename, values, wherecondition)
                        if showmessage['messageType'] == 'success':
                            response = {'category': '1', 'message': "Success"}
                        else:
                            response = {'category': '0', 'message': "Data not found"}
                    else:
                        response = {'category': '0', 'message': "Error"}
                elif ControlType == "Entry Only":
                    tablename = "UserPrivilege"
                    userAccessQuerry = "select * from UserPrivilege where LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                    userAccessData = DB.selectAllData(userAccessQuerry)
                    if len(userAccessData) > 0:
                        wherecondition = "LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                        values = {'EntryOnly': '1', 'ReadOnly': '1', 'NoControl': '0', 'UpdatedDate': UpdatedDate,
                                  'LicKey': LicKey}
                        showmessage = DB.updateData(tablename, values,
                                                    wherecondition)  # 'UpdateOnly':'0','FullControl':'0','DeleteOnly':'0','NoControl': '0',
                        if showmessage['messageType'] == 'success':
                            response = {'category': '1', 'message': "Success"}
                        else:
                            response = {'category': '0', 'message': "Error"}
                    else:
                        response = {'category': '0', 'message': "Data not found"}
                elif ControlType == "Read Only":
                    tablename = "UserPrivilege"
                    userAccessQuerry = "select * from UserPrivilege where LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                    userAccessData = DB.selectAllData(userAccessQuerry)
                    if len(userAccessData) > 0:
                        wherecondition = "LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                        values = {'ReadOnly': '1', 'NoControl': '0', 'UpdatedDate': UpdatedDate, 'LicKey': LicKey}
                        showmessage = DB.updateData(tablename, values, wherecondition)
                        if showmessage['messageType'] == 'success':
                            response = {'category': '1', 'message': "Success"}
                        else:
                            response = {'category': '0', 'message': "Error"}
                    else:
                        response = {'category': '0', 'message': "Data not found"}

                elif ControlType == "Delete Only":
                    tablename = "UserPrivilege"
                    userAccessQuerry = "select * from UserPrivilege where LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                    userAccessData = DB.selectAllData(userAccessQuerry)
                    if len(userAccessData) > 0:
                        wherecondition = "LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                        values = {'DeleteOnly': '1', 'NoControl': '0', 'UpdatedDate': UpdatedDate, 'LicKey': LicKey}
                        showmessage = DB.updateData(tablename, values, wherecondition)
                        if showmessage['messageType'] == 'success':
                            response = {'category': '1', 'message': "Success"}
                        else:
                            response = {'category': '0', 'message': "Error"}
                    else:
                        response = {'category': '0', 'message': "Data not found"}
                elif ControlType == "Update Only":
                    tablename = "UserPrivilege"
                    userAccessQuerry = "select * from UserPrivilege where LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                    userAccessData = DB.selectAllData(userAccessQuerry)
                    if len(userAccessData) > 0:
                        wherecondition = "LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                        values = {'UpdateOnly': '1', 'ReadOnly': '1', 'NoControl': '0', 'UpdatedDate': UpdatedDate,
                                  'LicKey': LicKey}
                        showmessage = DB.updateData(tablename, values, wherecondition)
                        if showmessage['messageType'] == 'success':
                            response = {'category': '1', 'message': "Success"}
                        else:
                            response = {'category': '0', 'message': "Error"}
                    else:
                        response = {'category': '0', 'message': "Data not found"}

                elif ControlType == "No Control":
                    tablename = "UserPrivilege"
                    userAccessQuerry = "select * from UserPrivilege where LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                    userAccessData = DB.selectAllData(userAccessQuerry)
                    if len(userAccessData) > 0:
                        wherecondition = "LicKey='" + LicKey + "' and EmpId='" + MasterId + "' and MenuMasterId= '" + MenuId + "' and SubMenuMasterId= '" + SubMenuId + "'"
                        values = {'FullControl': '0', 'EntryOnly': '0', 'ReadOnly': '0',
                                  'UpdateOnly': '0', 'DeleteOnly': '0', 'NoControl': '1', 'UpdatedDate': UpdatedDate,
                                  'LicKey': LicKey}
                        showmessage = DB.updateData(tablename, values, wherecondition)
                        if showmessage['messageType'] == 'success':
                            response = {'category': '1', 'message': "Success"}
                        else:
                            response = {'category': '0', 'message': "Error"}
                    else:
                        response = {'category': '0', 'message': "Data not found"}
                else:
                    response = {'category': '0', 'message': "Choose the Correct Type"}
            response = make_response(jsonify(response))
            return response


# EMPLOYEE SHIFT LIST
class RcAPIEmployeeShiftList(Resource):
    def get(self, MasterId):  # here Master is the EmpID
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '' or MasterId == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                # querry="select A.BaseLocationId,B.ShiftName,C.FromDate,C.ToDate ,D.BaseLocationId From EmployeeRegistration AS A,ShiftMaster AS B,EmployeeShiftHistory AS C,BaseLocation AS D where A.LicKey='"+LicKey+"' and B.LicKey='"+LicKey+"' and C.LicKey='"+LicKey+"' and D.LicKey='"+LicKey+"'and A.EmpId='"+MasterId+"' and A.BaseLocationId=D.BaseLocationId or D.BaseLocationId='0' and  B.ShiftMasterID=C.ShiftMasterID"
                querry = "select A.BaseLocationId,B.ShiftMasterId,B.ShiftName,D.LocationName as LocationName From EmployeeRegistration AS A,ShiftMaster AS B,BaseLocation AS D where A.LicKey='" + LicKey + "' and B.LicKey='" + LicKey + "' and D.LicKey='" + LicKey + "'and A.EmpId='" + MasterId + "' and A.BaseLocationId=D.BaseLocationId or D.BaseLocationId='0' GROUP by A.BaseLocationId"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    response = {'category': "1", 'message': "Success.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Erorr!No data found."}
            response = make_response(jsonify(response))
            return response


# API FOR  MULTIPLE ASSIGN SHIFT LISTING
class RcAPIGetMultiShifthistory(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                querry = "select A.* ,B.LocationName,B.BaseLocationId,C.EmpName,D.ShiftName from EmployeeShiftHistory AS A,BaseLocation AS B,EmployeeRegistration AS C,ShiftMaster AS D where A.LicKey ='" + LicKey + "' and A.EmpId=C.EmpId and C.BaseLocationID=B.BaseLocationID and A.ShiftMasterId=D.ShiftMasterId ORDER BY A.EmployeeShiftHistoryId DESC"
                ResponseData = DB.selectAllData(querry)
                response = {'category': '1', 'message': 'List of active shift history.', 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# API FOR REGISTRATION
class RcAPIRegistration(Resource):
    def post(self):
        RequestData = request.get_json()
        error = 0
        string = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        LicKey = ""
        varlen = len(string)
        for i in range(32):
            LicKey += string[math.floor(random.random() * varlen)]
        now = datetime.now()
        IssuedTime = now.strftime("%H:%M:%S")
        IssuedDate = now.strftime('%Y-%m-%d %H:%M:%S')
        CreatedDate = now.strftime('%Y-%m-%d')
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        LicenseValidInDays = '15'
        ExpiredDate = str(datetime.today() + timedelta(15))
        ExpiredTime = now.strftime('%H:%M:%S')
        LicenseType = '1'
        IsActive = ''
        IsDelete = '0'
        string = '0123456789abcdefghijklmnopqrstuvwxyz'
        SecretKeyToConfirmProfile = ''
        varlen = len(string)
        for i in range(10):
            SecretKeyToConfirmProfile += string[math.floor(random.random() * varlen)]
        OrganizationName = ''
        OrganizationEmailId = ''
        OrganizationMobileNo = ''
        OrganizationPassword = ''
        OrganizationConfirmPassword = ''
        DialCode = ''
        if 'OrganizationName' in RequestData and 'OrganizationEmailId' in RequestData and 'OrganizationMobileNo' in RequestData and 'OrganizationPassword' in RequestData and 'OrganizationConfirmPassword' in RequestData and 'DialCode' in RequestData:
            OrganizationName = RequestData['OrganizationName']
            OrganizationEmailId = RequestData['OrganizationEmailId']
            OrganizationMobileNo = RequestData['OrganizationMobileNo']
            OrganizationPassword = RequestData['OrganizationPassword']
            OrganizationConfirmPassword = RequestData['OrganizationConfirmPassword']
            DialCode = RequestData['DialCode']
        if (OrganizationName.isspace() == True or OrganizationName == '') or (
                OrganizationEmailId.isspace() == True or OrganizationEmailId == '') or (
                OrganizationMobileNo.isspace() == True or OrganizationMobileNo == '') \
                or (OrganizationPassword.isspace() == True or OrganizationPassword == '') or (
                OrganizationConfirmPassword.isspace() == True or OrganizationConfirmPassword == ''):
            response = {'category': "0", 'message': "All fields are mandatory."}
        else:
            OrganizationName = OrganizationName.strip()
            OrganizationEmailId = OrganizationEmailId.strip()
            OrganizationMobileNo = OrganizationMobileNo.strip()
            OrganizationPassword = OrganizationPassword.strip()
            OrganizationConfirmPassword = OrganizationConfirmPassword.strip()
            DialCode = DialCode.strip()
            validateemailcheck = checkemail(OrganizationEmailId)
            tablename = "OrganizationDetails"
            order = ""
            wherecondition = "`OrganizationEmailId`='" + OrganizationEmailId + "'"
            fields = ''
            if validateemailcheck:
                if (checkmobile(OrganizationMobileNo)):
                    ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                    if len(ResponseData) > 0:
                        error = error + 2
                        message = 'Email ID already exists !'
                    else:
                        wherecondition = "`OrganizationName`='" + OrganizationName + "'"
                        ResponseData1 = DB.retrieveAllData(tablename, fields, wherecondition, order)
                        if len(ResponseData1) > 0:
                            # error = error + 3
                            message = 'Organization name already exists.'
                        else:
                            pass
                else:
                    error = error + 4
                    message = 'Invalid Mobile No'
            else:
                error = error + 4
                message = 'Invalid Email Id'
            if error == 2:
                category = "2"
                response = {'category': category, 'message': message}
            elif error == 3:
                category = "3"
                response = {'category': category, 'message': message}
            elif error == 4:
                category = "4"
                response = {'category': category, 'message': message}
            else:
                querry = "SELECT CountryCode FROM Country WHERE DialCode='" + DialCode + "'"
                rsQuerry = DB.selectAllData(querry)
                for i in rsQuerry:
                    value = i.get("CountryCode")
                if OrganizationConfirmPassword == OrganizationPassword:
                    md5password = hashlib.md5()
                    md5password.update(OrganizationConfirmPassword.encode("utf-8"))
                    encryption_hashpass = md5password.hexdigest()
                    tablename = "OrganizationDetails"
                    values = {'LicKey': LicKey, 'IssuedDate': IssuedDate, 'IssuedTime': IssuedTime,
                              'LicenseValidInDays': LicenseValidInDays, 'ExpiredDate': ExpiredDate,
                              'ExpiredTime': ExpiredTime,
                              'LicenseType': LicenseType, 'IsDelete': IsDelete,
                              'SecretKeyToConfirmProfile': SecretKeyToConfirmProfile,
                              'OrganizationName': OrganizationName, 'OrganizationEmailId': OrganizationEmailId,
                              'OrgCountryCode': value, 'OrganizationMobileNo': OrganizationMobileNo,
                              'OrganizationPassword': encryption_hashpass, 'CreatedDate': CreatedDate}
                    # 'IsActive': IsActive,
                    # print(values)
                    showmessage = DB.insertData(tablename, values)
                    if showmessage['messageType'] == 'success':
                        org_email = OrganizationEmailId
                        org_name = OrganizationName
                        secret_key = SecretKeyToConfirmProfile
                        data = urllib.parse.urlencode(
                            {'org_email': org_email, 'org_name': org_name, 'secret_key': secret_key})
                        data = data.encode('utf-8')
                        # requests = urllib.request.Request("https://www.airface.in/Email/index.php")
                        requests = urllib.request.Request(
                            "http://65.0.51.114:5003/api/v1/email-send/'" + SecretKeyToConfirmProfile + "'")
                        f = urllib.request.urlopen(requests, data)
                        responseData = f.read()
                        response = {'category': "1", 'message': "Organization Added successfully.",
                                    'responseData': responseData}
                    else:
                        response = {'category': "5", 'message': "Please Contact ABSTech Support."}
                else:
                    response = {'category': '6', 'message': 'Wrong Credentials.'}
        response = make_response(jsonify(response))
        return response


class RcAPIEMailVarification(Resource):
    def post(self, MasterId):
        if MasterId == '':
            response = {'category': "0", 'message': "Master Id should not be blank."}
        else:
            querry = "select * from OrganizationDetails where SecretKeyToConfirmProfile=" + MasterId + ""
            responseData = DB.selectAllData(querry)
            if len(responseData):
                tablename = 'OrganizationDetails'
                wherecondition = "SecretKeyToConfirmProfile=" + MasterId + ""
                values = {'IsActive': str(1)}
                showmessage = DB.updateData(tablename, values, wherecondition)
                if showmessage['messageType'] == 'success':
                    response = {'category': "1", 'message': "Your registration is confirmed"}
                else:
                    response = {'category': '0', 'message': 'Error Occured!'}
            else:
                response = {'category': '0', 'message': 'DB Error Occured!'}
        response = make_response(jsonify(response))
        return response


# Get Employee Details for Create User
class RcAPIGetUser(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                EmpId = MasterId
                if LicKey == '' or EmpId == '':
                    response = {'category': "0", 'message': "All fields are mandatory."}
                else:
                    querry = "select A.EmpName,A.BaseLocationId,A.EmailId ,B.LocationName from EmployeeRegistration AS A ,BaseLocation AS B where A.LicKey='" + LicKey + "' and A.EmpId='" + EmpId + "' and A.BaseLocationId=B.BaseLocationId"
                    # A.EmployeeRegistrationId
                    ResponseData = DB.selectAllData(querry)
                    if len(ResponseData) == 0:
                        response = {'category': '0', 'message': 'Data not found !.'}
                    else:
                        response = {'category': "1", 'message': "success", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# CHECK STATUS FOR LEAVE
class RcAPILeaveStatus(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                today = str(today)
                querry = "select EmpId ,convert(LeaveDate,char) AS LeaveDate,Status from EmployeeLeaveHistory where LicKey='" + LicKey + "' and Status =0 and LeaveDate<='" + today + "' group by EmployeeLeaveHistoryId"
                responseData = DB.selectAllData(querry)
                count = len(responseData)
                if count > 0:
                    for i in range(count):
                        EmpId = responseData[i]['EmpId']
                        LeaveDate = responseData[i]['LeaveDate']
                        querry1 = "select count(*) AS count1 from ActivityDetails where EmpId='" + EmpId + "' and ADDate='" + LeaveDate + "' and LicKey='" + LicKey + "'"
                        responseData1 = DB.selectAllData(querry1)
                        count1 = responseData1[0]['count1']
                        if count1 > 0:
                            querry2 = "update EmployeeLeaveHistory set Status=2 where EmpId='" + EmpId + "' and LeaveDate='" + LeaveDate + "' and LicKey='" + LicKey + "' and Status=0 "
                            showmessage = DB.selectAllData(querry2)
                        if LeaveDate < today:
                            querry3 = "update EmployeeLeaveHistory set Status=1 where EmpId='" + EmpId + "' and LeaveDate='" + LeaveDate + "' and LicKey='" + LicKey + "' and Status=0 "
                            showmessage = DB.selectAllData(querry3)
                querry4 = "select A.EmployeeLeaveHistoryId,A.LicKey,A.EmpId,C.EmpName,A.BaseLocationId,B.LocationName,convert(A.LeaveDate,char) AS LeaveDate,A.LeaveType,A.LeavePurpose,A.Status,convert(A.CreatedDate,char) AS CreatedDate,convert(A.UpdatedDate,char) AS UpdatedDate from EmployeeLeaveHistory AS A,BaseLocation AS B,EmployeeRegistration AS C Where A.LicKey='" + LicKey + "' and A.EmpId=C.EmpId and A.BaseLocationId=B.BaseLocationId"
                ResponseData = DB.selectAllData(querry4)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
                response = make_response(jsonify(response))
                return response


# check status for compoff
class RcAPICompOffLeaveStatus(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                today = str(today)
                querry = "select EmpId ,convert(OffDate,char) AS OffDate,Status from CompOff where LicKey='" + LicKey + "' and Status =0 and OffDate<='" + today + "' group by CompOffId"
                responseData = DB.selectAllData(querry)
                count = len(responseData)
                if count > 0:
                    for i in range(count):
                        EmpId = responseData[i]['EmpId']
                        OffDate = responseData[i]['OffDate']
                        querry1 = "select count(*) AS count1 from ActivityDetails where EmpId='" + EmpId + "' and ADDate='" + OffDate + "' and LicKey='" + LicKey + "'"
                        responseData1 = DB.selectAllData(querry1)
                        count1 = responseData1[0]['count1']
                        if count1 > 0:
                            querry2 = "update CompOff set Status=2 where EmpId='" + EmpId + "' and OffDate='" + OffDate + "' and LicKey='" + LicKey + "' and Status=0 "
                            showmessage = DB.selectAllData(querry2)
                        if OffDate < today:
                            querry3 = "update CompOff set Status=1 where EmpId='" + EmpId + "' and OffDate='" + OffDate + "' and LicKey='" + LicKey + "' and Status=0 "
                            showmessage = DB.selectAllData(querry3)
                # querry4=""
                querry4 = "select A.CompOffId,A.LicKey,A.EmpId,C.EmpName,A.BaseLocationId,B.LocationName,convert(A.OffDate,char) AS OffDate,A.Status from CompOff AS A,BaseLocation AS B,EmployeeRegistration AS C Where A.LicKey='" + LicKey + "' and A.EmpId=C.EmpId and A.BaseLocationId=B.BaseLocationId"
                ResponseData = DB.selectAllData(querry4)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
                response = make_response(jsonify(response))
                return response


# API FOR  WEEKEND LEAVE LISTING
class RcAPIGetMultiWeekendDetails(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                querry = "select WeekendDetailsId, LicKey,BaseLocationId,ShiftMasterId,ShiftMonth,DayName,AllWeek,FirstWeek,SecondWeek,ThirdWeek,FourthWeek,FifthWeek,IsActive,IsDelete,CONVERT(CreatedDate,CHAR) AS CreatedDate,CONVERT(UpdatedDate,CHAR) AS UpdatedDate from WeekendDetails"
                ResponseData = DB.selectAllData(querry)
                response = {'category': "1", 'message': "List of all Weekends .", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# WEEKEND ADD
class RcAPIWeekendDetails(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            BaseLocationId = ''
            ShiftMasterId = ''
            ShiftMonth = ''
            Var_Sun = ''
            Var_Mon = ''
            Var_Tue = ''
            Var_Wed = ''
            Var_Thu = ''
            Var_Fri = ''
            Var_Sat = ''
            IsActive = '1'
            IsDelete = '0'
            if 'BaseLocationId' in RequestData and 'ShiftMasterId' in RequestData and 'ShiftMonth' in RequestData and 'Sun' in RequestData and 'Mon' in RequestData and 'Tue' in RequestData and 'Wed' in RequestData and 'Thu' in RequestData and 'Fri' in RequestData and 'Sat' in RequestData:
                BaseLocationId = RequestData['BaseLocationId']
                ShiftMasterId = RequestData['ShiftMasterId']
                ShiftMonth = RequestData['ShiftMonth']
                Var_Sun = RequestData['Sun']
                Var_Mon = RequestData['Mon']
                Var_Tue = RequestData['Tue']
                Var_Wed = RequestData['Wed']
                Var_Thu = RequestData['Thu']
                Var_Fri = RequestData['Fri']
                Var_Sat = RequestData['Sat']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            Year = now.strftime('%Y')
            if (LicKey.isspace() == True or LicKey == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    ShiftMasterId.isspace() == True or ShiftMasterId == '') \
                    or (ShiftMonth.isspace() == True or ShiftMonth == '') or (
                    Var_Sun.isspace() == True or Var_Sun == '') or (Var_Mon.isspace() == True or Var_Mon == '') \
                    or (Var_Tue.isspace() == True or Var_Tue == '') or (Var_Wed.isspace() == True or Var_Wed == '') or (
                    Var_Thu.isspace() == True or Var_Thu == '') \
                    or (Var_Fri.isspace() == True or Var_Fri == '') or (Var_Sat.isspace() == True or Var_Sat == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                BaseLocationId = BaseLocationId.strip()
                ShiftMasterId = ShiftMasterId.strip()
                ShiftMonth = ShiftMonth.strip()
                Var_Sun = Var_Sun.strip()
                Var_Mon = Var_Mon.strip()
                Var_Tue = Var_Tue.strip()
                Var_Wed = Var_Wed.strip()
                Var_Thu = Var_Thu.strip()
                Var_Fri = Var_Fri.strip()
                Var_Sat = Var_Sat.strip()
                var_Day_Array = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
                alldayQs = []
                error = 0
                for i in range(len(var_Day_Array)):
                    dayName = var_Day_Array[i]
                    daysArrayStr = RequestData[dayName]
                    daysArray = daysArrayStr.split(",")
                    count_daysArray = (len(daysArray))
                    if count_daysArray == 6:
                        if daysArray[0] == 'on':
                            AllWeek = 'on'
                            FirstWeek = 'on'
                            SecondWeek = 'on'
                            ThirdWeek = 'on'
                            FourthWeek = 'on'
                            FifthWeek = 'on'
                        else:
                            AllWeek = daysArray[0]
                            FirstWeek = daysArray[1]
                            SecondWeek = daysArray[2]
                            ThirdWeek = daysArray[3]
                            FourthWeek = daysArray[4]
                            FifthWeek = daysArray[5]
                        values = {'LicKey': LicKey, 'BaseLocationId': BaseLocationId, 'ShiftMasterId': ShiftMasterId,
                                  'ShiftMonth': ShiftMonth, 'DayName': dayName, 'AllWeek': AllWeek,
                                  'FirstWeek': FirstWeek, 'SecondWeek': SecondWeek, 'ThirdWeek': ThirdWeek,
                                  'FourthWeek': FourthWeek, 'FifthWeek': FifthWeek, 'IsActive': IsActive,
                                  'IsDelete': IsDelete, 'CreatedDate': CreatedDate, 'ShiftYear': Year,
                                  'UpdatedDate': CreatedDate}
                        alldayQs.append(values)
                    else:
                        error = error + 1
                if error > 0:
                    response = {'category': "0", 'message': "All day values should be 6 words separeted with comma."}
                else:
                    DB.deleteSingleRow("WeekendDetails",
                                       "BaseLocationId='" + BaseLocationId + "' and ShiftMasterId='" + ShiftMasterId + "' and ShiftMonth='" + ShiftMonth + "' and ShiftYear='" + Year + "' and LicKey='" + LicKey + "'")
                    for j in range(len(alldayQs)):
                        showmessage = DB.insertData("WeekendDetails", alldayQs[j])
                        if showmessage['messageType'] == 'success':
                            response = {'category': '1', 'message': 'Success.'}
                        else:
                            response = {'category': '0', 'message': 'Not inserted.'}
            response = make_response(jsonify(response))
            return response


# WEEKEND LOCATION
class RcAPIWeekendLocation(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                # querry = "Select A.LocationName,A.BaseLocationId from BaseLocation AS A,ShiftMaster AS B where A.LicKey ='" + LicKey + "' AND B.BaseLocationId =A.BaseLocationId GROUP BY A.BaseLocationId"
                querry = "SELECT BaseLocationId,LocationName FROM `BaseLocation` where LicKey='" + LicKey + "'"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': " weekend wise Location list.",
                                'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': " Data not found!"}
        response = make_response(jsonify(response))
        return response


# WEEKEND SHIFT
class RcAPIWeekendShift(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            LocationId = ''
            if 'LocationId' in RequestData:
                LocationId = RequestData['LocationId']
            if (LicKey.isspace() == True or LicKey == '') or (LocationId.isspace() == True or LocationId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                LocationId = LocationId.strip()
                querry = "SELECT ShiftMasterId,ShiftName FROM `ShiftMaster` where LicKey='" + LicKey + "' and BaseLocationId='" + LocationId + "'"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    response = {'category': '1', 'message': 'Success.', 'ResponseData': ResponseData}
                else:
                    response = {'category': '0', 'message': 'Data Not Found.'}
        response = make_response(jsonify(response))
        return response


class RcAPIWeekendDays(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            BaseLocationId = ''
            ShiftMasterId = ''
            if not RequestData:
                abort(400)
            BaseLocationId = ''
            ShiftMasterId = ''
            ShiftMonth = ''
            if 'BaseLocationId' in RequestData and 'ShiftMasterId' in RequestData and 'ShiftMonth' in RequestData:
                BaseLocationId = RequestData['BaseLocationId']
                ShiftMasterId = RequestData['ShiftMasterId']
                ShiftMonth = RequestData['ShiftMonth']
            if (LicKey.isspace() == True or LicKey == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    ShiftMasterId.isspace() == True or ShiftMasterId == '') or (
                    ShiftMonth.isspace() == True or ShiftMonth == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                BaseLocationId = BaseLocationId.strip()
                ShiftMasterId = ShiftMasterId.strip()
                ShiftMonth = ShiftMonth.strip()
                now = datetime.now()
                ADDate = now.strftime('%Y-%m-%d')
                tablename = 'WeekendDetails'
                wherecondition = "LicKey= '" + LicKey + "' AND BaseLocationId= '" + BaseLocationId + "' AND ShiftMasterId= '" + ShiftMasterId + "' and IsActive=1 and ShiftMonth= '" + ShiftMonth + "'  "
                order = ''
                fields = " DayName,AllWeek,FirstWeek,SecondWeek,ThirdWeek,FourthWeek,FifthWeek "
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "List of Weekend Days.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found."}
        response = make_response(jsonify(response))
        return response


#  Employee Status
class RcAPIUserStatus(Resource):
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey.isspace() == True or MasterId.isspace() == True:
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:

                Querry = "SELECT * FROM UserLogin WHERE UserLoginId   ='" + MasterId + "' LIMIT 1 "
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    ResponseData1 = ResponseData[0]['IsActive']
                    if ResponseData1 == 0:
                        tablename = 'UserLogin'
                        wherecondition = "`LicKey`= '" + LicKey + "' AND `UserLoginId`= '" + MasterId + "'"
                        values = {"IsActive": '1'}
                        ResponseData1 = DB.updateData(tablename, values, wherecondition)
                        response = {'category': "1", 'message': "User activated successfully."}
                    elif ResponseData1 == 1:
                        tablename = 'UserLogin'
                        wherecondition = "`LicKey`= '" + LicKey + "' AND `UserLoginId`= '" + MasterId + "'"
                        values = {"IsActive": '0'}
                        ResponseData1 = DB.updateData(tablename, values, wherecondition)
                        response = {'category': "1", 'message': "User deactivated successfully."}
                    else:
                        response = {'category': "0", 'message': "Data not found!"}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
        response = make_response(jsonify(response))
        return response


# API FOR LANGUAGE
class RcAPILanguage(Resource):
    def get(self):
        querry = "Select * from Language"
        ResponseData = DB.selectAllData(querry)
        response = {'category': "1", 'message': " Language list.", 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# API FOR SELECT LANGUAGE
class RcAPISelectLanguage(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            PageId = ''
            LangAbbr = ''
            if 'PageId' in RequestData and 'LangAbbr' in RequestData:
                PageId = RequestData['PageId']
                LangAbbr = RequestData['LangAbbr']
            if (LicKey.isspace() == True or LicKey == '') or (PageId.isspace() == True or PageId == '') or (
                    LangAbbr.isspace() == True or LangAbbr == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                PageId = PageId.strip()
                LangAbbr = LangAbbr.strip()
                querry = "select * from PageAttributes where PageId ='" + PageId + "' AND LangAbbr ='" + LangAbbr + "'"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    response = {'category': '1', 'message': 'Success.', 'ResponseData': ResponseData}
                else:
                    response = {'category': '0', 'message': 'Data Not Found.'}
            response = make_response(jsonify(response))
            return response


# @cross_origin
class RcAPIGetUserPrivelegeDetails(Resource):
    # @app.route("/api/v1/user-privelege-details")
    # @cross_origin
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            EmpId = ''
            MenuMasterId = ''
            SubMenuMasterId = ''
            if 'EmpId' in RequestData and 'MenuMasterId' in RequestData and 'SubMenuMasterId' in RequestData:
                EmpId = RequestData['EmpId']
                MenuMasterId = RequestData['MenuMasterId']
                SubMenuMasterId = RequestData['SubMenuMasterId']
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == '') or (
                    MenuMasterId.isspace() == True or MenuMasterId == '') or (
                    SubMenuMasterId.isspace() == True or SubMenuMasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpId = EmpId.strip()
                MenuMasterId = MenuMasterId.strip()
                SubMenuMasterId = SubMenuMasterId.strip()
                if SubMenuMasterId == '0':
                    querry = "select A.UserPrivilegeId,A.EmpId,A.LicKey,A.MenuMasterId,A.SubMenuMasterId,A.FullControl,A.EntryOnly,A.ReadOnly,A.UpdateOnly,A.NoControl,B.MenuName,B.MenuNameSp,B.MenuUrl,B.MenuIcon from UserPrivilege AS A, MenuMaster AS B WHERE A.EmpId='" + EmpId + "' and A.LicKey='" + LicKey + "' and A.MenuMasterId='" + MenuMasterId + "' and A.SubMenuMasterId='" + SubMenuMasterId + "' and A.MenuMasterId=B.MenuMasterId"
                    ResponseData = DB.selectAllData(querry)
                    if len(ResponseData) > 0:
                        response = {'category': "1", 'message': "List of all User Priveleges",
                                    'ResponseData': ResponseData}
                    else:
                        response = {'category': "0", 'message': "Data not found"}
                else:
                    querry = "select A.UserPrivilegeId,A.EmpId,A.LicKey,A.MenuMasterId,A.SubMenuMasterId,A.FullControl,A.EntryOnly,A.ReadOnly,A.UpdateOnly,A.NoControl,B.MenuName,B.MenuNameSp,B.MenuUrl,B.MenuIcon,C.SubMenuName,C.SubMenuNameSp,C.SubMenuUrl,C.SubMenuIcon from UserPrivilege AS A, MenuMaster AS B, SubMenuMaster AS C WHERE A.EmpId='" + EmpId + "' and A.LicKey='" + LicKey + "' and A.MenuMasterId='" + MenuMasterId + "' and A.SubMenuMasterId='" + SubMenuMasterId + "' and A.MenuMasterId=B.MenuMasterId and A.SubMenuMasterId=C.SubMenuMasterId"
                    ResponseData = DB.selectAllData(querry)
                    if len(ResponseData) > 0:
                        response = {'category': "1", 'message': "List of all User Priveleges",
                                    'ResponseData': ResponseData}
                    else:
                        response = {'category': "0", 'message': "Data not found"}

            response = make_response(jsonify(response))
            return response


class RcAPIGetUserPrivelegeSubMenu(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            EmpId = ''
            MenuMasterId = ''
            if 'EmpId' in RequestData and 'MenuMasterId' in RequestData:
                EmpId = RequestData['EmpId']
                MenuMasterId = RequestData['MenuMasterId']
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == '') or (
                    MenuMasterId.isspace() == True or MenuMasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpId = EmpId.strip()
                MenuMasterId = MenuMasterId.strip()
                querry = "select B.* from UserPrivilege AS A,SubMenuMaster AS B where A.EmpId='" + EmpId + "' and A.MenuMasterId='" + MenuMasterId + "' and A.NoControl=0 and A.MenuMasterId=B.MenuMasterId and A.LicKey='" + LicKey + "' GROUP by B.SubMenuMasterId "
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:

                    response = {'category': "1", 'message': "List of all User Sub Menu Priveleges",
                                'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}

            response = make_response(jsonify(response))
            return response


# Restore Employee Profile
class RcAPIRestoreEmployeeProfile(Resource):
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Master id as the employeeid
            if LicKey.isspace() == True or MasterId.isspace() == True:
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                querry = "select * from EmployeeRegistration where EmpId='" + MasterId + "' and LicKey='" + LicKey + "'"
                responseData = DB.selectAllData(querry)
                if len(responseData):
                    ResponseIsDelete = responseData[0]['IsDelete']
                    ResponseIsActive = responseData[0]['IsActive']
                    if ResponseIsDelete == 1:
                        tablename = 'EmployeeRegistration'
                        wherecondition = "`LicKey`= '" + LicKey + "' AND `EmpId`= '" + MasterId + "'"
                        formvalues = {"IsDelete": '0'}
                        ResponseData1 = DB.updateData(tablename, formvalues, wherecondition)
                        if ResponseIsActive == 0:
                            tablename = 'EmployeeRegistration'
                            wherecondition = "`LicKey`= '" + LicKey + "' AND `EmpId`= '" + MasterId + "'"
                            formvalues = {"IsActive": '1'}
                            ResponseData2 = DB.updateData(tablename, formvalues, wherecondition)
                        response = {'category': "1", 'message': "Employee profile restored."}
                    else:
                        response = {'category': "0", 'message': "Sorry! employee is not deleted"}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
        response = make_response(jsonify(response))
        return response


# Permanently Delete Employee
class RcAPIDeleteEmployee(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            EmpId = ''
            Status = ''
            if 'EmpId' in RequestData and 'Status' in RequestData:
                EmpId = RequestData['EmpId']
                Status = RequestData['Status']
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == '') or (
                    Status.isspace() == True or Status == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpId = EmpId.strip()
                Status = Status.strip()
                querry = "select * from EmployeeRegistration where  EmpId='" + EmpId + "' and LicKey='" + LicKey + "'"
                responseData = DB.selectAllData(querry)
                if len(responseData) > 0:
                    if Status == '0':
                        tablename = 'EmployeeRegistration'
                        wherecondition = "`LicKey`= '" + LicKey + "' AND `EmpId`= '" + EmpId + "'"
                        values = {"IsDelete": Status}
                        showmessage = DB.updateData(tablename, values, wherecondition)
                        if showmessage['messageType'] == 'success':
                            response = {'category': '1', 'message': 'Employee Activate successfully.'}
                        else:
                            response = {'category': '0', 'message': 'Something data base error.'}
                    else:
                        tablename1 = 'EmployeeRegistration'
                        tablename2 = 'ActivityDetails'
                        tablename3 = 'DatasetEncodings'
                        tablename4 = 'UserLogin'
                        tablename5 = 'EmployeeShiftHistory'
                        tablename6 = 'EmployeeLeaveHistory'
                        tablename7 = 'CompOff'
                        tablename8 = 'MonthlyActivity'
                        whereconditon = "`LicKey`= '" + LicKey + "' AND `EmpId`= '" + EmpId + "'"
                        delete1 = DB.deleteSingleRow(tablename1, whereconditon)
                        delete2 = DB.deleteSingleRow(tablename2, whereconditon)
                        delete3 = DB.deleteSingleRow(tablename3, whereconditon)
                        delete4 = DB.deleteSingleRow(tablename4, whereconditon)
                        delete5 = DB.deleteSingleRow(tablename5, whereconditon)
                        delete6 = DB.deleteSingleRow(tablename6, whereconditon)
                        delete7 = DB.deleteSingleRow(tablename7, whereconditon)
                        delete8 = DB.deleteSingleRow(tablename8, whereconditon)
                        response = {'category': "1", 'message': "Employee deleted successfully."}
                else:
                    response = {'category': "0", 'message': "Data not Found."}
            response = make_response(jsonify(response))
            return response


# Holiday Status Update
class RcAPIHolidayStatus(Resource):
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                Querry = "SELECT * FROM HolidayList WHERE HolidayListId  ='" + MasterId + "' LIMIT 1 "
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    now = datetime.now()
                    today = now.strftime('%Y-%m-%d')
                    querry = "select CONVERT(SetDate, CHAR) As SetDate from HolidayList where LicKey ='" + LicKey + "' AND `HolidayListId`= '" + MasterId + "'"
                    ResponseData1 = DB.selectAllData(querry)
                    if ResponseData1:
                        for i in ResponseData1:
                            value = i.get("SetDate")
                            if value > today:
                                Rsholiday = ResponseData[0]['IsActive']
                                if Rsholiday == 0:
                                    values = {"IsActive": '1'}
                                    ResponseData2 = DB.updateData("HolidayList", values,
                                                                  "`LicKey`= '" + LicKey + "' AND `HolidayListId`= '" + MasterId + "'")
                                    response = {'category': "1", 'message': "Holiday activated successfully."}
                                elif Rsholiday == 1:
                                    values = {"IsActive": '0'}
                                    ResponseData2 = DB.updateData("HolidayList", values,
                                                                  "`LicKey`= '" + LicKey + "' AND `HolidayListId`= '" + MasterId + "'")
                                    response = {'category': "1", 'message': "Holiday deactivated successfully."}
                                else:
                                    response = {'category': "0", 'message': "Data not found!"}
                            else:
                                response = {'category': "0", 'message': "You can not change the status."}
                    else:
                        response = {'category': "0", 'message': "Data not found."}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
        response = make_response(jsonify(response))
        return response


# API FOR DELETE EMPLOYEE IMAGE
class RcAPIDeleteEmployeeImage(Resource):
    def delete(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            EmpId = ''
            ImagePath = ''
            if 'EmpId' in RequestData and 'ImagePath' in RequestData:
                EmpId = RequestData['EmpId']
                ImagePath = RequestData['ImagePath']
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == '') or (
                    ImagePath.isspace() == True or ImagePath == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpId = EmpId.strip()
                ImagePath = ImagePath.strip()
                querry = "SELECT * FROM DatasetEncodings where `LicKey`= '" + LicKey + "' AND `EmpId`= '" + EmpId + "' AND `ImagePath`= '" + ImagePath + "'"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    tablename = 'DatasetEncodings'
                    wherecondition = "`LicKey`= '" + LicKey + "' AND `EmpId`= '" + EmpId + "' AND `ImagePath`= '" + ImagePath + "'"
                    showmessage = DB.deleteSingleRow(tablename, wherecondition)
                    if showmessage['messageType'] == 'success':
                        response = {'category': '1', 'message': 'Employee Image deleted successfully.'}
                    else:
                        response = {'category': '0', 'message': 'Something data base error.'}
                else:
                    response = {'category': '0', 'message': 'Data not found.'}
            response = make_response(jsonify(response))
            return response


'''class RcAPIEmployeeCSVUpload(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            now = datetime.now()
            CreatedDate = now.strftime('%Y_%m_%d')
            LicKey = VURS['LicKey']
            BaseLocationId = request.form['BaseLocationId']
            if 'file' not in request.files or  BaseLocationId.isspace() == True:
                response = {'category': "0", 'message':  "All fields are mandatory."}
            else:
                BaseLocationId = BaseLocationId.strip()
                employee_csv_file_dir = 'static/public/upload/employee-csvfile/'
                unique_id = ''.join(random.choice(string.ascii_uppercase) for i in range(8))
                if not os.path.exists(employee_csv_file_dir):
                    os.makedirs(employee_csv_file_dir)
                file = request.files['file']
                if file.filename == '':
                    response = {'category':  "0", 'message': "File name should not be blank."}
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_rename = str(CreatedDate) + "_" + unique_id + "_" + filename
                    fullfilepath = employee_csv_file_dir + file_rename
                    file.save(os.path.join(employee_csv_file_dir, file_rename))
                    # file upload check content details
                    succes_resp = []
                    error_resp = []
                    with open(fullfilepath) as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            EmpId = row['EmpId']
                            EmpName = row['EmpName']
                            EmailId = row['EmailId']
                            MobileNo = row['MobileNo']
                            error = 0
                            if EmpId == '' or EmpName == '' or EmailId == '' or MobileNo == '':
                                error_msg = {'category': "0", 'message': "All fields are mandatory.", 'EmpId': EmpId,
                                             'EmpName': EmpName, 'EmailId': EmailId, 'MobileNo': MobileNo,
                                             'BaseLocationId': BaseLocationId}
                                error_resp.append(error_msg)
                            else:
                                Rq_respose = insertNewEmployee(LicKey, EmpId, EmpName, EmailId, MobileNo,
                                                               BaseLocationId)
                                if Rq_respose['category'] == '1':
                                    succes_resp.append(Rq_respose['RequestData'])
                                else:
                                    error_resp.append(Rq_respose['RequestData'])
                    response = {'category':  "1", 'message': "CSV file upload successfully.", 'successData': succes_resp,
                                'errorData': error_resp}
                else:
                    response = {'category': "0", 'message': "File should be a valide one (.csv or .CSV format)"}
            responsedata = make_response(jsonify(response))
            return responsedata'''


class RcAPIEmployeeCSVUpload(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            now = datetime.now()
            CreatedDate = now.strftime('%Y_%m_%d')
            LicKey = VURS['LicKey']
            BaseLocationId = request.form['BaseLocationId']
            if 'file' not in request.files or BaseLocationId.isspace() == True:
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                BaseLocationId = BaseLocationId.strip()
                employee_csv_file_dir = 'static/public/upload/employee-csvfile/'
                unique_id = ''.join(random.choice(string.ascii_uppercase) for i in range(8))
                if not os.path.exists(employee_csv_file_dir):
                    os.makedirs(employee_csv_file_dir)
                file = request.files['file']
                if file.filename == '':
                    response = {'category': "0", 'message': "File name should not be blank."}
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_rename = str(CreatedDate) + "_" + unique_id + "_" + filename
                    fullfilepath = employee_csv_file_dir + file_rename
                    file.save(os.path.join(employee_csv_file_dir, file_rename))
                    # file upload check content details
                    succes_resp = []
                    error_resp = []
                    totalEmp = 0
                    totalSuccessEmp = 0
                    totalErrorEmp = 0
                    with open(fullfilepath) as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            EmpId = row['EmpId']
                            EmpName = row['EmpName']
                            EmailId = row['EmailId']
                            MobileNo = row['MobileNo']
                            error = 0
                            if EmpId == '' or EmpName == '' or EmailId == '' or MobileNo == '':
                                error_msg = {'category': "0", 'message': "All fields are mandatory.", 'EmpId': EmpId,
                                             'EmpName': EmpName, 'EmailId': EmailId, 'MobileNo': MobileNo,
                                             'BaseLocationId': BaseLocationId}
                                error_resp.append(error_msg)
                            else:
                                Rq_respose = insertNewEmployee(LicKey, EmpId, EmpName, EmailId, MobileNo,
                                                               BaseLocationId)
                                if Rq_respose['category'] == '1':
                                    succes_resp.append(Rq_respose['RequestData'])
                                else:
                                    error_resp.append(Rq_respose['RequestData'])
                    totalSuccessEmp = len(succes_resp)
                    totalErrorEmp = len(error_resp)
                    totalEmp = totalSuccessEmp + totalErrorEmp
                    response = {'category': "1", 'message': "CSV file upload successfully.", 'successData': succes_resp,
                                'errorData': error_resp, 'totalEmp': totalEmp, 'totalErrorEmp': totalErrorEmp,
                                'totalSuccessEmp': totalSuccessEmp}
                else:
                    response = {'category': "0", 'message': "File should be a valide one (.csv or .CSV format)"}
            responsedata = make_response(jsonify(response))
            return responsedata


# RcAPIDashboardLateComingShiftwise
class RcAPIDashboardLateComingShiftwise(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            date_obj = datetime.strptime(ADDate, '%Y-%m-%d')
            Sunday = date_obj - timedelta(days=date_obj.isoweekday())
            Saturday = Sunday + timedelta(days=6)
            intimearray = {}
            locationArrayData = []
            locationList = "SELECT A.BaseLocationId,A.LocationName FROM BaseLocation AS A,ShiftMaster AS B  WHERE A.LicKey = '" + LicKey + "' AND A.IsActive = 1  and A.BaseLocationId=B.BaseLocationId GROUP by BaseLocationId"
            rsLoc = DB.selectAllData(locationList)
            for i in range(len(rsLoc)):
                locationID = rsLoc[i]['BaseLocationId']
                locationName = rsLoc[i]['LocationName']
                shiftList = "SELECT ShiftMasterId,ShiftName FROM ShiftMaster WHERE LicKey = '" + LicKey + "' AND BaseLocationId = 0 OR  BaseLocationId = '" + str(
                    locationID) + "'"
                rsShift = DB.selectAllData(shiftList)
                shiftArrayData = []
                for j in range(len(rsShift)):
                    ShiftMasterId = rsShift[j]['ShiftMasterId']
                    ShiftName = rsShift[j]['ShiftName']
                    singleDayWiseData = []
                    for i in range(-1, 7, 1):
                        if i != -1:
                            modified_date = Sunday + timedelta(days=i)
                            if modified_date <= Saturday:
                                nextdate = modified_date
                                nextdate = str(nextdate)
                                var = nextdate.split(' ')
                                extractDate = var[0]
                                extractMonth = extractDate.split('-')
                                month = extractMonth[1]
                                query = "select A.EmpId,convert(D.ShiftMargin,char) AS ShiftMargin from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + extractDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.ShiftMasterId='" + str(
                                    ShiftMasterId) + "' and A.BaseLocationId='" + str(
                                    locationID) + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)<=ShiftMargin)"
                                Intime = DB.selectAllData(query)
                                todayintime = len(Intime)
                                query2 = "select A.EmpId,convert(D.ShiftMargin,char) AS ShiftMargin from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + extractDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.ShiftMasterId='" + str(
                                    ShiftMasterId) + "'  and A.BaseLocationId='" + str(
                                    locationID) + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
                                Latecoming = DB.selectAllData(query2)
                                countLateEmployee = len(Latecoming)
                                singleDateDataResponse = {'todayintime': todayintime, 'month': month,
                                                          'day': extractDate, 'LateEmployee': countLateEmployee}
                                singleDayWiseData.append(singleDateDataResponse)
                    shiftwisedata = {'ShiftMasterId': ShiftMasterId, 'ShiftName': ShiftName,
                                     'ResponseData': singleDayWiseData}
                    shiftArrayData.append(shiftwisedata)
                locationwisedata = {'BaseLocationId': locationID, 'LocationName': locationName,
                                    'shiftList': shiftArrayData}
                locationArrayData.append(locationwisedata)
            response = {'category': "1", 'message': "Latecoming and Intime Employee Info",
                        "ResponseData": locationArrayData}
            response = make_response(jsonify(response))
            return response


# API FOR  WEEKEND LISTING
class RcAPIGetWeekendDetails(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            BaseLocationId = ''
            ShiftMasterId = ''
            ShiftMonth = ''
            if 'BaseLocationId' in RequestData and 'ShiftMasterId' in RequestData and 'ShiftMonth' in RequestData:
                BaseLocationId = RequestData['BaseLocationId']
                ShiftMasterId = RequestData['ShiftMasterId']
                ShiftMonth = RequestData['ShiftMonth']
                now = datetime.now()
                CreatedDate = now.strftime('%Y-%m-%d')
                Year = now.strftime('%Y')
                if (LicKey.isspace() == True or LicKey == '') or (
                        BaseLocationId.isspace() == True or BaseLocationId == '') or (
                        ShiftMasterId.isspace() == True or ShiftMasterId == '') or (
                        ShiftMonth.isspace() or ShiftMonth == '') == True:
                    response = {'category': "0", 'message': "All fields are mandatory."}
                else:
                    BaseLocationId = BaseLocationId.strip()
                    ShiftMasterId = ShiftMasterId.strip()
                    ShiftMonth = ShiftMonth.strip()
                    querry = "SELECT * FROM `WeekendDetails` WHERE `BaseLocationId`='" + BaseLocationId + "' AND `ShiftMasterId`='" + ShiftMasterId + "' AND `ShiftMonth`= '" + ShiftMonth + "' AND `ShiftYear`= '" + Year + "' AND `LicKey`= '" + LicKey + "'"
                    ResponseData = DB.selectAllData(querry)
                    response = {'category': "1", 'message': "List of all Weekends .", 'ResponseData': ResponseData}
                response = make_response(jsonify(response))
                return response


class RcAPIWeekendShiftDetails(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            ShiftMasterId = ''
            if 'ShiftMasterId' in RequestData:
                ShiftMasterId = RequestData['ShiftMasterId']
            if (LicKey.isspace() == True or LicKey == '') or (ShiftMasterId.isspace() or ShiftMasterId == '') == True:
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                ShiftMasterId = ShiftMasterId.strip()
                querry = "select (CONVERT(A.ShiftMargin,CHAR)) AS ShiftMargin,(CONVERT(A.StartTime,CHAR)) AS StartTime,(CONVERT(A.EndTime,CHAR)) AS EndTime,A.ShiftName from ShiftMaster AS A ,BaseLocation AS B where A.LicKey='" + LicKey + "' and A.ShiftMasterId='" + str(
                    ShiftMasterId) + "' and A.BaseLocationId=B.BaseLocationId"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    response = {'category': '1', 'message': 'Success.',
                                'ResponseData': ResponseData}
                else:
                    response = {'category': '0', 'message': 'Data Not Found.'}
        response = make_response(jsonify(response))
        return response


# Zoho Listing
class RcAPZOHODataList(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory !."}
            else:
                qsZoho = "select A.ZohoMastreId ,A.ZohoEmailId,A.ZohoPassword,A.OrgnaizationLicKey,A.IsActive,convert(A.CreatedDate,char) AS GeneratedDate ,B.ZohoAuthKey AS AuthorizationKey  from ZohoMaster AS A, OrganizationDetails AS B where A.OrgnaizationLicKey='" + LicKey + "' and B.LicKey='" + LicKey + "' and B.IsActive=1 and B.IsDelete=0"
                rsZohoData = DB.selectAllData(qsZoho)
                response = {'category': '1', 'message': 'success', 'ResponseData': rsZohoData}
            response = make_response(jsonify(response))
            return response


# Get single Data,Add and delete zoho
class RcAPZOHORequest(Resource):
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            ZohoMailId = ''
            ZohoPassword = ''
            ZohoAuthKey = ''
            if 'ZohoMailId' in RequestData and 'ZohoPassword' in RequestData:
                ZohoMailId = RequestData['ZohoMailId']
                ZohoPassword = RequestData['ZohoPassword']
            if 'ZohoAuthKey' in RequestData:
                ZohoAuthKey = RequestData['ZohoAuthKey']
            if (LicKey.isspace() == True or LicKey == '') or (ZohoMailId.isspace() == True or ZohoMailId == '') or (
                    ZohoPassword.isspace() == True or ZohoPassword == ''):
                response = {'category': "0", 'message': "All fields are mandatory !."}
            else:
                ZohoMailId = ZohoMailId.strip()
                ZohoPassword = ZohoPassword.strip()
                ZohoAuthKey = ZohoAuthKey.strip()
                now = datetime.now()
                CreatedDate = now.strftime('%Y-%m-%d')
                tableName = "ZohoMaster"
                values = {"ZohoEmailId": ZohoMailId, "ZohoPassword": ZohoPassword, "OrgnaizationLicKey": LicKey,
                          "CreatedDate": CreatedDate}
                showmessage = DB.insertData(tableName, values)
                if showmessage['messageType'] == 'success':
                    tableName = "OrganizationDetails"
                    wherecondition = "LicKey='" + LicKey + "' and IsActive=1 and IsDelete=0"
                    values = {"ZohoAuthKey": ZohoAuthKey}
                    DB.updateData(tableName, values, wherecondition)
                    data = urllib.parse.urlencode(
                        {'EMAIL_ID': ZohoMailId, 'PASSWORD': ZohoPassword})
                    data = data.encode('utf-8')
                    requests = urllib.request.Request(
                        "https://accounts.zoho.in/apiauthtoken/nb/create?SCOPE=Zohopeople/peopleapi")
                    f = urllib.request.urlopen(requests, data)
                    responseData = f.read()
                    response = {'category': '1', 'message': 'success', 'ResponseData': responseData}
                else:
                    response = {'category': '0', 'message': 'insertion error'}
            response = make_response(jsonify(response))
            return response

    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory!."}
            else:
                tablename1 = 'ZohoMaster'
                whereconditon1 = "OrgnaizationLicKey = '" + LicKey + "' and ZohoMastreId ='" + MasterId + "'"
                DB.deleteSingleRow(tablename1, whereconditon1)

                tablename2 = 'OrganizationDetails'
                whereconditon2 = "LicKey = '" + LicKey + "' and IsDelete=0 and IsActive=1"
                values2 = {"ZohoAuthKey": " "}
                DB.updateData(tablename2, values2, whereconditon2)

                tablename3 = 'EmployeeRegistration'
                whereconditon3 = "LicKey = '" + LicKey + "' and IsZohoEmp=1"
                values3 = {"IsZohoEmp": "0"}
                DB.updateData(tablename3, values3, whereconditon3)
                response = {'category': '1', 'message': 'deletion successfull'}
            response = make_response(jsonify(response))
            return response

    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory!."}
            else:
                qsZoho = "SELECT * FROM ZohoMaster WHERE ZohoMastreId = '" + MasterId + "'"
                ResponseData = DB.selectAllData(qsZoho)
                response = {'category': '1', 'message': 'Single zoho data', 'responseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# MonthlyListHourWiseReport
class RcAPIMonthlyListHourWiseReport(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AttendanceMonth = ''
            AttendanceYear = ''
            BaseLocationId = ''
            # EmpId = ''
            if 'AttendanceYear' in RequestData and 'AttendanceMonth' in RequestData or 'BaseLocationId' in RequestData:
                AttendanceYear = RequestData['AttendanceYear']
                AttendanceMonth = RequestData['AttendanceMonth']
                # EmpId = RequestData['EmpId']
                BaseLocationId = RequestData['BaseLocationId']
            if (LicKey.isspace() == True or LicKey == '') or (
                    AttendanceMonth.isspace() == True or AttendanceMonth == '') or (
                    AttendanceYear.isspace() == True or AttendanceYear == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                AttendanceMonth = AttendanceMonth.strip()
                AttendanceYear = AttendanceYear.strip()
                BaseLocationId = BaseLocationId.strip()
                qsEmployeeName = "Select EmpId From EmployeeRegistration where LicKey='" + LicKey + "' and IsDelete=0 and IsActive=1"
                rsEmployeeName = DB.selectAllData(qsEmployeeName)
                result = []
                for empKey in rsEmployeeName:
                    empKey = empKey['EmpId']
                    qsData = "SELECT A.EmpId,A.BaseLocationId,B.EmpName,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-01' and LicKey='" + LicKey + "') AS D1_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate=ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-01' and LicKey='" + LicKey + "') AS D1_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-02' and LicKey='" + LicKey + "') AS D2_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-02' and LicKey='" + LicKey + "') AS D2_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-03' and LicKey='" + LicKey + "') AS D3_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-03' and LicKey='" + LicKey + "') AS D3_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-04' and LicKey='" + LicKey + "') AS D4_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-04' and LicKey='" + LicKey + "') AS D4_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-05' and LicKey='" + LicKey + "' ) AS D5_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-05' and LicKey='" + LicKey + "') AS D5_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-06' and LicKey='" + LicKey + "') AS D6_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-06' and LicKey='" + LicKey + "') AS D6_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-07' and LicKey='" + LicKey + "') AS D7_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-07' and LicKey='" + LicKey + "') AS D7_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-08' and LicKey='" + LicKey + "') AS D8_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-08' and LicKey='" + LicKey + "') AS D8_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-09' and LicKey='" + LicKey + "') AS D9_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-09' and LicKey='" + LicKey + "') AS D9_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-10' and LicKey='" + LicKey + "') AS D10_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-10' and LicKey='" + LicKey + "') AS D10_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-11' and LicKey='" + LicKey + "') AS D11_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-11' and LicKey='" + LicKey + "') AS D11_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-12' and LicKey='" + LicKey + "') AS D12_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-12' and LicKey='" + LicKey + "') AS D12_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-13' and LicKey='" + LicKey + "') AS D13_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-13' and LicKey='" + LicKey + "') AS D13_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-14' and LicKey='" + LicKey + "') AS D14_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-14' and LicKey='" + LicKey + "') AS D14_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-15' and LicKey='" + LicKey + "') AS D15_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-15' and LicKey='" + LicKey + "') AS D15_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-16' and LicKey='" + LicKey + "') AS D16_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-16' and LicKey='" + LicKey + "') AS D16_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-17' and LicKey='" + LicKey + "') AS D17_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-17' and LicKey='" + LicKey + "') AS D17_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-18' and LicKey='" + LicKey + "') AS D18_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-18' and LicKey='" + LicKey + "') AS D18_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-19' and LicKey='" + LicKey + "') AS D19_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-19' and LicKey='" + LicKey + "') AS D19_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-20' and LicKey='" + LicKey + "') AS D20_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-20' and LicKey='" + LicKey + "') AS D20_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-21' and LicKey='" + LicKey + "') AS D21_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-21' and LicKey='" + LicKey + "') AS D21_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-22' and LicKey='" + LicKey + "') AS D22_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-22' and LicKey='" + LicKey + "') AS D22_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-23' and LicKey='" + LicKey + "') AS D23_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-23' and LicKey='" + LicKey + "') AS D23_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-24' and LicKey='" + LicKey + "') AS D24_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-24' and LicKey='" + LicKey + "') AS D24_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-25' and LicKey='" + LicKey + "') AS D25_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-25' and LicKey='" + LicKey + "') AS D25_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-26' and LicKey='" + LicKey + "') AS D26_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-26' and LicKey='" + LicKey + "') AS D26_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-27' and LicKey='" + LicKey + "') AS D27_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-27' and LicKey='" + LicKey + "') AS D27_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-28' and LicKey='" + LicKey + "') AS D28_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-28' and LicKey='" + LicKey + "') AS D28_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-29' and LicKey='" + LicKey + "') AS D29_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-29' and LicKey='" + LicKey + "') AS D29_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-30' and LicKey='" + LicKey + "') AS D30_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-30' and LicKey='" + LicKey + "') AS D30_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-31' and LicKey='" + LicKey + "') AS D31_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='" + empKey + "' and ADDate='" + str(
                        AttendanceYear) + "-" + str(
                        AttendanceMonth) + "-31' and LicKey='" + LicKey + "') AS D31_OUT FROM ActivityDetails AS A,EmployeeRegistration AS B where A.LicKey='" + LicKey + "' and A.EmpId='" + empKey + "' AND A.BaseLocationId='" + BaseLocationId + "' and A.EmpId=B.EmpId group by A.EmpId"
                    # qsData="SELECT A.EmpId,A.BaseLocationId,B.EmpName,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'01'" "#and LicKey="+LicKey+") AS D1_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'01'" and LicKey="+LicKey+") AS D1_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'02'" and LicKey="+LicKey+") AS D2_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'02'" and LicKey="+LicKey+") AS D2_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'03'" and LicKey="+LicKey+") AS D3_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'03'" and LicKey="+LicKey+") AS D3_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'04'" and LicKey="+LicKey+") AS D4_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'04'" and LicKey="+LicKey+") AS D4_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-''05'" and LicKey="+LicKey+") AS D5_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'05'" and LicKey="+LicKey+") AS D5_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'06'" and LicKey="+LicKey+") AS D6_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'06'" and LicKey="+LicKey+") AS D6_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+-+str(AttendanceMonth)+'-'+'07'" and LicKey="+LicKey+") AS D7_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'07'" and LicKey="+LicKey+") AS D7_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'08'" and LicKey="+LicKey+") AS D8_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'08'" and LicKey="+LicKey+") AS D8_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'09'" and LicKey="+LicKey+") AS D9_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'09'" and LicKey="+LicKey+") AS D9_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'10'+" and LicKey="+LicKey+") AS D10_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'10'+" and LicKey="+LicKey+") AS D10_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'11'+" and LicKey="+LicKey+") AS D11_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'11" and LicKey='+LicKey+') AS D11_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='+empKey+' and ADDate='+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'12'" and LicKey="+LicKey+") AS D12_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'12'" and LicKey="+LicKey+") AS D12_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'13'" and LicKey="+LicKey+") AS D13_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'13'" and LicKey="+LicKey+") AS D13_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'14'" and LicKey="+LicKey+") AS D14_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'14'" and LicKey="+LicKey+") AS D14_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'15" and LicKey="'+LicKey+'") AS D15_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='+empKey+' and ADDate='+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'15'" and LicKey="+LicKey+") AS D15_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'16" and LicKey="+LicKey+") AS D16_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='+empKey+' and ADDate='+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'16" and LicKey='+LicKey+') AS D16_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate='+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'17'" and LicKey="+LicKey+") AS D17_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'17" and LicKey='+LicKey+') AS D17_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='+empKey+' and ADDate='+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'18'" and LicKey="+LicKey+") AS D18_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'18'" and LicKey="+LicKey+") AS D18_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'19'" and LicKey="+LicKey+") AS D19_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'19'" and LicKey="+LicKey+") AS D19_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'20'" and LicKey="+LicKey+") AS D20_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'20'" and LicKey="+LicKey+") AS D20_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'21'" and LicKey="+LicKey+") AS D21_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'21'" and LicKey="+LicKey+") AS D21_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'22'" and LicKey="+LicKey+") AS D22_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'22'" and LicKey="+LicKey+") AS D22_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'23'" and LicKey="+LicKey+") AS D23_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'23'" and LicKey="+LicKey+") AS D23_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'24'" and LicKey="+LicKey+") AS D24_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'24'" and LicKey="+LicKey+") AS D24_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'25'" and LicKey="+LicKey+") AS D25_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'25'" and LicKey="+LicKey+") AS D25_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'26'" and LicKey="+LicKey+") AS D26_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'26'" and LicKey="+LicKey+") AS D26_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'27'" and LicKey="+LicKey+") AS D27_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'27'" and LicKey="+LicKey+") AS D27_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'28'" and LicKey="+LicKey+") AS D28_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'28'" and LicKey="+LicKey+") AS D28_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'29'" and LicKey="+LicKey+") AS D29_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'29'" and LicKey="+LicKey+") AS D29_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'30'" and LicKey="+LicKey+") AS D30_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'30'" and LicKey="+LicKey+") AS D30_OUT,(Select CONVERT(TIME(min(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'31'" and LicKey="+LicKey+") AS D31_IN,(Select CONVERT(TIME(max(ADTime)),CHAR) from ActivityDetails where EmpId='"+empKey+"' and ADDate="+str(AttendanceYear)+'-'+str(AttendanceMonth)+'-'+'31'" and LicKey="+LicKey+") AS D31_OUT FROM ActivityDetails AS A,EmployeeRegistration AS B where A.LicKey="+LicKey+" and A.EmpId='"+empKey+"' AND A.BaseLocationId='"+Location+"' and A.EmpId=B.EmpId group by A.EmpId"
                    responseData = DB.selectAllData(qsData)
                    lenresponsedata = len(responseData)
                    if lenresponsedata > 0:
                        result.append(responseData[0])
                    # result=result+responseData
                response = {'category': "1", 'message': "success", 'responseData': result}
            return response


# Monthly Clone Activity
class RcAPIMonthlyClone(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            curDate = datetime.today().date()
            curDate = str(curDate)
            today = datetime.now()
            # for i in range(0, 4):
            for i in range(0, 1):
                dateindex = timedelta(days=i)
                curDate = today - dateindex
                curDate = datetime.strftime(curDate, "%Y-%m-%d")
                querry = "SELECT EmpId FROM EmployeeRegistration WHERE IsDelete = 0 AND IsActive = 1 and LicKey='" + LicKey + "'"
                regData = DB.selectAllData(querry)
                for i in range(len(regData)):
                    getEmpId = regData[i]['EmpId']
                    superQuerry = "select A.EmpId,A.FileLocation,B.EmpName,B.EmployeeRegistrationId,MIN(A.ADTime) AS FirstSeen,MAX(A.ADTime) AS LastSeen,MIN(A.ADTime) AS LastSeen,MIN(A.ADDate) AS ADDate,D.ShiftName From ActivityDetails AS A,EmployeeRegistration AS B, ShiftMaster AS D where A.EmployeeShiftHistoryId IN (select E.EmployeeShiftHistoryId From EmployeeShiftHistory AS E where E.StartDate='" + curDate + "' AND E.LicKey='" + LicKey + "') AND A.EmpId='" + getEmpId + "' AND A.ShiftMasterId =D.ShiftMasterId AND A.LicKey='" + LicKey + "' Group by A.EmployeeShiftHistoryId"
                    activityData = DB.selectAllData(superQuerry)
                    if len(activityData) > 0:
                        for Key in range(len(activityData)):
                            EmpId = activityData[Key]['EmpId']
                            ADDate = activityData[Key]['ADDate']
                            FirstSeen = activityData[Key]['FirstSeen']
                            LastSeen = activityData[Key]['LastSeen']
                            currentDate = datetime.strptime((str(ADDate)), "%Y-%m-%d")
                            currentTime = datetime.strptime((str(FirstSeen)), '%Y-%m-%d %H:%M:%S')
                            currentTime2 = datetime.strptime((str(LastSeen)), '%Y-%m-%d %H:%M:%S')
                            attmonth = currentDate.month
                            attyear = currentDate.year
                            attdate = currentDate.day
                            checkIn = datetime.strftime(currentTime, "%H:%M:%S")
                            checkOut = datetime.strftime(currentTime2, "%H:%M:%S")
                            querry3 = "SELECT * from MonthlyActivity where EmpId = '" + EmpId + "' AND AttendanceMonth='" + str(
                                attmonth) + "' AND AttendanceYear='" + str(attyear) + "'"
                            resultmonth = DB.selectAllData(querry3)
                            if len(resultmonth) > 0:
                                column1 = '`D' + str(attdate) + '_IN`'
                                column2 = '`D' + str(attdate) + '_OUT`'
                                values = {column1: checkIn, column2: checkOut}
                                RsMonthlyActivity = DB.updateData("MonthlyActivity", values,
                                                                  "LicKey='" + LicKey + "' AND EmpId='" + EmpId + "' AND AttendanceMonth='" + str(
                                                                      attmonth) + "' AND AttendanceYear='" + str(
                                                                      attyear) + "'")
                                response = {'category': '1', 'message': 'Monthly activity clone successfully.'}
                            else:
                                strLoop = "NULL,'" + str(getEmpId) + "','" + str(attmonth) + "'" + ",'" + str(
                                    attyear) + "',"
                                for j in range(1, 32):
                                    strLoop += (str("''")) + "," + (str("''")) + ","
                                QsMonthlyActivity = "INSERT INTO `MonthlyActivity`  VALUES (" + strLoop + "'" + LicKey + "')"
                                RsMonthlyActivity = DB.directinsertData(QsMonthlyActivity)
                                if RsMonthlyActivity['messageType'] == 'success':
                                    lastInsertId = RsMonthlyActivity['lastInsertId']
                                    column1 = 'D' + str(attdate) + '_IN'
                                    column2 = 'D' + str(attdate) + '_OUT'
                                    values = {column1: checkIn, column2: checkOut, 'AttendanceMonth': str(attmonth),
                                              'AttendanceYear': str(attyear)}
                                    DB.updateData("MonthlyActivity", values,
                                                  "LicKey='" + str(LicKey) + "' and EmpId='" + str(
                                                      EmpId) + "' AND MonthlyActivityId='" + str(lastInsertId) + "'")
                                    response = {'category': '1', 'message': 'Monthly activity clone successfully.'}
                                else:
                                    response = {'category': '0', 'message': 'Error Occured'}
                    else:
                        now = datetime.now()
                        date = now.strftime('%Y-%m-%d')
                        today = datetime.strptime(date, "%Y-%m-%d")
                        attmonth = today.month
                        attyear = today.year
                        QsMonthlyActivityDelete = "DELETE FROM `MonthlyActivity` WHERE `LicKey` = '" + str(
                            LicKey) + "' AND attendancemonth='" + str(attmonth) + "' AND attendanceyear='" + str(
                            attyear) + "' AND EmpId='" + str(getEmpId) + "'"
                        RsMonthlyActivityDelete = DB.selectAllData(QsMonthlyActivityDelete)
                        strLoop = "NULL,'" + str(getEmpId) + "','" + str(attmonth) + "'" + ",'" + str(attyear) + "',"
                        for j in range(1, 32):
                            strLoop += (str("''")) + "," + (str("''")) + ","
                        QsMonthlyActivity = "INSERT INTO `MonthlyActivity`  VALUES (" + strLoop + "'" + LicKey + "')"
                        RsMonthlyActivity = DB.directinsertData(QsMonthlyActivity)
                        if RsMonthlyActivity['messageType'] == 'success':
                            lastInsertId = RsMonthlyActivity['lastInsertId']
                            response = {'category': '1', 'message': 'Monthly activity clone successfully.'}
                        else:
                            response = {'category': '0', 'message': 'Error Occured'}
            return make_response(jsonify(response))


# API Monthly Report Hour Wise
class RcAPIMonthlyReportHourWise(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            AttendanceMonth = AttendanceYear = BaseLocationId = ''
            if 'AttendanceYear' in RequestData and 'AttendanceMonth' in RequestData or 'BaseLocationId' in RequestData:
                AttendanceYear, AttendanceMonth, BaseLocationId = RequestData['AttendanceYear'], RequestData[
                    'AttendanceMonth'], RequestData['BaseLocationId']

            if 'ShiftId' in RequestData:
                ShiftId = RequestData['ShiftId']
            else:
                ShiftId = ""

            if (LicKey.isspace() == True or LicKey == '') or (
                    AttendanceMonth.isspace() == True or AttendanceMonth == '') or (
                    AttendanceYear.isspace() == True or AttendanceYear == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                AttendanceMonth = AttendanceMonth.strip()
                AttendanceYear = AttendanceYear.strip()
                BaseLocationId = BaseLocationId.strip()
                if len(ShiftId) > 0:
                    QsForActivity = "SELECT  A.MonthlyActivityId,A.AttendanceMonth,A.AttendanceYear,B.EmpId,B.EmpName,(CONVERT(A.D1_IN,CHAR)) AS D1_IN,(CONVERT(A.D1_OUT,CHAR)) AS D1_OUT, (CONVERT(A.D2_IN,CHAR)) AS D2_IN,(CONVERT(A.D2_OUT,CHAR)) AS D2_OUT, (CONVERT(A.D3_IN,CHAR)) AS D3_IN,(CONVERT(A.D3_OUT,CHAR)) AS D3_OUT, (CONVERT(A.D4_IN,CHAR)) AS D4_IN,(CONVERT(A.D4_OUT,CHAR)) AS D4_OUT, (CONVERT(A.D5_IN,CHAR)) AS D5_IN,(CONVERT(A.D5_OUT,CHAR)) AS D5_OUT, (CONVERT(A.D6_IN,CHAR)) AS D6_IN,(CONVERT(A.D6_OUT,CHAR)) AS D6_OUT,(CONVERT(A.D7_IN,CHAR)) AS D7_IN,(CONVERT(A.D7_OUT,CHAR)) AS D7_OUT, (CONVERT(A.D8_IN,CHAR)) AS D8_IN,(CONVERT(A.D8_OUT,CHAR)) AS D8_OUT, (CONVERT(A.D9_IN,CHAR)) AS D9_IN,(CONVERT(A.D9_OUT,CHAR)) AS D9_OUT, (CONVERT(A.D10_IN,CHAR)) AS D10_IN,(CONVERT(A.D10_OUT,CHAR)) AS D10_OUT, (CONVERT(A.D11_IN,CHAR)) AS D11_IN,(CONVERT(A.D11_OUT,CHAR)) AS D11_OUT, (CONVERT(A.D12_IN,CHAR)) AS D12_IN,(CONVERT(A.D12_OUT,CHAR)) AS D12_OUT, (CONVERT(A.D13_IN,CHAR)) AS D13_IN,(CONVERT(A.D13_OUT,CHAR)) AS D13_OUT, (CONVERT(A.D14_IN,CHAR)) AS D14_IN,(CONVERT(A.D14_OUT,CHAR)) AS D14_OUT, (CONVERT(A.D15_IN,CHAR)) AS D15_IN,(CONVERT(A.D15_OUT,CHAR)) AS D15_OUT, (CONVERT(A.D16_IN,CHAR)) AS D16_IN,(CONVERT(A.D16_OUT,CHAR)) AS D16_OUT, (CONVERT(A.D17_IN,CHAR)) AS D17_IN,(CONVERT(A.D17_OUT,CHAR)) AS D17_OUT, (CONVERT(A.D18_IN,CHAR)) AS D18_IN ,(CONVERT(A.D18_OUT,CHAR)) AS D18_OUT, (CONVERT(A.D19_IN,CHAR)) AS D19_IN,(CONVERT(A.D19_OUT,CHAR)) AS D19_OUT, (CONVERT(A.D20_IN,CHAR)) AS D20_IN,(CONVERT(A.D20_OUT,CHAR)) AS D20_OUT, (CONVERT(A.D21_IN,CHAR)) AS D21_IN,(CONVERT(A.D21_OUT,CHAR)) AS D21_OUT, (CONVERT(A.D22_IN,CHAR)) AS D22_IN,(CONVERT(A.D22_OUT,CHAR)) AS D22_OUT, (CONVERT(A.D23_IN,CHAR)) AS D23_IN,(CONVERT(A.D23_OUT,CHAR)) AS D23_OUT, (CONVERT(A.D24_IN,CHAR)) AS D24_IN,(CONVERT(A.D24_OUT,CHAR)) AS D24_OUT, (CONVERT(A.D25_IN,CHAR)) AS D25_IN,(CONVERT(A.D25_OUT,CHAR)) AS D25_OUT, (CONVERT(A.D26_IN,CHAR)) AS D26_IN,(CONVERT(A.D26_OUT,CHAR)) AS D26_OUT, (CONVERT(A.D27_IN,CHAR)) AS D27_IN,(CONVERT(A.D27_OUT,CHAR)) AS D27_OUT, (CONVERT(A.D28_IN,CHAR)) AS D28_IN,(CONVERT(A.D28_OUT,CHAR)) AS D28_OUT, (CONVERT(A.D29_IN,CHAR)) AS D29_IN,(CONVERT(A.D29_OUT,CHAR)) AS D29_OUT, (CONVERT(A.D30_IN,CHAR)) AS D30_IN,(CONVERT(A.D30_OUT,CHAR)) AS D30_OUT, (CONVERT(A.D31_IN,CHAR)) AS D31_IN,(CONVERT(A.D31_OUT,CHAR)) AS D31_OUT from MonthlyActivity as A ,EmployeeRegistration as B where A.AttendanceMonth = '" + AttendanceMonth + "' and  A.AttendanceYear='" + AttendanceYear + "'  AND A.LicKey = B.LicKey AND A.EmpId = B.EmpId and A.EmpId in (SELECT EmpId FROM employeeshifthistory WHERE ShiftMasterId='" + ShiftId + "' and LicKey='" + LicKey + "' ) ORDER BY A.AttendanceMonth,A.MonthlyActivityId ASC"
                    # "SELECT A.AttendanceYear,B.EmpId,B.EmpName,(CONVERT(A.D31_OUT,CHAR)) AS D31_OUT from MonthlyActivity as A ,EmployeeRegistration as B where A.AttendanceMonth = '06' and A.AttendanceYear='2021' AND A.LicKey = B.LicKey AND A.EmpId = B.EmpId and A.EmpId in (SELECT EmpId FROM employeeshifthistory WHERE ShiftMasterId=1 and LicKey='WTRA8KKESZAG30SH7W8U7DVHIUWY3QNI' and extract(year from StartDate)='2021' and extract(month from StartDate)='06' ) ORDER BY A.AttendanceMonth,A.MonthlyActivityId ASC"
                    RsForActivityDetails = DB.selectAllData(QsForActivity)
                    if len(RsForActivityDetails) > 0:
                        response = {'category': "1", 'message': "List of monthly reports",
                                    'ResponseData': RsForActivityDetails}
                    else:
                        response = {'category': "0", 'message': "Data not found"}
                else:
                    QsForActivityDetails = "SELECT  A.MonthlyActivityId,A.AttendanceMonth,A.AttendanceYear,B.EmpId,B.EmpName,(CONVERT(A.D1_IN,CHAR)) AS D1_IN,(CONVERT(A.D1_OUT,CHAR)) AS D1_OUT, (CONVERT(A.D2_IN,CHAR)) AS D2_IN,(CONVERT(A.D2_OUT,CHAR)) AS D2_OUT, (CONVERT(A.D3_IN,CHAR)) AS D3_IN,(CONVERT(A.D3_OUT,CHAR)) AS D3_OUT, (CONVERT(A.D4_IN,CHAR)) AS D4_IN,(CONVERT(A.D4_OUT,CHAR)) AS D4_OUT, (CONVERT(A.D5_IN,CHAR)) AS D5_IN,(CONVERT(A.D5_OUT,CHAR)) AS D5_OUT, (CONVERT(A.D6_IN,CHAR)) AS D6_IN,(CONVERT(A.D6_OUT,CHAR)) AS D6_OUT, (CONVERT(A.D7_IN,CHAR)) AS D7_IN,(CONVERT(A.D7_OUT,CHAR)) AS D7_OUT, (CONVERT(A.D8_IN,CHAR)) AS D8_IN,(CONVERT(A.D8_OUT,CHAR)) AS D8_OUT, (CONVERT(A.D9_IN,CHAR)) AS D9_IN,(CONVERT(A.D9_OUT,CHAR)) AS D9_OUT, (CONVERT(A.D10_IN,CHAR)) AS D10_IN,(CONVERT(A.D10_OUT,CHAR)) AS D10_OUT, (CONVERT(A.D11_IN,CHAR)) AS D11_IN,(CONVERT(A.D11_OUT,CHAR)) AS D11_OUT, (CONVERT(A.D12_IN,CHAR)) AS D12_IN,(CONVERT(A.D12_OUT,CHAR)) AS D12_OUT, (CONVERT(A.D13_IN,CHAR)) AS D13_IN,(CONVERT(A.D13_OUT,CHAR)) AS D13_OUT, (CONVERT(A.D14_IN,CHAR)) AS D14_IN,(CONVERT(A.D14_OUT,CHAR)) AS D14_OUT, (CONVERT(A.D15_IN,CHAR)) AS D15_IN,(CONVERT(A.D15_OUT,CHAR)) AS D15_OUT, (CONVERT(A.D16_IN,CHAR)) AS D16_IN,(CONVERT(A.D16_OUT,CHAR)) AS D16_OUT, (CONVERT(A.D17_IN,CHAR)) AS D17_IN,(CONVERT(A.D17_OUT,CHAR)) AS D17_OUT, (CONVERT(A.D18_IN,CHAR)) AS D18_IN,(CONVERT(A.D18_OUT,CHAR)) AS D18_OUT, (CONVERT(A.D19_IN,CHAR)) AS D19_IN,(CONVERT(A.D19_OUT,CHAR)) AS D19_OUT, (CONVERT(A.D20_IN,CHAR)) AS D20_IN,(CONVERT(A.D20_OUT,CHAR)) AS D20_OUT, (CONVERT(A.D21_IN,CHAR)) AS D21_IN,(CONVERT(A.D21_OUT,CHAR)) AS D21_OUT, (CONVERT(A.D22_IN,CHAR)) AS D22_IN,(CONVERT(A.D22_OUT,CHAR)) AS D22_OUT, (CONVERT(A.D23_IN,CHAR)) AS D23_IN,(CONVERT(A.D23_OUT,CHAR)) AS D23_OUT, (CONVERT(A.D24_IN,CHAR)) AS D24_IN,(CONVERT(A.D24_OUT,CHAR)) AS D24_OUT, (CONVERT(A.D25_IN,CHAR)) AS D25_IN,(CONVERT(A.D25_OUT,CHAR)) AS D25_OUT, (CONVERT(A.D26_IN,CHAR)) AS D26_IN,(CONVERT(A.D26_OUT,CHAR)) AS D26_OUT, (CONVERT(A.D27_IN,CHAR)) AS D27_IN,(CONVERT(A.D27_OUT,CHAR)) AS D27_OUT, (CONVERT(A.D28_IN,CHAR)) AS D28_IN,(CONVERT(A.D28_OUT,CHAR)) AS D28_OUT, (CONVERT(A.D29_IN,CHAR)) AS D29_IN,(CONVERT(A.D29_OUT,CHAR)) AS D29_OUT, (CONVERT(A.D30_IN,CHAR)) AS D30_IN,(CONVERT(A.D30_OUT,CHAR)) AS D30_OUT, (CONVERT(A.D31_IN,CHAR)) AS D31_IN,(CONVERT(A.D31_OUT,CHAR)) AS D31_OUT from MonthlyActivity as A ,EmployeeRegistration as B where A.AttendanceMonth = '" + AttendanceMonth + "' and  A.AttendanceYear='" + AttendanceYear + "'  AND A.LicKey = B.LicKey AND A.EmpId = B.EmpId ORDER BY A.AttendanceMonth,A.MonthlyActivityId ASC"
                    # print(QsForActivityDetails)
                    RsForActivityDetails = DB.selectAllData(QsForActivityDetails)
                    if len(RsForActivityDetails) > 0:
                        response = {'category': "1", 'message': "List of monthly report",
                                    'ResponseData': RsForActivityDetails}
                    else:
                        response = {'category': "0", 'message': "Data not found"}
                return response


# API Monthly Report Day wise
class RcAPIMonthlyReportDaywise(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AttendanceMonth = AttendanceYear = Location = ''
            if 'AttendanceYear' in RequestData and 'AttendanceMonth' in RequestData and 'BaseLocationId' in RequestData:
                AttendanceYear, AttendanceMonth, Location = RequestData['AttendanceYear'], RequestData[
                    'AttendanceMonth'], RequestData['BaseLocationId']
            if 'ShiftId' in RequestData:
                shift_id = RequestData['ShiftId']
            else:
                shift_id = ""
            if (LicKey.isspace() == True or LicKey == '') or (
                    AttendanceMonth.isspace() == True or AttendanceMonth == '') or (
                    AttendanceYear.isspace() == True or AttendanceYear == '') or (
                    Location.isspace() == True or Location == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                if shift_id == "":
                    # removeing right & left space
                    AttendanceMonth = AttendanceMonth.strip()
                    AttendanceYear = AttendanceYear.strip()
                    Location = Location.strip()
                    # removeing right & left space
                    curDate = datetime.today().date()
                    curDate = str(curDate)
                    today = datetime.now()
                    startDate = "01-" + AttendanceMonth + "-" + AttendanceYear
                    monthdays_list = calendar.monthcalendar(int(AttendanceYear), int(AttendanceMonth))
                    allMonthdatesArray = []
                    multiWeekArray = []
                    for aryIndex in range(len(monthdays_list)):
                        weeklyDayDateAppendAry = []
                        weeklyDaynoArray = monthdays_list[aryIndex]
                        for weekaryIndex in range(len(weeklyDaynoArray)):
                            singleWeekArray = []
                            singleDayno = weeklyDaynoArray[weekaryIndex]
                            date = str(singleDayno) + "-" + str(AttendanceMonth) + "-" + str(AttendanceYear)
                            passdate = str(AttendanceYear) + "-" + str(AttendanceMonth) + "-" + str(singleDayno)
                            if singleDayno != 0:
                                # For Get month all Date
                                AttendanceDate_str = str(singleDayno)
                                AttendanceMonth_str = str(AttendanceMonth)
                                AttendanceDate_str = AttendanceDate_str.zfill(2)
                                AttendanceMonth_str = AttendanceMonth_str.zfill(2)
                                assigndate = str(AttendanceYear) + "-" + str(AttendanceMonth_str) + "-" + str(
                                    AttendanceDate_str)
                                DayName = findDay(date)
                                datewisesingleArray = {"DayName": DayName, "Date": assigndate}
                            else:
                                datewisesingleArray = ""
                            weeklyDayDateAppendAry.append(datewisesingleArray)
                        multiWeekArray.append(weeklyDayDateAppendAry)
                    # print(multiWeekArray)
                    # print(len(multiWeekArray))
                    qsQuerry = "SELECT * FROM WeekendDetails WHERE LicKey = '" + LicKey + "' AND BaseLocationId= '" + Location + "' AND IsDelete = 0 "
                    rsQuerry = DB.selectAllData(qsQuerry)
                    if Location != '0':
                        qsQuerry = "SELECT EmpId,EmpName,BaseLocationId FROM EmployeeRegistration WHERE LicKey = '" + LicKey + "' AND BaseLocationId= '" + Location + "' AND IsDelete = 0 "
                        rsQuerry = DB.selectAllData(qsQuerry)
                    else:
                        qsQuerry = "SELECT EmpId,EmpName,BaseLocationId FROM EmployeeRegistration WHERE LicKey = '" + LicKey + "'  AND IsDelete = 0 "
                        rsQuerry = DB.selectAllData(qsQuerry)
                    resultArray = []
                    qsQuerryHolidayList = "SELECT Convert(SetDate,CHAR) AS SetDate,Holiday FROM HolidayList WHERE LicKey = '" + LicKey + "' AND BaseLocationId= '" + Location + "' AND IsActive = 1  AND SetMonth= '" + AttendanceMonth + "' AND extract(year from SetDate)='" + AttendanceYear + "'"
                    rsQuerryHolidayList = DB.selectAllData(qsQuerryHolidayList)
                    querry = "SELECT * FROM EmployeeRegistration WHERE IsDelete = 0 AND IsActive = 1 and LicKey='" + LicKey + "' ORDER BY EmpId ASC"
                    rsQuerry = DB.selectAllData(querry)
                    for empKey in rsQuerry:
                        qsQuerryCompOffList = "SELECT Convert(OffDate,CHAR) AS OffDate FROM CompOff WHERE LicKey = '" + LicKey + "' AND EmpId= '" + \
                                              empKey[
                                                  'EmpId'] + "' AND BaseLocationId= '" + Location + "' AND Status = 1 AND extract(month from OffDate)='" + AttendanceMonth + "' AND extract(year from OffDate)='" + AttendanceYear + "'"
                        rsQuerryCompOffList = DB.selectAllData(qsQuerryCompOffList)
                        qsQuerryLeaveList = "SELECT Convert(LeaveDate,CHAR) AS LeaveDate,LeavePurpose FROM EmployeeLeaveHistory WHERE LicKey = '" + LicKey + "' AND EmpId= '" + \
                                            empKey[
                                                'EmpId'] + "' AND BaseLocationId= '" + Location + "' AND Status = 1 AND extract(month from LeaveDate)='" + AttendanceMonth + "' AND extract(year from LeaveDate)='" + AttendanceYear + "'"
                        rsQuerryLeaveList = DB.selectAllData(qsQuerryLeaveList)
                        result = []

                        qsShift = "SELECT ShiftMasterId from EmployeeShiftHistory WHERE EmpId='" + empKey[
                            'EmpId'] + "' and ShiftMonth='" + str(AttendanceMonth) + "' and ShiftYear='" + str(
                            AttendanceYear) + "' ORDER BY StartDate ASC LIMIT 1"
                        RsShiftList = DB.selectAllData(qsShift)
                        if len(RsShiftList) > 0:
                            ShiftMasterId = str(RsShiftList[0]['ShiftMasterId'])
                        else:
                            ShiftMasterId = '0'
                        # WeekEnd Get Dates
                        qsQuerryForWeekEndList = "SELECT WeekendDetailsId,BaseLocationId,ShiftMasterId,ShiftMonth,DayName,AllWeek,FirstWeek,SecondWeek,ThirdWeek,FourthWeek,FifthWeek FROM WeekendDetails WHERE LicKey = '" + LicKey + "' AND ShiftMasterId= '" + str(
                            ShiftMasterId) + "' AND ShiftMonth= '" + str(AttendanceMonth) + "' AND IsDelete = 0 "
                        rsQuerryForWeekEndList = DB.selectAllData(qsQuerryForWeekEndList)
                        WeekendDates = []
                        for countIndex in range(len(rsQuerryForWeekEndList)):
                            FirstWeekData = rsQuerryForWeekEndList[countIndex]['FirstWeek']
                            SecondWeekData = rsQuerryForWeekEndList[countIndex]['SecondWeek']
                            ThirdWeekData = rsQuerryForWeekEndList[countIndex]['ThirdWeek']
                            FourthWeekData = rsQuerryForWeekEndList[countIndex]['FourthWeek']
                            FifthWeekData = rsQuerryForWeekEndList[countIndex]['FifthWeek']
                            WeekEndDayName = rsQuerryForWeekEndList[countIndex]['DayName']
                            if FirstWeekData == "on":
                                if multiWeekArray[0] != "":
                                    for j in range(len(multiWeekArray[0])):
                                        if multiWeekArray[0][j] != "":
                                            if multiWeekArray[0][j]['DayName'] == WeekEndDayName:
                                                WeekendDates.append(multiWeekArray[0][j]['Date'])
                            if SecondWeekData == "on":
                                if multiWeekArray[1] != "":
                                    for j in range(len(multiWeekArray[1])):
                                        if multiWeekArray[1][j] != "":
                                            if multiWeekArray[1][j]['DayName'] == WeekEndDayName:
                                                WeekendDates.append(multiWeekArray[1][j]['Date'])
                            if ThirdWeekData == "on":
                                if multiWeekArray[2] != "":
                                    for j in range(len(multiWeekArray[2])):
                                        if multiWeekArray[2][j] != "":
                                            if multiWeekArray[2][j]['DayName'] == WeekEndDayName:
                                                WeekendDates.append(multiWeekArray[2][j]['Date'])
                            if FourthWeekData == "on":
                                if multiWeekArray[3] != "":
                                    for j in range(len(multiWeekArray[3])):
                                        if multiWeekArray[3][j] != "":
                                            if multiWeekArray[3][j]['DayName'] == WeekEndDayName:
                                                WeekendDates.append(multiWeekArray[3][j]['Date'])
                            if len(multiWeekArray) > 4:
                                if FifthWeekData == "on":
                                    if multiWeekArray[4] != "":
                                        for j in range(len(multiWeekArray[4])):
                                            if multiWeekArray[4][j] != "":
                                                if multiWeekArray[4][j]['DayName'] == WeekEndDayName:
                                                    WeekendDates.append(multiWeekArray[4][j]['Date'])

                        qsMonth = "SELECT MonthlyActivityId,EmpId,'" + empKey[
                            'EmpName'] + "' AS EmpName,AttendanceMonth,AttendanceYear,(CONVERT(D1_IN,CHAR)) AS D1_IN,(CONVERT(D2_IN,CHAR)) AS D2_IN,(CONVERT(D3_IN,CHAR)) AS D3_IN,(CONVERT(D4_IN,CHAR)) AS D4_IN, (CONVERT(D5_IN,CHAR)) AS D5_IN,(CONVERT(D6_IN,CHAR)) AS D6_IN,(CONVERT(D7_IN,CHAR)) AS D7_IN,(CONVERT(D8_IN,CHAR)) AS D8_IN,(CONVERT(D9_IN,CHAR)) AS D9_IN, (CONVERT(D10_IN,CHAR)) AS D10_IN,(CONVERT(D11_IN,CHAR)) AS D11_IN,(CONVERT(D12_IN,CHAR)) AS D12_IN,(CONVERT(D13_IN,CHAR)) AS D13_IN,(CONVERT(D14_IN,CHAR)) AS D14_IN,(CONVERT(D15_IN,CHAR)) AS D15_IN,(CONVERT(D16_IN,CHAR)) AS D16_IN,(CONVERT(D17_IN,CHAR)) AS D17_IN,(CONVERT(D18_IN,CHAR)) AS D18_IN,(CONVERT(D19_IN,CHAR)) AS D19_IN,(CONVERT(D20_IN,CHAR)) AS D20_IN,(CONVERT(D21_IN,CHAR)) AS D21_IN,(CONVERT(D22_IN,CHAR)) AS D22_IN,(CONVERT(D23_IN,CHAR)) AS D23_IN,(CONVERT(D24_IN,CHAR)) AS D24_IN,(CONVERT(D25_IN,CHAR)) AS D25_IN,(CONVERT(D26_IN,CHAR)) AS D26_IN,(CONVERT(D27_IN,CHAR)) AS D27_IN,(CONVERT(D28_IN,CHAR)) AS D28_IN,(CONVERT(D29_IN,CHAR)) AS D29_IN,(CONVERT(D30_IN,CHAR)) AS D30_IN,(CONVERT(D31_IN,CHAR)) AS D31_IN from MonthlyActivity where AttendanceMonth = '" + AttendanceMonth + "' and  AttendanceYear='" + AttendanceYear + "' and EmpId='" + \
                                  empKey[
                                      'EmpId'] + "' AND LicKey = '" + LicKey + "' ORDER BY AttendanceMonth,MonthlyActivityId ASC"
                        rsMonth = DB.selectAllData(qsMonth)
                        if rsMonth:
                            timearray = []
                            timearray = rsMonth
                            timearray[0]['HolidayList'] = rsQuerryHolidayList
                            timearray[0]['CompOff'] = rsQuerryCompOffList
                            timearray[0]['Leave'] = rsQuerryLeaveList
                            timearray[0]['Weekend'] = WeekendDates
                            resultArray.append(timearray[0])
                        else:
                            timearray = []
                            timeArr = {}
                            timeArr['EmpName'] = empKey['EmpName']
                            timeArr['EmpId'] = empKey['EmpId']
                            timeArr['AttendanceMonth'] = AttendanceMonth
                            timeArr['AttendanceYear'] = AttendanceYear
                            timeArr['D1_IN'] = timeArr['D2_IN'] = timeArr['D3_IN'] = timeArr['D4_IN'] = timeArr[
                                'D5_IN'] = \
                                timeArr['D6_IN'] = timeArr['D7_IN'] = timeArr['D8_IN'] = timeArr['D9_IN'] = timeArr[
                                'D10_IN'] = \
                                timeArr['D11_IN'] = timeArr['D12_IN'] = timeArr['D13_IN'] = timeArr['D14_IN'] = timeArr[
                                'D15_IN'] = timeArr['D16_IN'] = timeArr['D17_IN'] = timeArr['D18_IN'] = timeArr[
                                'D19_IN'] = \
                                timeArr['D20_IN'] = timeArr['D21_IN'] = timeArr['D22_IN'] = timeArr['D23_IN'] = timeArr[
                                'D24_IN'] = timeArr['D25_IN'] = timeArr['D26_IN'] = timeArr['D27_IN'] = timeArr[
                                'D28_IN'] = \
                                timeArr['D29_IN'] = timeArr['D30_IN'] = timeArr['D31_IN'] = '00:00:00'
                            timeArr['HolidayList'] = rsQuerryHolidayList
                            timeArr['CompOff'] = rsQuerryCompOffList
                            timeArr['Leave'] = rsQuerryLeaveList
                            timeArr['Weekend'] = []
                            resultArray.append(timeArr)
                    response = {'category': "1", 'message': "success", 'ResponseData': resultArray}
                else:
                    AttendanceMonth = AttendanceMonth.strip()
                    AttendanceYear = AttendanceYear.strip()
                    Location = Location.strip()
                    # removeing right & left space
                    curDate = datetime.today().date()
                    curDate = str(curDate)
                    today = datetime.now()
                    startDate = "01-" + AttendanceMonth + "-" + AttendanceYear
                    monthdays_list = calendar.monthcalendar(int(AttendanceYear), int(AttendanceMonth))
                    allMonthdatesArray = []
                    multiWeekArray = []
                    for aryIndex in range(len(monthdays_list)):
                        weeklyDayDateAppendAry = []
                        weeklyDaynoArray = monthdays_list[aryIndex]
                        for weekaryIndex in range(len(weeklyDaynoArray)):
                            singleWeekArray = []
                            singleDayno = weeklyDaynoArray[weekaryIndex]
                            date = str(singleDayno) + "-" + str(AttendanceMonth) + "-" + str(AttendanceYear)
                            passdate = str(AttendanceYear) + "-" + str(AttendanceMonth) + "-" + str(singleDayno)
                            if singleDayno != 0:
                                # For Get month all Date
                                AttendanceDate_str = str(singleDayno)
                                AttendanceMonth_str = str(AttendanceMonth)
                                AttendanceDate_str = AttendanceDate_str.zfill(2)
                                AttendanceMonth_str = AttendanceMonth_str.zfill(2)
                                assigndate = str(AttendanceYear) + "-" + str(AttendanceMonth_str) + "-" + str(
                                    AttendanceDate_str)
                                DayName = findDay(date)
                                datewisesingleArray = {"DayName": DayName, "Date": assigndate}
                            else:
                                datewisesingleArray = ""
                            weeklyDayDateAppendAry.append(datewisesingleArray)
                        multiWeekArray.append(weeklyDayDateAppendAry)
                    # print(multiWeekArray)
                    # print(len(multiWeekArray))
                    qsQuerry = "SELECT * FROM WeekendDetails WHERE LicKey = '" + LicKey + "' AND BaseLocationId= '" + Location + "' AND ShiftMasterId = '" + shift_id + "' and IsDelete = 0 "
                    rsQuerry = DB.selectAllData(qsQuerry)
                    if Location != '0':
                        qsQuerry = "SELECT B.ShiftMasterId, A.EmpId,A.EmpName,A.BaseLocationId FROM EmployeeRegistration A  JOIN EmployeeShiftHistory B where B.ShiftMasterId='" + shift_id + "' and B.EmpId = A.EmpId and   A.LicKey = '" + LicKey + "' AND A.BaseLocationId= '" + Location + "' AND A.IsDelete = 0 "
                        rsQuerry = DB.selectAllData(qsQuerry)
                    else:
                        qsQuerry = "SELECT B.ShiftMasterId, A.EmpId,A.EmpName,A.BaseLocationId FROM EmployeeRegistration A  JOIN EmployeeShiftHistory B where B.ShiftMasterId='" + shift_id + "' and B.EmpId = A.EmpId  and  A.LicKey = '" + LicKey + "'  AND A.IsDelete = 0"
                        rsQuerry = DB.selectAllData(qsQuerry)
                    resultArray = []
                    qsQuerryHolidayList = "SELECT Convert(A.SetDate,CHAR) AS SetDate,A.Holiday FROM HolidayList A Join shiftmaster B WHERE B.ShiftMasterId='" + shift_id + "' and B.BaseLocationId='" + Location + "'  and A.LicKey = '" + LicKey + "' AND A.BaseLocationId= '" + Location + "' AND A.IsActive = 1 AND A.SetMonth= '" + AttendanceMonth + "' AND extract(year from A.SetDate)='" + AttendanceYear + "'"
                    rsQuerryHolidayList = DB.selectAllData(qsQuerryHolidayList)
                    querry = "SELECT DISTINCT A.EmpId,B.ShiftMasterId,A.EmpName,A.BaseLocationId FROM EmployeeRegistration A JOIN employeeshifthistory B WHERE B.ShiftMasterId='" + shift_id + "' and A.LicKey = '" + LicKey + "' and B.LicKey = '" + LicKey + "' AND A.IsDelete = 0 and A.IsActive=1 and A.EmpId=B.EmpId"
                    rsQuerry = DB.selectAllData(querry)
                    for empKey in rsQuerry:
                        qsQuerryCompOffList = "SELECT Convert(OffDate,CHAR) AS OffDate FROM CompOff WHERE LicKey = '" + LicKey + "' AND EmpId= '" + \
                                              empKey[
                                                  'EmpId'] + "' AND BaseLocationId= '" + Location + "' AND Status = 1 AND extract(month from OffDate)='" + AttendanceMonth + "' AND extract(year from OffDate)='" + AttendanceYear + "'"
                        rsQuerryCompOffList = DB.selectAllData(qsQuerryCompOffList)
                        qsQuerryLeaveList = "SELECT Convert(A.LeaveDate,CHAR) AS LeaveDate,A.LeavePurpose FROM EmployeeLeaveHistory A JOIN ShiftMaster B where B.ShiftmasterId='" + shift_id + "' and B.BaseLocationId='" + Location + "' and A.LicKey ='" + LicKey + "' and B.LicKey='" + LicKey + "' AND A.EmpId= '" + \
                                            empKey[
                                                'EmpId'] + "' AND A.BaseLocationId= '" + Location + "' AND A.Status = 1 AND extract(month from A.LeaveDate)='" + AttendanceMonth + "' AND extract(year from A.LeaveDate)='" + AttendanceYear + "'"
                        rsQuerryLeaveList = DB.selectAllData(qsQuerryLeaveList)
                        result = []
                        qsShift = "SELECT ShiftMasterId from EmployeeShiftHistory WHERE EmpId='" + empKey[
                            'EmpId'] + "' and ShiftMonth='" + str(AttendanceMonth) + "' and ShiftYear='" + str(
                            AttendanceYear) + "' and ShiftMasterId='" + shift_id + "' ORDER BY StartDate ASC LIMIT 1"
                        RsShiftList = DB.selectAllData(qsShift)
                        if len(RsShiftList) > 0:
                            ShiftMasterId = str(RsShiftList[0]['ShiftMasterId'])
                        else:
                            ShiftMasterId = '0'
                        # WeekEnd Get Dates
                        qsQuerryForWeekEndList = "SELECT WeekendDetailsId,BaseLocationId,ShiftMasterId,ShiftMonth,DayName,AllWeek,FirstWeek,SecondWeek,ThirdWeek,FourthWeek,FifthWeek FROM WeekendDetails WHERE LicKey = '" + LicKey + "' AND ShiftMasterId= '" + shift_id + "' AND ShiftMonth= '" + AttendanceMonth + "' AND IsDelete = 0"
                        rsQuerryForWeekEndList = DB.selectAllData(qsQuerryForWeekEndList)
                        WeekendDates = []
                        for countIndex in range(len(rsQuerryForWeekEndList)):
                            FirstWeekData = rsQuerryForWeekEndList[countIndex]['FirstWeek']
                            SecondWeekData = rsQuerryForWeekEndList[countIndex]['SecondWeek']
                            ThirdWeekData = rsQuerryForWeekEndList[countIndex]['ThirdWeek']
                            FourthWeekData = rsQuerryForWeekEndList[countIndex]['FourthWeek']
                            FifthWeekData = rsQuerryForWeekEndList[countIndex]['FifthWeek']
                            WeekEndDayName = rsQuerryForWeekEndList[countIndex]['DayName']
                            if FirstWeekData == "on":
                                if multiWeekArray[0] != "":
                                    for j in range(len(multiWeekArray[0])):
                                        if multiWeekArray[0][j] != "":
                                            if multiWeekArray[0][j]['DayName'] == WeekEndDayName:
                                                WeekendDates.append(multiWeekArray[0][j]['Date'])
                            if SecondWeekData == "on":
                                if multiWeekArray[1] != "":
                                    for j in range(len(multiWeekArray[1])):
                                        if multiWeekArray[1][j] != "":
                                            if multiWeekArray[1][j]['DayName'] == WeekEndDayName:
                                                WeekendDates.append(multiWeekArray[1][j]['Date'])
                            if ThirdWeekData == "on":
                                if multiWeekArray[2] != "":
                                    for j in range(len(multiWeekArray[2])):
                                        if multiWeekArray[2][j] != "":
                                            if multiWeekArray[2][j]['DayName'] == WeekEndDayName:
                                                WeekendDates.append(multiWeekArray[2][j]['Date'])
                            if FourthWeekData == "on":
                                if multiWeekArray[3] != "":
                                    for j in range(len(multiWeekArray[3])):
                                        if multiWeekArray[3][j] != "":
                                            if multiWeekArray[3][j]['DayName'] == WeekEndDayName:
                                                WeekendDates.append(multiWeekArray[3][j]['Date'])
                            if len(multiWeekArray) > 4:
                                if FifthWeekData == "on":
                                    if multiWeekArray[4] != "":
                                        for j in range(len(multiWeekArray[4])):
                                            if multiWeekArray[4][j] != "":
                                                if multiWeekArray[4][j]['DayName'] == WeekEndDayName:
                                                    WeekendDates.append(multiWeekArray[4][j]['Date'])

                        qsMonth = "SELECT MonthlyActivityId,EmpId,'" + empKey[
                            'EmpName'] + "' AS EmpName,AttendanceMonth,AttendanceYear,(CONVERT(D1_IN,CHAR)) AS D1_IN,(CONVERT(D2_IN,CHAR)) AS D2_IN,(CONVERT(D3_IN,CHAR)) AS D3_IN,(CONVERT(D4_IN,CHAR)) AS D4_IN, (CONVERT(D5_IN,CHAR)) AS D5_IN,(CONVERT(D6_IN,CHAR)) AS D6_IN,(CONVERT(D7_IN,CHAR)) AS D7_IN,(CONVERT(D8_IN,CHAR)) AS D8_IN,(CONVERT(D9_IN,CHAR)) AS D9_IN, (CONVERT(D10_IN,CHAR)) AS D10_IN,(CONVERT(D11_IN,CHAR)) AS D11_IN,(CONVERT(D12_IN,CHAR)) AS D12_IN,(CONVERT(D13_IN,CHAR)) AS D13_IN,(CONVERT(D14_IN,CHAR)) AS D14_IN,(CONVERT(D15_IN,CHAR)) AS D15_IN,(CONVERT(D16_IN,CHAR)) AS D16_IN,(CONVERT(D17_IN,CHAR)) AS D17_IN,(CONVERT(D18_IN,CHAR)) AS D18_IN,(CONVERT(D19_IN,CHAR)) AS D19_IN,(CONVERT(D20_IN,CHAR)) AS D20_IN,(CONVERT(D21_IN,CHAR)) AS D21_IN,(CONVERT(D22_IN,CHAR)) AS D22_IN,(CONVERT(D23_IN,CHAR)) AS D23_IN,(CONVERT(D24_IN,CHAR)) AS D24_IN,(CONVERT(D25_IN,CHAR)) AS D25_IN,(CONVERT(D26_IN,CHAR)) AS D26_IN,(CONVERT(D27_IN,CHAR)) AS D27_IN,(CONVERT(D28_IN,CHAR)) AS D28_IN,(CONVERT(D29_IN,CHAR)) AS D29_IN,(CONVERT(D30_IN,CHAR)) AS D30_IN,(CONVERT(D31_IN,CHAR)) AS D31_IN from MonthlyActivity where AttendanceMonth = '" + AttendanceMonth + "' and  AttendanceYear='" + AttendanceYear + "' and EmpId='" + \
                                  empKey['EmpId'] + "' AND LicKey = '" + LicKey + "' and EmpId='" + empKey[
                                      'EmpId'] + "' ORDER BY AttendanceMonth,MonthlyActivityId ASC"
                        # print(qsMonth)
                        rsMonth = DB.selectAllData(qsMonth)
                        if rsMonth:
                            timearray = []
                            timearray = rsMonth
                            timearray[0]['HolidayList'] = rsQuerryHolidayList
                            timearray[0]['CompOff'] = rsQuerryCompOffList
                            timearray[0]['Leave'] = rsQuerryLeaveList
                            timearray[0]['Weekend'] = WeekendDates
                            resultArray.append(timearray[0])
                        else:
                            timearray = []
                            timeArr = {}
                            timeArr['EmpName'] = empKey['EmpName']
                            timeArr['EmpId'] = empKey['EmpId']
                            timeArr['AttendanceMonth'] = AttendanceMonth
                            timeArr['AttendanceYear'] = AttendanceYear
                            timeArr['D1_IN'] = timeArr['D2_IN'] = timeArr['D3_IN'] = timeArr['D4_IN'] = timeArr[
                                'D5_IN'] = \
                                timeArr['D6_IN'] = timeArr['D7_IN'] = timeArr['D8_IN'] = timeArr['D9_IN'] = timeArr[
                                'D10_IN'] = \
                                timeArr['D11_IN'] = timeArr['D12_IN'] = timeArr['D13_IN'] = timeArr['D14_IN'] = timeArr[
                                'D15_IN'] = timeArr['D16_IN'] = timeArr['D17_IN'] = timeArr['D18_IN'] = timeArr[
                                'D19_IN'] = \
                                timeArr['D20_IN'] = timeArr['D21_IN'] = timeArr['D22_IN'] = timeArr['D23_IN'] = timeArr[
                                'D24_IN'] = timeArr['D25_IN'] = timeArr['D26_IN'] = timeArr['D27_IN'] = timeArr[
                                'D28_IN'] = \
                                timeArr['D29_IN'] = timeArr['D30_IN'] = timeArr['D31_IN'] = '00:00:00'
                            timeArr['HolidayList'] = rsQuerryHolidayList
                            timeArr['CompOff'] = rsQuerryCompOffList
                            timeArr['Leave'] = rsQuerryLeaveList
                            timeArr['Weekend'] = []
                            resultArray.append(timeArr)
                    response = {'category': "1", 'message': "success", 'ResponseData': resultArray}
            return response


# API FOR Single Timesheet Delete
class RcAPIMonthlySummeryList(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AttendanceMonth = ''
            if 'AttendanceMonth' in RequestData:
                AttendanceMonth = RequestData['AttendanceMonth']
            if (LicKey.isspace() == True or LicKey == '') or (
                    AttendanceMonth.isspace() == True or AttendanceMonth == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                AttendanceMonth = AttendanceMonth.strip()
                now = datetime.now()
                date = now.strftime('%Y-%m-%d')
                today = datetime.strptime(date, "%Y-%m-%d")
                AttendanceYear = today.year
                qsZoho = "SELECT A.*,B.EmpName FROM MonthlySummery AS A,EmployeeRegistration AS B WHERE A.AttendanceMonth = '" + str(
                    AttendanceMonth) + "' and A.AttendanceYear='" + str(
                    AttendanceYear) + "' and A.LicKey='" + LicKey + "' and A.EmpId=B.EmpId"
                ResponseData = DB.selectAllData(qsZoho)
                response = {'category': '1', 'message': 'List of MonthlySummery', 'responseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# Assign Shift
class RcAPIEmployeeShiftHistory(Resource):
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                EmpId = ShiftMasterId = FromDate = ToDate = BaseLocationId = ''
                if 'EmpId' in RequestData and 'ShiftMasterId' in RequestData and 'FromDate' in RequestData and 'ToDate' in RequestData and 'BaseLocationId' in RequestData:
                    EmpId, ShiftMasterId, FromDate, ToDate, BaseLocationId = RequestData['EmpId'], RequestData[
                        'ShiftMasterId'], RequestData['FromDate'], RequestData['ToDate'], RequestData['BaseLocationId']
                now = datetime.now()
                month = FromDate.split('-')
                ShiftMonth = month[1]
                ShiftYear = month[0]
                CreatedDate = now.strftime('%Y-%m-%d %H:%M:%S')
                TodayDate = now.strftime('%Y-%m-%d')
                if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == '') or (
                        ShiftMasterId.isspace() == True or ShiftMasterId == '') or (
                        FromDate.isspace() == True or FromDate == '') or (ToDate.isspace() == True or ToDate == '') or (
                        BaseLocationId.isspace() == True or BaseLocationId == ''):
                    response = {'category': '0', 'message': 'All fields are mandatory.'}
                else:
                    EmpId = EmpId.strip()
                    ShiftMasterId = ShiftMasterId.strip()
                    FromDate = FromDate.strip()
                    ToDate = ToDate.strip()
                    BaseLocationId = BaseLocationId.strip()
                    if FromDate <= ToDate and TodayDate <= FromDate:
                        SuccessresponseArray = []
                        ErrorresponseArray = []
                        start = datetime.strptime(FromDate, "%Y-%m-%d")
                        end = datetime.strptime(ToDate, "%Y-%m-%d")
                        endNextDate = end + timedelta(days=1)
                        endNextDate.strftime('%Y-%m-%d')
                        date_array = (start + timedelta(days=x) for x in range(0, (endNextDate - start).days))
                        for date_object in date_array:
                            AssignDate = date_object.strftime("%Y-%m-%d")
                            date_obj = datetime.strptime(AssignDate, '%Y-%m-%d')
                            NextDate = date_obj + timedelta(days=1)
                            NextDate.strftime('%Y-%m-%d')
                            RsShiftMaster = DB.retrieveAllData("ShiftMaster", "",
                                                               "`LicKey`='" + LicKey + "' AND  `ShiftMasterId`='" + ShiftMasterId + "'",
                                                               "")
                            lengthofRsShiftMaster = len(RsShiftMaster)
                            if lengthofRsShiftMaster > 0:
                                IsNightShift = str(RsShiftMaster[0]['IsNightShift'])
                                if IsNightShift != '1':
                                    NextDate = AssignDate
                            # print(type(AssignDate))
                            Assign_Month = AssignDate.split('-')
                            assign_ShiftMonth = Assign_Month[1]
                            QRShiftMaster = DB.retrieveAllData("ShiftMaster", "",
                                                               "`LicKey`='" + LicKey + "' AND `ShiftMasterId`='" + ShiftMasterId + "' AND `BaseLocationId`='" + BaseLocationId + "'",
                                                               "")
                            if QRShiftMaster:
                                EmpIdArray = EmpId.split(",")
                                for i in range(len(EmpIdArray)):
                                    EmployeeId = EmpIdArray[i]
                                    ResponseData = DB.retrieveAllData("EmployeeRegistration", "",
                                                                      "`LicKey`='" + LicKey + "' AND `EmpId`='" + EmployeeId + "' AND `BaseLocationId`='" + BaseLocationId + "'",
                                                                      "")
                                    if len(ResponseData) > 0:
                                        ResponseOfShift = DB.retrieveAllData("EmployeeShiftHistory", "",
                                                                             "`LicKey`='" + LicKey + "' AND  `EmpId`='" + EmployeeId + "' AND `StartDate`='" + AssignDate + "'",
                                                                             "")
                                        if len(ResponseOfShift) > 0:
                                            if ResponseOfShift[0]['ShiftMasterId'] != int(ShiftMasterId):
                                                values = {'ShiftMasterId': str(ShiftMasterId), 'EndDate': str(NextDate),
                                                          'UpdatedDate': CreatedDate, 'ShiftYear': str(ShiftYear),
                                                          'ShiftMonth': str(assign_ShiftMonth)}
                                                showmessage = DB.updateData("EmployeeShiftHistory", values,
                                                                            "`LicKey`='" + LicKey + "' AND  `EmpId`='" + EmployeeId + "' AND `StartDate`='" + AssignDate + "'")
                                                if showmessage['messageType'] == 'success':
                                                    succresponse = {'category': '1',
                                                                    'message': 'Assign shift added Successfully.'}
                                                    SuccessresponseArray.append(succresponse)
                                                else:
                                                    errresponse = {'category': '0', 'message': 'Error Occured'}
                                                    ErrorresponseArray.append(errresponse)
                                            else:
                                                errresponse = {'category': '0',
                                                               'message': 'Already Assign shift available(' + AssignDate + ').'}
                                                ErrorresponseArray.append(errresponse)
                                        else:
                                            values = {'LicKey': LicKey, 'EmpId': EmployeeId,
                                                      'ShiftMasterId': ShiftMasterId, 'StartDate': str(AssignDate),
                                                      'EndDate': str(NextDate), 'CreatedDate': CreatedDate,
                                                      'UpdatedDate': CreatedDate, 'ShiftYear': str(ShiftYear),
                                                      'ShiftMonth': str(assign_ShiftMonth)}
                                            showmessage = DB.insertData("EmployeeShiftHistory", values)
                                            if showmessage['messageType'] == 'success':
                                                succresponse = {'category': '1',
                                                                'message': 'Assign shift added Successfully.',
                                                                'AssignDate': str(AssignDate), 'EmpId': str(EmployeeId)}
                                                SuccessresponseArray.append(succresponse)
                                            else:
                                                errresponse = {'category': '0', 'message': 'Error Occured'}
                                                ErrorresponseArray.append(errresponse)
                                    else:
                                        message = "This EmpId : " + str(EmployeeId) + " is not available."
                                        errresponse = {'category': '0', 'message': message}
                                        ErrorresponseArray.append(errresponse)
                            else:
                                message = "This ShiftMasterId : " + str(ShiftMasterId) + " is not available."
                                errresponse = {'category': '0', 'message': message}
                                ErrorresponseArray.append(errresponse)
                            lengthofsuccess = len(SuccessresponseArray)
                            if lengthofsuccess > 0:
                                response = {'category': '1', 'message': 'Assign shift added Successfully.',
                                            'SuccessResponse': SuccessresponseArray}
                            else:
                                response = {'category': '0', 'message': 'Assign shift not added.',
                                            'ErrorResponse': ErrorresponseArray}
                    else:
                        message = "Start date should be less than End date."
                        response = {'category': '0', 'message': message}
            response = make_response(jsonify(response))
            return response

    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank.", 'RequestData': RequestData}
            else:
                EmpId = ShiftMasterId = AssignDate = ''
                if 'EmpId' in RequestData and 'ShiftMasterId' in RequestData and 'AssignDate' in RequestData:
                    EmpId, ShiftMasterId, AssignDate = RequestData['EmpId'], RequestData['ShiftMasterId'], RequestData[
                        'AssignDate']
                now = datetime.now()
                UpdatedDate = now.strftime('%Y-%m-%d')
                if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == '') or (
                        EmpId.isspace() == True or EmpId == '') or (
                        ShiftMasterId.isspace() == True or ShiftMasterId == '') or (
                        AssignDate.isspace() == True or AssignDate == ''):
                    response = {'category': "0", 'message': "All fields are mandatory."}
                else:
                    MasterId = MasterId.strip()
                    EmpId = EmpId.strip()
                    ShiftMasterId = ShiftMasterId.strip()
                    AssignDate = AssignDate.strip()
                    curDate = datetime.now()
                    month = AssignDate.split('-')
                    ShiftMonth = month[1]
                    ShiftYear = month[0]
                    CreatedDate = now.strftime('%Y-%m-%d %H:%M:%S')
                    ResponseOfShift = DB.retrieveAllData("EmployeeShiftHistory", "",
                                                         "`LicKey`='" + LicKey + "' AND `EmployeeShiftHistoryId`='" + MasterId + "'",
                                                         "")
                    if ResponseOfShift:
                        date_obj = datetime.strptime(AssignDate, '%Y-%m-%d')
                        NextDate = date_obj + timedelta(days=1)
                        RsShiftMaster = DB.retrieveAllData("ShiftMaster", "",
                                                           "`LicKey`='" + LicKey + "' AND  `ShiftMasterId`='" + ShiftMasterId + "'",
                                                           "")
                        lengthofRsShiftMaster = len(RsShiftMaster)
                        if lengthofRsShiftMaster > 0:
                            IsNightShift = str(RsShiftMaster[0]['IsNightShift'])
                            if IsNightShift != '1':
                                NextDate = AssignDate
                        # condition for: Can not update for Past date, current date
                        if str(ResponseOfShift[0]['StartDate']) > str(curDate) and str(AssignDate) > str(curDate):
                            values = {'EmpId': EmpId, 'StartDate': str(AssignDate), 'EndDate': str(NextDate),
                                      'ShiftMasterId': str(ShiftMasterId), 'UpdatedDate': str(curDate),
                                      'ShiftYear': str(ShiftYear), 'ShiftMonth': str(ShiftMonth)}
                            showmessage = DB.updateData("EmployeeShiftHistory", values,
                                                        "`LicKey`='" + LicKey + "' AND `EmployeeShiftHistoryId`='" + MasterId + "'")
                            if showmessage['messageType'] == 'success':
                                response = {'category': '1', 'message': 'Assign shift updated Successfully.'}
                            else:
                                response = {'category': '0', 'message': 'Error Occured'}
                        else:
                            response = {'category': '0', 'message': 'Sorry! you can not change record of past date.'}
                    else:
                        response = {'category': '0', 'message': 'Data not found.'}
            response = make_response(jsonify(response))
            return response

    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            now = datetime.now()
            todayDate = now.strftime('%Y-%m-%d')
            todayDate = datetime.strptime(todayDate, "%Y-%m-%d")
            if MasterId == '':
                response = {'category': '0', 'message': 'Master Id should not be blank.'}
            else:
                ResponseData1 = DB.selectAllData(
                    "Select * from EmployeeShiftHistory where `LicKey`= '" + LicKey + "' AND `EmployeeShiftHistoryId`= '" + MasterId + "'")
                if len(ResponseData1) > 0:
                    StartDateStr = str(ResponseData1[0]['StartDate'])
                    StartDate = datetime.strptime(StartDateStr, "%Y-%m-%d")
                    if StartDate > todayDate:
                        ResponseData = DB.deleteSingleRow('EmployeeShiftHistory',
                                                          "`LicKey`= '" + LicKey + "' AND `EmployeeShiftHistoryId`= '" + MasterId + "'")
                        response = {'category': '1', 'message': 'EmployeeShiftHistory deleted successfully.'}
                    else:
                        response = {'category': '0', 'message': 'Past or today Employee Shift History can not delete.'}
                else:
                    response = {'category': '0', 'message': 'Data not found'}
            response = make_response(jsonify(response))
            return response

    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                querry = "select EmployeeShiftHistoryId,EmpId,ShiftMasterId,CONVERT(StartDate,CHAR) AS StartDate,CONVERT(EndDate,CHAR) AS EndDate,CONVERT(CreatedDate,CHAR) AS CreatedDate,CONVERT(UpdatedDate,CHAR) AS UpdatedDate from EmployeeShiftHistory where LicKey='" + LicKey + "' and EmployeeShiftHistoryId='" + MasterId + "'"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# EMPLOYEE SHIFT History LIST Serch date wise

class RcAPIGetEmployeeShiftHistory(Resource):
    def post(self):  # here Master is the EmpID
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            SearchDate = ''
            if 'SearchDate' in RequestData:
                SearchDate = RequestData['SearchDate']
            if LicKey.isspace() == True or SearchDate.isspace() == True:
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                SearchDate = SearchDate.strip()
                SearchDate = datetime.strptime(SearchDate, "%Y-%m-%d")
                querry = "Select A.EmpId, B.EmpName, C.LocationName,C.BaseLocationId,A.EmployeeShiftHistoryId, D.ShiftMasterId, convert(A.StartDate,char) AS StartDate, convert(A.EndDate,char) AS EndDate, convert(D.StartTime,char) AS StartTime, convert(D.EndTime,char) AS EndTime, D.ShiftName from EmployeeShiftHistory AS A, EmployeeRegistration AS B,BaseLocation AS C,ShiftMaster AS D WHERE A.EmpId=B.EmpId and B.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.StartDate='" + str(
                    SearchDate) + "' GROUP BY A.EmpId ORDER BY A.EmployeeShiftHistoryId DESC"
                ResponseData = DB.selectAllData(querry)
                response = {'category': "1", 'message': "Success.", 'ResponseData': ResponseData}
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Erorr!No data found."}
            response = make_response(jsonify(response))
            return response


# Get Employee Details for Create User
class RcAPIUserHistory(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                EmpId = MasterId
                if LicKey == '' or EmpId == '':
                    response = {'category': "0", 'message': "All fields are mandatory."}
                else:
                    querry = "select UserPrivilegeId,EmpId,LicKey,MenuMasterId,SubMenuMasterId,FullControl,EntryOnly,ReadOnly,UpdateOnly,NoControl,DeleteOnly,convert(UpdatedDate,char) AS UpdatedDate  from UserPrivilege  where LicKey='" + LicKey + "' and EmpId='" + MasterId + "' "
                    # A.EmployeeRegistrationId
                    ResponseData = DB.selectAllData(querry)
                    if len(ResponseData) == 0:
                        response = {'category': '0', 'message': 'Data not found !.'}
                    else:
                        response = {'category': "1", 'message': "success", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


# API summary report
'''class RcAPIMonthlySummaryReport(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AttendanceMonth = ''
            AttendanceYear = ''
            BaseLocationId = ''
            if 'AttendanceYear' in RequestData and 'AttendanceMonth' in RequestData and 'BaseLocationId' in RequestData:
                AttendanceYear = RequestData['AttendanceYear']
                AttendanceMonth = RequestData['AttendanceMonth']
                BaseLocationId = RequestData['BaseLocationId']
            if (LicKey.isspace() == True or LicKey == '' ) or (AttendanceMonth.isspace() == True or  AttendanceMonth == '' ) or (AttendanceYear.isspace() == True or AttendanceYear == '' ) or (BaseLocationId.isspace() == True or BaseLocationId == '') :
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                AttendanceMonth = AttendanceMonth.strip()
                AttendanceYear = AttendanceYear.strip()
                BaseLocationId = BaseLocationId.strip()
                curDate = datetime.today().date()
                ResponseData=[]
                Query1="select EmpId,EmpName from EmployeeRegistration where IsActive=1 and IsDelete=0 and BaseLocationId='"+BaseLocationId+"' and LicKey='"+LicKey+"' GROUP BY EmpId"
                ResponseData1 = DB.selectAllData(Query1)
                for i in range(len(ResponseData1)):
                    EmpId=ResponseData1[i]['EmpId']
                    EmpName=ResponseData1[i]['EmpName']
                    Query2="Select ImagePath From DatasetEncodings WHERE EmpId='"+EmpId+"' and LicKey='"+LicKey+"' and BaseLocationId='"+BaseLocationId+"' LIMIT 1"
                    ResponseData2 = DB.selectAllData(Query2)
                    if len(ResponseData2) == 0:
                        ImagePath = 'N/A'
                    else:
                        ImagePath = ResponseData2[0]['ImagePath']
                    #UnpaidLeave
                    Query3="Select count(EmployeeLeaveHistoryId) AS UnpaidLeave from EmployeeLeaveHistory where EmpId='"+EmpId+"' and BaseLocationId='"+BaseLocationId+"' and LeaveType=0 and Status=1 and LicKey='"+LicKey+"'"
                    ResponseData3 = DB.selectAllData(Query3)
                    UnpaidLeave = ResponseData3[0]['UnpaidLeave']

                    # PaidLeave
                    Query4="Select count(EmployeeLeaveHistoryId) AS PaidLeave from EmployeeLeaveHistory where EmpId='"+EmpId+"' and BaseLocationId='"+BaseLocationId+"' and LeaveType=1 and Status=1 and extract(month from LeaveDate)='"+AttendanceMonth+"' and extract(year from LeaveDate)='"+AttendanceYear+"' and LicKey='"+LicKey+"'"
                    ResponseData4 = DB.selectAllData(Query4)
                    PaidLeave = ResponseData4[0]['PaidLeave']

                    #Tour
                    Query5 = "Select count(EmployeeLeaveHistoryId) AS Tour from EmployeeLeaveHistory where EmpId='" + EmpId + "' and BaseLocationId='" + BaseLocationId + "' and LeaveType=2 and Status=1 and LicKey='"+LicKey+"'"
                    ResponseData5 = DB.selectAllData(Query5)
                    Tour = ResponseData5[0]['Tour']

                    #CompOff
                    Query6="SELECT count(CompOffId) AS CompOff FROM CompOff where LicKey='"+LicKey+"'and EmpId='" + EmpId + "' and Status=1 and extract(month from OffDate)='"+AttendanceMonth+"' and extract(year from OffDate)='"+AttendanceYear+"' and BaseLocationId='" + BaseLocationId + "'"
                    ResponseData6 = DB.selectAllData(Query6)
                    CompOff = ResponseData6[0]['CompOff']

                    #Holiday
                    Query7="SELECT CONVERT(SetDate,CHAR) AS SetDate FROM HolidayList where BaseLocationId='"+BaseLocationId+"' and IsActive=1 and extract(month from SetDate)='"+AttendanceMonth+"' and extract(year from SetDate)='"+AttendanceYear+"' and LicKey='"+LicKey+"' and CURRENT_DATE>SetDate"
                    ResponseData7 = DB.selectAllData(Query7)
                    Holiday=0
                    for j in range(len(ResponseData7)):
                        HolidayDate = ResponseData7[j]['SetDate']
                        Query8="SELECT ActivityDetailsId FROM ActivityDetails where EmployeeShiftHistoryId IN (SELECT EmployeeShiftHistoryId FROM `EmployeeShiftHistory` where StartDate='"+HolidayDate+"' and LicKey='"+LicKey+"' and EmpId='"+EmpId+"')"
                        ResponseData8 = DB.selectAllData(Query8)
                        if len(ResponseData8)==0:
                            Holiday=Holiday+1

                    #WorkedDays
                    Query9="select ActivityDetailsId from ActivityDetails where EmployeeShiftHistoryId in (SELECT EmployeeShiftHistoryId FROM EmployeeShiftHistory where LicKey='"+LicKey+"' and ShiftMonth='"+AttendanceMonth+"' and ShiftYear='"+AttendanceYear+"' and EmpId='"+EmpId+"' GROUP BY EmployeeShiftHistoryId ORDER BY StartDate) group by EmployeeShiftHistoryId"
                    ResponseData9 = DB.selectAllData(Query9)
                    WorkedDays=len(ResponseData9)

                    #WorkedHours
                    Query10="select TIMEDIFF(max(ADTime),min(ADTime)) AS TimeDifference from ActivityDetails where EmployeeShiftHistoryId in (SELECT EmployeeShiftHistoryId FROM EmployeeShiftHistory where LicKey='"+LicKey+"' and ShiftMonth='"+AttendanceMonth+"' and ShiftYear='"+AttendanceYear+"'and EmpId='"+EmpId+"' GROUP BY EmployeeShiftHistoryId ORDER BY StartDate) group by EmployeeShiftHistoryId"
                    ResponseData10 = DB.selectAllData(Query10)
                    WorkedHours=0
                    for k in range(len(ResponseData10)):
                        TimeDifference = ResponseData10[k]['TimeDifference']
                        TotalHoursinsec = strhourtosec(str(TimeDifference))
                        WorkedHours=WorkedHours+TotalHoursinsec
                    seconds = WorkedHours
                    a = str(seconds // 3600)
                    b = str((seconds % 3600) // 60)
                    c = str((seconds % 3600) % 60)
                    TotalworksHoursOfMonth = "{}:{}:{}".format(a, b, c)
                    Query11="SELECT ShiftMasterId,StartDate FROM `EmployeeShiftHistory` where LicKey='"+LicKey+"' and EmpId='"+EmpId+"' and ShiftMonth='"+AttendanceMonth+"' and ShiftYear='"+AttendanceYear+"' ORDER BY StartDate ASC "
                    ResponseData11 = DB.selectAllData(Query11)
                    weekendCount = 0
                    for l in range(len(ResponseData11)):
                        ShiftMasterId = ResponseData11[l]['ShiftMasterId']
                        Query12="SELECT * FROM WeekendDetails where BaseLocationId='"+str(BaseLocationId)+"' and ShiftMasterId='"+str(ShiftMasterId)+"' and ShiftMonth='"+str(AttendanceMonth)+"' and ShiftYear='"+str(AttendanceYear)+"' and IsActive=1 and IsDelete=0 and LicKey='"+LicKey+"' LIMIT 5"
                        ResponseData12 = DB.selectAllData(Query12)
                        for m in range(len(ResponseData12)):
                            if ResponseData12[m]['FirstWeek'] == "on":
                                weekendCount = weekendCount + 1
                            if ResponseData12[m]['SecondWeek'] == "on":
                                weekendCount = weekendCount + 1
                            if ResponseData12[m]['ThirdWeek'] == "on":
                                weekendCount = weekendCount + 1
                            if ResponseData12[m]['FourthWeek'] == "on":
                                weekendCount = weekendCount + 1
                            if ResponseData12[m]['FifthWeek'] == "on":
                                weekendCount = weekendCount + 1
                    newArr = {}
                    newArr['EmpId'] = EmpId
                    newArr['EmpName'] = EmpName
                    newArr['ImagePath'] = ImagePath
                    newArr['UnpaidLeave'] = UnpaidLeave
                    newArr['PaidLeave'] = PaidLeave
                    newArr['Tour'] = Tour
                    newArr['CompOff'] = CompOff
                    newArr['Holiday'] = Holiday
                    newArr['WorkedDays'] = WorkedDays
                    newArr['WorkedHours'] = TotalworksHoursOfMonth
                    newArr['Weekend'] = weekendCount
                    ResponseData.append(newArr)
                response = {'category': '1', 'message': "success",'response':ResponseData}
            response = make_response(jsonify(response))
            return response'''


# API summary report
class RcAPIMonthlySummaryReport(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AttendanceMonth = ''
            AttendanceYear = ''
            BaseLocationId = ''
            if 'AttendanceYear' in RequestData and 'AttendanceMonth' in RequestData and 'BaseLocationId' in RequestData:
                AttendanceYear = RequestData['AttendanceYear']
                AttendanceMonth = RequestData['AttendanceMonth']
                BaseLocationId = RequestData['BaseLocationId']
            if (LicKey.isspace() == True or LicKey == '') or (
                    AttendanceMonth.isspace() == True or AttendanceMonth == '') or (
                    AttendanceYear.isspace() == True or AttendanceYear == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                AttendanceMonth = AttendanceMonth.strip()
                AttendanceYear = AttendanceYear.strip()
                BaseLocationId = BaseLocationId.strip()
                curDate = datetime.today().date()
                ResponseData = []
                Query1 = "select EmpId,EmpName from EmployeeRegistration where IsActive=1 and IsDelete=0 and BaseLocationId='" + BaseLocationId + "' and LicKey='" + LicKey + "' GROUP BY EmpId"
                ResponseData1 = DB.selectAllData(Query1)
                for i in range(len(ResponseData1)):
                    EmpId = ResponseData1[i]['EmpId']
                    EmpName = ResponseData1[i]['EmpName']
                    Query2 = "Select ImagePath From DatasetEncodings WHERE EmpId='" + EmpId + "' and LicKey='" + LicKey + "' and BaseLocationId='" + BaseLocationId + "' LIMIT 1"
                    ResponseData2 = DB.selectAllData(Query2)
                    if len(ResponseData2) == 0:
                        ImagePath = 'N/A'
                    else:
                        ImagePath = ResponseData2[0]['ImagePath']
                    # UnpaidLeave
                    Query3 = "Select count(EmployeeLeaveHistoryId) AS UnpaidLeave from EmployeeLeaveHistory where EmpId='" + EmpId + "' and BaseLocationId='" + BaseLocationId + "' and LeaveType=0 and Status=1 and LicKey='" + LicKey + "'"
                    ResponseData3 = DB.selectAllData(Query3)
                    UnpaidLeave = ResponseData3[0]['UnpaidLeave']

                    # PaidLeave
                    Query4 = "Select count(EmployeeLeaveHistoryId) AS PaidLeave from EmployeeLeaveHistory where EmpId='" + EmpId + "' and BaseLocationId='" + BaseLocationId + "' and LeaveType=1 and Status=1 and extract(month from LeaveDate)='" + AttendanceMonth + "' and extract(year from LeaveDate)='" + AttendanceYear + "' and LicKey='" + LicKey + "'"
                    ResponseData4 = DB.selectAllData(Query4)
                    PaidLeave = ResponseData4[0]['PaidLeave']

                    # Tour
                    Query5 = "Select count(EmployeeLeaveHistoryId) AS Tour from EmployeeLeaveHistory where EmpId='" + EmpId + "' and BaseLocationId='" + BaseLocationId + "' and LeaveType=2 and Status=1 and LicKey='" + LicKey + "'"
                    ResponseData5 = DB.selectAllData(Query5)
                    Tour = ResponseData5[0]['Tour']

                    # CompOff
                    Query6 = "SELECT count(CompOffId) AS CompOff FROM CompOff where LicKey='" + LicKey + "'and EmpId='" + EmpId + "' and Status=1 and extract(month from OffDate)='" + AttendanceMonth + "' and extract(year from OffDate)='" + AttendanceYear + "' and BaseLocationId='" + BaseLocationId + "'"
                    ResponseData6 = DB.selectAllData(Query6)
                    CompOff = ResponseData6[0]['CompOff']

                    # Holiday
                    Query7 = "SELECT CONVERT(SetDate,CHAR) AS SetDate FROM HolidayList where BaseLocationId='" + BaseLocationId + "' and IsActive=1 and extract(month from SetDate)='" + AttendanceMonth + "' and extract(year from SetDate)='" + AttendanceYear + "' and LicKey='" + LicKey + "' and CURRENT_DATE>SetDate"
                    ResponseData7 = DB.selectAllData(Query7)
                    Holiday = 0
                    for j in range(len(ResponseData7)):
                        HolidayDate = ResponseData7[j]['SetDate']
                        Query8 = "SELECT ActivityDetailsId FROM ActivityDetails where EmployeeShiftHistoryId IN (SELECT EmployeeShiftHistoryId FROM `EmployeeShiftHistory` where StartDate='" + HolidayDate + "' and LicKey='" + LicKey + "' and EmpId='" + EmpId + "')"
                        ResponseData8 = DB.selectAllData(Query8)
                        if len(ResponseData8) == 0:
                            Holiday = Holiday + 1

                    # WorkedDays
                    Query9 = "select ActivityDetailsId from ActivityDetails where EmployeeShiftHistoryId in (SELECT EmployeeShiftHistoryId FROM EmployeeShiftHistory where LicKey='" + LicKey + "' and ShiftMonth='" + AttendanceMonth + "' and ShiftYear='" + AttendanceYear + "' and EmpId='" + EmpId + "' GROUP BY EmployeeShiftHistoryId ORDER BY StartDate) group by EmployeeShiftHistoryId"
                    ResponseData9 = DB.selectAllData(Query9)
                    WorkedDays = len(ResponseData9)

                    # WorkedHours
                    Query10 = "select TIMEDIFF(max(ADTime),min(ADTime)) AS TimeDifference from ActivityDetails where EmployeeShiftHistoryId in (SELECT EmployeeShiftHistoryId FROM EmployeeShiftHistory where LicKey='" + LicKey + "' and ShiftMonth='" + AttendanceMonth + "' and ShiftYear='" + AttendanceYear + "'and EmpId='" + EmpId + "' GROUP BY EmployeeShiftHistoryId ORDER BY StartDate) group by EmployeeShiftHistoryId"
                    ResponseData10 = DB.selectAllData(Query10)
                    WorkedHours = 0
                    for k in range(len(ResponseData10)):
                        TimeDifference = ResponseData10[k]['TimeDifference']
                        TotalHoursinsec = strhourtosec(str(TimeDifference))
                        WorkedHours = WorkedHours + TotalHoursinsec
                    seconds = WorkedHours
                    a = str(seconds // 3600)
                    b = str((seconds % 3600) // 60)
                    c = str((seconds % 3600) % 60)
                    TotalworksHoursOfMonth = "{}:{}:{}".format(a, b, c)
                    Query11 = "SELECT ShiftMasterId,StartDate FROM `EmployeeShiftHistory` where LicKey='" + LicKey + "' and EmpId='" + EmpId + "' and ShiftMonth='" + AttendanceMonth + "' and ShiftYear='" + AttendanceYear + "' ORDER BY StartDate ASC "
                    ResponseData11 = DB.selectAllData(Query11)
                    # print(Query11)
                    weekendCount = 0
                    Query12 = "SELECT * FROM WeekendDetails where BaseLocationId='" + BaseLocationId + "' and ShiftMasterId in (SELECT ShiftMasterId FROM `EmployeeShiftHistory` where LicKey='" + LicKey + "' and EmpId='" + EmpId + "' and ShiftMonth='" + AttendanceMonth + "' and ShiftYear='" + AttendanceYear + "' ORDER BY StartDate ASC) and ShiftMonth='" + AttendanceMonth + "' and ShiftYear='" + AttendanceYear + "' and IsActive=1 and IsDelete=0 and LicKey='" + LicKey + "'"
                    ResponseData12 = DB.selectAllData(Query12)
                    for m in range(len(ResponseData12)):
                        if ResponseData12[m]['FirstWeek'] == "on":
                            weekendCount = weekendCount + 1
                        if ResponseData12[m]['SecondWeek'] == "on":
                            weekendCount = weekendCount + 1
                        if ResponseData12[m]['ThirdWeek'] == "on":
                            weekendCount = weekendCount + 1
                        if ResponseData12[m]['FourthWeek'] == "on":
                            weekendCount = weekendCount + 1
                        if ResponseData12[m]['FifthWeek'] == "on":
                            weekendCount = weekendCount + 1
                    newArr = {}
                    newArr['EmpId'] = EmpId
                    newArr['EmpName'] = EmpName
                    newArr['ImagePath'] = ImagePath
                    newArr['UnpaidLeave'] = UnpaidLeave
                    newArr['PaidLeave'] = PaidLeave
                    newArr['Tour'] = Tour
                    newArr['CompOff'] = CompOff
                    newArr['Holiday'] = Holiday
                    newArr['WorkedDays'] = WorkedDays
                    newArr['WorkedHours'] = TotalworksHoursOfMonth
                    newArr['Weekend'] = weekendCount
                    ResponseData.append(newArr)
                response = {'category': '1', 'message': "success", 'response': ResponseData}
            response = make_response(jsonify(response))
            return response


# API FOR Get Location EMPLOYEE LISTING
class RcAPIEmployeeListLocationWise(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                ResponseData = DB.retrieveAllData("EmployeeRegistration", "",
                                                  "`LicKey`= '" + LicKey + "' and `BaseLocationId`= '" + MasterId + "'  and IsActive=1 and IsDelete=0",
                                                  "")
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# API FOR GET SHIFTS LocationWise
class RcAPIGetShiftsLocationWise(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                querry = "select A.ShiftMasterId,A.BaseLocationId,A.LicKey,A.ShiftName,CONVERT(A.ShiftMargin,CHAR) AS ShiftMargin,CONVERT(A.StartTime,CHAR) AS StartTime,CONVERT(A.ShiftLength,CHAR) AS ShiftLength,CONVERT(A.EndTime,CHAR) AS EndTime,CONVERT(A.CreatedDate,CHAR) AS CreatedDate,B.LocationName from ShiftMaster AS A ,BaseLocation AS B where A.LicKey='" + LicKey + "' and A.BaseLocationId='" + MasterId + "' and A.BaseLocationId=B.BaseLocationId ORDER By ShiftMasterId ASC"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
                response = make_response(jsonify(response))
                return response


class RcServicesInsertActivityDetails(Resource):
    def post(self):
        VURS = authVerifyUser.authServices()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            EmpId = ADTime = ADDate = Prob = EmpImage = ''
            EmpId = request.form['EmpId']
            ADTime = request.form['ADTime']
            ADDate = request.form['ADDate']
            Prob = request.form['Prob']
            Source = request.form['Source']
            image_64_encodedata = request.form['EmpImage']
            image_64_encode = image_64_encodedata.replace('data:image/png;base64,', '')
            image_64_encode = bytes(image_64_encode, 'utf-8')
            image_64_decode = base64.decodestring(image_64_encode)
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')
            filename = now.strftime('%Y%m%d%H%M%S')
            pathimgfull = "images/full/" + str(LicKey) + "/" + str(today)
            pathimgthump = "images/thumb/" + str(LicKey) + "/" + str(today)
            filedirfull = 'static/public/' + pathimgfull
            filedirthump = 'static/public/' + pathimgthump
            savefilefulldir = 'static/public/' + pathimgfull + "/" + str(filename) + ".png"
            savefilethumpdir = 'static/public/' + pathimgthump + "/" + str(filename) + ".png"
            if LicKey.isspace() == True or EmpId.isspace() == True or ADTime.isspace() == True or ADDate.isspace() == True or Prob.isspace() == True or image_64_encodedata.isspace() == True or Source.isspace() == True:
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpId = EmpId.strip()
                ADTime = ADTime.strip()
                ADDate = ADDate.strip()
                Prob = Prob.strip()
                image_64_encodedata = image_64_encodedata.strip()
                Source = Source.strip()
                QsShiftDetails = "SELECT A.EmployeeShiftHistoryId, A.EmpId,A.StartDate,A.EndDate,B.IsNightShift,B.BaseLocationId,A.ShiftMasterId,convert(B.StartTime,char) AS StartTime,convert(B.EndTime,char) AS EndTime from EmployeeShiftHistory AS A ,ShiftMaster AS B  where A.LicKey='" + str(
                    LicKey) + "' AND A.StartDate='" + str(ADDate) + "' AND A.EmpId='" + str(
                    EmpId) + "' AND A.ShiftMasterId=B.ShiftMasterId"
                RsShiftDetails = DB.selectAllData(QsShiftDetails)
                if len(RsShiftDetails) > 0:
                    BaseLocationId = RsShiftDetails[0]['BaseLocationId']
                    EmployeeShiftHistoryId = RsShiftDetails[0]['EmployeeShiftHistoryId']
                    ShiftMasterId = RsShiftDetails[0]['ShiftMasterId']
                    StartDate = RsShiftDetails[0]['StartDate']
                    EndDate = RsShiftDetails[0]['EndDate']
                    if not os.path.exists(filedirfull):
                        os.makedirs(filedirfull)
                    if not os.path.exists(filedirthump):
                        os.makedirs(filedirthump)
                    if image_64_encode:
                        image_result = open(savefilefulldir,
                                            'wb')  # create a writable image and write the decoding result
                        image_result.write(image_64_decode)
                        FileLocation = savefilefulldir
                        EmpImage = savefilefulldir
                        querydata = "INSERT INTO ActivityDetails (ActivityDetailsId,EmpId,EmployeeShiftHistoryId,ShiftMasterId,BaseLocationId,ADTime,ADDate ,Prob,Source,FileLocation,LicKey ,EmpImage) VALUES (NULL,'" + str(
                            EmpId) + "','" + str(EmployeeShiftHistoryId) + "','" + str(ShiftMasterId) + "','" + str(
                            BaseLocationId) + "','" + str(ADTime) + "','" + str(ADDate) + "','" + str(
                            Prob) + "','" + str(
                            Source) + "','" + FileLocation + "','" + LicKey + "','" + EmpImage + "')"
                        insertactivity = DB.directinsertData(querydata)
                    response = {'category': "1", 'message': "Recent log inserted successfully."}
                else:
                    response = {'category': "0", 'message': "Shift is not assign yet."}
            responceData = make_response(jsonify(response))
            return response


class RcServicesGetEncodingsSets(Resource):
    def get(self):
        VURS = authVerifyUser.authServices()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                ResponseData = DB.retrieveAllData("DatasetEncodings", "", "`LicKey`= '" + LicKey + "'",
                                                  "DatasetEncodingsId ASC")
                response = {'category': "1", 'message': "List of encodings.", 'ResponseData': ResponseData}
            return make_response(jsonify(response))


class RcAPIDashboardSEC(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            # ADDate='2020-11-12'#static date
            latecoming = 0
            LateEmpid = []
            currentDate = datetime.strptime(ADDate, "%Y-%m-%d")
            month = currentDate.month
            querry1 = "select COUNT(DISTINCT EmpID) AS TotalNoOfEmployees from EmployeeRegistration Where IsActive=1 and IsDelete=0 and LicKey='" + LicKey + "'"
            totalNoOfEmployees = DB.selectAllData(querry1)
            totalEmp = totalNoOfEmployees[0]['TotalNoOfEmployees']
            querry2 = "select count(DISTINCT EmpId) AS PresentEmployees from ActivityDetails where LicKey='" + LicKey + "' and ADDate='" + ADDate + "' "
            # querry2="select A.EmpId from ActivityDetails as A,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='"+ADDate+"' and E.LicKey='"+LicKey+"') and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='"+LicKey+"' group by A.EmployeeShiftHistoryId"
            presentEmployees = DB.selectAllData(querry2)
            presentEmp = presentEmployees[0]['PresentEmployees']
            AbsentEmployees = totalEmp - presentEmp
            # querry3="select A.EmpId from ActivityDetails AS A,ShiftMaster AS B where A.LicKey='"+LicKey+"' and A.ShiftMasterId=B.ShiftMasterId and GroupBy A.EmpId"
            querry4 = "select A.EmpId, A.EmpImage, B.EmpName, B.EmployeeRegistrationId, A.EmployeeShiftHistoryId, A.ShiftMasterId, convert(D.ShiftMargin,char) AS ShiftMargin, convert(min(A.ADTime),char) AS FirstSeen, convert(max(A.ADTime),char) AS LastSeen, convert(min(A.ADDate),char) AS ADDate, C.LocationName, D.ShiftName from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
            ResponseData = DB.selectAllData(querry4)
            countOfLatecoming = len(ResponseData)
            ResponseData = {'TotalNoOfEmployees': totalEmp, 'PresentEmployees': presentEmp,
                            'AbsentEmployees': AbsentEmployees, 'Latecoming': countOfLatecoming}  #
            response = {'category': '1', 'message': 'Dashboard Info.', 'ResponseDataA': ResponseData}  #
            response = make_response(jsonify(response))
            return response


# Swapping Activity log
class RcAPISingleTimesheetSwapping(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # ActivityDetailsId ID as a MasterId
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            OldEmpId = NewEmpId = ActivityDetailsId = BaseLocationId = ''
            if 'OldEmpId' in RequestData and 'NewEmpId' in RequestData and 'ActivityDetailsId' in RequestData and 'BaseLocationId' in RequestData:
                OldEmpId, NewEmpId, ActivityDetailsId, BaseLocationId = RequestData['OldEmpId'], RequestData[
                    'NewEmpId'], RequestData['ActivityDetailsId'], RequestData['BaseLocationId']
            if (LicKey.isspace() == True or LicKey == '') or (OldEmpId.isspace() == True or OldEmpId == '') or (
                    NewEmpId.isspace() == True or NewEmpId == '') or (
                    ActivityDetailsId.isspace() == True or ActivityDetailsId == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                OldEmpId = OldEmpId.strip()
                NewEmpId = NewEmpId.strip()
                ActivityDetailsId = ActivityDetailsId.strip()
                BaseLocationId = BaseLocationId.strip()
                ActivityDetailsIdArray = ActivityDetailsId.split(",")
                responseArray = []
                success = 0
                for i in range(len(ActivityDetailsIdArray)):
                    ActivityDetailId = ActivityDetailsIdArray[i]
                    RsActivityDetails = DB.retrieveAllData("ActivityDetails", "",
                                                           "`LicKey`= '" + LicKey + "' AND `EmpId`= '" + OldEmpId + "' AND `ActivityDetailsId`= '" + ActivityDetailId + "'",
                                                           "")
                    if len(RsActivityDetails) > 0:
                        values = {"EmpId": NewEmpId, "BaseLocationId": BaseLocationId}
                        showmessage = DB.updateData("ActivityDetails", values,
                                                    "`LicKey`= '" + LicKey + "' AND `EmpId`= '" + OldEmpId + "' AND `ActivityDetailsId`= '" + ActivityDetailId + "'")
                        if showmessage['messageType'] == 'success':
                            response = {'category': '1', 'message': 'Swapping activity log successfully.',
                                        'ActivityDetailsId': ActivityDetailId}
                            success = success + 1
                        else:
                            response = {'category': '0', 'message': 'Something data base error.',
                                        'ActivityDetailsId': ActivityDetailId}
                    else:
                        response = {'category': '0', 'message': 'Data not found.',
                                    'ActivityDetailsId': ActivityDetailId}
                    responseArray.append(response)

                if success > 0:
                    response = {'category': "1", 'message': "Timesheet swapping successfully.",
                                'ResponseData': responseArray}
                else:
                    response = {'category': "0", 'message': "Timesheet swapping not success.",
                                'ResponseData': responseArray}
            response = make_response(jsonify(response))
            return response


# API FOR Single Timesheet Delete
class RcAPISingleTimesheetDelete(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            EmpId = ActivityDetailsId = ''
            EmpImage = FileLocation = 'NULL'
            if 'EmpId' in RequestData and 'ActivityDetailsId' in RequestData:
                EmpId, ActivityDetailsId = RequestData['EmpId'], RequestData['ActivityDetailsId']
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == '') or (
                    ActivityDetailsId.isspace() == True or ActivityDetailsId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpId = EmpId.strip()
                ActivityDetailsId = ActivityDetailsId.strip()
                ActivityDetailsIdArray = ActivityDetailsId.split(",")
                responseArray = []
                success = 0
                for i in range(len(ActivityDetailsIdArray)):
                    ActivityDetailId = ActivityDetailsIdArray[i]
                    RsActivityDetails = DB.retrieveAllData("ActivityDetails", "",
                                                           "`LicKey`= '" + LicKey + "' AND `EmpId`= '" + EmpId + "' AND `ActivityDetailsId`= '" + ActivityDetailId + "'",
                                                           "")
                    if len(RsActivityDetails) > 0:
                        values = {'EmpImage': EmpImage, 'FileLocation': FileLocation}
                        DeleteActivityDetails = "DELETE FROM `ActivityDetails` WHERE `LicKey`= '" + LicKey + "' AND `EmpId`= '" + EmpId + "' AND `ActivityDetailsId`= '" + ActivityDetailId + "'"
                        showmessage = DB.selectAllData(DeleteActivityDetails)
                        response = {'category': '1', 'message': 'Image deleted successfully.',
                                    'ActivityDetailsId': ActivityDetailId}
                        success = success + 1
                    else:
                        response = {'category': '0', 'message': 'Data not found.',
                                    'ActivityDetailsId': ActivityDetailId}
                    responseArray.append(response)
                if success > 0:
                    response = {'category': "1", 'message': "Timesheet delete successfully.",
                                'ResponseData': responseArray}
                else:
                    response = {'category': "0", 'message': "Timesheet delete not success.",
                                'ResponseData': responseArray}
            response = make_response(jsonify(response))
            return response


class RcAPIAbsentPresentLocationAndShiftWise(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            date_obj = datetime.strptime(ADDate, '%Y-%m-%d')
            Sunday = date_obj - timedelta(days=date_obj.isoweekday())
            Saturday = Sunday + timedelta(days=6)
            mainArr = []
            presentarray = {}
            # locationList = "SELECT BaseLocationId,LocationName FROM BaseLocation WHERE BaseLocation.LicKey = '" + LicKey + "' AND IsActive = 1 LIMIT 0,5"
            locationList = "SELECT A.BaseLocationId,A.LocationName FROM BaseLocation AS A,ShiftMaster AS B  WHERE A.LicKey = '" + LicKey + "' AND A.IsActive = 1  and A.BaseLocationId=B.BaseLocationId GROUP by BaseLocationId"
            rsLoc = DB.selectAllData(locationList)
            allresponseData = []
            locationArrayData = []
            for i in range(len(rsLoc)):
                locationID = rsLoc[i]['BaseLocationId']
                locationName = rsLoc[i]['LocationName']
                shiftList = "SELECT ShiftMasterId,ShiftName FROM ShiftMaster WHERE LicKey = '" + LicKey + "' AND BaseLocationId = '" + str(
                    locationID) + "'"
                rsShift = DB.selectAllData(shiftList)
                shiftArrayData = []
                weekAttendanceArray = []
                for j in range(len(rsShift)):
                    ShiftMasterId = rsShift[j]['ShiftMasterId']
                    ShiftName = rsShift[j]['ShiftName']
                    singleDayWiseData = []
                    for i in range(1, 8):
                        modified_date = Sunday + timedelta(days=i)
                        presentarray['modified_date'] = modified_date
                        nextdate = modified_date
                        nextdate = str(nextdate)
                        var = nextdate.split(' ')
                        extractDate = var[0]
                        extractMonth = extractDate.split('-')
                        month = extractMonth[1]
                        presentQuerry = "select A.EmpId from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN (select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + extractDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and D.ShiftMasterId='" + str(
                            ShiftMasterId) + "' and C.BaseLocationId='" + str(
                            locationID) + "' group by A.EmployeeShiftHistoryId"
                        presentEmpData = DB.selectAllData(presentQuerry)
                        todayPresent = len(presentEmpData)
                        now = datetime.now()
                        date = now.strftime('%Y-%m-%d')
                        date = datetime.strptime(date, '%Y-%m-%d')
                        absentQuerry = "Select F.EmpId FROM BaseLocation AS G, EmployeeShiftHistory AS H, ShiftMaster AS I, EmployeeRegistration AS F left join DatasetEncodings AS J on (F.EmpId=J.EmpId) where F.EmpId NOT IN (select A.EmpId from ActivityDetails as A,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + extractDate + "' and E.LicKey='" + LicKey + "') and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId) and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0 and G.BaseLocationId=F.BaseLocationId and H.StartDate='" + extractDate + "' and F.EmpId=H.EmpId and H.ShiftMasterId=I.ShiftMasterId and I.ShiftMasterId='" + str(
                            ShiftMasterId) + "' and G.BaseLocationId='" + str(locationID) + "' GROUP BY F.EmpId"
                        absentEmpData = DB.selectAllData(absentQuerry)
                        todayabsent = len(absentEmpData)
                        # todayabsent = countEmployee - todayPresent
                        singleDateDataResponse = {'todayPresent': todayPresent, 'todayabsent': todayabsent,
                                                  'date': extractDate}
                        singleDayWiseData.append(singleDateDataResponse)
                    shiftwisedata = {'ShiftMasterId': ShiftMasterId, 'ShiftName': ShiftName,
                                     'ResponseData': singleDayWiseData}
                    shiftArrayData.append(shiftwisedata)
                locationwisedata = {'BaseLocationId': locationID, 'LocationName': locationName,
                                    'shiftList': shiftArrayData}
                locationArrayData.append(locationwisedata)
            response = {'category': "1", 'message': "Present and Absent Info.", "ResponseData": locationArrayData}
            response = make_response(jsonify(response))
            return response


# CHANGE PASSWORD OF USER
class RcAPIUserChangePassword(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            oldPassword = newPassword = confirmPassword = ''
            RequestData = request.get_json()
            if 'oldPassword' in RequestData and 'newPassword' in RequestData and 'confirmPassword' in RequestData and 'emailId' in RequestData:
                oldPassword = RequestData['oldPassword']
                newPassword = RequestData['newPassword']
                confirmPassword = RequestData['confirmPassword']
                emailId = RequestData['emailId']
            if (LicKey.isspace() == True or LicKey == '') or (oldPassword.isspace() == True or oldPassword == '') or (
                    newPassword.isspace() == True or newPassword == '') or (
                    confirmPassword.isspace() == True or confirmPassword == '') or (
                    emailId.isspace() == True or emailId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
                response = make_response(jsonify(response))
                return response
            else:
                oldPassword = oldPassword.strip()
                newPassword = newPassword.strip()
                confirmPassword = confirmPassword.strip()
                if newPassword == confirmPassword:
                    md5oldpassword = hashlib.md5()
                    md5oldpassword.update(oldPassword.encode("utf-8"))
                    oldhashpass = md5oldpassword.hexdigest()
                    md5newpassword = hashlib.md5()
                    md5newpassword.update(newPassword.encode("utf-8"))
                    newhashpass = md5newpassword.hexdigest()
                    tablename = 'UserLogin'
                    wherecondition = "`LicKey`= '" + LicKey + "' and UserName='" + emailId + "'"
                    order = 'UserName DESC'
                    fields = ""
                    dataRecords = DB.retrieveAllData(tablename, fields, wherecondition, order)
                    ResponseData = dataRecords
                    if ResponseData:
                        if ResponseData[0]['Password'] == oldhashpass:
                            values = {'Password': newhashpass}
                            showMsg = DB.updateData(tablename, values, wherecondition)
                            if showMsg['messageType'] == 'success':
                                response = {'category': "1", 'message': "User Password updated successfully"}
                                response = make_response(jsonify(response))
                                return response
                            else:
                                response = {'category': "0", 'message': "Sorry! error occured. Please try again later."}
                                response = make_response(jsonify(response))
                                return response
                        else:
                            response = {'category': "0", 'message': "Sorry! Credential do not match (Old Password)."}
                            response = make_response(jsonify(response))
                            return response
                    else:
                        response = {'category': "0", 'message': "Sorry! your credential not valid."}
                        response = make_response(jsonify(response))
                        return response
                else:
                    response = {'category': "0", 'message': "Sorry! new password and confirm password do not match!"}
                    response = make_response(jsonify(response))
                    return response


# GET USER PROFILE
class RcAPIUserInfo(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            EmailId = ''
            RequestData = request.get_json()
            if 'EmailId' in RequestData and 'EmailId' in RequestData:
                EmailId = RequestData['EmailId']
            if (LicKey.isspace() == True or LicKey == '') or (EmailId.isspace() == True or EmailId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                Querry = "select A.UserName ,B.MobileNo,C.AdminImg,C.OrganizationName,D.ImagePath,D.EmpId,D.EmpName From UserLogin AS A,EmployeeRegistration AS B , OrganizationDetails AS C , DatasetEncodings AS D where A.LicKey='" + LicKey + "' and B.LicKey='" + LicKey + "' and D.LicKey='" + LicKey + "' and A.BaseLocationId=D.BaseLocationId and A.EmpId=D.EmpId and A.IsDelete=0 and B.IsDelete=0 and A.IsActive=1 and B.IsActive=1 and  C.IsDelete=0 and C.IsActive=1  and A.UserName='" + EmailId + "' Group by A.UserLoginId "
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Welcome to profile.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Sorry! Data not found."}
            response = make_response(jsonify(response))
            return response


# OLD PASSWORD VERIFICATION FOR USER
class RcAPIUserOldPassword(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            OldPassword = ''
            EmailId = ''
            RequestData = request.get_json()
            if 'oldPassword' in RequestData and 'emailId' in RequestData:
                OldPassword = RequestData['oldPassword']
                EmailId = RequestData['emailId']
            if (LicKey.isspace() == True or LicKey == '') or (OldPassword.isspace() == True or OldPassword == '') or (
                    EmailId.isspace() == True or EmailId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                OldPassword = OldPassword.strip()
                EmailId = EmailId.strip()
                md5OldPassword = hashlib.md5()
                md5OldPassword.update(OldPassword.encode("utf-8"))
                Oldhashpass = md5OldPassword.hexdigest()
                querry = "select Password from UserLogin where LicKey='" + LicKey + "' and UserName='" + EmailId + "'"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    Password = ResponseData[0]['Password']
                    if Password == Oldhashpass:
                        response = {'category': "1", 'message': "Success"}
                    else:
                        response = {'category': "0", 'message': "Sorry! Invalid Password"}
                else:
                    response = {'category': "0", 'message': "Sorry!Data not found"}

            response = make_response(jsonify(response))
            return response


# API Multi Geofence Area LIST
class RcAPIMultiGeofenceArea(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                # QsGeofenceArea = "SELECT * FROM GeofenceArea WHERE LicKey='" + LicKey + "'"
                QsGeofenceArea = "select A.*,count(B.UserLoginId) AS NoOfUsers from GeofenceArea AS A Left Join UserLogin AS B on (A.GeofenceAreaId=B.GeofenceAreaId and A.LicKey='" + LicKey + "' and A.LicKey=B.LicKey) GROUP BY A.GeofenceAreaId ORDER BY A.GeofenceAreaId DESC"
                RsGeofenceArea = DB.selectAllData(QsGeofenceArea)
                if len(RsGeofenceArea) > 0:
                    response = {'category': "1", 'message': "List of all Geofence area.",
                                'ResponseData': RsGeofenceArea}
                else:
                    response = {'category': "0", 'message': "Data not found."}
            response = make_response(jsonify(response))
            return response


# SINGLE GeofenceArea LIST,ADD GeofenceArea & DELETE GeofenceArea
class RcAPIGeofenceArea(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Mastrer id as a unquie id of the table
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                GeofenceAreaData = DB.retrieveAllData("GeofenceArea", "",
                                                      "`LicKey`= '" + LicKey + "' and `GeofenceAreaId`= '" + MasterId + "'",
                                                      "")
                if len(GeofenceAreaData) > 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': GeofenceAreaData}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
            response = make_response(jsonify(response))
            return response

    # DELETE Geofence Area
    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Mastrer id as a GeofenceAreaId
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                QsGeofenceArea = "SELECT * FROM `GeofenceArea` WHERE LicKey='" + LicKey + "' AND `GeofenceAreaId`= '" + MasterId + "'"
                RsGeofenceArea = DB.selectAllData(QsGeofenceArea)
                if len(RsGeofenceArea) > 0:
                    deletelocation = DB.deleteSingleRow("GeofenceArea",
                                                        "LicKey= '" + LicKey + "' AND `GeofenceAreaId`= '" + MasterId + "'")
                    response = {'category': '1', 'message': 'Geofence area deleted successfully.'}
                else:
                    response = {'category': "0", 'message': "Data not found."}
            response = make_response(jsonify(response))
            return response

    # UPDATE Geofence Area
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AreaName = Shape = Latlang = ''
            if 'AreaName' in RequestData and 'Shape' in RequestData and 'Latlang' in RequestData:
                AreaName, Shape, Latlang = RequestData['AreaName'], RequestData['Shape'], RequestData['Latlang']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == '') or (
                    AreaName.isspace() == True or AreaName == '') or (Shape.isspace() == True or Shape == '') or (
                    Latlang.isspace() or Latlang == '') == True:
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                MasterId = MasterId.strip()
                AreaName = AreaName.strip()
                Shape = Shape.strip()
                Latlang = Latlang.strip()
                GeofenceAreaData = DB.retrieveAllData("GeofenceArea", "",
                                                      "`LicKey`= '" + LicKey + "' AND `AreaName`= '" + AreaName + "' AND `GeofenceAreaId` != '" + MasterId + "'",
                                                      "")
                if len(GeofenceAreaData) > 0:
                    response = {'category': "0", 'message': "This area name already exist.!"}
                else:
                    values = {'AreaName': AreaName, 'Shape': Shape, 'Latlang': Latlang, 'CreatedDate': CreatedDate}
                    showmessage = DB.updateData("GeofenceArea", values,
                                                "`LicKey`='" + LicKey + "' AND `GeofenceAreaId` = '" + MasterId + "'")
                    if showmessage['messageType'] == 'success':
                        response = {'category': '1', 'message': 'Geofence area updated successfully.'}
                    else:
                        response = {'category': '1', 'message': 'error occured'}
            response = make_response(jsonify(response))
            return response

    # ADD Geofence Area
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AreaName = Shape = Latlang = ''
            IsActive = '1'
            if 'AreaName' in RequestData and 'Shape' in RequestData and 'Latlang' in RequestData:
                AreaName, Shape, Latlang = RequestData['AreaName'], RequestData['Shape'], RequestData['Latlang']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (AreaName.isspace() == True or AreaName == '') or (
                    Shape.isspace() == True or Shape == '') or (Latlang.isspace() or Latlang == '') == True:
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                IsActive = IsActive.strip()
                AreaName = AreaName.strip()
                Shape = Shape.strip()
                Latlang = Latlang.strip()
                GeofenceAreaData = DB.retrieveAllData("GeofenceArea", "",
                                                      "`LicKey`= '" + LicKey + "' AND `AreaName`= '" + AreaName + "'",
                                                      "")
                if len(GeofenceAreaData) > 0:
                    response = {'category': "0", 'message': "This area name already exist.!"}
                else:
                    values = {'AreaName': AreaName, 'Shape': Shape, 'Latlang': Latlang, 'LicKey': LicKey,
                              'CreatedDate': CreatedDate}
                    showmessage = DB.insertData("GeofenceArea", values)
                    if showmessage['messageType'] == 'success':
                        response = {'category': '1', 'message': 'Geofence area added successfully.'}
                    else:
                        response = {'category': '1', 'message': 'error occured'}
            response = make_response(jsonify(response))
            return response


# Geofence check me out check
class RcAPIGeofenceCheckMeOut(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '' or MasterId == '':
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                RsOrganizationDetails = DB.selectAllData(
                    "SELECT * FROM `OrganizationDetails` WHERE `LicKey` = '" + LicKey + "'")
                countRsOrganizationDetails = len(RsOrganizationDetails)
                if countRsOrganizationDetails > 0:
                    values = {'IsGeofences': str(MasterId)}
                    RsUpdateOrganizationDetails = DB.updateData("OrganizationDetails", values,
                                                                "`LicKey`= '" + LicKey + "'")
                    if RsUpdateOrganizationDetails['messageType'] == 'success':
                        response = {'category': "1", 'message': "Geofence Check Me Out Update Successfully."}
                    else:
                        response = {'category': "0", 'message': "Sorry! error occured. Please try again later."}
                else:
                    response = {'category': "0", 'message': "Sorry! data not found."}
        response = make_response(jsonify(response))
        return response


class RcAPIUserPageAccess(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            PageUrl = ''
            EmpId = ''
            RequestData = request.get_json()
            if 'PageUrl' in RequestData and 'EmpId' in RequestData:
                PageUrl = RequestData['PageUrl']
                EmpId = RequestData['EmpId']
            if (LicKey.isspace() == True or LicKey == '') or (PageUrl.isspace() == True or PageUrl == '') or (
                    EmpId.isspace() == True or EmpId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                PageUrl = PageUrl.strip()
                Query = "select MenuUrl from   MenuMaster where MenuUrl='" + PageUrl + "'"
                ResponseData = DB.selectAllData(Query)
                if len(ResponseData) > 0:
                    Query1 = "select * from   MenuMaster where MenuUrl='" + PageUrl + "'"
                    ResponseData1 = DB.selectAllData(Query1)
                    MenuMasterId = ResponseData1[0]['MenuMasterId']
                    Query2 = "select * from  UserPrivilege where MenuMasterId='" + str(
                        MenuMasterId) + "' and EmpId='" + EmpId + "' and LicKey='" + LicKey + "'"
                    ResponseData2 = DB.selectAllData(Query2)
                    if len(ResponseData2) > 0:
                        response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData2}
                    else:
                        response = {'category': "0", 'message': "Data not found"}
                else:
                    Query3 = "select * from SubMenuMaster where SubMenuUrl='" + PageUrl + "'"
                    ResponseData3 = DB.selectAllData(Query3)
                    if len(ResponseData3) > 0:
                        MenuMasterId = ResponseData3[0]['MenuMasterId']
                        SubMenuMasterId = ResponseData3[0]['SubMenuMasterId']
                        Query4 = "select * from  UserPrivilege where MenuMasterId='" + str(
                            MenuMasterId) + "' and SubMenuMasterId='" + str(
                            SubMenuMasterId) + "' and  EmpId='" + EmpId + "' and LicKey='" + LicKey + "'"
                        ResponseData4 = DB.selectAllData(Query4)
                        if len(ResponseData4) > 0:
                            response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData4}
                        else:
                            response = {'category': "0", 'message': "Data not found"}
                    else:
                        response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# Mobile Requirements
class RcAPIMobileLocationList(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            locationList = "select BaseLocationId,LocationName FROM BaseLocation WHERE LicKey = '" + LicKey + "' AND IsActive = 1"
            item = {"BaseLocationId": 0, "LocationName": "All Location"}
            ResponseData = DB.selectAllData(locationList)
            ResponseData.append(item)
            if ResponseData:
                response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
            else:
                response = {'category': "0", 'message': "Data not found!"}
            response = make_response(jsonify(response))
            return response


class RcAPIMobileShiftList(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            BaseLocationId = ''
            RequestData = request.get_json()
            if 'BaseLocationId' in RequestData:
                BaseLocationId = RequestData['BaseLocationId']
            if (LicKey.isspace() == True or LicKey == '') or (BaseLocationId.isspace() == True or BaseLocationId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                if BaseLocationId == '0':
                    ResponseData = [{"ShiftMasterId": '0', "ShiftName": "All Shift"}]
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    locationList = "select ShiftMasterId,ShiftName FROM ShiftMaster WHERE LicKey = '" + LicKey + "' and BaseLocationId='" + BaseLocationId + "'"
                    item = {"ShiftMasterId": '0', "ShiftName": "All Shift"}
                    ResponseData = DB.selectAllData(locationList)
                    if len(ResponseData) != 0:
                        ResponseData.append(item)
                        response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                    else:
                        response = {'category': "0", 'message': "Data not found!"}
            response = make_response(jsonify(response))
            return response


class RcAPIMobileDashboard(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            BaseLocationId = ''
            ShiftMasterId = ''
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            # ADDate = '2020-11-12'
            LateComingEmployees = 0
            LateEmpid = []
            currentDate = datetime.strptime(ADDate, "%Y-%m-%d")
            month = currentDate.month
            if 'BaseLocationId' in RequestData and 'ShiftMasterId' in RequestData:
                BaseLocationId = RequestData["BaseLocationId"]
                ShiftMasterId = RequestData["ShiftMasterId"]
            # if (LicKey.isspace() == True or LicKey == '') or (BaseLocationId.isspace() == True or BaseLocationId == '') or (ShiftMasterId.isspace() == True or ShiftMasterId == '') :
            if (LicKey.isspace() == True or LicKey == '') or (BaseLocationId.isspace() == True) or (
                    ShiftMasterId.isspace() == True):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                BaseLocationId = BaseLocationId.strip()
                ShiftMasterId = ShiftMasterId.strip()
                if (BaseLocationId == '0' and ShiftMasterId == '0'):
                    querry1 = "select COUNT(DISTINCT EmpID) AS TotalNoOfEmployees from EmployeeRegistration Where IsActive=1 and IsDelete=0 and LicKey='" + LicKey + "'"
                    totalNoOfEmployees = DB.selectAllData(querry1)
                    totalEmp = totalNoOfEmployees[0]['TotalNoOfEmployees']
                    querry2 = "SELECT COUNT(DISTINCT EmpId) AS PresentEmployees from ActivityDetails  where LicKey='" + LicKey + "' and EmployeeShiftHistoryId IN(Select EmployeeShiftHistoryId from EmployeeShiftHistory where StartDate='" + ADDate + "' and LicKey='" + LicKey + "')"
                    presentEmployees = DB.selectAllData(querry2)
                    presentEmp = presentEmployees[0]['PresentEmployees']
                    AbsentEmployees = totalEmp - presentEmp
                    querry3 = "select A.EmpId, A.EmpImage, B.EmpName, B.EmployeeRegistrationId, A.EmployeeShiftHistoryId, A.ShiftMasterId, convert(D.ShiftMargin,char) AS ShiftMargin, convert(min(A.ADTime),char) AS FirstSeen, convert(max(A.ADTime),char) AS LastSeen, convert(min(A.ADDate),char) AS ADDate, C.LocationName, D.ShiftName from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
                    ResponseData = DB.selectAllData(querry3)
                    countOfLatecoming = len(ResponseData)
                    response = {'category': "1", 'TotalNoOfEmployees': totalEmp, 'PresentEmployees': presentEmp,
                                'AbsentEmployees': AbsentEmployees, 'LateComingEmployees': countOfLatecoming}
                elif (BaseLocationId != '' and BaseLocationId != '0' and ShiftMasterId == '0'):
                    querry4 = "select COUNT(DISTINCT EmpID) AS TotalNoOfEmployees from EmployeeRegistration Where IsActive=1 and IsDelete=0 and LicKey='" + LicKey + "' and BaseLocationId ='" + BaseLocationId + "'"
                    totalNoOfEmployees = DB.selectAllData(querry4)
                    totalEmp = totalNoOfEmployees[0]['TotalNoOfEmployees']
                    querry5 = "SELECT count(DISTINCT EmpId) AS PresentEmployees FROM ActivityDetails where LicKey='" + LicKey + "' and EmployeeShiftHistoryId IN (Select EmployeeShiftHistoryId from EmployeeShiftHistory where StartDate='" + ADDate + "' and LicKey='" + LicKey + "' and EmpId IN (Select EmpId from EmployeeRegistration where LicKey='" + LicKey + "' and IsActive='1' and IsDelete='0' and BaseLocationId ='" + BaseLocationId + "'))"
                    PresentEmployees = DB.selectAllData(querry5)
                    presentEmp = PresentEmployees[0]['PresentEmployees']
                    AbsentEmployees = totalEmp - presentEmp
                    querry6 = "select A.EmpId, A.EmpImage, B.EmpName, B.EmployeeRegistrationId, A.EmployeeShiftHistoryId, A.ShiftMasterId, convert(D.ShiftMargin,char) AS ShiftMargin, convert(min(A.ADTime),char) AS FirstSeen, convert(max(A.ADTime),char) AS LastSeen, convert(min(A.ADDate),char) AS ADDate, C.LocationName, D.ShiftName from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and C.BaseLocationId='" + BaseLocationId + "'and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
                    ResponseData = DB.selectAllData(querry6)
                    countOfLatecoming = len(ResponseData)
                    response = {'category': "1", 'TotalNoOfEmployees': totalEmp, 'PresentEmployees': presentEmp,
                                'AbsentEmployees': AbsentEmployees, 'LateComingEmployees': countOfLatecoming}
                else:
                    querry10 = "select COUNT(DISTINCT EmpID) AS TotalNoOfEmployees from EmployeeShiftHistory Where ShiftMasterId IN (SELECT ShiftMasterId from ShiftMaster where LicKey='" + LicKey + "' and BaseLocationId ='" + BaseLocationId + "' and  ShiftMasterId ='" + ShiftMasterId + "') And LicKey='" + LicKey + "'"
                    TotalNoOfEmployees = DB.selectAllData(querry10)
                    totalEmp = TotalNoOfEmployees[0]['TotalNoOfEmployees']
                    querry11 = "select count(DISTINCT EmpId) AS PresentEmployees from ActivityDetails where LicKey='" + LicKey + "'  and EmployeeShiftHistoryId IN(Select EmployeeShiftHistoryId from EmployeeShiftHistory where LicKey='" + LicKey + "'  and StartDate='" + ADDate + "' and ShiftMasterId IN(select ShiftMasterId from ShiftMaster where LicKey='" + LicKey + "' and BaseLocationId='" + BaseLocationId + "' and ShiftMasterId ='" + ShiftMasterId + "'))"
                    PresentEmployees = DB.selectAllData(querry11)
                    presentEmp = PresentEmployees[0]['PresentEmployees']
                    AbsentEmployees = totalEmp - presentEmp
                    querry12 = "select A.EmpId, A.EmpImage, B.EmpName, B.EmployeeRegistrationId, A.EmployeeShiftHistoryId, A.ShiftMasterId, convert(D.ShiftMargin,char) AS ShiftMargin, convert(min(A.ADTime),char) AS FirstSeen, convert(max(A.ADTime),char) AS LastSeen, convert(min(A.ADDate),char) AS ADDate, C.LocationName, D.ShiftName from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and C.BaseLocationId='" + BaseLocationId + "' and A.BaseLocationId=C.BaseLocationId and D.ShiftMasterId='" + ShiftMasterId + "' and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.BaseLocationId='" + BaseLocationId + "' and D.ShiftMasterId='" + ShiftMasterId + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
                    ResponseData = DB.selectAllData(querry12)
                    countOfLatecoming = len(ResponseData)
                    response = {'category': "1", 'TotalNoOfEmployees': totalEmp, 'PresentEmployees': presentEmp,
                                'AbsentEmployees': AbsentEmployees, 'LateComingEmployees': countOfLatecoming}
            response = make_response(jsonify(response))
            return response


class RcAPIMobLocationShiftEmployees(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            BaseLocationId = ''
            ShiftMasterId = ''
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            LateComingEmployees = 0
            LateEmpid = []
            currentDate = datetime.strptime(ADDate, "%Y-%m-%d")
            month = currentDate.month
            if 'BaseLocationId' in RequestData and 'ShiftMasterId' in RequestData:
                BaseLocationId = RequestData["BaseLocationId"]
                ShiftMasterId = RequestData["ShiftMasterId"]
            if (LicKey.isspace() == True or LicKey == '') or (BaseLocationId.isspace() == True) or (
                    ShiftMasterId.isspace() == True):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                BaseLocationId = BaseLocationId.strip()
                ShiftMasterId = ShiftMasterId.strip()
                if (BaseLocationId == '0' and ShiftMasterId == '0'):
                    # Querry="select A.*,B.LocationName from EmployeeRegistration As A,BaseLocation As B Where A.IsActive=1 and A.IsDelete=0 and A.LicKey='"+LicKey+"' and B.LicKey='"+LicKey+"' and B.IsActive=1"
                    Querry = "select A.*,B.LocationName,C.ImagePath from BaseLocation As B,DatasetEncodings AS C RIGHT JOIN EmployeeRegistration As A on (A.EmpId=C.EmpId and C.LicKey='" + LicKey + "' and C.BaseLocationId=A.BaseLocationId and C.IsActive=1 and A.IsActive=1 and A.IsDelete=0 and A.LicKey='" + LicKey + "') Where A.IsActive=1 and A.IsDelete=0 and A.LicKey='" + LicKey + "' and B.LicKey='" + LicKey + "' and B.IsActive=1 GROUP BY A.EmployeeRegistrationId"
                    RsEmpRegs = DB.selectAllData(Querry)
                    response = {'category': "1", 'ResponseData': RsEmpRegs, 'message': "Employee List"}

                elif (BaseLocationId != '' and BaseLocationId != '0' and ShiftMasterId == '0'):
                    # Querry1="select A.*,B.LocationName from EmployeeRegistration As A ,BaseLocation AS B Where A.IsActive=1 and A.IsDelete=0 and A.LicKey='"+LicKey+"' and A.BaseLocationId ='"+BaseLocationId+"' and B.BaseLocationId='"+BaseLocationId+"' and B.IsActive=1 and B.LicKey='"+LicKey+"'"
                    QUERY1 = "select A.*,B.LocationName,C.ImagePath from BaseLocation AS B ,DatasetEncodings AS C RIGHT JOIN EmployeeRegistration As A on (A.EmpId=C.EmpId and C.LicKey='" + LicKey + "' and C.BaseLocationId=1 and C.IsActive=1 and A.IsActive=1 and A.IsDelete=0 and A.LicKey='" + LicKey + "') Where A.IsActive=1 and A.IsDelete=0 and A.LicKey='" + LicKey + "' and A.BaseLocationId ='" + BaseLocationId + "' and B.BaseLocationId='" + BaseLocationId + "' and B.IsActive=1 and B.LicKey='" + LicKey + "' GROUP by A.EmployeeRegistrationId"
                    RsEmployeeRegistration = DB.selectAllData(QUERY1)
                    response = {'category': "1", 'ResponseData': RsEmployeeRegistration, 'message': "Employee List"}

                elif (ShiftMasterId != '' and ShiftMasterId != '0' and BaseLocationId == '0'):
                    # Query1 = "select C.LocationName,A.* from EmployeeRegistration AS A ,EmployeeShiftHistory AS B,BaseLocation AS C Where B.ShiftMasterId IN (SELECT ShiftMasterId from ShiftMaster where LicKey='" + LicKey + "'  and ShiftMasterId ='" + ShiftMasterId + "') And B.LicKey='" + LicKey + "' and A.LicKey='" + LicKey + "' and A.IsActive=1 and A.IsDelete=0 and A.EmpId=B.EmpId  and C.IsActive=1 and C.LicKey='"+LicKey+"' GROUP By A.EmployeeRegistrationId"#and BaseLocationId ='" + BaseLocationId + "',and C.BaseLocationId='"+BaseLocationId+"'
                    Query1 = "select D.ImagePath,C.LocationName,A.* from EmployeeShiftHistory AS B,BaseLocation AS C ,DatasetEncodings AS D RIGHT JOIN EmployeeRegistration As A on (A.EmpId=D.EmpId and D.LicKey='" + LicKey + "' and D.BaseLocationId=A.BaseLocationId and D.IsActive=1 and A.IsActive=1 and A.IsDelete=0 and A.LicKey='" + LicKey + "') Where B.ShiftMasterId IN (SELECT ShiftMasterId from ShiftMaster where LicKey='" + LicKey + "' and ShiftMasterId ='" + ShiftMasterId + "') And B.LicKey='" + LicKey + "' and A.LicKey='" + LicKey + "' and A.IsActive=1 and A.IsDelete=0 and A.EmpId=B.EmpId and C.IsActive=1 and C.LicKey='" + LicKey + "' GROUP By A.EmployeeRegistrationId"
                    RsEmployeeRegistration = DB.selectAllData(Query1)
                    response = {'category': "1", 'ResponseData': RsEmployeeRegistration, 'message': "Employee List"}

                else:
                    # Querry = "select C.LocationName,A.* from EmployeeRegistration AS A ,EmployeeShiftHistory AS B,BaseLocation AS C Where B.ShiftMasterId IN (SELECT ShiftMasterId from ShiftMaster where LicKey='" + LicKey + "' and BaseLocationId ='" + BaseLocationId + "' and ShiftMasterId ='" + ShiftMasterId + "') And B.LicKey='" + LicKey + "' and A.LicKey='" + LicKey + "' and A.IsActive=1 and A.IsDelete=0 and A.EmpId=B.EmpId and C.BaseLocationId='"+BaseLocationId+"' and C.IsActive=1 and C.LicKey='"+LicKey+"' GROUP By A.EmployeeRegistrationId"
                    Query = "select D.ImagePath, C.LocationName,A.* from EmployeeShiftHistory AS B,BaseLocation AS C,DatasetEncodings AS D RIGHT JOIN EmployeeRegistration As A on (A.EmpId=D.EmpId and D.LicKey='" + LicKey + "' and D.BaseLocationId='" + BaseLocationId + "' and D.IsActive=1 and A.IsActive=1 and A.IsDelete=0 and A.LicKey='" + LicKey + "') Where B.ShiftMasterId IN (SELECT ShiftMasterId from ShiftMaster where LicKey='" + LicKey + "' and BaseLocationId ='" + BaseLocationId + "' and ShiftMasterId ='" + ShiftMasterId + "') And B.LicKey='" + LicKey + "' and A.LicKey='" + LicKey + "' and A.IsActive=1 and A.IsDelete=0 and A.EmpId=B.EmpId and C.BaseLocationId='" + BaseLocationId + "' and C.IsActive=1 and C.LicKey='" + LicKey + "' GROUP By A.EmployeeRegistrationId"
                    RsEmployeeRegistration = DB.selectAllData(Query)
                    response = {'category': "1", 'ResponseData': RsEmployeeRegistration, 'message': "Employee List"}
            response = make_response(jsonify(response))
            return response


# API FOR Get Location wise user listing
class RcAPIUserListLocationWise(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                fields = "UserLoginId, LicKey, BaseLocationId, EmpId, UserName, UserProfileImg, MarkAttendance, MarkAttendanceType, GeofenceAreaId, IsAdmin, CreatedDate, UpdatedDate, IsActive, IsDelete"
                ResponseData = DB.retrieveAllData("UserLogin", fields,
                                                  "`LicKey`= '" + LicKey + "' and `BaseLocationId`= '" + MasterId + "'  and IsActive=1 and IsDelete=0",
                                                  "")
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# EMPLOYEE SHIFT History LIST Serch date wise
class RcAPIGetEmployeeShiftMapping(Resource):
    def post(self):  # here Master is the EmpID
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            FromDate = ''
            ToDate = ''
            EmpId = ''
            if 'FromDate' in RequestData and 'ToDate' in RequestData and 'EmpId' in RequestData:
                FromDate, ToDate, EmpId = RequestData['FromDate'], RequestData['ToDate'], RequestData['EmpId']
            if LicKey.isspace() == True or FromDate.isspace() == True or ToDate.isspace() == True or EmpId.isspace() == True:
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                FromDate = FromDate.strip()
                # FromDate = datetime.strptime(FromDate, "%Y-%m-%d")
                ToDate = ToDate.strip()
                # ToDate = datetime.strptime(ToDate, "%Y-%m-%d")
                EmpId = EmpId.strip()
                # querry = "Select A.EmpId, B.EmpName, C.LocationName,C.BaseLocationId,A.EmployeeShiftHistoryId, D.ShiftMasterId, convert(A.StartDate,char) AS StartDate, convert(A.EndDate,char) AS EndDate, convert(D.StartTime,char) AS StartTime, convert(D.EndTime,char) AS EndTime, D.ShiftName from EmployeeShiftHistory AS A, EmployeeRegistration AS B,BaseLocation AS C,ShiftMaster AS D WHERE A.EmpId=B.EmpId and B.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.StartDate='" + str(SearchDate) + "' GROUP BY A.EmpId"
                querry = "Select A.EmpId, B.EmpName, C.LocationName,C.BaseLocationId,A.EmployeeShiftHistoryId, D.ShiftMasterId, convert(A.StartDate,char) AS StartDate, convert(A.EndDate,char) AS EndDate, convert(D.StartTime,char) AS StartTime, convert(D.EndTime,char) AS EndTime, D.ShiftName from EmployeeShiftHistory AS A, EmployeeRegistration AS B,BaseLocation AS C,ShiftMaster AS D WHERE A.EmpId=B.EmpId and B.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.EmpId='" + str(
                    EmpId) + "' and A.StartDate BETWEEN '" + str(FromDate) + "' AND '" + str(
                    ToDate) + "' ORDER BY A.StartDate DESC"
                ResponseData = DB.selectAllData(querry)
                response = {'category': "1", 'message': "Success.", 'ResponseData': ResponseData}
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Success.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Erorr!No data found."}
            response = make_response(jsonify(response))
            return response


# MOBILE API
class RcAPIMobilePresentEmployee(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            BaseLocationId = ''
            ShiftMasterId = ''
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            # ADDate = '2020-11-12'
            PresentEmployee = 0
            PresentEmployee = []
            currentDate = datetime.strptime(ADDate, "%Y-%m-%d")
            month = currentDate.month
            if 'BaseLocationId' in RequestData and 'ShiftMasterId' in RequestData:
                BaseLocationId = RequestData["BaseLocationId"]
                ShiftMasterId = RequestData["ShiftMasterId"]
            # if (LicKey.isspace() == True or LicKey == '') or (BaseLocationId.isspace() == True or BaseLocationId == '') or (ShiftMasterId.isspace() == True or ShiftMasterId == '') :
            if (LicKey.isspace() == True or LicKey == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    ShiftMasterId.isspace() == True or ShiftMasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                BaseLocationId = BaseLocationId.strip()
                ShiftMasterId = ShiftMasterId.strip()
                if (BaseLocationId == '0' and ShiftMasterId == '0'):
                    query1 = "select A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(Select EmployeeShiftHistoryId from EmployeeShiftHistory where StartDate='" + ADDate + "' and LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId"
                    # print(query1)
                    presentEmp = DB.selectAllData(query1)
                    response = {'category': "1", 'message': "Present Employee Info.", 'ResponseData': presentEmp}
                elif (BaseLocationId != '' and BaseLocationId != '0' and ShiftMasterId == '0'):
                    query2 = "select A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN (Select EmployeeShiftHistoryId from EmployeeShiftHistory where StartDate='" + ADDate + "' and LicKey='" + LicKey + "' and EmpId IN (Select EmpId from EmployeeRegistration where LicKey='" + LicKey + "' and IsActive='1' and IsDelete='0' and BaseLocationId ='" + BaseLocationId + "')) and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId"
                    presentEmp = DB.selectAllData(query2)
                    response = {'category': "1", 'message': "Present Employee Info.", 'ResponseData': presentEmp}
                else:
                    query3 = "select A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN (Select EmployeeShiftHistoryId from EmployeeShiftHistory where LicKey='" + LicKey + "'  and StartDate='" + ADDate + "' and ShiftMasterId IN(select ShiftMasterId from ShiftMaster where LicKey='" + LicKey + "' and BaseLocationId='" + BaseLocationId + "' and ShiftMasterId ='" + ShiftMasterId + "')) and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId"
                    presentEmp = DB.selectAllData(query3)
                    response = {'category': "1", 'message': "Present Employee Info.", 'ResponseData': presentEmp}
            response = make_response(jsonify(response))
            return response


class RcAPIMobileAbsentEmployee(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            BaseLocationId = ''
            ShiftMasterId = ''
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            # ADDate = '2020-11-12'
            AbsentEmployees = 0
            AbsentEmployees = []
            currentDate = datetime.strptime(ADDate, "%Y-%m-%d")
            month = currentDate.month
            if 'BaseLocationId' in RequestData and 'ShiftMasterId' in RequestData:
                BaseLocationId = RequestData["BaseLocationId"]
                ShiftMasterId = RequestData["ShiftMasterId"]
            if (LicKey.isspace() == True or LicKey == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    ShiftMasterId.isspace() == True or ShiftMasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                BaseLocationId = BaseLocationId.strip()
                ShiftMasterId = ShiftMasterId.strip()
                if (BaseLocationId == '0' and ShiftMasterId == '0'):
                    query1 = "Select F.EmpId,G.LocationName,F.EmpName,H.ShiftMasterId,I.ShiftName,J.ImagePath FROM BaseLocation AS G, EmployeeShiftHistory AS H, ShiftMaster AS I, EmployeeRegistration AS F left join DatasetEncodings AS J on (F.EmpId=J.EmpId and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0) where F.EmpId NOT IN (select A.EmpId from ActivityDetails as A,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "') and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId) and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0 and G.BaseLocationId=F.BaseLocationId  and F.EmpId=H.EmpId and H.ShiftMasterId=I.ShiftMasterId GROUP BY F.EmpId"
                    # print(query1)
                    ResponseData = DB.selectAllData(query1)
                    response = {'category': "1", 'message': "Absent Employee Info.", 'ResponseData': ResponseData}
                elif (BaseLocationId != '' and BaseLocationId != '0' and ShiftMasterId == '0'):
                    query2 = "Select F.EmpId,G.LocationName,G.BaseLocationId,F.EmpName,H.ShiftMasterId,I.ShiftName,J.ImagePath FROM BaseLocation AS G, EmployeeShiftHistory AS H, ShiftMaster AS I, EmployeeRegistration AS F left join DatasetEncodings AS J on (F.EmpId=J.EmpId and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0) where F.EmpId NOT IN (select A.EmpId from ActivityDetails as A,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "') and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId) and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0 and G.BaseLocationId='" + BaseLocationId + "' and G.BaseLocationId=F.BaseLocationId  and F.EmpId=H.EmpId and H.ShiftMasterId=I.ShiftMasterId GROUP BY F.EmpId"
                    ResponseData = DB.selectAllData(query2)
                    response = {'category': "1", 'message': "Absent Employee Info.", 'ResponseData': ResponseData}
                else:
                    query3 = "Select F.EmpId,G.LocationName,G.BaseLocationId,F.EmpName,H.ShiftMasterId,I.ShiftName,J.ImagePath FROM BaseLocation AS G, EmployeeShiftHistory AS H, ShiftMaster AS I, EmployeeRegistration AS F left join DatasetEncodings AS J on (F.EmpId=J.EmpId and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0) where F.EmpId NOT IN (select A.EmpId from ActivityDetails as A,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "') and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId) and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0 and G.BaseLocationId='" + BaseLocationId + "' and H.ShiftMasterId='" + ShiftMasterId + "'  and G.BaseLocationId=F.BaseLocationId  and F.EmpId=H.EmpId and H.ShiftMasterId=I.ShiftMasterId GROUP BY F.EmpId"
                    ResponseData = DB.selectAllData(query3)
                    response = {'category': "1", 'message': "Absent Employee Info.", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


class RcAPIMobileLateComing(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            BaseLocationId = ''
            ShiftMasterId = ''
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            # ADDate = '2020-11-12'
            currentDate = datetime.strptime(ADDate, "%Y-%m-%d")
            month = currentDate.month
            if 'BaseLocationId' in RequestData and 'ShiftMasterId' in RequestData:
                BaseLocationId = RequestData["BaseLocationId"]
                ShiftMasterId = RequestData["ShiftMasterId"]
            if (LicKey.isspace() == True or LicKey == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    ShiftMasterId.isspace() == True or ShiftMasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                BaseLocationId = BaseLocationId.strip()
                ShiftMasterId = ShiftMasterId.strip()
                if (BaseLocationId == '0' and ShiftMasterId == '0'):
                    querry1 = "select A.EmpId, A.EmpImage, B.EmpName, B.EmployeeRegistrationId, A.EmployeeShiftHistoryId, A.ShiftMasterId, convert(D.ShiftMargin,char) AS ShiftMargin, convert(min(A.ADTime),char) AS FirstSeen, convert(max(A.ADTime),char) AS LastSeen, convert(min(A.ADDate),char) AS ADDate, C.LocationName, D.ShiftName from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
                    ResponseData = DB.selectAllData(querry1)
                    response = {'category': "1", 'message': "LateComing Employee Info.", 'ResponseData': ResponseData}
                elif (BaseLocationId != '' and BaseLocationId != '0' and ShiftMasterId == '0'):
                    querry2 = "select A.EmpId, A.EmpImage, B.EmpName, B.EmployeeRegistrationId, A.EmployeeShiftHistoryId, A.ShiftMasterId, convert(D.ShiftMargin,char) AS ShiftMargin, convert(min(A.ADTime),char) AS FirstSeen, convert(max(A.ADTime),char) AS LastSeen, convert(min(A.ADDate),char) AS ADDate, C.LocationName, D.ShiftName from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and C.BaseLocationId='" + BaseLocationId + "'and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
                    ResponseData = DB.selectAllData(querry2)
                    response = {'category': "1", 'message': "LateComing Employee Info.", 'ResponseData': ResponseData}
                else:
                    querry3 = "select A.EmpId, A.EmpImage, B.EmpName, B.EmployeeRegistrationId, A.EmployeeShiftHistoryId, A.ShiftMasterId, convert(D.ShiftMargin,char) AS ShiftMargin, convert(min(A.ADTime),char) AS FirstSeen, convert(max(A.ADTime),char) AS LastSeen, convert(min(A.ADDate),char) AS ADDate, C.LocationName, D.ShiftName from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and C.BaseLocationId='" + BaseLocationId + "' and A.BaseLocationId=C.BaseLocationId and D.ShiftMasterId='" + ShiftMasterId + "' and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.BaseLocationId='" + BaseLocationId + "' and D.ShiftMasterId='" + ShiftMasterId + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
                    ResponseData = DB.selectAllData(querry3)
                    response = {'category': "1", 'message': "LateComing Employee Info.", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response


class RcAPIMobileUserPrivilegeDetails(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            EmpId = ''
            RequestData = request.get_json()
            if 'EmpId' in RequestData:
                EmpId = RequestData['EmpId']
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                UserPrivilege = "Select A.UserPrivilegeId ,A.EmpId,A.LicKey,A.MenuMasterId,A.SubMenuMasterId,A.FullControl,A.EntryOnly,A.ReadOnly,A.UpdateOnly,A.NoControl,A.DeleteOnly,B.MenuName,C.SubMenuName from UserPrivilege AS A, MenuMaster AS B, SubMenuMaster AS C where A.EmpId = '" + EmpId + "' and A.LicKey='" + LicKey + "' and A.MenuMasterId=B.MenuMasterId and A.SubMenuMasterId=C.SubMenuMasterId Group By UserPrivilegeId "
                ResponseData = DB.selectAllData(UserPrivilege)
                if len(ResponseData) != 0:
                    response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "This Employee is not available in UserPrivilege."}
        response = make_response(jsonify(response))
        return response


# UPDATE PROFILE
class RcAPIMobileUpdateProfile(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            OrganizationEmailId = ''
            OrganizationMobileNo = ''
            OrganizationName = ''
            if 'OrganizationEmailId' in RequestData and 'OrganizationMobileNo' in RequestData and 'OrganizationName' in RequestData:
                OrganizationEmailId = RequestData['OrganizationEmailId']
                OrganizationMobileNo = RequestData['OrganizationMobileNo']
                OrganizationName = RequestData['OrganizationName']
            if (LicKey.isspace() == True or LicKey == '') or (
                    OrganizationEmailId.isspace() == True or OrganizationEmailId == '') or (
                    OrganizationMobileNo.isspace() == True or OrganizationMobileNo == '') or (
                    OrganizationName.isspace() == True or OrganizationName == ''):
                response = {'category': "0", 'message': 'All fields are mandatory.'}
            else:
                OrganizationEmailId = OrganizationEmailId.strip()
                OrganizationMobileNo = OrganizationMobileNo.strip()
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                tablename = "OrganizationDetails"
                wherecondition = "LicKey ='" + LicKey + "' and IsActive=1 and IsDelete=0'"
                fields = ""
                order = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    tablename = "OrganizationDetails"
                    wherecondition = "LicKey ='" + LicKey + "' and IsActive=1 and IsDelete=0"
                    values = {'OrganizationEmailId': OrganizationEmailId, 'OrganizationMobileNo': OrganizationMobileNo
                        , 'OrganizationName': OrganizationName}
                    Update_profile = DB.updateData(tablename, values, wherecondition)
                    response = {'category': '1', 'message': 'Profile updated successfully.'}
                else:
                    response = {'category': '0', 'message': 'Some data base error.'}
            response = make_response(jsonify(response))
            return response


# ADD ADMIN PROFILE
class RcAPIMobileAdminProfile(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AdminImg = ''
            adminName = ""
            if 'AdminImg' in RequestData:
                AdminImg = RequestData['AdminImg']
            if (LicKey.isspace() == True or LicKey == '') or (AdminImg.isspace() == True or AdminImg == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                AdminImg = AdminImg.strip()
                adminName = adminName.strip()
                now = datetime.now()
                file = now.strftime('%Y%m%d%H%M%S')
                if AdminImg != '':
                    encodeAdminImg = AdminImg.replace('data:image/png;base64,', '')
                    encodeImg = bytes(encodeAdminImg, 'utf-8')
                    decodeImg = base64.decodestring(encodeImg)
                    imgPath = "images/logoImg"
                    imgField = 'static/public/' + imgPath
                    # imgDir = imgField + "/" + str(file) + ".png"
                    imgDir = imgField + "/" + 'ABSTECH SERVICES' + ".png"
                    if not os.path.exists(imgField):
                        os.makedirs(imgField)
                        if encodeImg:
                            resultImg = open(imgDir, 'wb')
                            resultImg.write(decodeImg)
                        else:
                            # pass
                            a = 1
                    else:
                        resultImg = open(imgDir, 'wb')
                        resultImg.write(decodeImg)
                else:
                    imgDir = ''
                tablename = "OrganizationDetails"
                wherecondition = "`LicKey` ='" + LicKey + "' and IsDelete=0 and IsActive=1"
                fields = ""
                order = ""
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    if imgDir != '':
                        tablename = "OrganizationDetails"
                        wherecondition = "`LicKey` ='" + LicKey + "' and  `IsDelete`=0 and `IsActive`=1 "
                        values = {'AdminImg': imgDir}
                        showmessage = DB.updateData(tablename, values, wherecondition)
                        if showmessage['messageType'] == 'success':
                            response = {'category': "1", 'message': "Organization logo updated successfully."}
                            response = make_response(jsonify(response))
                            return response
                        else:
                            response = {'category': "0", 'message': "Sorry! error occured. Please try again later."}
                            response = make_response(jsonify(response))
                            return response
                    else:
                        response = {'category': '0', 'message': "Not a valid account"}
                else:
                    response = {'category': '0', 'message': 'Something data base error.'}
            response = make_response(jsonify(response))
            return response


# Prameet Code
# GET DATASET ENCODINGS
class RcAPIGetEncodings(Resource):
    def post(self):
        LicKey = request.form['MasterId']
        if LicKey == '':
            category = "0"
            message = "LicKey should not be blank."
            response = {'category': category, 'message': message}
        else:
            querryGetEncodings = "SELECT ESH.ShiftMasterId ShiftMasterId,ESH.EmployeeShiftHistoryId EmployeeShiftHistory,SM.IsNightShift NightShift,DE.* FROM `EmployeeShiftHistory` as ESH, `DatasetEncodings` as DE,`ShiftMaster` as SM where DE.`LicKey`= '" + LicKey + "' AND DE.IsActive = 1 GROUP BY DE.DatasetEncodingsId ORDER BY `EmployeeShiftHistory`  DESC"
            ResponseData = DB.selectAllData(querryGetEncodings)
            category = '1'
            message = 'List of Single Active shift.'
            response = {'category': category, 'message': message, 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


class RcAPIInsertActivityDetails(Resource):
    def post(self):
        # print("====================Test========================")
        EmpId = ADTime = ADDate = Prob = EmpImage = ''
        LicKey = request.form['LicKey']
        EmpId = request.form['EmpId']
        ADTime = request.form['ADTime']
        ADDate = request.form['ADDate']
        Prob = request.form['Prob']
        Source = request.form['Source']
        LocalId = request.form['LocalDataId']
        image_64_encodedata = request.form['EmpImage']
        image_64_encode = image_64_encodedata.replace('data:image/png;base64,', '')
        image_64_encode = bytes(image_64_encode, 'utf-8')
        image_64_decode = base64.decodestring(image_64_encode)
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        filename = now.strftime('%Y%m%d%H%M%S')
        pathimgfull = "images/full/" + str(LicKey) + "/" + str(today)
        pathimgthump = "images/thumb/" + str(LicKey) + "/" + str(today)
        filedirfull = 'static/public/' + pathimgfull
        filedirthump = 'static/public/' + pathimgthump
        savefilefulldir = 'static/public/' + pathimgfull + "/" + str(filename) + ".png"
        savefilethumpdir = 'static/public/' + pathimgthump + "/" + str(filename) + ".png"
        if LicKey.isspace() == True or EmpId.isspace() == True or ADTime.isspace() == True or ADDate.isspace() == True or Prob.isspace() == True or image_64_encodedata.isspace() == True or Source.isspace() == True:
            response = {'category': "0", 'message': "All fields are mandatory."}
        else:
            # Removing space from left and right side
            EmpId = EmpId.strip()
            ADTime = ADTime.strip()
            ADDate = ADDate.strip()
            Prob = Prob.strip()
            image_64_encodedata = image_64_encodedata.strip()
            Source = Source.strip()
            # Removing space from left and right side
            QsShiftDetails = "SELECT A.EmployeeShiftHistoryId, A.EmpId,A.StartDate,A.EndDate,B.IsNightShift,B.BaseLocationId,A.ShiftMasterId,convert(B.StartTime,char) AS StartTime,convert(B.EndTime,char) AS EndTime from EmployeeShiftHistory AS A ,ShiftMaster AS B  where A.LicKey='" + str(
                LicKey) + "' AND A.StartDate='" + str(ADDate) + "' AND A.EmpId='" + str(
                EmpId) + "' AND A.ShiftMasterId=B.ShiftMasterId"
            # print(QsShiftDetails)
            RsShiftDetails = DB.selectAllData(QsShiftDetails)
            if len(RsShiftDetails) > 0:
                BaseLocationId = RsShiftDetails[0]['BaseLocationId']
                EmployeeShiftHistoryId = RsShiftDetails[0]['EmployeeShiftHistoryId']
                ShiftMasterId = RsShiftDetails[0]['ShiftMasterId']
                IsNightShift = RsShiftDetails[0]['IsNightShift']
                StartTime = RsShiftDetails[0]['StartTime']
                EndTime = RsShiftDetails[0]['EndTime']
                if not os.path.exists(filedirfull):
                    os.makedirs(filedirfull)
                if not os.path.exists(filedirthump):
                    os.makedirs(filedirthump)
                if image_64_encode:
                    image_result = open(savefilefulldir, 'wb')  # create a writable image and write the decoding result
                    image_result.write(image_64_decode)
                    FileLocation = savefilefulldir
                    EmpImage = savefilefulldir
                    querydata = "INSERT INTO ActivityDetails (ActivityDetailsId,EmpId,EmployeeShiftHistoryId,ShiftMasterId,BaseLocationId,ADTime,ADDate ,Prob,Source,FileLocation,LicKey ,EmpImage) VALUES (NULL,'" + str(
                        EmpId) + "','" + str(EmployeeShiftHistoryId) + "','" + str(ShiftMasterId) + "','" + str(
                        BaseLocationId) + "','" + str(ADTime) + "','" + str(ADDate) + "','" + str(Prob) + "','" + str(
                        Source) + "','" + FileLocation + "','" + LicKey + "','" + EmpImage + "')"
                    insertactivity = DB.directinsertData(querydata)
                    # for notificatiosend
                    checkingPunchInTime = "SELECT * FROM ActivityDetails WHERE EmpId='" + str(
                        EmpId) + "' AND EmployeeShiftHistoryId='" + str(
                        EmployeeShiftHistoryId) + "' AND ShiftMasterId='" + str(
                        ShiftMasterId) + "' AND BaseLocationId='" + str(BaseLocationId) + "' AND ADDate='" + str(
                        ADDate) + "'"
                    RscheckingPunchInTime = DB.selectAllData(checkingPunchInTime)

                    if len(RscheckingPunchInTime) == 0:
                        NotificationTitle = "Airface Pro"
                        NotificationMessage = str(ADTime) + " | " + EmpId + " Attendance taken."
                        FCMMessageSend(LicKey, "admin", "Airface Pro", NotificationMessage)
                response = {'category': "1", 'localId': LocalId, 'message': "Recent log inserted successfully."}
            else:
                response = {'category': "0", 'message': "Shift is not assign yet."}
        responceData = make_response(jsonify(response))
        return response


# Forgot Password For Mobile API
class RcAPIMobileForgotPassword(Resource):
    def post(self):
        EmailId = ''
        RequestData = request.get_json()
        if 'EmailId' in RequestData:
            EmailId = RequestData['EmailId']
        if (EmailId.isspace() == True or EmailId == ''):
            response = {'category': "0", 'message': "All fields are mandatory."}
        else:
            Querry = "select * from OrganizationDetails where OrganizationEmailId='" + EmailId + "'  and IsActive=1 and IsDelete=0"
            ResponseData = DB.selectAllData(Querry)
            if len(ResponseData) > 0:
                string = '0123456789abcdefghijklmnopqrstuvwxyz'
                SecretKeyToConfirmProfile = ''
                varlen = len(string)
                for i in range(6):
                    SecretKeyToConfirmProfile += string[math.floor(random.random() * varlen)]
                values = {"SecretKeyToConfirmProfile": SecretKeyToConfirmProfile}
                wherecondition = "IsActive=1 and IsDelete=0 and OrganizationEmailId='" + EmailId + "' "
                DB.updateData('OrganizationDetails', values, wherecondition)
                # From here otp will send to email
                response = {'category': "1", 'message': "Otp Sent to your EmailId", 'Otp': SecretKeyToConfirmProfile}
            else:
                response = {'category': "0", 'message': "This Account Does not exist."}
        response = make_response(jsonify(response))
        return response


# Forgot Password For Mobile API
class RcAPIMobileResetPassword(Resource):
    def post(self):
        Otp = ''
        NewPassword = ''
        RequestData = request.get_json()
        if 'Otp' in RequestData and 'NewPassword' in RequestData:
            Otp = RequestData['Otp']
            NewPassword = RequestData['NewPassword']
        if (Otp.isspace() == True or Otp == '') or (NewPassword.isspace() == True or NewPassword == ''):
            response = {'category': "0", 'message': "All fields are mandatory."}
        else:
            md5password = hashlib.md5()
            md5password.update(NewPassword.encode("utf-8"))
            EncryptedPassword = md5password.hexdigest()
            Querry = "select * from OrganizationDetails where SecretKeyToConfirmProfile='" + Otp + "'  and IsActive=1 and IsDelete=0"
            ResponseData = DB.selectAllData(Querry)
            if len(ResponseData) > 0:
                values = {"OrganizationPassword": EncryptedPassword}
                wherecondition = "IsActive=1 and IsDelete=0 and SecretKeyToConfirmProfile='" + Otp + "' "
                DB.updateData('OrganizationDetails', values, wherecondition)
                response = {'category': "1", 'message': "Reset Password successfully done"}
            else:
                response = {'category': "0", 'message': "Otp didn't matched"}
        response = make_response(jsonify(response))
        return response


# Single time sheet for mobile
class RcAPIMobileSingleTimesheet(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if (LicKey.isspace() == True or LicKey == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                now = datetime.now()
                Today = now.strftime('%Y-%m-%d')
                ResponseData = []
                QScheckinactivitydetails = "SELECT count(*) as noofactivity FROM ActivityDetails  WHERE EmpId = '" + MasterId + "' AND ADDate = '" + Today + "' AND LicKey='" + LicKey + "'  ORDER BY ActivityDetailsId DESC"  # convert(A.ADTime,char) AS ADTime,
                # Querry = "SELECT B.EmpName,A.ActivityDetailsId,convert(A.ADDate,char) AS ADDate,convert(A.ADTime,char) AS ADTime,A.EmpImage,A.EmpId FROM ActivityDetails as A,EmployeeRegistration AS B WHERE A.EmpId = '"+MasterId+"' AND A.ADDate = '"+Today+"' AND A.LicKey='"+LicKey+"' and B.EmpId='"+MasterId+"' and B.LicKey='"+LicKey+"' and B.IsActive=1 and IsDelete=0 ORDER BY A.ActivityDetailsId DESC"
                RScheckinactivitydetails = DB.selectAllData(QScheckinactivitydetails)
                lenofactivity = int(RScheckinactivitydetails[0]['noofactivity'])
                if lenofactivity > 1:
                    QsIntimedata = "SELECT B.EmpName,A.ActivityDetailsId,convert(A.ADDate,char) AS ADDate,convert(min(A.ADTime),char) AS FirstSeen,A.EmpImage,A.EmpId FROM ActivityDetails as A,EmployeeRegistration AS B WHERE A.EmpId = '" + MasterId + "' AND A.ADDate = '" + Today + "' AND A.LicKey='" + LicKey + "' and B.EmpId='" + MasterId + "' and B.LicKey='" + LicKey + "' and B.IsActive=1 and B.IsDelete=0 and A.ADTime=(SELECT min(ADTime) from ActivityDetails where ADDate='" + Today + "' and EmpId='" + MasterId + "' and LicKey='" + LicKey + "') ORDER BY A.ActivityDetailsId DESC Limit 0,1"
                    Qsouttimedata = "SELECT B.EmpName,A.ActivityDetailsId,convert(A.ADDate,char) AS ADDate,convert(max(A.ADTime),char) AS LastSeen,A.EmpImage,A.EmpId FROM ActivityDetails as A,EmployeeRegistration AS B WHERE A.EmpId = '" + MasterId + "' AND A.ADDate = '" + Today + "' AND A.LicKey='" + LicKey + "' and B.EmpId='" + MasterId + "' and B.LicKey='" + LicKey + "' and B.IsActive=1 and B.IsDelete=0 and A.ADTime=(SELECT max(ADTime) from ActivityDetails where ADDate='" + Today + "' and EmpId='" + MasterId + "' and LicKey='" + LicKey + "') ORDER BY A.ActivityDetailsId DESC Limit 0,1"
                    RsIntimedata = DB.selectAllData(QsIntimedata)
                    Rsouttimedata = DB.selectAllData(Qsouttimedata)
                    indata = RsIntimedata
                    outdata = Rsouttimedata
                elif lenofactivity == 1:
                    QsIntimedata = "SELECT B.EmpName,A.ActivityDetailsId,convert(A.ADDate,char) AS ADDate,convert(min(A.ADTime),char) AS ADTime,A.EmpImage,A.EmpId FROM ActivityDetails as A,EmployeeRegistration AS B WHERE A.EmpId = '" + MasterId + "' AND A.ADDate = '" + Today + "' AND A.LicKey='" + LicKey + "' and B.EmpId='" + MasterId + "' and B.LicKey='" + LicKey + "' and B.IsActive=1 and IsDelete=0 ORDER BY A.ActivityDetailsId DESC"
                    RsIntimedata = DB.selectAllData(QsIntimedata)
                    indata = RsIntimedata
                    outdata = []
                    outdatalist = {"ADDate": "", "ADTime": "", "ActivityDetailsId": "", "EmpId": "", "EmpImage": "",
                                   "EmpName": ""}
                    outdata.append(outdatalist)
                else:
                    blankdatashow = {"ADDate": "", "ADTime": "", "ActivityDetailsId": "", "EmpId": "", "EmpImage": "",
                                     "EmpName": ""}
                    indata = []
                    outdata = []
                    indata.append(blankdatashow)
                    outdata.append(blankdatashow)
                response = {'category': "1", 'message': "List of daily recent images in a range", 'InSeen': indata,
                            'OutSeen': outdata}
        response = make_response(jsonify(response))
        return response


# All activity report for mobile team
class RcAPIMobileAllActivityReport(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if (LicKey.isspace() == True or LicKey == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                now = datetime.now()
                Today = now.strftime('%Y-%m-%d')
                # Today='2020-12-10'
                querry = "Select A.EmpId,B.EmpName,convert(A.ADTime,char) AS ADTime,A.Source,A.EmpImage,convert(A.ADDate,char) AS ADDate from ActivityDetails as A,EmployeeRegistration as B where A.EmpId=B.EmpId and A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + Today + "' and E.LicKey='" + LicKey + "') and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId order by A.ADDate DESC"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "List of recent report.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# PDF generation of shift list for mobile team BY IN/ODI01/053
class RcAPIMobileGetMultiShiftPDF(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                ShiftQuerry = "select A.ShiftMasterId,A.BaseLocationId,A.LicKey, A.ShiftName,MINUTE(TIMEDIFF(A.ShiftMargin ,A.StartTime)) as ShiftMargin,CONVERT(A.StartTime,CHAR) AS StartTime, CONVERT(A.ShiftLength,CHAR) AS ShiftLength,CONVERT(A.EndTime,CHAR) AS EndTime,IsEditable, CONVERT(A.CreatedDate,CHAR) AS CreatedDate,B.LocationName from ShiftMaster AS A ,BaseLocation AS B where A.LicKey='" + LicKey + "' and A.BaseLocationId=B.BaseLocationId ORDER By ShiftName ASC"
                RsShiftList = DB.selectAllData(ShiftQuerry)
                pdflink = ''
                if len(RsShiftList) > 0:
                    RsOfPDF = CREATEPDF.shiftList(RsShiftList)
                    response = {'category': "1", 'message': "List of all shifts", 'pdflink': RsOfPDF}
                else:
                    response = {'category': "0", 'message': "No data found"}
            response = make_response(jsonify(response))
            return response


# EXCEL generation of shift list for mobile team BY IN/ODI01/053
class RcAPIMobileMultiShiftExcel(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                excellink = ''
                ShiftQuerry = "select A.ShiftMasterId,A.BaseLocationId,A.LicKey, A.ShiftName,MINUTE(TIMEDIFF(A.ShiftMargin ,A.StartTime)) as ShiftMargin,CONVERT(A.StartTime,CHAR) AS StartTime, CONVERT(A.ShiftLength,CHAR) AS ShiftLength,CONVERT(A.EndTime,CHAR) AS EndTime,IsEditable, CONVERT(A.CreatedDate,CHAR) AS CreatedDate,B.LocationName from ShiftMaster AS A ,BaseLocation AS B where A.LicKey='" + LicKey + "' and A.BaseLocationId=B.BaseLocationId ORDER By ShiftName ASC"
                RsShiftList = DB.selectAllData(ShiftQuerry)
                # lenOfRsEmployeeList = len(RsShiftList)
                if len(RsShiftList) > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'Shift_Setting_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("Shift Setting")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:G1', 'Shift Setting', bold)
                    worksheet.write('A2', 'Sl. No', bold)
                    worksheet.write('B2', 'Shift Name', bold)
                    worksheet.write('C2', 'Shift Start Time', bold)
                    worksheet.write('D2', 'Shift End Time', bold)
                    worksheet.write('E2', 'Shift Length', bold)
                    worksheet.write('F2', 'Shift Margin', bold)
                    worksheet.write('G2', 'Location', bold)
                    row = 2
                    col = 0
                    for j in range(len(RsShiftList)):
                        ShiftName = RsShiftList[j]['ShiftName']
                        StartTime = RsShiftList[j]['StartTime']
                        EndTime = RsShiftList[j]['EndTime']
                        ShiftLength = RsShiftList[j]['ShiftLength']
                        ShiftMargin = str(RsShiftList[j]['ShiftMargin'])
                        LocationName = RsShiftList[j]['LocationName']
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, ShiftName)
                        worksheet.write(row, col + 2, StartTime)
                        worksheet.write(row, col + 3, EndTime)
                        worksheet.write(row, col + 4, ShiftLength)
                        worksheet.write(row, col + 5, str(ShiftMargin))
                        worksheet.write(row, col + 6, LocationName)
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "List of all shifts", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response


# PDF generation of Employee Shift Mapping for mobile team BY IN/ODI01/053
class RcAPIMobileGetMultiShiftMappingPDF(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            SearchDate = ''
            if 'SearchDate' in RequestData:
                SearchDate = RequestData['SearchDate']
            if LicKey.isspace() == True or SearchDate.isspace() == True:
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                SearchDate = SearchDate.strip()
                SearchDate = datetime.strptime(SearchDate, "%Y-%m-%d")
                ShiftMappingQuerry = "Select A.LicKey,A.EmpId, B.EmpName, C.LocationName,C.BaseLocationId,A.EmployeeShiftHistoryId, D.ShiftMasterId, convert(A.StartDate,char) AS StartDate, convert(A.EndDate,char) AS EndDate, convert(D.StartTime,char) AS StartTime, convert(D.EndTime,char) AS EndTime, D.ShiftName from EmployeeShiftHistory AS A, EmployeeRegistration AS B,BaseLocation AS C,ShiftMaster AS D WHERE A.EmpId=B.EmpId and B.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.StartDate='" + str(
                    SearchDate) + "' GROUP BY A.EmpId"
                RsShiftMappingList = DB.selectAllData(ShiftMappingQuerry)
                pdflink = ''
                if len(RsShiftMappingList) > 0:
                    RsOfPDF = CREATEPDF.shiftMappingList(RsShiftMappingList)
                    response = {'category': "1", 'message': "List of all mapped shifts", 'pdflink': RsOfPDF}
                else:
                    response = {'category': "0", 'message': "No data found"}
            response = make_response(jsonify(response))
            return response


# EXCEL generation of Employee Shift Mapping for mobile team BY IN/ODI01/053
class RcAPIMobileGetMultiShiftMappingEXCEL(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            SearchDate = ''
            if 'SearchDate' in RequestData:
                SearchDate = RequestData['SearchDate']
            if LicKey.isspace() == True or SearchDate.isspace() == True:
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                SearchDate = SearchDate.strip()
                SearchDate = datetime.strptime(SearchDate, "%Y-%m-%d")
                excellink = ''
                ShiftMappingQuerry = "Select A.EmpId, B.EmpName, C.LocationName,C.BaseLocationId,A.EmployeeShiftHistoryId, D.ShiftMasterId, convert(A.StartDate,char) AS StartDate, convert(A.EndDate,char) AS EndDate, convert(D.StartTime,char) AS StartTime, convert(D.EndTime,char) AS EndTime, D.ShiftName from EmployeeShiftHistory AS A, EmployeeRegistration AS B,BaseLocation AS C,ShiftMaster AS D WHERE A.EmpId=B.EmpId and B.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.StartDate='" + str(
                    SearchDate) + "' GROUP BY A.EmpId"
                RsShiftMappingList = DB.selectAllData(ShiftMappingQuerry)
                # lenOfRsEmployeeList = len(RsShiftList)
                if len(RsShiftMappingList) > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'Employee_Shift_Mapping_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("Employee Shift Mapping")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:G1', 'Employee Shift Mapping', bold)
                    worksheet.write('A2', 'Sl. No', bold)
                    worksheet.write('B2', 'EmpId', bold)
                    worksheet.write('C2', 'EmpName', bold)
                    worksheet.write('D2', 'Location', bold)
                    worksheet.write('E2', 'Shift Name', bold)
                    worksheet.write('F2', 'StartTime', bold)
                    worksheet.write('G2', 'EndTime', bold)
                    row = 2
                    col = 0
                    for j in range(len(RsShiftMappingList)):
                        EmpId = RsShiftMappingList[j]['EmpId']
                        EmpName = RsShiftMappingList[j]['EmpName']
                        LocationName = RsShiftMappingList[j]['LocationName']
                        ShiftName = RsShiftMappingList[j]['ShiftName']
                        StartTime = str(RsShiftMappingList[j]['StartTime'])
                        EndTime = RsShiftMappingList[j]['EndTime']
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, EmpId)
                        worksheet.write(row, col + 2, EmpName)
                        worksheet.write(row, col + 3, LocationName)
                        worksheet.write(row, col + 4, ShiftName)
                        worksheet.write(row, col + 5, str(StartTime))
                        worksheet.write(row, col + 6, EndTime)
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "List of all mapped shifts", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response


# PDF generation of  User List for mobile team BY IN/ODI01/053
class RcAPIMobileGetMultiUserDetailsPDF(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                UserQuerry = "Select A.UserLoginId,A.LicKey,CONVERT(A.CreatedDate,CHAR) AS CreatedDate,A.BaseLocationId,A.EmpId,A.UserName,A.UserProfileImg,A.MarkAttendance,A.IsAdmin,A.IsActive AS status,A.IsDelete,A.GeofenceAreaId,B.AreaName,B.Shape,B.Latlang,C.LocationName,D.EmployeeRegistrationId ,D.EmpName from EmployeeRegistration AS D,BaseLocation AS C,UserLogin AS A left join GeofenceArea AS B ON (A.GeofenceAreaId=B.GeofenceAreaId) where A.LicKey='" + LicKey + "' and A.BaseLocationId=C.BaseLocationId and A.EmpId=D.EmpId and A.LicKey=D.LicKey"
                RsUserList = DB.selectAllData(UserQuerry)
                pdflink = ''
                if len(RsUserList) > 0:
                    RsOfPDF = CREATEPDF.userList(RsUserList)
                    response = {'category': "1", 'message': "List of all users", 'pdflink': RsOfPDF}
                else:
                    response = {'category': "0", 'message': "No data found"}
            response = make_response(jsonify(response))
            return response


# EXCEL generation of user list for mobile team BY IN/ODI01/053
class RcAPIMobileGetMultiUserDetailsExcel(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                excellink = ''
                UserQuerry = "Select A.UserLoginId,A.LicKey,CONVERT(A.CreatedDate,CHAR) AS CreatedDate,A.BaseLocationId,A.EmpId,A.UserName,A.UserProfileImg,A.MarkAttendance,A.IsAdmin,A.IsActive AS status,A.IsDelete,A.GeofenceAreaId,B.AreaName,B.Shape,B.Latlang,C.LocationName,D.EmployeeRegistrationId ,D.EmpName from EmployeeRegistration AS D,BaseLocation AS C,UserLogin AS A left join GeofenceArea AS B ON (A.GeofenceAreaId=B.GeofenceAreaId) where A.LicKey='" + LicKey + "' and A.BaseLocationId=C.BaseLocationId and A.EmpId=D.EmpId and A.LicKey=D.LicKey"
                RsUserList = DB.selectAllData(UserQuerry)
                if len(RsUserList) > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'User_Authentication_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("User Authentication")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:G1', 'User Authentication', bold)
                    worksheet.write('A2', 'Sl. No', bold)
                    worksheet.write('B2', 'Location', bold)
                    worksheet.write('C2', 'Employee Id', bold)
                    worksheet.write('D2', 'User Name', bold)
                    worksheet.write('E2', 'Created Date', bold)
                    row = 2
                    col = 0
                    for j in range(len(RsUserList)):
                        LocationName = RsUserList[j]['LocationName']
                        EmpId = RsUserList[j]['EmpId']
                        UserName = RsUserList[j]['UserName']
                        CreatedDate = RsUserList[j]['CreatedDate']
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, LocationName)
                        worksheet.write(row, col + 2, EmpId)
                        worksheet.write(row, col + 3, UserName)
                        worksheet.write(row, col + 4, CreatedDate)
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "List of all users", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response


# to get the check in and check out time of each employee based on time BY IN/ODI01/027
class RcAPIMobileAttendanceInfo(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            ADDate = ''
            EmpId = ''
            if 'ADDate' in RequestData and 'EmpId' in RequestData:
                ADDate = RequestData['ADDate']
                EmpId = RequestData['EmpId']
            if (LicKey.isspace() == True or LicKey == '') or (ADDate.isspace() == True or ADDate == '') or (
                    EmpId.isspace() == True or EmpId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                ADDate = ADDate.strip()
                EmpId = EmpId.strip()
                QsActivityDetails = "SELECT ActivityDetailsId,CONVERT(ADTime,char) AS ADTime,EmpImage FROM `ActivityDetails` where EmpId='" + EmpId + "' and ADDate='" + ADDate + "' and LicKey='" + LicKey + "' ORDER BY ADTime ASC"
                QUERY2 = "Select A.EmpName,DAYNAME(B.ADDate) AS DayName,convert(B.ADDate,CHAR) AS ADDate,CONVERT(min(B.ADTime),CHAR) as FirstSeen,CONVERT(max(B.ADTime),CHAR) as LastSeen,CONVERT(TIMEDIFF(max(B.ADTime),min(B.ADTime)),CHAR) AS TotalHours from ActivityDetails AS B,EmployeeRegistration AS A where B.EmpId='" + EmpId + "' and B.ADDate='" + ADDate + "' and B.LicKey='" + LicKey + "' and A.EmpId=B.EmpId"
                RsActivityDetails = DB.selectAllData(QsActivityDetails)
                ResponseData1 = DB.selectAllData(QUERY2)
                ResponseData = []
                if len(RsActivityDetails) > 0:
                    no = 0
                    for j in range(len(RsActivityDetails)):
                        arrayData = {}
                        arrayData['ActivityDetailsId'] = RsActivityDetails[j]['ActivityDetailsId']
                        arrayData['ADTime'] = RsActivityDetails[j]['ADTime']
                        arrayData['EmpImage'] = RsActivityDetails[j]['EmpImage']
                        no += 1
                        if (no % 2) == 0:
                            IsType = 'Out'
                        else:
                            IsType = 'In'
                        arrayData['Type'] = IsType
                        ResponseData.append(arrayData)
                allresponse = {'timesheetdetails': ResponseData1, 'activitylog': ResponseData}
                response = {'category': "1", 'message': "List of Attendance Info", 'ResponseData': allresponse}
        response = make_response(jsonify(response))
        return response


# API Monthly Report Day wise for mobile team BY IN/ODI01/027
class RcAPIMobileMonthlyReportDaywise(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AttendanceMonth = ''
            AttendanceYear = ''
            Location = ''
            if 'AttendanceYear' in RequestData and 'AttendanceMonth' in RequestData and 'BaseLocationId' in RequestData:
                AttendanceYear, AttendanceMonth, Location = RequestData['AttendanceYear'], RequestData[
                    'AttendanceMonth'], RequestData['BaseLocationId']
            if (LicKey.isspace() == True or LicKey == '') or (
                    AttendanceYear.isspace() == True or AttendanceYear == '') or (
                    AttendanceYear.isspace() == True or AttendanceYear == '') or (
                    Location.isspace() == True or Location == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                # removeing right & left space
                AttendanceMonth = AttendanceMonth.strip()
                AttendanceYear = AttendanceYear.strip()
                Location = Location.strip()
                # removeing right & left space
                curDate = datetime.today().date()
                curDate = str(curDate)
                today = datetime.now()
                startDate = "01-" + AttendanceMonth + "-" + AttendanceYear
                monthdays_list = calendar.monthcalendar(int(AttendanceYear), int(AttendanceMonth))
                allMonthdatesArray = []
                multiWeekArray = []
                for aryIndex in range(len(monthdays_list)):
                    weeklyDayDateAppendAry = []
                    weeklyDaynoArray = monthdays_list[aryIndex]
                    for weekaryIndex in range(len(weeklyDaynoArray)):
                        singleWeekArray = []
                        singleDayno = weeklyDaynoArray[weekaryIndex]
                        date = str(singleDayno) + "-" + str(AttendanceMonth) + "-" + str(AttendanceYear)
                        passdate = str(AttendanceYear) + "-" + str(AttendanceMonth) + "-" + str(singleDayno)
                        if singleDayno != 0:
                            # For Get month all Date
                            AttendanceDate_str = str(singleDayno)
                            AttendanceMonth_str = str(AttendanceMonth)
                            AttendanceDate_str = AttendanceDate_str.zfill(2)
                            AttendanceMonth_str = AttendanceMonth_str.zfill(2)
                            assigndate = str(AttendanceYear) + "-" + str(AttendanceMonth_str) + "-" + str(
                                AttendanceDate_str)
                            DayName = findDay(date)
                            datewisesingleArray = {"DayName": DayName, "Date": assigndate}
                        else:
                            datewisesingleArray = ""
                        weeklyDayDateAppendAry.append(datewisesingleArray)
                    multiWeekArray.append(weeklyDayDateAppendAry)
                qsQuerry = "SELECT * FROM WeekendDetails WHERE LicKey = '" + LicKey + "' AND BaseLocationId= '" + Location + "' AND IsDelete = 0 "
                rsQuerry = DB.selectAllData(qsQuerry)
                if Location != '0':
                    qsQuerry = "SELECT EmpId,EmpName,BaseLocationId FROM EmployeeRegistration WHERE LicKey = '" + LicKey + "' AND BaseLocationId= '" + Location + "' AND IsDelete = 0"
                    rsQuerry = DB.selectAllData(qsQuerry)
                else:
                    qsQuerry = "SELECT EmpId,EmpName,BaseLocationId FROM EmployeeRegistration WHERE LicKey = '" + LicKey + "' AND IsDelete = 0 "
                    rsQuerry = DB.selectAllData(qsQuerry)
                resultArray = []
                qsQuerryHolidayList = "SELECT Convert(SetDate,CHAR) AS SetDate,Holiday FROM HolidayList WHERE LicKey = '" + LicKey + "' AND BaseLocationId= '" + Location + "' AND IsActive = 1  AND SetMonth= '" + AttendanceMonth + "'"
                rsQuerryHolidayList = DB.selectAllData(qsQuerryHolidayList)
                # querry = "SELECT * FROM EmployeeRegistration WHERE IsDelete = 0 AND IsActive = 1 and LicKey='" + LicKey + "' LIMIT 0,5"
                querry = "SELECT * FROM EmployeeRegistration WHERE IsDelete = 0 AND IsActive = 1 and LicKey='" + LicKey + "'"
                rsQuerry = DB.selectAllData(querry)
                employeeListData = []
                for empKey in rsQuerry:
                    qsQuerryCompOffList = "SELECT Convert(OffDate,CHAR) AS OffDate FROM CompOff WHERE LicKey = '" + LicKey + "' AND EmpId= '" + \
                                          empKey[
                                              'EmpId'] + "' AND BaseLocationId= '" + Location + "' AND Status = 1 AND extract(month from OffDate)='" + AttendanceMonth + "' AND extract(year from OffDate)='" + AttendanceYear + "'"
                    rsQuerryCompOffList = DB.selectAllData(qsQuerryCompOffList)
                    qsQuerryLeaveList = "SELECT Convert(LeaveDate,CHAR) AS LeaveDate FROM EmployeeLeaveHistory WHERE LicKey = '" + LicKey + "' AND EmpId= '" + \
                                        empKey[
                                            'EmpId'] + "' AND BaseLocationId= '" + Location + "' AND Status = 1 AND extract(month from LeaveDate)='" + AttendanceMonth + "' AND extract(year from LeaveDate)='" + AttendanceYear + "'"
                    rsQuerryLeaveList = DB.selectAllData(qsQuerryLeaveList)
                    LeaveDates = []
                    if len(rsQuerryLeaveList) > 0:
                        for leaveKey in rsQuerryLeaveList:
                            LeaveDate = str(leaveKey['LeaveDate'])
                            LeaveDates.append(LeaveDate)
                    CompOffDates = []
                    if len(rsQuerryCompOffList) > 0:
                        for CompOffKey in rsQuerryCompOffList:
                            CompOffDate = str(CompOffKey['OffDate'])
                            CompOffDates.append(CompOffDate)
                    HolidaysDates = []
                    if len(rsQuerryHolidayList) > 0:
                        for HolidayKey in rsQuerryHolidayList:
                            HolidayDate = str(HolidayKey['SetDate'])
                            HolidaysDates.append(HolidayDate)
                    result = []
                    qsShift = "SELECT ShiftMasterId from EmployeeShiftHistory WHERE EmpId='" + empKey[
                        'EmpId'] + "' and ShiftMonth='" + str(AttendanceMonth) + "' and ShiftYear='" + str(
                        AttendanceYear) + "' ORDER BY StartDate ASC LIMIT 1"
                    RsShiftList = DB.selectAllData(qsShift)
                    if len(RsShiftList) > 0:
                        ShiftMasterId = str(RsShiftList[0]['ShiftMasterId'])
                    else:
                        ShiftMasterId = '0'
                    # WeekEnd Get Dates
                    qsQuerryForWeekEndList = "SELECT WeekendDetailsId,BaseLocationId,ShiftMasterId,ShiftMonth,DayName,AllWeek,FirstWeek,SecondWeek,ThirdWeek,FourthWeek,FifthWeek FROM WeekendDetails WHERE LicKey = '" + LicKey + "' AND ShiftMasterId= '" + str(
                        ShiftMasterId) + "' AND ShiftMonth= '" + str(AttendanceMonth) + "' AND IsDelete = 0 "
                    rsQuerryForWeekEndList = DB.selectAllData(qsQuerryForWeekEndList)
                    WeekendDates = []
                    for countIndex in range(len(rsQuerryForWeekEndList)):
                        FirstWeekData = rsQuerryForWeekEndList[countIndex]['FirstWeek']
                        SecondWeekData = rsQuerryForWeekEndList[countIndex]['SecondWeek']
                        ThirdWeekData = rsQuerryForWeekEndList[countIndex]['ThirdWeek']
                        FourthWeekData = rsQuerryForWeekEndList[countIndex]['FourthWeek']
                        FifthWeekData = rsQuerryForWeekEndList[countIndex]['FifthWeek']
                        WeekEndDayName = rsQuerryForWeekEndList[countIndex]['DayName']
                        if FirstWeekData == "on":
                            if multiWeekArray[0] != "":
                                for j in range(len(multiWeekArray[0])):
                                    if multiWeekArray[0][j] != "":
                                        if multiWeekArray[0][j]['DayName'] == WeekEndDayName:
                                            WeekendDates.append(multiWeekArray[0][j]['Date'])
                        if SecondWeekData == "on":
                            if multiWeekArray[1] != "":
                                for j in range(len(multiWeekArray[1])):
                                    if multiWeekArray[1][j] != "":
                                        if multiWeekArray[1][j]['DayName'] == WeekEndDayName:
                                            WeekendDates.append(multiWeekArray[1][j]['Date'])
                        if ThirdWeekData == "on":
                            if multiWeekArray[2] != "":
                                for j in range(len(multiWeekArray[2])):
                                    if multiWeekArray[2][j] != "":
                                        if multiWeekArray[2][j]['DayName'] == WeekEndDayName:
                                            WeekendDates.append(multiWeekArray[2][j]['Date'])
                        if FifthWeekData == "on":
                            if multiWeekArray[3] != "":
                                for j in range(len(multiWeekArray[3])):
                                    if multiWeekArray[3][j] != "":
                                        if multiWeekArray[3][j]['DayName'] == WeekEndDayName:
                                            WeekendDates.append(multiWeekArray[3][j]['Date'])
                        if FifthWeekData == "on":
                            if multiWeekArray[4] != "":
                                for j in range(len(multiWeekArray[4])):
                                    if multiWeekArray[4][j] != "":
                                        if multiWeekArray[4][j]['DayName'] == WeekEndDayName:
                                            WeekendDates.append(multiWeekArray[4][j]['Date'])

                    qsMonth = "SELECT MonthlyActivityId,EmpId,'" + empKey[
                        'EmpName'] + "' AS EmpName,AttendanceMonth,AttendanceYear,(CONVERT(D1_IN,CHAR)) AS D1_IN,(CONVERT(D2_IN,CHAR)) AS D2_IN,(CONVERT(D3_IN,CHAR)) AS D3_IN,(CONVERT(D4_IN,CHAR)) AS D4_IN, (CONVERT(D5_IN,CHAR)) AS D5_IN,(CONVERT(D6_IN,CHAR)) AS D6_IN,(CONVERT(D7_IN,CHAR)) AS D7_IN,(CONVERT(D8_IN,CHAR)) AS D8_IN,(CONVERT(D9_IN,CHAR)) AS D9_IN, (CONVERT(D10_IN,CHAR)) AS D10_IN,(CONVERT(D11_IN,CHAR)) AS D11_IN,(CONVERT(D12_IN,CHAR)) AS D12_IN,(CONVERT(D13_IN,CHAR)) AS D13_IN,(CONVERT(D14_IN,CHAR)) AS D14_IN,(CONVERT(D15_IN,CHAR)) AS D15_IN,(CONVERT(D16_IN,CHAR)) AS D16_IN,(CONVERT(D17_IN,CHAR)) AS D17_IN,(CONVERT(D18_IN,CHAR)) AS D18_IN,(CONVERT(D19_IN,CHAR)) AS D19_IN,(CONVERT(D20_IN,CHAR)) AS D20_IN,(CONVERT(D21_IN,CHAR)) AS D21_IN,(CONVERT(D22_IN,CHAR)) AS D22_IN,(CONVERT(D23_IN,CHAR)) AS D23_IN,(CONVERT(D24_IN,CHAR)) AS D24_IN,(CONVERT(D25_IN,CHAR)) AS D25_IN,(CONVERT(D26_IN,CHAR)) AS D26_IN,(CONVERT(D27_IN,CHAR)) AS D27_IN,(CONVERT(D28_IN,CHAR)) AS D28_IN,(CONVERT(D29_IN,CHAR)) AS D29_IN,(CONVERT(D30_IN,CHAR)) AS D30_IN,(CONVERT(D31_IN,CHAR)) AS D31_IN from MonthlyActivity where AttendanceMonth = '" + AttendanceMonth + "' and  AttendanceYear='" + AttendanceYear + "' and EmpId='" + \
                              empKey[
                                  'EmpId'] + "' AND LicKey = '" + LicKey + "' ORDER BY AttendanceMonth,MonthlyActivityId ASC"
                    rsMonth = DB.selectAllData(qsMonth)
                    singleMonthEmployeeData = []
                    noOfPresent = 0
                    if rsMonth:
                        for Dayno in range(1, 32):
                            variable = 'D' + str(Dayno) + '_IN'
                            colValue = rsMonth[0][variable]
                            IsWeekend = IsLeave = IsCompOff = IsHoliday = IsPresent = "0"
                            AttendanceDate_str = str(Dayno)
                            AttendanceMonth_str = str(AttendanceMonth)
                            AttendanceDate_str = AttendanceDate_str.zfill(2)
                            AttendanceMonth_str = AttendanceMonth_str.zfill(2)
                            assigndate = str(AttendanceYear) + "-" + str(AttendanceMonth_str) + "-" + str(
                                AttendanceDate_str)
                            if assigndate in WeekendDates:
                                IsWeekend = "1"
                            if assigndate in LeaveDates:
                                IsLeave = "1"
                            if assigndate in CompOffDates:
                                IsCompOff = "1"
                            if assigndate in HolidaysDates:
                                IsHoliday = "1"
                            if colValue != '00:00:00':
                                IsPresent = "1"
                                noOfPresent += 1
                            singleMonthdata = {'IsHoliday': IsHoliday, 'IsWeekend': IsWeekend, 'IsCompOff': IsCompOff,
                                               'IsLeave': IsLeave, 'IsPresent': IsPresent,
                                               'DayNo': str(AttendanceDate_str), variable: str(colValue)}
                            singleMonthEmployeeData.append(singleMonthdata)
                    else:
                        for Dayno in range(1, 32):
                            variable = 'D' + str(Dayno) + '_IN'
                            colValue = '00:00:00'
                            IsWeekend = IsLeave = IsCompOff = IsHoliday = IsPresent = "0"
                            AttendanceDate_str = str(Dayno)
                            AttendanceMonth_str = str(AttendanceMonth)
                            AttendanceDate_str = AttendanceDate_str.zfill(2)
                            AttendanceMonth_str = AttendanceMonth_str.zfill(2)
                            assigndate = str(AttendanceYear) + "-" + str(AttendanceMonth_str) + "-" + str(
                                AttendanceDate_str)
                            if assigndate in WeekendDates:
                                IsWeekend = "1"
                            if assigndate in LeaveDates:
                                IsLeave = "1"
                            if assigndate in CompOffDates:
                                IsCompOff = "1"
                            if assigndate in HolidaysDates:
                                IsHoliday = "1"
                            if colValue != '00:00:00':
                                IsPresent = "1"
                            singleMonthdata = {'IsHoliday': IsHoliday, 'IsWeekend': IsWeekend, 'IsCompOff': IsCompOff,
                                               'IsLeave': IsLeave, 'IsPresent': IsPresent,
                                               'DayNo': str(AttendanceDate_str), variable: str(colValue)}
                            singleMonthEmployeeData.append(singleMonthdata)
                    singleEmployeeDataList = {'EmpName': empKey['EmpName'], 'EmpId': empKey['EmpId'],
                                              'AttendanceMonth': AttendanceMonth, 'AttendanceYear': AttendanceYear,
                                              'allDaysList': singleMonthEmployeeData, 'NoOfPresents': noOfPresent}
                    employeeListData.append(singleEmployeeDataList)
                response = {'category': "1", 'message': "success", 'ResponseData': employeeListData}
            response = make_response(jsonify(response))
            return response


# API FOR MULTIPLE LOCATION PDF for mobile team BY IN/ODI01/052
class RcAPILocationPdf(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                QsLocationList = "SELECT A.BaseLocationId,A.IsActive,A.LocationName,A.LicKey,A.SystemInfo ,CASE WHEN A.IsActive = 1 THEN 'Active' ELSE 'Inactive' END AS Status,CONVERT(A.CreatedDate,CHAR) As CreatedDate,count(B.EmpId) AS NO_OF_EMPLOYEES from BaseLocation AS A left join EmployeeRegistration AS B on (A.BaseLocationId=B.BaseLocationId and A.LicKey='" + LicKey + "' and B.IsActive=1 and B.IsDelete=0) GROUP BY A.BaseLocationId Having A.LicKey='" + LicKey + "'"
                RsLocationList = DB.selectAllData(QsLocationList)
                lenOfRsLocationList = len(RsLocationList)
                pdflink = ''
                if lenOfRsLocationList > 0:
                    RsOfPDF = CREATEPDF.locationList(RsLocationList)
                response = {'category': "1", 'message': "List of all location", 'pdflink': RsOfPDF}
            response = make_response(jsonify(response))
            return response


# API FOR MULTIPLE LOCATION Excel for mobile team BY IN/ODI01/052
class RcAPILocationExcel(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                excellink = ''
                QsLocationList = "SELECT A.BaseLocationId,A.LocationName,A.LicKey,A.SystemInfo ,CASE WHEN A.IsActive = 1 THEN 'Active' ELSE 'Inactive' END AS Status,  CONVERT(A.CreatedDate,CHAR) As CreatedDate,count(B.EmpId) AS NO_OF_EMPLOYEES from BaseLocation AS A left join EmployeeRegistration AS B on (A.BaseLocationId=B.BaseLocationId and A.LicKey='" + LicKey + "' and B.IsActive=1 and B.IsDelete=0) GROUP BY A.BaseLocationId Having A.LicKey='" + LicKey + "' "
                RsLocationList = DB.selectAllData(QsLocationList)
                lenOfRsLocationList = len(RsLocationList)
                if lenOfRsLocationList > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'Location_Details_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("Location Details")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:F1', 'Location Details', bold)
                    worksheet.write('A2', 'Sl No.', bold)
                    worksheet.write('B2', 'Location Name', bold)
                    worksheet.write('C2', 'System Info', bold)
                    worksheet.write('D2', 'No Of Employees', bold)
                    worksheet.write('E2', 'Created Date', bold)
                    worksheet.write('F2', 'Status', bold)
                    row = 2
                    col = 0
                    for j in range(len(RsLocationList)):
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, RsLocationList[j]['LocationName'])
                        worksheet.write(row, col + 2, RsLocationList[j]['SystemInfo'])
                        worksheet.write(row, col + 3, RsLocationList[j]['NO_OF_EMPLOYEES'])
                        worksheet.write(row, col + 4, RsLocationList[j]['CreatedDate'])
                        worksheet.write(row, col + 5, RsLocationList[j]['Status'])
                        worksheet.write(row, col, str(j + 1))
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "List of all location", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response


# API FOR Compoff PDF for mobile team BY IN/ODI01/052
class RcAPICompoffPdf(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                QsCompoffList = "select A.LicKey,A.EmpId,CONVERT(A.OffDate,CHAR) As OffDate, CASE WHEN A.Status = 1 THEN 'Taken' WHEN A.Status = 2 THEN 'Cancelled' ELSE 'Pending' END AS Status,B.EmpName,C.LocationName From CompOff AS A,EmployeeRegistration AS B,BaseLocation AS C where A.LicKey='" + LicKey + "' and A.LicKey=B.LicKey and A.EmpId=B.EmpID and A.BaseLocationId=C.BaseLocationId ORDER BY OffDate ASC  "
                RsCompoffList = DB.selectAllData(QsCompoffList)
                lenOfRsCompoffList = len(RsCompoffList)
                pdflink = ''
                if lenOfRsCompoffList > 0:
                    RsOfPDF = CREATEPDF.compoffList(RsCompoffList)
                response = {'category': "1", 'message': "List of Compoff Leave", 'pdflink': RsOfPDF}
            response = make_response(jsonify(response))
            return response


# API FOR Compoff Excel for mobile team BY IN/ODI01/052
class RcAPICompoffExcel(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                excellink = ''
                QsCompoffList = "select A.LicKey,A.EmpId,CONVERT(A.OffDate,CHAR) As OffDate,CASE WHEN A.Status = 1 THEN 'Taken' WHEN A.Status = 2 THEN 'Cancelled' ELSE 'Pending' END AS Status,B.EmpName,C.LocationName From CompOff AS A,EmployeeRegistration AS B,BaseLocation AS C where A.LicKey='" + LicKey + "' and A.LicKey=B.LicKey and A.EmpId=B.EmpID and A.BaseLocationId=C.BaseLocationId ORDER BY OffDate ASC "
                RsCompoffList = DB.selectAllData(QsCompoffList)
                lenOfRsCompoffList = len(RsCompoffList)
                if lenOfRsCompoffList > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'Off_Management_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("Off Management")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:F1', 'Off Management', bold)
                    worksheet.write('A2', 'Sl No.', bold)
                    worksheet.write('B2', 'Employee ID', bold)
                    worksheet.write('C2', 'Employee Name', bold)
                    worksheet.write('D2', 'Location', bold)
                    worksheet.write('E2', 'OffDate', bold)
                    worksheet.write('F2', 'Status', bold)
                    row = 2
                    col = 0
                    for j in range(len(RsCompoffList)):
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, RsCompoffList[j]['EmpId'])
                        worksheet.write(row, col + 2, RsCompoffList[j]['EmpName'])
                        worksheet.write(row, col + 3, RsCompoffList[j]['LocationName'])
                        worksheet.write(row, col + 4, RsCompoffList[j]['OffDate'])
                        worksheet.write(row, col + 5, RsCompoffList[j]['Status'])
                        worksheet.write(row, col, str(j + 1))
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "List of Compoff Leave", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response


# API FOR Leave PDF for mobile team BY IN/ODI01/052
class RcAPILeavePdf(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                QsLeaveList = "select A.EmployeeLeaveHistoryId ,A.BaseLocationId ,A.EmpID,A.LicKey,CONVERT(A.LeaveDate,CHAR) As LeaveDate,A.LeaveType,A.LeavePurpose,CASE WHEN A.Status = 1 THEN 'Taken' WHEN A.Status = 2 THEN 'Cancelled' ELSE 'Pending' END AS Status,B.LocationName,C.EmpName From EmployeeLeaveHistory AS A,BaseLocation AS B,EmployeeRegistration AS C Where A.BaseLocationId=B.BaseLocationId and A.EmpID=C.EmpID and A.Lickey='" + LicKey + "' and A.LicKey='" + LicKey + "' and B.LicKey='" + LicKey + "' "
                RsLeaveList = DB.selectAllData(QsLeaveList)
                lenOfRsLeaveList = len(RsLeaveList)
                pdflink = ''
                if lenOfRsLeaveList > 0:
                    RsOfPDF = CREATEPDF.leaveList(RsLeaveList)
                response = {'category': "1", 'message': "List of Leave", 'pdflink': RsOfPDF}
            response = make_response(jsonify(response))
            return response


# API FOR Leave Excel for mobile team BY IN/ODI01/052
class RcAPILeaveExcel(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                excellink = ''
                QsLeaveList = "select A.EmployeeLeaveHistoryId ,A.BaseLocationId ,A.EmpID,A.LicKey,CONVERT(A.LeaveDate,CHAR) As LeaveDate,A.LeaveType,A.LeavePurpose,CASE WHEN A.Status = 1 THEN 'Taken' WHEN A.Status = 2 THEN 'Cancelled' ELSE 'Pending' END AS Status,B.LocationName,C.EmpName From EmployeeLeaveHistory AS A,BaseLocation AS B,EmployeeRegistration AS C Where A.BaseLocationId=B.BaseLocationId and A.EmpID=C.EmpID and A.Lickey='" + LicKey + "' and A.LicKey='" + LicKey + "' and B.LicKey='" + LicKey + "' "
                RsLeaveList = DB.selectAllData(QsLeaveList)
                lenOfRsLeaveList = len(RsLeaveList)
                if lenOfRsLeaveList > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'Leave_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("Leave Management")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:G1', 'Leave Management', bold)
                    worksheet.write('A2', '#', bold)
                    worksheet.write('B2', 'Employee Name', bold)
                    worksheet.write('C2', 'Location', bold)
                    worksheet.write('D2', 'Leave Date', bold)
                    worksheet.write('E2', 'Leave Type', bold)
                    worksheet.write('F2', 'Leave Purpose ', bold)
                    worksheet.write('G2', 'Status', bold)
                    row = 2
                    col = 0
                    for j in range(len(RsLeaveList)):
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, RsLeaveList[j]['EmpName'])
                        worksheet.write(row, col + 2, RsLeaveList[j]['LocationName'])
                        worksheet.write(row, col + 3, RsLeaveList[j]['LeaveDate'])
                        worksheet.write(row, col + 4, RsLeaveList[j]['LeaveType'])
                        worksheet.write(row, col + 5, RsLeaveList[j]['LeavePurpose'])
                        worksheet.write(row, col + 6, RsLeaveList[j]['Status'])
                        worksheet.write(row, col, str(j + 1))
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "List of Leave", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response


# PDF generation of  User List for mobile team BY IN/ODI01/053
class RcAPIMobileRecentReportPdf(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                now = datetime.now()
                Today = now.strftime('%Y-%m-%d')
                # Today='2020-11-11'
                recentQuerry = "Select A.LicKey,A.EmpId,B.EmpName,convert(A.ADTime,char) AS ADTime,A.Source,A.EmpImage,convert(A.ADDate,char) AS ADDate from ActivityDetails as A,EmployeeRegistration as B where A.EmpId=B.EmpId and A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + Today + "' and E.LicKey='" + LicKey + "') and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId order by A.ADDate DESC"
                recentActivityData = DB.selectAllData(recentQuerry)
                pdflink = ''
                if len(recentActivityData) > 0:
                    LicKey = recentActivityData[0]['LicKey']
                    RsOfPDF = CREATEPDF.recentReport(recentActivityData)
                    response = {'category': "1", 'message': "Recent report details.", 'pdflink': RsOfPDF}
                else:
                    response = {'category': "0", 'message': "No data found"}
            response = make_response(jsonify(response))
            return response


# EXCEL generation of user list for mobile team BY IN/ODI01/053
class RcAPIMobileRecentReportExcel(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                excellink = ''
                now = datetime.now()
                Today = now.strftime('%Y-%m-%d')
                # Today='2020-11-11'
                recentQuerry = "Select A.LicKey,A.EmpId,B.EmpName,convert(A.ADTime,char) AS ADTime,A.Source,A.EmpImage,convert(A.ADDate,char) AS ADDate from ActivityDetails as A,EmployeeRegistration as B where A.EmpId=B.EmpId and A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + Today + "' and E.LicKey='" + LicKey + "') and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId order by A.ADDate DESC"
                recentActivityData = DB.selectAllData(recentQuerry)
                if len(recentActivityData) > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'All_Activity_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("All Activity")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:G1', 'All Activity', bold)
                    worksheet.write('A2', 'Sl. No', bold)
                    worksheet.write('B2', 'Employee Id', bold)
                    worksheet.write('C2', 'Name', bold)
                    worksheet.write('D2', 'Seen Date', bold)
                    worksheet.write('E2', 'Camera Seen', bold)
                    row = 2
                    col = 0
                    for j in range(len(recentActivityData)):
                        EmpId = recentActivityData[j]['EmpId']
                        EmpName = recentActivityData[j]['EmpName']
                        ADTime = recentActivityData[j]['ADTime']
                        Source = recentActivityData[j]['Source']
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, EmpId)
                        worksheet.write(row, col + 2, EmpName)
                        worksheet.write(row, col + 3, ADTime)
                        worksheet.write(row, col + 4, Source)
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "Recent report details.", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response


# PDF generation of  Daily Report for mobile team BY IN/ODI01/053
class RcAPIMobileDailyReportPdf(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            StartDate = ''
            if 'StartDate' in RequestData:
                StartDate = RequestData['StartDate']
            if (LicKey.isspace() == True or LicKey == '') or (StartDate.isspace() == True or StartDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory.", 'RequestData': RequestData}
            else:
                StartDate = StartDate.strip()
                QSDailyActivity = "select 'Present' as Status,A.LicKey,A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + StartDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId"
                DailyActivityData = DB.selectAllData(QSDailyActivity)
                pdflink = ''
                if len(DailyActivityData) > 0:
                    # LicKey = DailyActivityData[0]['LicKey']
                    RsOfPDF = CREATEPDF.dailyReport(DailyActivityData)
                    response = {'category': "1", 'message': "Daily report details.", 'pdflink': RsOfPDF}
                else:
                    response = {'category': "0", 'message': "No data found"}
            response = make_response(jsonify(response))
            return response


# EXCEL generation of Daily Report for mobile team BY IN/ODI01/053
class RcAPIMobileDailyReportExcel(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            StartDate = ''
            if 'StartDate' in RequestData:
                StartDate = RequestData['StartDate']
            if (LicKey.isspace() == True or LicKey == '') or (StartDate.isspace() == True or StartDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                excellink = ''
                StartDate = StartDate.strip()
                QSDailyActivity = "select 'Present' as Status,A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + StartDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId"
                DailyActivityData = DB.selectAllData(QSDailyActivity)
                if len(DailyActivityData) > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'Daily_Activity_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("Daily Activity")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:G1', 'Daily Activity', bold)
                    worksheet.write('A2', 'Sl. No', bold)
                    worksheet.write('B2', 'Employee Id', bold)
                    worksheet.write('C2', 'Name', bold)
                    worksheet.write('D2', 'Location', bold)
                    worksheet.write('E2', 'First Seen', bold)
                    worksheet.write('F2', 'Last Seen ', bold)
                    worksheet.write('G2', 'Shift ', bold)
                    worksheet.write('H2', 'Status ', bold)
                    row = 2
                    col = 0
                    for j in range(len(DailyActivityData)):
                        EmpId = DailyActivityData[j]['EmpId']
                        EmpName = DailyActivityData[j]['EmpName']
                        LocationName = DailyActivityData[j]['LocationName']
                        FirstSeen = DailyActivityData[j]['FirstSeen']
                        LastSeen = DailyActivityData[j]['LastSeen']
                        ShiftName = DailyActivityData[j]['ShiftName']
                        Status = DailyActivityData[j]['Status']
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, EmpId)
                        worksheet.write(row, col + 2, EmpName)
                        worksheet.write(row, col + 3, LocationName)
                        worksheet.write(row, col + 4, FirstSeen)
                        worksheet.write(row, col + 5, LastSeen)
                        worksheet.write(row, col + 6, ShiftName)
                        worksheet.write(row, col + 7, Status)
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "Daily report details.", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response


# API FOR Holiday PDF  for mobile team BY IN/ODI01/052
class RcAPIHolidayPdf(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                QsHolidayList = "select A.LicKey,CONVERT(A.SetDate,CHAR) As SetDate,A.Holiday,CASE WHEN A.IsActive = 1 THEN 'Active' ELSE 'InActive' END AS Status,B.LocationName From HolidayList AS A ,BaseLocation AS B where A.Lickey='" + LicKey + "' and A.BaseLocationID=B.BaseLocationID ORDER BY SetDate ASC"
                RsHolidayList = DB.selectAllData(QsHolidayList)
                lenOfRsHolidayList = len(RsHolidayList)
                pdflink = ''
                if lenOfRsHolidayList > 0:
                    RsOfPDF = CREATEPDF.holidayList(RsHolidayList)
                response = {'category': "1", 'message': "List of Holiday", 'pdflink': RsOfPDF}
            response = make_response(jsonify(response))
            return response


# API FOR Holiday Excel  for mobile team BY IN/ODI01/052
class RcAPIHolidayExcel(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                excellink = ''
                QsHolidayList = "select A.LicKey,CONVERT(A.SetDate,CHAR) As SetDate,A.Holiday,CASE WHEN A.IsActive = 1 THEN 'Active' ELSE 'Inactive' END AS Status,B.LocationName From HolidayList AS A ,BaseLocation AS B where A.Lickey='" + LicKey + "' and A.BaseLocationID=B.BaseLocationID ORDER BY SetDate ASC"
                RsHolidayList = DB.selectAllData(QsHolidayList)
                lenOfRsHolidayList = len(RsHolidayList)
                if lenOfRsHolidayList > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'Holiday_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("Holiday Setting")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:E1', 'Holiday Setting', bold)
                    worksheet.write('A2', 'Sl No.', bold)
                    worksheet.write('B2', 'Location', bold)
                    worksheet.write('C2', 'Date', bold)
                    worksheet.write('D2', 'Holiday', bold)
                    worksheet.write('E2', 'Status', bold)
                    row = 2
                    col = 0
                    for j in range(len(RsHolidayList)):
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, RsHolidayList[j]['LocationName'])
                        worksheet.write(row, col + 2, RsHolidayList[j]['SetDate'])
                        worksheet.write(row, col + 3, RsHolidayList[j]['Holiday'])
                        worksheet.write(row, col + 4, RsHolidayList[j]['Status'])
                        worksheet.write(row, col, str(j + 1))
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "List of Holiday ", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response


# API FOR MULTIPLE GEOFENCE AREA Excel for mobile team BY IN/ODI01/052
class RcAPIGeofenceAreaExcel(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                excellink = ''
                QsGeofenceList = "select A.LicKey,A.AreaName,A.Latlang,count(B.UserLoginId) AS NoOfUsers ,CONVERT(A.CreatedDate,CHAR) As CreatedDate from GeofenceArea AS A Left Join UserLogin AS B on (A.GeofenceAreaId=B.GeofenceAreaId and A.LicKey='" + LicKey + "' and A.LicKey=B.LicKey) GROUP BY A.GeofenceAreaId"
                RsGeofenceList = DB.selectAllData(QsGeofenceList)
                lenOfRsLocationList = len(RsGeofenceList)
                if lenOfRsLocationList > 0:
                    today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y%m%d%H%M%S')
                    fileFolderPath = "static/report-file/" + str(LicKey) + "/" + str(today) + "/Excel"
                    if not os.path.exists(fileFolderPath):
                        os.makedirs(fileFolderPath)
                    uniqueid = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
                    fileName = 'Geofence_' + tdayTimeStamp + '_' + uniqueid + '.xlsx'
                    fullFileDirName = fileFolderPath + '/' + fileName
                    workbook = xlsxwriter.Workbook(fullFileDirName)
                    worksheet = workbook.add_worksheet("Airface | Geofence")
                    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    # Write some data headers.
                    worksheet.merge_range('A1:E1', 'Airface | Geofence', bold)
                    worksheet.write('A2', 'Sl No.', bold)
                    worksheet.write('B2', 'Area Name', bold)
                    worksheet.write('C2', 'Latitude & Longitude', bold)
                    worksheet.write('D2', 'No Of Users', bold)
                    worksheet.write('E2', 'Created Date', bold)
                    row = 2
                    col = 0
                    for j in range(len(RsGeofenceList)):
                        worksheet.write(row, col, str(j + 1))
                        worksheet.write(row, col + 1, RsGeofenceList[j]['AreaName'])
                        worksheet.write(row, col + 2, RsGeofenceList[j]['Latlang'])
                        worksheet.write(row, col + 3, RsGeofenceList[j]['NoOfUsers'])
                        worksheet.write(row, col + 4, RsGeofenceList[j]['CreatedDate'])
                        row += 1
                    workbook.close()
                    excellink = fullFileDirName
                response = {'category': "1", 'message': "List of Geofence Area", 'excellink': excellink}
            response = make_response(jsonify(response))
            return response


# API FOR Geofence Area PDF for mobile team BY IN/ODI01/052
class RcAPIGeofencePdf(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                QsGeofenceList = "select A.LicKey,A.AreaName,A.Shape,A.Latlang,count(B.UserLoginId) AS NoOfUsers ,CONVERT(A.CreatedDate,CHAR) As CreatedDate from GeofenceArea AS A Left Join UserLogin AS B on (A.GeofenceAreaId=B.GeofenceAreaId and A.LicKey='" + LicKey + "' and A.LicKey=B.LicKey) GROUP BY A.GeofenceAreaId"
                RsGeofenceList = DB.selectAllData(QsGeofenceList)
                lenOfRsGeofenceList = len(RsGeofenceList)
                pdflink = ''
                if lenOfRsGeofenceList > 0:
                    RsOfPDF = CREATEPDF.geofenceList(RsGeofenceList)
                response = {'category': "1", 'message': "List of Geofence Area", 'pdflink': RsOfPDF}
            response = make_response(jsonify(response))
            return response


# API FOR LISTING OF DELETED EMPLOYEES for mobile team BY IN/ODI01/052
class RcAPIDeletedEmployeeList(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                querry = "select A.*,B.ImagePath,C.LocationName,CONVERT(A.CreatedDate,CHAR) AS CreatedDate from BaseLocation as C,EmployeeRegistration AS A left join DatasetEncodings AS B ON (A.EmpId=B.EmpId and A.LicKey='" + LicKey + "' and  B.LicKey='" + LicKey + "') where A.LicKey='" + LicKey + "' and A.IsDelete=1 and (A.IsActive=1 OR A.IsActive=0) and C.BaseLocationId=A.BaseLocationId GROUP BY A.EmpId ORDER BY A.UpdatedDate DESC"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "List of  deleted employees", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# API FOR Employee Enrollment for MobileTeam BY IN/ODI01/053
class RcAPIMobileEnroll(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # master id as a employee id
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'DatasetEncodings'
                wherecondition = "`LicKey`= '" + LicKey + "' and `EmpId`= '" + MasterId + "'"
                order = ""
                fields = "DatasetEncodingsId,ImagePath,EmpId,EmpName"
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                response = {'category': "1", 'message': "Success", 'ResponseData': ResponseData}
            response = make_response(jsonify(response))
            return response

    # DELETE EMPLOYEE ENROLLMENT
    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # masterid as a TABLE UNIQUE ID
            if MasterId == '':
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                tablename = 'DatasetEncodings'
                wherecondition = "`LicKey`= '" + LicKey + "' AND `DatasetEncodingsId`= '" + MasterId + "'"
                Querry = "select * from DatasetEncodings where LicKey= '" + LicKey + "' AND `DatasetEncodingsId`= '" + MasterId + "'"
                CountEncodings = DB.selectAllData(Querry)
                if len(CountEncodings) > 0:
                    imagePath = CountEncodings[0]['ImagePath']
                    if os.path.exists(imagePath):
                        os.remove(imagePath)
                        delete1 = DB.deleteSingleRow(tablename, wherecondition)
                        response = {'category': "1", 'message': "Deletion of Enrolled Employee successfull."}
                    else:
                        response = {'category': "0", 'message': "File does not exists!"}
                else:
                    response = {'category': "0", 'message': "Error!The Enrollment Id Doesn't Exist."}
            response = make_response(jsonify(response))
            return response

    # EMPLOYEE ENROLLMENT
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID AS a Employee Id
            # File image as base64 encoded
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            EmpName = ''
            EmpId = ''
            BaseLocationId = ''
            ImagePath = ''
            if 'EmpName' in RequestData and 'EmpId' in RequestData and 'BaseLocationId' in RequestData and 'ImagePath' in RequestData:
                EmpName = RequestData['EmpName']
                EmpId = RequestData['EmpId']
                BaseLocationId = RequestData['BaseLocationId']
                ImagePath = RequestData['ImagePath']
            now = datetime.now()
            createdDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (EmpName.isspace() == True or EmpName == '') or (
                    EmpId.isspace() == True or EmpId == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == '') or (
                    ImagePath == [] or ImagePath == [''] or ImagePath == [' ']):
                response = {'category': "0", 'message': "All fields are mandatory.",
                            'ImagePath': ""}  # ,'RequestData': RequestData
            else:
                EmpName = EmpName.strip()
                EmpId = EmpId.strip()
                BaseLocationId = BaseLocationId.strip()
                len(ImagePath)
                tablename = "EmployeeRegistration"
                order = ""
                fields = ""
                wherecondition = "`LicKey`='" + LicKey + "' AND `EmpId`='" + EmpId + "' AND `IsActive` = '1'"
                ResponseData = DB.retrieveAllData(tablename, fields, wherecondition, order)
                if len(ResponseData) > 0:
                    photo = ''
                    prefixDir = 'static/'
                    directory = 'public/face-video/'
                    slass = str('/')
                    licDirectory = str(directory + LicKey)
                    licEmployeeDirectory = str(licDirectory + slass + EmpId)

                    if not os.path.exists(prefixDir + directory):
                        os.makedirs(prefixDir + directory)

                    if not os.path.exists(prefixDir + licDirectory):
                        os.makedirs(prefixDir + licDirectory)

                    if not os.path.exists(prefixDir + licEmployeeDirectory):
                        os.makedirs(prefixDir + licEmployeeDirectory)
                    for i in range(len(ImagePath)):
                        singleImageData = ImagePath[i]
                        imageBlobStr = singleImageData.replace("data:image/png;base64,", '')
                        imageBlobStr = bytes(imageBlobStr, 'ascii')
                        no = str(i)
                        fileNameAsTime = datetime.now().strftime("%Y%m%d%H%M%S")
                        digits = "0123456789"
                        autoGenNo = ""
                        for i in range(4): autoGenNo += digits[math.floor(random.random() * 10)]
                        picName = autoGenNo + '_' + fileNameAsTime
                        imageName = str(picName + no + '.png')
                        shortImagePath = str(licEmployeeDirectory + slass + imageName)
                        image_path = str(prefixDir + licEmployeeDirectory + slass + imageName)
                        with open(image_path, "wb") as fh:
                            fh.write(base64.decodebytes(imageBlobStr))
                        knownFaceEncodings = []
                        knownFaceNames = []
                        name1 = EmpId + "_" + EmpName
                        emp_id_split = name1.split('_', 3)
                        c1 = name1 + "_image"
                        c2 = name1 + "_face_encoding"
                        c1 = face_recognition.load_image_file(image_path)
                        c2 = face_recognition.face_encodings(c1)
                        if len(c2) > 0:
                            c2 = c2[0]
                        knownFaceEncodings.append(c2)
                        knownFaceNames.append(name1)
                        IsActive = "1"
                        path = prefixDir + shortImagePath
                        strLoop = "NULL,'" + EmpId + "','" + EmpName + "'" + ",'" + IsActive + "','" + LicKey + "','" + path + "',"
                        n = len(c2)
                        j = 0
                        for j in range(len(c2)):
                            if j < 127:
                                strLoop += (str(c2[j])) + ","
                            else:
                                strLoop += str(c2[j])
                        if (n > 0):
                            tablename = "DatasetEncodings"
                            wherecondition = "`EmpId` = '" + EmpId + "' AND `LicKey` = '" + LicKey + "'"
                            order = ''
                            fields = ""
                            ResponseData1 = DB.retrieveAllData(tablename, fields, wherecondition, order)
                            countlen = len(ResponseData1)
                            countlen = int(countlen)
                            if countlen < 12:
                                # print(str(countlen) + "12 if")
                                sql_encoding = "INSERT INTO `DatasetEncodings`  VALUES (" + strLoop + "," + BaseLocationId + ")"
                                showmessage = DB.directinsertData(sql_encoding)
                                tablename = "EmployeeRegistration"
                                values = {'IsEnrolled': str(1)}
                                wherecondition = "EmpId='" + EmpId + "' and LicKey='" + LicKey + "'"
                                DB.updateData(tablename, values, wherecondition)
                                response = {'category': '1',
                                            'message': "Congratulation! your employee enroll successfully.",
                                            'ImagePath': str(path)}
                                ResponseData = make_response(jsonify(response))
                            elif countlen == 12:
                                # print(str(countlen) + "12 else")
                                response = {'category': '0',
                                            'message': "Sorry! already you added maximum no of image for profile.",
                                            'ImagePath': ""}
                                ResponseData = make_response(jsonify(response))
                            else:
                                # print(str(countlen) + "12 else")
                                response = {'category': '0',
                                            'message': "Sorry! already you added maximum no of image for profile.",
                                            'ImagePath': ""}
                                ResponseData = make_response(jsonify(response))
                        else:
                            response = {'category': "0",
                                        'message': "Enrollment of this employee not gone well! Please enroll again.",
                                        'ImagePath': ""}
                            ResponseData = make_response(jsonify(response))
                else:
                    response = {'category': "0", 'message': "Sorry! this account is invalid or inactive.",
                                'ImagePath': ""}
            response = make_response(jsonify(response))
            return response


# By IN_OI01_027
# API Monthly Report Hour Wise
class RcAPIMobileMonthlyReportHourWise(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AttendanceMonth = ''
            AttendanceYear = ''
            BaseLocationId = ''
            EmpId = ''
            if 'AttendanceYear' in RequestData and 'AttendanceMonth' in RequestData and 'EmpId' in RequestData or 'BaseLocationId' in RequestData:
                AttendanceYear = RequestData['AttendanceYear']
                AttendanceMonth = RequestData['AttendanceMonth']
                EmpId = RequestData['EmpId']
                BaseLocationId = RequestData['BaseLocationId']
            if (LicKey.isspace() == True or LicKey == '') or (
                    AttendanceMonth.isspace() == True or AttendanceMonth == '') or (
                    EmpId.isspace() == True or EmpId == '') or (
                    AttendanceYear.isspace() == True or AttendanceYear == '') or (
                    BaseLocationId.isspace() == True or BaseLocationId == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                AttendanceMonth = AttendanceMonth.strip()
                EmpId = EmpId.strip()
                AttendanceYear = AttendanceYear.strip()
                BaseLocationId = BaseLocationId.strip()
                # QsForActivityDetails = "SELECT  A.MonthlyActivityId,A.AttendanceMonth,A.AttendanceYear,B.EmpId,B.EmpName,(CONVERT(A.D1_IN,CHAR)) AS D1_IN,(CONVERT(A.D1_OUT,CHAR)) AS D1_OUT, (CONVERT(A.D2_IN,CHAR)) AS D2_IN,(CONVERT(A.D2_OUT,CHAR)) AS D2_OUT, (CONVERT(A.D3_IN,CHAR)) AS D3_IN,(CONVERT(A.D3_OUT,CHAR)) AS D3_OUT, (CONVERT(A.D4_IN,CHAR)) AS D4_IN,(CONVERT(A.D4_OUT,CHAR)) AS D4_OUT, (CONVERT(A.D5_IN,CHAR)) AS D5_IN,(CONVERT(A.D5_OUT,CHAR)) AS D5_OUT, (CONVERT(A.D6_IN,CHAR)) AS D6_IN,(CONVERT(A.D6_OUT,CHAR)) AS D6_OUT, (CONVERT(A.D7_IN,CHAR)) AS D7_IN,(CONVERT(A.D7_OUT,CHAR)) AS D7_OUT, (CONVERT(A.D8_IN,CHAR)) AS D8_IN,(CONVERT(A.D8_OUT,CHAR)) AS D8_OUT, (CONVERT(A.D9_IN,CHAR)) AS D9_IN,(CONVERT(A.D9_OUT,CHAR)) AS D9_OUT, (CONVERT(A.D10_IN,CHAR)) AS D10_IN,(CONVERT(A.D10_OUT,CHAR)) AS D10_OUT, (CONVERT(A.D11_IN,CHAR)) AS D11_IN,(CONVERT(A.D11_OUT,CHAR)) AS D11_OUT, (CONVERT(A.D12_IN,CHAR)) AS D12_IN,(CONVERT(A.D12_OUT,CHAR)) AS D12_OUT, (CONVERT(A.D13_IN,CHAR)) AS D13_IN,(CONVERT(A.D13_OUT,CHAR)) AS D13_OUT, (CONVERT(A.D14_IN,CHAR)) AS D14_IN,(CONVERT(A.D14_OUT,CHAR)) AS D14_OUT, (CONVERT(A.D15_IN,CHAR)) AS D15_IN,(CONVERT(A.D15_OUT,CHAR)) AS D15_OUT, (CONVERT(A.D16_IN,CHAR)) AS D16_IN,(CONVERT(A.D16_OUT,CHAR)) AS D16_OUT, (CONVERT(A.D17_IN,CHAR)) AS D17_IN,(CONVERT(A.D17_OUT,CHAR)) AS D17_OUT, (CONVERT(A.D18_IN,CHAR)) AS D18_IN,(CONVERT(A.D18_OUT,CHAR)) AS D18_OUT, (CONVERT(A.D19_IN,CHAR)) AS D19_IN,(CONVERT(A.D19_OUT,CHAR)) AS D19_OUT, (CONVERT(A.D20_IN,CHAR)) AS D20_IN,(CONVERT(A.D20_OUT,CHAR)) AS D20_OUT, (CONVERT(A.D21_IN,CHAR)) AS D21_IN,(CONVERT(A.D21_OUT,CHAR)) AS D21_OUT, (CONVERT(A.D22_IN,CHAR)) AS D22_IN,(CONVERT(A.D22_OUT,CHAR)) AS D22_OUT, (CONVERT(A.D23_IN,CHAR)) AS D23_IN,(CONVERT(A.D23_OUT,CHAR)) AS D23_OUT, (CONVERT(A.D24_IN,CHAR)) AS D24_IN,(CONVERT(A.D24_OUT,CHAR)) AS D24_OUT, (CONVERT(A.D25_IN,CHAR)) AS D25_IN,(CONVERT(A.D25_OUT,CHAR)) AS D25_OUT, (CONVERT(A.D26_IN,CHAR)) AS D26_IN,(CONVERT(A.D26_OUT,CHAR)) AS D26_OUT, (CONVERT(A.D27_IN,CHAR)) AS D27_IN,(CONVERT(A.D27_OUT,CHAR)) AS D27_OUT, (CONVERT(A.D28_IN,CHAR)) AS D28_IN,(CONVERT(A.D28_OUT,CHAR)) AS D28_OUT, (CONVERT(A.D29_IN,CHAR)) AS D29_IN,(CONVERT(A.D29_OUT,CHAR)) AS D29_OUT, (CONVERT(A.D30_IN,CHAR)) AS D30_IN,(CONVERT(A.D30_OUT,CHAR)) AS D30_OUT, (CONVERT(A.D31_IN,CHAR)) AS D31_IN,(CONVERT(A.D31_OUT,CHAR)) AS D31_OUT from MonthlyActivity as A ,EmployeeRegistration as B where A.AttendanceMonth = '" + AttendanceMonth + "' and  A.AttendanceYear='" + AttendanceYear + "'  AND A.LicKey = B.LicKey AND A.EmpId ='"+EmpId+"'  ORDER BY A.AttendanceMonth,A.MonthlyActivityId ASC" #and  B.EmpId='"+EmpId+"'
                QsForActivityDetails = "SELECT  A.MonthlyActivityId,A.AttendanceMonth,A.AttendanceYear,A.EmpId,B.EmpName,(CONVERT(A.D1_IN,CHAR)) AS D1_IN,(CONVERT(A.D1_OUT,CHAR)) AS D1_OUT, (CONVERT(A.D2_IN,CHAR)) AS D2_IN,(CONVERT(A.D2_OUT,CHAR)) AS D2_OUT, (CONVERT(A.D3_IN,CHAR)) AS D3_IN,(CONVERT(A.D3_OUT,CHAR)) AS D3_OUT, (CONVERT(A.D4_IN,CHAR)) AS D4_IN,(CONVERT(A.D4_OUT,CHAR)) AS D4_OUT, (CONVERT(A.D5_IN,CHAR)) AS D5_IN,(CONVERT(A.D5_OUT,CHAR)) AS D5_OUT, (CONVERT(A.D6_IN,CHAR)) AS D6_IN,(CONVERT(A.D6_OUT,CHAR)) AS D6_OUT, (CONVERT(A.D7_IN,CHAR)) AS D7_IN,(CONVERT(A.D7_OUT,CHAR)) AS D7_OUT, (CONVERT(A.D8_IN,CHAR)) AS D8_IN,(CONVERT(A.D8_OUT,CHAR)) AS D8_OUT, (CONVERT(A.D9_IN,CHAR)) AS D9_IN,(CONVERT(A.D9_OUT,CHAR)) AS D9_OUT, (CONVERT(A.D10_IN,CHAR)) AS D10_IN,(CONVERT(A.D10_OUT,CHAR)) AS D10_OUT, (CONVERT(A.D11_IN,CHAR)) AS D11_IN,(CONVERT(A.D11_OUT,CHAR)) AS D11_OUT, (CONVERT(A.D12_IN,CHAR)) AS D12_IN,(CONVERT(A.D12_OUT,CHAR)) AS D12_OUT, (CONVERT(A.D13_IN,CHAR)) AS D13_IN,(CONVERT(A.D13_OUT,CHAR)) AS D13_OUT, (CONVERT(A.D14_IN,CHAR)) AS D14_IN,(CONVERT(A.D14_OUT,CHAR)) AS D14_OUT, (CONVERT(A.D15_IN,CHAR)) AS D15_IN,(CONVERT(A.D15_OUT,CHAR)) AS D15_OUT, (CONVERT(A.D16_IN,CHAR)) AS D16_IN,(CONVERT(A.D16_OUT,CHAR)) AS D16_OUT, (CONVERT(A.D17_IN,CHAR)) AS D17_IN,(CONVERT(A.D17_OUT,CHAR)) AS D17_OUT, (CONVERT(A.D18_IN,CHAR)) AS D18_IN,(CONVERT(A.D18_OUT,CHAR)) AS D18_OUT, (CONVERT(A.D19_IN,CHAR)) AS D19_IN,(CONVERT(A.D19_OUT,CHAR)) AS D19_OUT, (CONVERT(A.D20_IN,CHAR)) AS D20_IN,(CONVERT(A.D20_OUT,CHAR)) AS D20_OUT, (CONVERT(A.D21_IN,CHAR)) AS D21_IN,(CONVERT(A.D21_OUT,CHAR)) AS D21_OUT, (CONVERT(A.D22_IN,CHAR)) AS D22_IN,(CONVERT(A.D22_OUT,CHAR)) AS D22_OUT, (CONVERT(A.D23_IN,CHAR)) AS D23_IN,(CONVERT(A.D23_OUT,CHAR)) AS D23_OUT, (CONVERT(A.D24_IN,CHAR)) AS D24_IN,(CONVERT(A.D24_OUT,CHAR)) AS D24_OUT, (CONVERT(A.D25_IN,CHAR)) AS D25_IN,(CONVERT(A.D25_OUT,CHAR)) AS D25_OUT, (CONVERT(A.D26_IN,CHAR)) AS D26_IN,(CONVERT(A.D26_OUT,CHAR)) AS D26_OUT, (CONVERT(A.D27_IN,CHAR)) AS D27_IN,(CONVERT(A.D27_OUT,CHAR)) AS D27_OUT, (CONVERT(A.D28_IN,CHAR)) AS D28_IN,(CONVERT(A.D28_OUT,CHAR)) AS D28_OUT, (CONVERT(A.D29_IN,CHAR)) AS D29_IN,(CONVERT(A.D29_OUT,CHAR)) AS D29_OUT, (CONVERT(A.D30_IN,CHAR)) AS D30_IN,(CONVERT(A.D30_OUT,CHAR)) AS D30_OUT, (CONVERT(A.D31_IN,CHAR)) AS D31_IN,(CONVERT(A.D31_OUT,CHAR)) AS D31_OUT from MonthlyActivity as A ,EmployeeRegistration as B where A.AttendanceMonth = '" + AttendanceMonth + "' and  A.AttendanceYear='" + AttendanceYear + "'  AND A.LicKey = B.LicKey AND A.EmpId ='" + EmpId + "' and  B.EmpId='" + EmpId + "' ORDER BY A.AttendanceMonth,A.MonthlyActivityId ASC"  # and  B.EmpId='"+EmpId+"'
                RsForActivityDetails = DB.selectAllData(QsForActivityDetails)
                if len(RsForActivityDetails) > 0:
                    response = {'category': "1", 'message': "List of monthly report",
                                'ResponseData': RsForActivityDetails}
                else:
                    response = {'category': "0", 'message': "Data not found"}
                return response


# By IN_OI01_027 Dt-19-01-21
# API FOR Documents
class RcAPICreateDocument(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Master id as a unquie id of the table
            # if MasterId == '':
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                MasterId = MasterId.strip()
                RsAPIDocument = DB.selectAllData(
                    "SELECT A.*,B.ProjectName,C.ModuleName FROM APIDocument as A ,Project as B , Module as C where A.ProjectId = B.ProjectId and A.ModuleId = C.ModuleId and A.APIDocumentId = '" + str(
                        MasterId) + "'")
                if len(RsAPIDocument) > 0:
                    response = {'category': "1", 'message': "List of single document.", 'ResponseData': RsAPIDocument}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response

    # Add CreateDocument
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            ProjectId = ModuleId = URL = Purpose = Title = Method = HeaderParameter = BodyParameter = SuccessResponse = FailureResponse = TablesUsed = Note = DocumentType = ''
            IsActive = '1'
            IsDelete = '0'
            if 'ProjectId' in RequestData and 'ModuleId' in RequestData and 'URL' in RequestData and 'Purpose' in RequestData and 'Title' in RequestData and 'Method' in RequestData and 'HeaderParameter' in RequestData and 'BodyParameter' in RequestData and 'SuccessResponse' in RequestData and 'FailureResponse' in RequestData and 'Note' in RequestData and 'DocumentType' in RequestData:
                ProjectId = RequestData['ProjectId']
                ModuleId = RequestData['ModuleId']
                URL = RequestData['URL']
                Purpose = RequestData['Purpose']
                Title = RequestData['Title']
                Method = RequestData['Method']
                HeaderParameter = RequestData['HeaderParameter']
                BodyParameter = RequestData['BodyParameter']
                SuccessResponse = RequestData['SuccessResponse']
                FailureResponse = RequestData['FailureResponse']
                TablesUsed = RequestData['TablesUsed']
                Note = RequestData['Note']
                DocumentType = RequestData['DocumentType']
            now = datetime.now()
            CreatedDate = now.strftime('%Y-%m-%d')
            if (ProjectId.isspace() == True or ProjectId == '') or (ModuleId.isspace() == True or ModuleId == '') or (
                    URL.isspace() == True or URL == '') or (Purpose.isspace() == True or Purpose == '') or (
                    Title.isspace() == True or Title == '') or (Method.isspace() == True or Method == '') or (
                    HeaderParameter.isspace() == True or HeaderParameter == '') or (
                    BodyParameter.isspace() == True or BodyParameter == '') or (
                    SuccessResponse.isspace() == True or SuccessResponse == '') or (
                    FailureResponse.isspace() == True or FailureResponse == '') or (
                    TablesUsed.isspace() == True or TablesUsed == '') or (Note.isspace() == True or Note == '') or (
                    DocumentType.isspace() == True or DocumentType == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                ProjectId = ProjectId.strip()
                ModuleId = ModuleId.strip()
                URL = URL.strip()
                Purpose = Purpose.strip()
                Title = Title.strip()
                Method = Method.strip()
                HeaderParameter = HeaderParameter.strip()
                BodyParameter = BodyParameter.strip()
                SuccessResponse = SuccessResponse.strip()
                FailureResponse = FailureResponse.strip()
                TablesUsed = TablesUsed.strip()
                DocumentType = DocumentType.strip()
                Note = Note.strip()
                values = {'ProjectId': ProjectId, 'ModuleId': ModuleId, 'URL': URL, 'Purpose': Purpose, 'Title': Title,
                          'Method': Method, 'HeaderParameter': HeaderParameter, 'BodyParameter': BodyParameter,
                          'SuccessResponse': SuccessResponse, 'FailureResponse': FailureResponse,
                          'TablesUsed': TablesUsed, 'Note': Note, 'IsActive': IsActive, 'IsDelete': IsDelete,
                          'CreatedDate': CreatedDate, 'UpdatedDate': CreatedDate, 'DocumentType': DocumentType}
                showmessage = DB.insertData("APIDocument", values)
                if showmessage['messageType'] == 'success':
                    response = {'category': "1", 'message': "Record added successfully."}
                else:
                    response = {'category': "0", 'message': "Sorry ! something Error in DB. try it again."}
            response = make_response(jsonify(response))
            return response

    # Update Document
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            ProjectId = ModuleId = URL = Purpose = Title = Method = HeaderParameter = BodyParameter = SuccessResponse = FailureResponse = TablesUsed = Note = DocumentType = ''
            if 'ProjectId' in RequestData and 'ModuleId' in RequestData and 'URL' in RequestData and 'Purpose' in RequestData and 'Title' in RequestData and 'Method' in RequestData and 'HeaderParameter' in RequestData and 'BodyParameter' in RequestData and 'SuccessResponse' in RequestData and 'FailureResponse' in RequestData and 'Note' in RequestData and 'DocumentType' in RequestData:
                ProjectId = RequestData['ProjectId']
                ModuleId = RequestData['ModuleId']
                URL = RequestData['URL']
                Purpose = RequestData['Purpose']
                Title = RequestData['Title']
                Method = RequestData['Method']
                HeaderParameter = RequestData['HeaderParameter']
                BodyParameter = RequestData['BodyParameter']
                SuccessResponse = RequestData['SuccessResponse']
                FailureResponse = RequestData['FailureResponse']
                TablesUsed = RequestData['TablesUsed']
                Note = RequestData['Note']
                DocumentType = RequestData['DocumentType']
            now = datetime.now()
            UpdatedDate = now.strftime('%Y-%m-%d')
            if (ProjectId.isspace() == True or ProjectId == '') or (ModuleId.isspace() == True or ModuleId == '') or (
                    URL.isspace() == True or URL == '') or (Purpose.isspace() == True or Purpose == '') or (
                    Title.isspace() == True or Title == '') or (Method.isspace() == True or Method == '') or (
                    HeaderParameter.isspace() == True or HeaderParameter == '') or (
                    BodyParameter.isspace() == True or BodyParameter == '') or (
                    SuccessResponse.isspace() == True or SuccessResponse == '') or (
                    FailureResponse.isspace() == True or FailureResponse == '') or (
                    TablesUsed.isspace() == True or TablesUsed == '') or (Note.isspace() == True or Note == '') or (
                    DocumentType.isspace() == True or DocumentType == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                ProjectId = ProjectId.strip()
                ModuleId = ModuleId.strip()
                URL = URL.strip()
                Purpose = Purpose.strip()
                Title = Title.strip()
                Method = Method.strip()
                HeaderParameter = HeaderParameter.strip()
                BodyParameter = BodyParameter.strip()
                SuccessResponse = SuccessResponse.strip()
                FailureResponse = FailureResponse.strip()
                TablesUsed = TablesUsed.strip()
                Note = Note.strip()
                DocumentType = DocumentType.strip()
                wherecondition = "`APIDocumentId` ='" + MasterId + "'"
                values = {'ProjectId': ProjectId, 'ModuleId': ModuleId, 'URL': URL, 'Purpose': Purpose, 'Title': Title,
                          'Method': Method, 'HeaderParameter': HeaderParameter, 'BodyParameter': BodyParameter,
                          'SuccessResponse': SuccessResponse, 'FailureResponse': FailureResponse,
                          'TablesUsed': TablesUsed, 'Note': Note, 'UpdatedDate': UpdatedDate,
                          'DocumentType': DocumentType}
                showmessage = DB.updateData("APIDocument", values, wherecondition)
                if showmessage['messageType'] == 'success':
                    response = {'category': "1", 'message': "Record updated successfully."}
                else:
                    response = {'category': "0", 'message': "Data Not Found."}
            response = make_response(jsonify(response))
            return response


# By IN_OI01_027 Dt-19-01-21
# API FOR MULTIPLE Documents LISTING
class RcAPIMultiAPICreateDocument(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                data = DB.selectAllData(
                    "SELECT A.*,B.ProjectName,C.ModuleName FROM APIDocument as A ,Project as B , Module as C where A.ProjectId = B.ProjectId and A.ModuleId = C.ModuleId  ORDER BY A.APIDocumentId ASC")  # and A.IsActive = 1 and A.IsDelete = 0
                if len(data) > 0:
                    response = {'category': "1", 'message': "List of all api documents", 'ResponseData': data}
                else:
                    response = {'category': "0", 'message': "Data not found"}
            response = make_response(jsonify(response))
            return response


# By IN_OI01_052 Dt-19-01-21
# Project List
class RcAPIProjects(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                projectslist = "select ProjectId ,ProjectName,IsActive ,IsDelete ,(CONVERT(CreatedDate,CHAR)) AS CreatedDate ,(CONVERT(UpdatedDate,CHAR)) AS UpdatedDate  from Project  "
                ResponseData = DB.selectAllData(projectslist)
                if len(ResponseData) == 0:
                    response = {'category': '0', 'message': 'Data not found !.'}
                else:
                    response = {'category': "1", 'message': "List of Projects.", 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# By IN_OI01_052 Dt-19-01-21
# Module List
class RcAPIModules(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                moduleslist = "select ModuleId ,ProjectId ,ModuleName,IsActive ,IsDelete ,(CONVERT(CreatedDate,CHAR)) AS CreatedDate ,(CONVERT(UpdatedDate,CHAR)) AS UpdatedDate  from Module "
                ResponseData = DB.selectAllData(moduleslist)
                if len(ResponseData) == 0:
                    response = {'category': '0', 'message': 'Data not found !.'}
                else:
                    response = {'category': "1", 'message': "List of modules.", 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# By IN_OI01_052 Dt-19-01-21
# Get Modules
class RcAPIGetModules(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '' or MasterId == '':
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                getmodule = "select ModuleId ,ProjectId ,ModuleName,IsActive ,IsDelete ,(CONVERT(CreatedDate,CHAR)) AS CreatedDate ,(CONVERT(UpdatedDate,CHAR)) AS UpdatedDate  from Module where ProjectId='" + MasterId + "' "
                ResponseData = DB.selectAllData(getmodule)
                if len(ResponseData) == 0:
                    response = {'category': '0', 'message': 'Data not found !.'}
                else:
                    response = {'category': "1", 'message': "List of Single module.", 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# By IN_OI01_052 Dt-19-01-21
# Get API Documents
class RcAPIGetApiDocuments(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '' or MasterId == '':
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                apidoc = "select APIDocumentId ,DocumentType,ProjectId ,ModuleId,URL,Purpose ,Title ,Method ,HeaderParameter ,BodyParameter ,SuccessResponse ,FailureResponse ,TablesUsed ,Note,IsActive ,IsDelete ,(CONVERT(CreatedDate,CHAR)) AS CreatedDate ,(CONVERT(UpdatedDate,CHAR)) AS UpdatedDate  from APIDocument  where ModuleId='" + MasterId + "' "
                ResponseData = DB.selectAllData(apidoc)
                if len(ResponseData) == 0:
                    response = {'category': '0', 'message': 'Data not found !.'}
                else:
                    response = {'category': "1", 'message': "Module Wise api documents.", 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# By IN_OI01_052 Dt-19-01-21
# TempDeleteDocument
class RcAPITempDeleteDocument(Resource):
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                MasterId = MasterId.strip()
                querry = "select * from APIDocument where  APIDocumentId ='" + MasterId + "'"
                responseData = DB.selectAllData(querry)
                if len(responseData):
                    ResponseData1 = responseData[0]['IsDelete']
                    if ResponseData1 == 0:
                        values = {"IsDelete": '1'}
                        showmessage = DB.updateData('APIDocument', values, "APIDocumentId = '" + MasterId + "'")
                        if showmessage['messageType'] == 'success':
                            response = {'category': "1", 'message': "Document deleted temporarily."}
                        else:
                            response = {'category': '0', 'message': 'Please try again.'}
                    else:
                        response = {'category': "0", 'message': "Data not found!"}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
        response = make_response(jsonify(response))
        return response


# Permanently Delete Document
class RcAPIPermanentDeleteDocument(Resource):
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            error = 0
            Status = ''
            if 'Status' in RequestData:
                Status = RequestData['Status']
            if (Status.isspace() == True or Status == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                Status = Status.strip()
                Querry = "select * from APIDocument where  APIDocumentId ='" + MasterId + "'"
                responseData = DB.selectAllData(Querry)
                if len(responseData) > 0:
                    if Status == '0':
                        values = {"IsDelete": Status}
                        showmessage = DB.updateData('APIDocument', values, "APIDocumentId = '" + MasterId + "'")
                        if showmessage['messageType'] == 'success':
                            response = {'category': '1', 'message': "Document Restore successfully."}
                        else:
                            response = {'category': '0', 'message': "Something data base error."}
                    else:
                        delete = DB.deleteSingleRow('APIDocument', "APIDocumentId = '" + MasterId + "'")
                        if showmessage['messageType'] == 'success':
                            response = {'category': "1", 'message': "Document deleted successfully."}
                        else:
                            response = {'category': '0', 'message': "Something data base error."}
                else:
                    response = {'category': "0", 'message': "Data not Found."}
            response = make_response(jsonify(response))
            return response


#  Document Status
class RcAPIDocumentStatus(Resource):
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if (LicKey.isspace() == True or LicKey == '') or (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                MasterId = MasterId.strip()
                Querry = "SELECT * FROM APIDocument  WHERE APIDocumentId   ='" + MasterId + "' and Isdelete=0 LIMIT 1 "
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    ResponseData1 = ResponseData[0]['IsActive']
                    if ResponseData1 == 0:
                        values = {"IsActive": '1'}
                        ResponseData1 = DB.updateData('APIDocument', values, " APIDocumentId = '" + MasterId + "'")
                        response = {'category': "1", 'message': "Document activated successfully."}
                    elif ResponseData1 == 1:
                        values = {"IsActive": '0'}
                        ResponseData1 = DB.updateData('APIDocument', values, "APIDocumentId = '" + MasterId + "'")
                        response = {'category': "1", 'message': "Document deactivated successfully."}
                    else:
                        response = {'category': "0", 'message': "Data not found!"}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
        response = make_response(jsonify(response))
        return response


#  Document Status
class RcAPIFCMTokenList(Resource):
    def get(self, MasterId):
        today, tdayTimeStamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        message = "Current Time: " + str(tdayTimeStamp)
        FCMMessageSend("94FF48C90C9CEC57A85EE00424215159", str(MasterId), "Airface", message)
        response = {'category': "1", 'message': "Success"}
        return response


# User Project List
class RcAPIUserProjects(Resource):
    def get(self):
        querry = "select ProjectId ,ProjectName,IsActive ,IsDelete ,(CONVERT(CreatedDate,CHAR)) AS CreatedDate ,(CONVERT(UpdatedDate,CHAR)) AS UpdatedDate  from Project where IsActive = '1' and  IsDelete = '0'"
        ResponseData = DB.selectAllData(querry)
        if len(ResponseData) == 0:
            response = {'category': '0', 'message': 'Data not found !.'}
        else:
            response = {'category': "1", 'message': "Project List", 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# User Module List
class RcAPIUserModules(Resource):
    def get(self):
        usermodules = "select ModuleId ,ProjectId ,ModuleName,IsActive ,IsDelete ,(CONVERT(CreatedDate,CHAR)) AS CreatedDate ,(CONVERT(UpdatedDate,CHAR)) AS UpdatedDate  from Module where IsActive = '1' and  IsDelete = '0'"
        ResponseData = DB.selectAllData(usermodules)
        if len(ResponseData) == 0:
            response = {'category': '0', 'message': 'Data not found !.'}
        else:
            response = {'category': "1", 'message': "success", 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# User Get Modules
class RcAPIGetUserModules(Resource):
    def get(self, MasterId):
        getmodule = "select ModuleId ,ProjectId ,ModuleName,IsActive ,IsDelete ,(CONVERT(CreatedDate,CHAR)) AS CreatedDate ,(CONVERT(UpdatedDate,CHAR)) AS UpdatedDate  from Module where ProjectId='" + MasterId + "' and  IsActive = '1' and  IsDelete = '0'"
        ResponseData = DB.selectAllData(getmodule)
        if len(ResponseData) == 0:
            response = {'category': '0', 'message': 'Data not found !.'}
        else:
            response = {'category': "1", 'message': "success", 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# Get User API Documents
class RcAPIUserApiDocuments(Resource):
    def get(self, MasterId):
        apidoc = "SELECT A.*,B.ProjectName,C.ModuleName FROM APIDocument as A ,Project as B , Module as C where A.ProjectId = B.ProjectId and A.ModuleId = C.ModuleId and C.ModuleId = '" + str(
            MasterId) + "' and A.IsActive = 1 and A.IsDelete = 0 and B.IsActive = 1 and B.IsDelete = 0 and C.IsActive = 1 and C.IsDelete = 0"
        ResponseData = DB.selectAllData(apidoc)
        if len(ResponseData) == 0:
            response = {'category': '0', 'message': 'Data not found !.'}
        else:
            response = {'category': "1", 'message': "Api Documents List", 'ResponseData': ResponseData}
        response = make_response(jsonify(response))
        return response


# User Single API Documents
class RcAPIUserDocument(Resource):
    def get(self, MasterId):
        MasterId = MasterId.strip()
        querry = "SELECT A.*,B.ProjectName,C.ModuleName FROM APIDocument as A ,Project as B , Module as C where A.ProjectId = B.ProjectId and A.ModuleId = C.ModuleId and A.APIDocumentId = '" + str(
            MasterId) + "' and A.IsActive = 1 and A.IsDelete = 0 and B.IsActive = 1 and B.IsDelete = 0 and C.IsActive = 1 and C.IsDelete = 0"
        RsAPIDocument = DB.selectAllData(querry)
        if len(RsAPIDocument) > 0:
            response = {'category': "1", 'message': "Documents List.", 'ResponseData': RsAPIDocument}
        else:
            response = {'category': "0", 'message': "Data not found"}
        response = make_response(jsonify(response))
        return response


# By IN_OI01_053 Dt-19-01-21
# Get API Documents
class RcAPILogout(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            FCMTokenNo = ''
            AndroidId = ''
            if 'FCMTokenNo' in RequestData and 'AndroidId' in RequestData:
                FCMTokenNo = RequestData['FCMTokenNo']
                AndroidId = RequestData['AndroidId']
            if (LicKey.isspace() == True or LicKey == '') or (FCMTokenNo.isspace() == True or FCMTokenNo == '') or (
                    AndroidId.isspace() == True or AndroidId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                FCMQuerry = "select * from  FCMTokenSession where LicKey='" + LicKey + "' and AndroidId ='" + str(
                    AndroidId) + "'"
                FCMData = DB.selectAllData(FCMQuerry)
                if len(FCMData) > 0:
                    deletelocation = DB.deleteSingleRow("FCMTokenSession",
                                                        "LicKey='" + LicKey + "' and AndroidId ='" + AndroidId + "'")
                    response = {'category': '1', 'message': 'You are now signed out.'}
                else:
                    response = {'category': "0", 'message': "Give valid AndroidId."}
        response = make_response(jsonify(response))
        return response


# Restore Employee Profile
class RcAPIMultiEmployeeRestore(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            EmpId = ''
            if 'EmpId' in RequestData:
                EmpId = RequestData['EmpId']
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpId = EmpId.strip()
                if EmpId == 'all':
                    Query1 = "select EmpId from EmployeeRegistration where IsDelete=1 and LicKey='" + LicKey + "' "
                    TempDelData = DB.selectAllData(Query1)
                    if len(TempDelData) > 0:
                        tablename = 'EmployeeRegistration'
                        wherecondition = "`LicKey`= '" + LicKey + "' AND IsDelete= '1'"
                        formvalues = {"IsDelete": '0'}
                        ResponseData1 = DB.updateData(tablename, formvalues, wherecondition)
                        response = {'category': "1", 'message': "Employee restored successfully"}
                    else:
                        response = {'category': "0", 'message': "Employee is not permanently deleted!"}
                else:
                    list = EmpId.split(",")
                    list1 = str(list)[1:-1]
                    if len(list) <= 5:
                        Query2 = "select * from EmployeeRegistration  WHERE EmpId IN(select EmpId from EmployeeRegistration where EmpId in(" + list1 + ") and IsDelete=1 and LicKey='" + LicKey + "') and LicKey ='" + LicKey + "' and IsDelete=1"
                        ResponseData = DB.selectAllData(Query2)
                        if len(ResponseData) > 0:
                            # Query3="Update EmployeeRegistration SET  IsDelete='0' where EmpId IN(select EmpId from EmployeeRegistration where empId in("+list1+") and IsDelete=1 and LicKey='"+LicKey+"')"
                            Query3 = "Update EmployeeRegistration SET  IsDelete='0' where EmpId IN(" + list1 + ") and IsDelete=1 and LicKey='" + LicKey + "'"
                            # print(Query3)
                            UpdateDate = DB.selectAllData(Query3)
                            response = {'category': "1", 'message': "Employees restored successfully"}
                        else:
                            response = {'category': "0", 'message': "Data not found!"}
                    else:
                        response = {'category': "0",
                                    'message': "You can choose five employees at a time.Not more than this."}
            response = make_response(jsonify(response))
            return response


# MultiEmployeeDelete
class RcAPIMultiEmployeeDelete(Resource):
    def put(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            EmpId = ''
            if 'EmpId' in RequestData:
                EmpId = RequestData['EmpId']
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpId = EmpId.strip()
                if EmpId == 'all':
                    TempDel = "select EmpId from EmployeeRegistration where IsDelete=1 and LicKey='" + LicKey + "' "
                    # print(TempDel)
                    TempDelData = DB.selectAllData(TempDel)
                    if len(TempDelData) > 0:
                        Querry1 = "Delete from DatasetEncodings where EmpId IN(select EmpId from EmployeeRegistration where IsDelete=1 and LicKey='" + LicKey + "') and LicKey='" + LicKey + "'"
                        ResponseData1 = DB.selectAllData(Querry1)
                        Querry2 = "Delete from CompOff where EmpId IN(select EmpId from EmployeeRegistration where IsDelete=1 and LicKey='" + LicKey + "') and LicKey='" + LicKey + "'"
                        ResponseData2 = DB.selectAllData(Querry2)
                        Querry3 = "Delete from ActivityDetails where EmpId IN(select EmpId from EmployeeRegistration where IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "' "
                        ResponseData3 = DB.selectAllData(Querry3)
                        Querry4 = "Delete from UserLogin where EmpId IN(select EmpId from EmployeeRegistration where IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "'"
                        ResponseData4 = DB.selectAllData(Querry4)
                        Querry5 = "Delete from EmployeeLeaveHistory where EmpId IN(select EmpId from EmployeeRegistration where IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "' "
                        ResponseData5 = DB.selectAllData(Querry5)
                        Querry6 = "Delete from MonthlyActivity where EmpId IN(select EmpId from EmployeeRegistration where IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "'"
                        ResponseData6 = DB.selectAllData(Querry6)
                        Querry7 = "Delete from UserPrivilege where EmpId IN(select EmpId from EmployeeRegistration where IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "'"
                        ResponseData7 = DB.selectAllData(Querry7)
                        Querry8 = "Delete from EmployeeShiftHistory where EmpId IN(select EmpId from EmployeeRegistration where IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "'"
                        ResponseData8 = DB.selectAllData(Querry8)
                        Querry9 = "Delete from EmployeeRegistration where IsDelete='1' and LicKey='" + LicKey + "'"
                        # print(Querry9)
                        ResponseData9 = DB.selectAllData(Querry9)
                        response = {'category': "1", 'message': "Employee deleted  permanently."}
                    else:
                        response = {'category': "0", 'message': "Data not found!"}
                else:
                    list = EmpId.split(",")
                    list1 = str(list)[1:-1]
                    if len(list) <= 5:
                        # print(len(list))
                        Querry1 = "Delete from DatasetEncodings where EmpId IN(select EmpId from EmployeeRegistration where EmpId in(" + list1 + ") and IsDelete=1 and LicKey='" + LicKey + "') and LicKey='" + LicKey + "'"
                        ResponseData1 = DB.selectAllData(Querry1)

                        Querry2 = "Delete from CompOff where EmpId IN(select EmpId from EmployeeRegistration where EmpId in(" + list1 + ") and IsDelete=1 and LicKey='" + LicKey + "') and LicKey='" + LicKey + "'"
                        ResponseData2 = DB.selectAllData(Querry2)

                        Querry3 = "Delete from ActivityDetails where EmpId IN(select EmpId from EmployeeRegistration where EmpId in(" + list1 + ") and IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "' "
                        ResponseData3 = DB.selectAllData(Querry3)

                        Querry4 = "Delete from UserLogin where EmpId IN(select EmpId from EmployeeRegistration where EmpId in(" + list1 + ") and IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "'"
                        ResponseData4 = DB.selectAllData(Querry4)

                        Querry5 = "Delete from EmployeeLeaveHistory where EmpId IN(select EmpId from EmployeeRegistration where EmpId in(" + list1 + ") and IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "' "
                        ResponseData5 = DB.selectAllData(Querry5)
                        Querry6 = "Delete from MonthlyActivity where EmpId IN(select EmpId from EmployeeRegistration where EmpId in(" + list1 + ") and IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "'"
                        ResponseData6 = DB.selectAllData(Querry6)
                        Querry7 = "Delete from UserPrivilege where EmpId IN(select EmpId from EmployeeRegistration where EmpId in(" + list1 + ") and IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "'"
                        ResponseData7 = DB.selectAllData(Querry7)
                        Querry8 = "Delete from EmployeeShiftHistory where EmpId IN(select EmpId from EmployeeRegistration where EmpId in(" + list1 + ") and IsDelete=1 and LicKey='" + LicKey + "')  and LicKey='" + LicKey + "'"
                        ResponseData8 = DB.selectAllData(Querry8)
                        # Querry9 = "Delete from EmployeeRegistration where EmpId IN(select EmpId from EmployeeRegistration where EmpId in("+list1+") and IsDelete=1 and LicKey='"+LicKey+"') "
                        Querry9 = "Delete from EmployeeRegistration where EmpId IN (" + list1 + ") and IsDelete='1' and LicKey='" + LicKey + "'"
                        # print(Querry9)
                        ResponseData9 = DB.selectAllData(Querry9)
                        response = {'category': "1", 'message': "Employee deleted  permanently.."}
                    else:
                        response = {'category': "0",
                                    'message': "You can choose 5 employees at a time.Not more than this."}
            response = make_response(jsonify(response))
            return response


# SINGLE NOTIFICATION LIST,ADD,DELETE NOTIFICATION
class RcAPINotification(Resource):
    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                Querry = "Select * from Notifications where `LicKey`= '" + LicKey + "' and NotificationsId = '" + MasterId + "' and IsActive=1 and IsDelete=0"
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Notifications List.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
            response = make_response(jsonify(response))
            return response

    def delete(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            # Mastrer id as a unquie id of the table
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "Master Id should not be blank."}
            else:
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                querry = "select * from Notifications where LicKey ='" + LicKey + "' AND NotificationsId= '" + MasterId + "'"
                ResponseData = DB.selectAllData(querry)
                if ResponseData:
                    wherecondition = "`LicKey`= '" + LicKey + "' AND NotificationsId= '" + MasterId + "'"
                    showmessage = DB.deleteSingleRow('Notifications', wherecondition)
                    if showmessage['messageType'] == 'success':
                        response = {'category': "1", 'message': "Notifications deleted successfully."}
                    else:
                        response = {'category': "0", 'message': "Database Error."}
                else:
                    response = {'category': "0", 'message': "Data not found."}
            response = make_response(jsonify(response))
            return response


# API FOR  MULTIPLE NOTIFICATION LISTING
class RcAPIMultiNotification(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                Querry = "Select * from Notifications where `LicKey`= '" + LicKey + "' and IsActive=1 and IsDelete=0 ORDER BY NotificationsId "
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    response = {'category': "1", 'message': "Notifications List.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
            response = make_response(jsonify(response))
            return response

    def delete(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                ResponseData = DB.selectAllData("DELETE FROM Notifications where `LicKey`= '" + LicKey + "'")
                # print(ResponseData)
                response = {'category': "1", 'message': "Notifications deleted successfully."}
            response = make_response(jsonify(response))
            return response


class RcAPIMonthlyCornJob(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            AttendanceMonth = ''
            AttendanceYear = ''
            if 'AttendanceYear' in RequestData and 'AttendanceMonth' in RequestData:
                AttendanceYear = RequestData['AttendanceYear']
                AttendanceMonth = RequestData['AttendanceMonth']
            if (LicKey.isspace() == True or LicKey == '') or (
                    AttendanceMonth.isspace() == True or AttendanceMonth == '') or (
                    AttendanceYear.isspace() == True or AttendanceYear == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                curDate = datetime.today().date()
                QsEmployeeList = "SELECT EmpId FROM EmployeeRegistration WHERE IsDelete = 0 AND IsActive = 1 and LicKey='" + LicKey + "' "
                RsEmployeeList = DB.selectAllData(QsEmployeeList)
                for i in range(len(RsEmployeeList)):
                    updatevalueArray = ""
                    getEmpId = RsEmployeeList[i]['EmpId']
                    QsActivityDetailscheck = "SELECT * from MonthlyActivity where EmpId='" + getEmpId + "' and  AttendanceMonth = '" + AttendanceMonth + "' and  AttendanceYear='" + AttendanceYear + "' AND LicKey = '" + LicKey + "' GROUP BY EmpId ORDER BY EmpId ASC "
                    RsActivityDetailscheck = DB.selectAllData(QsActivityDetailscheck)
                    QsActivityDetails = "SELECT Extract(Day from ADDate) As CurentDay, EmpId, MIN(ADTime) AS FIRSTSEEN,MAX(ADTime) AS LASTSEEN from ActivityDetails where EmpId = '" + getEmpId + "' AND  Extract(Month from ADDate)='" + AttendanceMonth + "' and Extract(Year from ADDate)='" + AttendanceYear + "' AND LicKey = '" + LicKey + "' GROUP BY ADDate ORDER BY ADDate ASC "
                    RsActivityDetails = DB.selectAllData(QsActivityDetails)
                    for j in range(len(RsActivityDetails)):
                        FIRSTSEEN = RsActivityDetails[j]['FIRSTSEEN']
                        LASTSEEN = RsActivityDetails[j]['LASTSEEN']
                        FIRSTSEENTime = date_time_obj = datetime.strptime(str(FIRSTSEEN), '%Y-%m-%d %H:%M:%S')
                        LASTSEENTime = date_time_obj = datetime.strptime(str(LASTSEEN), '%Y-%m-%d %H:%M:%S')
                        firstAtttime = datetime.strftime(FIRSTSEENTime, "%H:%M:%S")
                        lastAtttime = datetime.strftime(LASTSEENTime, "%H:%M:%S")
                        if updatevalueArray == '':
                            dayInValue = "'D" + str(RsActivityDetails[j]['CurentDay']) + "_IN' : '" + str(
                                firstAtttime) + "'," + "'D" + str(
                                RsActivityDetails[j]['CurentDay']) + "_OUT' : '" + str(
                                lastAtttime) + "'"
                        else:
                            dayInValue = ",'D" + str(RsActivityDetails[j]['CurentDay']) + "_IN' : '" + str(
                                firstAtttime) + "'," + "'D" + str(
                                RsActivityDetails[j]['CurentDay']) + "_OUT' : '" + str(
                                lastAtttime) + "'"
                        updatevalueArray = updatevalueArray + dayInValue
                    singleValueArray = "{" + "'EmpId': '" + getEmpId + "', 'LicKey': '" + LicKey + "', 'attendancemonth': '" + AttendanceMonth + "', 'attendanceyear': '" + AttendanceYear + "'," + updatevalueArray + "}"
                    my_dict = ast.literal_eval(singleValueArray)
                    # print(my_dict)
                    DB.insertData('MonthlyActivity', my_dict)
                    if len(RsActivityDetailscheck) > 0:
                        DeleteMonthlyActivityId = RsActivityDetailscheck[0]['MonthlyActivityId']
                        querry = "delete from  MonthlyActivity where MonthlyActivityId='" + str(
                            DeleteMonthlyActivityId) + "' and LicKey='" + LicKey + "' and EmpId='" + getEmpId + "'"
                        DB.selectAllData(querry)
                return "true"


# BY 3SD1025
# BackendServiceAPI
class ReverseLog(Resource):
    def post(self):
        verifiedUser = authVerifyUser.checkAuthenticate()
        if verifiedUser['authenticate'] == "False":
            return verifiedUser
        else:

            licKey = verifiedUser['LicKey']
            requestData = request.get_json()
            if not requestData: return {'status': 1000, "errorNo": "1", 'message': "Request parameter require."}
            if len(requestData) > 7: return {'status': 1001, "errorNo": "1", 'message': "Too many request parameters."}
            empid = ''
            time = ''
            date = ''
            camera_id = ''
            # photo = ''
            blobimage = ''
            if 'empid' in requestData and 'time' in requestData and 'date' in requestData and 'camera_id' in requestData and 'blobimage' in requestData:
                empid = requestData['empid']
                time = requestData['time']
                date = requestData['date']
                camera_id = requestData['camera_id']
                blobimage = requestData['blobimage']
            if (licKey.isspace() == True or licKey == '') or (empid.isspace() == True or empid == '') or (
                    time.isspace() == True or time == '') or (date.isspace() == True or date == '') or (
                    camera_id.isspace() == True or camera_id == '') or (
                    blobimage.isspace() == True or blobimage == ''):  #
                response = {'status': 1002, "errorNo": "1", 'message': "Parameters are missing. Please provide them."}
            else:
                photo = ''
                empid = empid.strip()
                time = time.strip()
                date = date.strip()
                camera_id = camera_id.strip()
                blobimage = blobimage.strip()

                blobimage_encode = blobimage.replace('data:image/png;base64,', '')
                blobimage_encode = bytes(blobimage_encode, 'utf-8')
                # image_64_decode = base64.decodestring(blobimage_encode)
                image_64_decode = base64.urlsafe_b64decode(blobimage_encode)
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                filename = now.strftime('%Y%m%d%H%M%S')
                pathimgfull = "reverselog/" + str(licKey) + "/" + str(today)
                filedirfull = 'static/public/' + pathimgfull
                savefilefulldir = 'static/public/' + pathimgfull + "/" + str(filename) + ".png"
                if not os.path.exists(filedirfull):
                    os.makedirs(filedirfull)
                if blobimage_encode:
                    image_result = open(savefilefulldir, 'wb')  # create a writable image and write
                    image_result.write(image_64_decode)
                    frame = cv2.imread(savefilefulldir)
                    # cv2.imshow("frame",frame)
                    if frame is None:
                        # print("Frame not found.")
                        response = {"status": 3000, 'errorNo': "1", 'message': "Frame not found."}
                        responseData = make_response(jsonify(response))
                        # return responseData
                    else:
                        face_locations = face_recognition.face_locations(frame)
                        # print(face_locations)
                        array = []
                        employeeID = ""
                        if face_locations != []:
                            face_encodings = face_recognition.face_encodings(frame, face_locations)
                            finalstring = ""
                            k = 0
                            distance = "SELECT sqrt("
                            i = 0
                            for j in range(0, 128):
                                string1 = "power(" + "c" + str(j) + " - ("
                                k = +1
                                if j == 127:
                                    string2 = "), 2) "
                                else:
                                    string2 = "), 2) +"
                                finalstring += string1 + str(face_encodings[i][j]) + string2
                            distance = distance + finalstring + ") As sqrt_val,`EmpId` from DatasetEncodings ORDER BY `sqrt_val`  ASC LIMIT 1"
                            resultData = DB.selectAllData(distance)
                            print(resultData[0]['sqrt_val'])
                            if resultData[0]['sqrt_val'] <= 0.42:
                                Prob = "100"
                                employeeID = resultData[0]['EmpId']
                                QsShiftDetails = "SELECT A.EmployeeShiftHistoryId, A.EmpId,A.StartDate,A.EndDate,B.IsNightShift,B.BaseLocationId,A.ShiftMasterId,convert(B.StartTime,char) AS StartTime,convert(B.EndTime,char) AS EndTime from EmployeeShiftHistory AS A ,ShiftMaster AS B  where A.LicKey='" + str(
                                    licKey) + "' AND A.StartDate='" + str(today) + "' AND A.EmpId='" + str(
                                    employeeID) + "' AND A.ShiftMasterId=B.ShiftMasterId"
                                RsShiftDetails = DB.selectAllData(QsShiftDetails)
                                if len(RsShiftDetails) > 0:
                                    BaseLocationId = RsShiftDetails[0]['BaseLocationId']
                                    EmployeeShiftHistoryId = RsShiftDetails[0]['EmployeeShiftHistoryId']
                                    ShiftMasterId = RsShiftDetails[0]['ShiftMasterId']
                                    IsNightShift = RsShiftDetails[0]['IsNightShift']
                                    StartTime = RsShiftDetails[0]['StartTime']
                                    EndTime = RsShiftDetails[0]['EndTime']
                                    checkLengthQuery = "select * from ActivityDetails where EmpId='" + employeeID + "' AND ADDate = CURRENT_DATE and LicKey='" + licKey + "'"
                                    lengthData = DB.selectAllData(checkLengthQuery)
                                    if len(lengthData) > 0:
                                        # time comparision then insert into ActivityDetails#24-03-2021
                                        maxTimQuery = "SELECT EmpId,timediff(CURRENT_TIME,CAST(max(ADTime) AS TIME)) as timedifference,CASE when timediff(CURRENT_TIME,CAST(max(ADTime) AS TIME))>=20 THEN 'ENTRY'  END AS Result FROM `ActivityDetails` WHERE EmpId ='" + employeeID + "' AND ADDate = CURRENT_DATE and LicKey='" + licKey + "'"
                                        maxTimeData = DB.selectAllData(maxTimQuery)
                                        if maxTimeData[0]['Result'] == 'ENTRY':
                                            print("entry")

                                        else:
                                            # print("time out")
                                            employeeID = ""
                                    else:
                                        print("entry")

                            array.append(employeeID)
                        if employeeID != '':
                            # print("inserting data")
                            # print(employeeID)
                            photo = 'sgad'
                            image_64_encodedata = blobimage
                            image_64_encode = image_64_encodedata.replace('data:image/png;base64,', '')
                            image_64_encode = bytes(image_64_encode, 'utf-8')
                            image_64_decode = base64.decodestring(image_64_encode)
                            now = datetime.now()
                            today = now.strftime('%Y-%m-%d')
                            filename = now.strftime('%Y%m%d%H%M%S')
                            pathimgfull = "images/full/" + str(licKey) + "/" + str(today)
                            pathimgthump = "images/thumb/" + str(licKey) + "/" + str(today)
                            filedirfull = 'static/public/' + pathimgfull
                            filedirthump = 'static/public/' + pathimgthump
                            savefilefulldir = 'static/public/' + pathimgfull + "/" + str(filename) + ".png"
                            savefilethumpdir = 'static/public/' + pathimgthump + "/" + str(filename) + ".png"
                            if not os.path.exists(filedirfull):
                                os.makedirs(filedirfull)
                            if not os.path.exists(filedirthump):
                                os.makedirs(filedirthump)
                            if image_64_encode:
                                image_result = open(savefilefulldir,
                                                    'wb')  # create a writable image and write the decoding result
                                image_result.write(image_64_decode)
                                querydata = "INSERT INTO ActivityDetails (ActivityDetailsId ,EmpId,EmployeeShiftHistoryId,ShiftMasterId,BaseLocationId,ADTime,ADDate ,Prob,Source,FileLocation,LicKey ,EmpImage) VALUES (NULL,'" + str(
                                    employeeID) + \
                                            "','" + str(EmployeeShiftHistoryId) + "','" + str(
                                    ShiftMasterId) + "','" + str(BaseLocationId) + "','" + str(time) + "','" + str(
                                    date) + \
                                            "','" + str(Prob) + "','" + str(camera_id) + "','" + str(savefilefulldir) + \
                                            "','" + str(licKey) + "','" + str(savefilefulldir) + "')"
                                insertactivity = DB.directinsertData(querydata)
                                # insertactivity = DB.singleQuery(querydata)
                                response = {'status': 2001, 'errorNo': 0,
                                            'message': "Recent log inserted successfully."}
                                responseData = make_response(jsonify(response))
                            else:
                                response = {'status': 3001, 'errorNo': 1,
                                            'message': "Couldn't be inserted!check your file again."}
                                responseData = make_response(jsonify(response))
                            response = {'status': 2000, 'errorNo': 0, 'message': "Image save successfully."}
                            responseData = make_response(jsonify(response))
                        else:
                            response = {'status': 3000, 'errorNo': 1, 'message': "Sorry! not match."}
                            responseData = make_response(jsonify(response))
                else:
                    response = {'status': 3000, 'errorNo': 1, 'message': "Please check your file again."}
            responseData = make_response(jsonify(response))
            return responseData


# CAMERA ADD FOR ENTERPRISE
class AddUpdateCamera(Resource):
    def post(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            Status = "1"
            CameraName = ""

            CameraURL = ""
            if 'CameraName' in RequestData and 'CameraURL' in RequestData:
                CameraName = RequestData['CameraName']

                CameraURL = RequestData['CameraURL']
            now = datetime.now()
            GeneratedDate = now.strftime('%Y-%m-%d')
            if (LicKey.isspace() == True or LicKey == '') or (CameraName.isspace() == True or CameraName == '') or (
                    CameraURL.isspace() == True or CameraURL == ''):

                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                CameraName = CameraName.strip()
                CameraURL = CameraURL.strip()
                tableName = "Camera"
                whereCondition = " LicKey='" + LicKey + "'"
                fields = "count(*)"
                order = ""
                cameraDtls = DB.retrieveAllData(tableName, fields, whereCondition, order)
                noOfCam = cameraDtls[0]['count(*)']
                if noOfCam >= 2:
                    response = {'category': '0', 'message': 'Cannot add More Camera !'}
                else:
                    tableName = "Camera"
                    values = {'CameraName': CameraName, 'CameraUrl': CameraURL, 'Status': Status,
                              'CreatedDate': GeneratedDate, 'LicKey': LicKey}
                    # 'LaneNo': laneNo, 'BarrierAuthKey': barrierAuthKey,'SocketIp': socketIp,'SocketPort':socketPort,
                    cameraDtlsData = DB.insertData(tableName, values)
                    if cameraDtlsData['messageType'] == 'success':
                        response = {'category': '1', 'message': 'Camera Added Successfully'}
                    else:
                        response = {'category': '0', 'message': "Camera couldn't be added  !"}
            response = make_response(jsonify(response))
            return response

    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
        else:
            licKey = VURS['LicKey']
            requestData = request.get_json()
            status = "1"
            CameraName = ''
            CameraUrl = ''
            if 'CameraName' in requestData and 'CameraURL' in requestData:
                CameraName = requestData['CameraName']
                CameraURL = requestData['CameraURL']
            if (licKey.isspace() == True or licKey == '') or (CameraName.isspace() == True or CameraName == '') or (
                    CameraURL.isspace() == True or CameraURL == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                now = datetime.now()
                CreatedDate = now.strftime('%Y-%m-%d')
                CameraName = CameraName.strip()
                CameraURL = CameraURL.strip()
                tableName = "Camera"
                whereCondition = "CameraId='" + MasterId + "' and LicKey='" + licKey + "'"
                fields = "*"
                order = ""
                cameraDtls = DB.retrieveAllData(tableName, fields, whereCondition, order)
                if len(cameraDtls) > 0:
                    tableName = "Camera"
                    values = {'CameraName': CameraName, 'CameraUrl': CameraURL, 'CreatedDate': CreatedDate}
                    cameraDtlsData = DB.updateData(tableName, values, whereCondition)
                    if cameraDtlsData['messageType'] == 'success':
                        response = {'category': '1', 'message': 'Camera updated successfully'}
                    else:
                        response = {'category': '0', 'message': "Camera couldn't be updated  !"}
                else:
                    response = {'category': '0', 'message': "No data available !"}
            response = make_response(jsonify(response))
            return response

    def get(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        # MASTER ID AS NOT VALID BUT YOU HAVE TO SEND THERE ANY THING IN URL
        else:
            licKey = VURS['LicKey']
            if (licKey.isspace() == True or licKey == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                now = datetime.now()
                CreatedDate = now.strftime('%Y-%m-%d')
                tableName = "Camera"
                whereCondition = "CameraId='" + MasterId + "' and LicKey='" + licKey + "'"
                fields = "*"
                order = ""
                cameraDtls = DB.retrieveAllData(tableName, fields, whereCondition, order)
                if len(cameraDtls) > 0:
                    response = {'category': '1', 'message': 'Camera Details.', "ResponseData": cameraDtls}
                else:
                    response = {'category': '0', 'message': "No data available !"}
            response = make_response(jsonify(response))
            return response


#  Camera Status
class ActiveDeactiveCamera(Resource):
    def put(self, MasterId):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if (MasterId.isspace() == True or MasterId == ''):
                response = {'category': "0", 'message': "All fields are mandatory"}
            else:
                MasterId = MasterId.strip()
                Querry = "SELECT * FROM Camera WHERE CameraId  ='" + MasterId + "' and LicKey='" + LicKey + "' LIMIT 1 "
                ResponseData = DB.selectAllData(Querry)
                if len(ResponseData) > 0:
                    ResponseData1 = ResponseData[0]['Status']
                    if ResponseData1 == 0:
                        tablename = 'Camera'
                        wherecondition = "CameraId= '" + MasterId + "' and LicKey='" + LicKey + "' "
                        values = {"Status": '1'}
                        ResponseData1 = DB.updateData(tablename, values, wherecondition)
                        response = {'category': "1", 'message': "Camera activated successfully."}
                    elif ResponseData1 == 1:
                        tablename = 'Camera'
                        wherecondition = "CameraId= '" + MasterId + "' and LicKey='" + LicKey + "'"
                        values = {"Status": '0'}
                        ResponseData1 = DB.updateData(tablename, values, wherecondition)
                        response = {'category': "1", 'message': "Camera deactivated successfully."}
                    else:
                        response = {'category': "0", 'message': "Data not found!"}
                else:
                    response = {'category': "0", 'message': "Data not found!"}
        response = make_response(jsonify(response))
        return response


# MULTIPLE CAMERALISTING
class EnterpriseCameraList(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            if LicKey == '':
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                querry = "select * from Camera AS A ORDER BY A.CameraId DESC"
                ResponseData = DB.selectAllData(querry)
                if len(ResponseData) > 0:
                    response = {'category': '1', 'message': 'Camera Listing.', 'ResponseData': ResponseData}
                else:
                    response = {'category': '0', 'message': 'Data not found'}
            response = make_response(jsonify(response))
            return response


# DAILY REPORT
class DailyIncidentReport(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            IncidentDate = ''
            if 'IncidentDate' in RequestData:
                IncidentDate = RequestData['IncidentDate']
            if (IncidentDate.isspace() == True or IncidentDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory.", 'RequestData': RequestData}
            else:
                IncidentDate = IncidentDate.strip()
                ReportList = []
                getEmpId = "select Distinct(EmpId) from IncidentReportDetails where LicKey ='" + LicKey + "'"
                resultEmpId = DB.selectAllData(getEmpId)
                for i in range(len(resultEmpId)):
                    EmpId = resultEmpId[i]['EmpId']
                    dailyIncidentReport = "select A.EmpId,convert (A.IncidentDate,char) AS IncidentDate,A.PhotoPath,B.EmpName,B.EmployeeRegistrationId,convert(min(A.IncidentTime),char) AS FirstSeen,convert(max(A.IncidentTime),char) AS LastSeen,(SELECT CameraName FROM Camera WHERE CameraId IN(select CameraId from IncidentReportDetails where IncidentTime IN (SELECT convert(max(IncidentTime),char) from IncidentReportDetails WHERE LicKey='" + LicKey + "' and EmpId='" + EmpId + "' and IncidentDate='" + IncidentDate + "') and LicKey='" + LicKey + "'  and EmpId='" + EmpId + "') and LicKey='" + LicKey + "') AS LastSeenCamera,(SELECT CameraName FROM Camera WHERE CameraId IN(select CameraId from IncidentReportDetails where IncidentTime IN (SELECT convert(min(IncidentTime),char) from IncidentReportDetails WHERE LicKey='" + LicKey + "' and EmpId='" + EmpId + "'  and IncidentDate='" + IncidentDate + "') and LicKey='" + LicKey + "' and EmpId='" + EmpId + "') and LicKey='" + LicKey + "') AS FirstSeenCamera from IncidentReportDetails as A,EmployeeRegistration as B where A.IncidentDate ='" + IncidentDate + "' and A.EmpId='" + EmpId + "' and B.EmpId='" + EmpId + "' and A.LicKey='" + LicKey + "'"
                    # print(dailyIncidentReport)
                    ResponseData = DB.selectAllData(dailyIncidentReport)
                    if ResponseData[0]['EmpId'] == None:
                        continue
                    ReportList.append(ResponseData)
                if ReportList:
                    response = {'category': "1", 'message': "Daily incident report details.",
                                'ResponseData': ReportList}
                else:
                    response = {'category': "0", 'message': "Data not Found."}
            response = make_response(jsonify(response))
            return response


# ALL ACTIVITY LIST REPORT
class RecentIncidentReport(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            querry = "Select A.EmpId,B.EmpName,convert(cast(A.IncidentTime as time(0)),char) AS IncidentTime,A.CameraId,C.CameraName,A.PhotoPath,convert(A.IncidentDate,char) AS IncidentDate from EmployeeRegistration as B , IncidentReportDetails as A LEFT JOIN Camera AS C ON (C.CameraId=A.CameraId and C.LicKey='" + LicKey + "') where A.EmpId=B.EmpId  and A.LicKey='" + LicKey + "' order by A.IncidentTime DESC Limit 50"
            ResponseData = DB.selectAllData(querry)
            if len(ResponseData) > 0:
                response = {'category': "1", 'message': "Recent incident report details.", 'ResponseData': ResponseData}
            else:
                response = {'category': "0", 'message': "Data not found"}
        response = make_response(jsonify(response))
        return response


# DAILY REPORT
class ThresholdPoints(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            ThresholdPoint = ''
            ThresholdDate = ''
            if 'ThresholdPoint' in RequestData and 'ThresholdDate' in RequestData:
                ThresholdPoint = RequestData['ThresholdPoint']
                ThresholdDate = RequestData['ThresholdDate']
            if (ThresholdPoint.isspace() == True or ThresholdPoint == '') or (
                    ThresholdDate.isspace() == True or ThresholdDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory.", 'RequestData': RequestData}
            else:
                ThresholdPoint = ThresholdPoint.strip()
                ThresholdDate = ThresholdDate.strip()
                values = {'LicKey': LicKey, 'ThresholdPoints': ThresholdPoint, 'ThresholdDate': ThresholdDate}
                insertResult = DB.insertData("Threshold", values)
                if insertResult['messageType'] == 'success':
                    response = {'category': "1", 'message': "Success."}
                else:
                    response = {'category': "0", 'message': "Data not Found."}
            response = make_response(jsonify(response))
            return response


# CONTACT TRACING
class ContactTracing(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            EmpId = ""
            FromDate = ""
            ToDate = ""
            TimeDifference = ""
            if 'EmpId' in RequestData and 'FromDate' in RequestData and 'ToDate' in RequestData and 'TimeDifference' in RequestData:
                EmpId = RequestData['EmpId']
                FromDate = RequestData['FromDate']
                ToDate = RequestData['ToDate']
                TimeDifference = RequestData['TimeDifference']
            if (LicKey.isspace() == True or LicKey == '') or (EmpId.isspace() == True or EmpId == '') or (
                    FromDate.isspace() == True or FromDate == '') or (ToDate.isspace() == True or ToDate == '') or (
                    TimeDifference.isspace() == True or TimeDifference == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                EmpId = EmpId.strip()
                FromDate = FromDate.strip()
                ToDate = ToDate.strip()
                TimeDifference = TimeDifference.strip()
                dateQuery = "select ADTime,Source from ActivityDetails where ADDate >='" + FromDate + "' and ADDate <='" + ToDate + "' and EmpId='" + EmpId + "' and LicKey='" + LicKey + "'"
                queryData = DB.selectAllData(dateQuery)
                responceData = []
                if len(queryData) > 0:
                    for i in range(len(queryData)):
                        addTime = queryData[i]['ADTime']
                        cameraId = queryData[i]['Source']
                        activityQuery = "select A.*,B.EmpName,C.CameraName from ActivityDetails as A,EmployeeRegistration as B,Camera as C where A.Source ='" + str(
                            cameraId) + "' and A.ADTime<= '" + str(
                            addTime) + "' + interval '" + TimeDifference + "' minute AND A.ADTime>='" + str(
                            addTime) + "' + interval '" + '-' + TimeDifference + "' minute AND A.EmpId !='" + EmpId + "' and A.LicKey='" + LicKey + "' and A.EmpId=B.EmpId and A.Source=C.CameraId"
                        activityData = DB.selectAllData(activityQuery)
                        responceData.append(activityData)
                    response = {'category': '1', 'message': 'Contact tracing report.', 'response': responceData}
                else:
                    response = {'category': '0', 'message': "Data not found !"}
            response = make_response(jsonify(response))
            return response


# ThresholdtReport
class ThresholdtReport(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            querry = "Select ThresholdId ,LicKey,ThresholdPoints,convert(ThresholdDate,char) as ThresholdDate from Threshold where LicKey='" + LicKey + "' order by ThresholdId DESC"
            ResponseData = DB.selectAllData(querry)
            if len(ResponseData) > 0:
                response = {'category': "1", 'message': "Threshold report details.", 'ResponseData': ResponseData}
            else:
                response = {'category': "0", 'message': "Data not found"}
        response = make_response(jsonify(response))
        return response


# LoadIncidentActivity
class LoadIncidentActivity(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            EmpId = ''
            CameraId = ''
            IncidentDate = ''
            IncidentTime = ''
            if request.form['EmpId'] and request.form['CameraId'] and request.form['IncidentDate'] and request.form[
                'IncidentTime'] and request.files['Image']:
                EmpId = request.form['EmpId']
                CameraId = request.form['CameraId']
                IncidentDate = request.form['IncidentDate']
                IncidentTime = request.form['IncidentTime']
                Image = request.files['Image']
            if (EmpId.isspace() == True or EmpId == '') or (CameraId.isspace() == True or CameraId == '') or (
                    IncidentDate.isspace() == True or IncidentDate == '') or (
                    IncidentTime.isspace() == True or IncidentTime == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                now = datetime.now()
                CreatedDate = now.strftime('%Y-%m-%d')
                photoPath = 'static/public/upload/recent_Image/'
                uniqueId = ''.join(random.choice(string.ascii_uppercase) for i in range(8))
                if not os.path.exists(photoPath):
                    os.makedirs(photoPath)
                if Image and allowed_Img_Ext(Image.filename):
                    fileName = secure_filename(Image.filename)
                    fileRename = uniqueId + str(CreatedDate) + "_" + fileName
                    fullFilePath = photoPath + fileRename
                    Image.save(os.path.join(photoPath, fileRename))
                tableName = "IncidentReportDetails"
                values = {"EmpId": EmpId, "CameraId": CameraId, "IncidentDate": IncidentDate,
                          "IncidentTime": IncidentTime, "PhotoPath": fullFilePath, "LicKey": LicKey}
                insertResult = DB.insertData(tableName, values)
                if insertResult['messageType'] == 'success':
                    response = {'category': "1", 'message': "Incident activity inserted."}
                else:
                    response = {'category': "0", 'message': "Data not Found."}
            response = make_response(jsonify(response))
            return response


class ShiftWiseDashboardCount(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            # ADDate = '2021-06-03'
            responseData = []
            Shift_wise = "select ShiftMasterId ,ShiftName from ShiftMaster where LicKey='" + LicKey + "' group by ShiftMasterId"
            total_shift = DB.selectAllData(Shift_wise)
            for i in range(len(total_shift)):
                ShiftName = total_shift[i]['ShiftName']
                ShiftMasterId = total_shift[i]['ShiftMasterId']
                emp__total = "select A.EmpId from EmployeeShiftHistory A Left Join EmployeeRegistration B on (A.EmpId=B.EmpId) where B.IsActive=1 and B.IsDelete=0 and A.ShiftMasterId='" + str(
                    ShiftMasterId) + "' GROUP by A.empId"
                total_Emp = DB.selectAllData(emp__total)
                activity = "select * from ActivityDetails where ShiftMasterId='" + str(
                    ShiftMasterId) + "' and ADDate='" + ADDate + "' and LicKey='" + LicKey + "' and EmployeeShiftHistoryId in (select EmployeeShiftHistoryId from EmployeeShiftHistory where StartDate='" + ADDate + "') GROUP by EmployeeShiftHistoryId "
                present_emp = DB.selectAllData(activity)
                absent_emp = len(total_Emp) - len(present_emp)
                if len(total_Emp) == 0:
                    absent_emp = 0
                late_coming = "select DISTINCT(A.EmpId) ,D.ShiftMasterId, min(A.ADTime) as fr,convert(D.ShiftMargin,char) AS ShiftMargin from ActivityDetails as A ,ShiftMaster AS D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + ADDate + "' and E.LicKey='" + LicKey + "' and E.ShiftMasterId='" + str(
                    ShiftMasterId) + "') and A.ShiftMasterId='" + str(
                    ShiftMasterId) + "' and A.LicKey='" + LicKey + "' and D.ShiftMasterId='" + str(
                    ShiftMasterId) + "' group by A.ShiftMasterId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
                # print(late_coming)
                late_coming_rslt = DB.selectAllData(late_coming)
                newArr = {}
                newArr['ShiftName'] = ShiftName
                newArr['ShiftMasterId'] = str(ShiftMasterId)
                newArr['TotalEmployee'] = len(total_Emp)
                newArr['PresentEmployees'] = len(present_emp)
                newArr['AbsentEmployees'] = absent_emp
                newArr['LateEmployees'] = len(late_coming_rslt)
                responseData.append(newArr)
            response = {'category': '1', 'message': 'Shift wise dashboard info.', 'ResponseData': responseData}
            response = make_response(jsonify(response))
            return response

        # 05-08-2021


class ShiftWiseDailyReport(Resource):
    def post(self):

        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            if not RequestData:
                abort(400)
            StartDate = ''
            shift_id = ''
            if 'StartDate' in RequestData:
                StartDate = RequestData['StartDate']
            if 'ShiftId' in RequestData:
                shift_id = RequestData['ShiftId']
            else:
                shift_id = ""
            if (StartDate.isspace() == True or StartDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                StartDate = StartDate.strip()
                shift_id = shift_id.strip()
                if len(shift_id) > 0:
                    enterpriseDailyReport = "select '1' as Status,convert(D.ShiftMargin,char) As ShiftMargin,A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName,CASE When CAST(min(A.ADTime) AS TIME) > D.ShiftMargin THEN CONVERT(TIMEDIFF (CAST(min(A.ADTime) AS TIME),D.ShiftMargin) ,CHAR) END AS LateDuration ,CASE When CAST(min(A.ADTime) AS TIME) < D.ShiftMargin THEN CONVERT(TIMEDIFF (D.ShiftMargin,CAST(min(A.ADTime) AS TIME)) ,CHAR) END AS EarlyCheckInDuration ,(SELECT CameraName FROM Camera WHERE CameraId IN(select Source from ActivityDetails where ADTime IN (SELECT convert(max(ADTime),char) from ActivityDetails WHERE LicKey='" + LicKey + "' and EmpId=A.EmpId) and LicKey='" + LicKey + "') and LicKey='" + LicKey + "') AS LastSeenCamera,(SELECT CameraName FROM Camera WHERE CameraId IN(select Source from ActivityDetails where ADTime IN (SELECT convert(min(ADTime),char) from ActivityDetails WHERE LicKey='" + LicKey + "' and EmpId=A.EmpId) and LicKey='" + LicKey + "') and LicKey='" + LicKey + "') AS FirstSeenCamera from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + StartDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId='" + shift_id + "' and A.LicKey='" + LicKey + "' group by B.EmployeeRegistrationId"
                else:
                    enterpriseDailyReport = "select '1' as Status,A.EmpId,A.EmpImage,B.EmpName,B.EmployeeRegistrationId, A.EmployeeShiftHistoryId,convert(min(A.ADTime),char) AS FirstSeen,convert(max(A.ADTime),char) AS LastSeen,convert(min(A.ADDate),char) AS ADDate,C.LocationName,D.ShiftName, CASE When CAST(min(A.ADTime) AS TIME) > D.ShiftMargin THEN CONVERT(TIMEDIFF (CAST(min(A.ADTime) AS TIME),D.ShiftMargin) ,CHAR) END AS LateDuration ,CASE When CAST(min(A.ADTime) AS TIME) < D.ShiftMargin THEN CONVERT(TIMEDIFF (D.ShiftMargin,CAST(min(A.ADTime) AS TIME)) ,CHAR) END AS EarlyCheckInDuration ,(SELECT CameraName FROM Camera WHERE CameraId IN(select Source from ActivityDetails where ADTime IN (SELECT convert(max(ADTime),char) from ActivityDetails WHERE LicKey='" + LicKey + "' and EmpId=A.EmpId) and LicKey='" + LicKey + "') and LicKey='" + LicKey + "') AS LastSeenCamera,(SELECT CameraName FROM Camera WHERE CameraId IN(select Source from ActivityDetails where ADTime IN (SELECT convert(min(ADTime),char) from ActivityDetails WHERE LicKey='" + LicKey + "' and EmpId=A.EmpId) and LicKey='" + LicKey + "') and LicKey='" + LicKey + "') AS FirstSeenCamera from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + StartDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by B.EmployeeRegistrationId"
                ResponseData = DB.selectAllData(enterpriseDailyReport)
                if ResponseData:
                    response = {'category': "1", 'message': "Shift wise daily report.", 'ResponseData': ResponseData}
                else:
                    response = {'category': "0", 'message': "Data not Found."}
            response = make_response(jsonify(response))
            return response


class ShiftWiseAbsentEmployee(Resource):
    def post(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            RequestData = request.get_json()
            searchDate = ''
            shift_id = ''
            if 'searchDate' in RequestData:
                searchDate = RequestData["searchDate"]
            if 'ShiftId' in RequestData:
                shift_id = RequestData['ShiftId']
            else:
                shift_id = ""
            if (LicKey.isspace() == True or LicKey == '') or (searchDate.isspace() == True or searchDate == ''):
                response = {'category': "0", 'message': "All fields are mandatory."}
            else:
                searchDate = searchDate.strip()
                shift_id = shift_id.strip()
                if len(shift_id) > 0:
                    Querry = "Select F.EmpId,G.LocationName,F.EmpName,H.ShiftMasterId,I.ShiftName,J.ImagePath FROM BaseLocation AS G, EmployeeShiftHistory AS H, ShiftMaster AS I, EmployeeRegistration AS F left join DatasetEncodings AS J on (F.EmpId=J.EmpId and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0) where F.EmpId NOT IN (select A.EmpId from ActivityDetails as A,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + searchDate + "' and E.LicKey='" + LicKey + "') and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId='" + shift_id + "' and D.ShiftMasterId='" + shift_id + "' and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId) and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0 and G.BaseLocationId=F.BaseLocationId and H.StartDate='" + searchDate + "' and F.EmpId=H.EmpId and H.ShiftMasterId='" + shift_id + "' and I.ShiftMasterId='" + shift_id + "' GROUP BY F.EmpId"
                    absentEmp = DB.selectAllData(Querry)
                    if len(absentEmp) > 0:
                        response = {'category': "1", 'message': "Absent Employee Information.",
                                    'ResponseData': absentEmp}
                    else:
                        response = {'category': "0", 'message': "Data not found on this date."}
                else:
                    Querry = "Select F.EmpId,G.LocationName,F.EmpName,H.ShiftMasterId,I.ShiftName,J.ImagePath FROM BaseLocation AS G, EmployeeShiftHistory AS H, ShiftMaster AS I, EmployeeRegistration AS F left join DatasetEncodings AS J on (F.EmpId=J.EmpId and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0) where F.EmpId NOT IN (select A.EmpId from ActivityDetails as A,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + searchDate + "' and E.LicKey='" + LicKey + "') and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId) and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0 and G.BaseLocationId=F.BaseLocationId and H.StartDate='" + searchDate + "' and F.EmpId=H.EmpId and H.ShiftMasterId=I.ShiftMasterId GROUP BY F.EmpId"
                    absentEmp = DB.selectAllData(Querry)
                    if len(absentEmp) > 0:
                        response = {'category': "1", 'message': "Absent Employee Information.",
                                    'ResponseData': absentEmp}
                    else:
                        response = {'category': "0", 'message': "Data not found on this date."}
            response = make_response(jsonify(response))
            return response


class AbsentPresentGraph(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            date_obj = datetime.strptime(ADDate, '%Y-%m-%d')
            Sunday = date_obj - timedelta(days=date_obj.isoweekday())
            presentarray = {}
            locationList = "SELECT A.BaseLocationId,A.LocationName FROM BaseLocation AS A,ShiftMaster AS B  WHERE A.LicKey = '" + LicKey + "' AND A.IsActive = 1  and A.BaseLocationId=B.BaseLocationId GROUP by BaseLocationId"
            rsLoc = DB.selectAllData(locationList)
            locationArrayData = []
            for i in range(len(rsLoc)):
                locationID = rsLoc[i]['BaseLocationId']
                locationName = rsLoc[i]['LocationName']
                shiftList = "SELECT ShiftMasterId,ShiftName FROM ShiftMaster WHERE LicKey = '" + LicKey + "' AND BaseLocationId = '" + str(
                    locationID) + "'"
                rsShift = DB.selectAllData(shiftList)
                shiftArrayData = []
                for j in range(len(rsShift)):
                    ShiftMasterId = rsShift[j]['ShiftMasterId']
                    ShiftName = rsShift[j]['ShiftName']
                    singleDayWiseData = []
                    for i in range(1, 8):
                        modified_date = Sunday + timedelta(days=i)
                        presentarray['modified_date'] = modified_date
                        nextdate = modified_date
                        nextdate = str(nextdate)
                        var = nextdate.split(' ')
                        extractDate = var[0]
                        extractMonth = extractDate.split('-')
                        month = extractMonth[1]
                        presentQuerry = "select A.EmpId from ActivityDetails as A,EmployeeRegistration as B,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN (select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + extractDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and D.ShiftMasterId='" + str(
                            ShiftMasterId) + "' and C.BaseLocationId='" + str(
                            locationID) + "' group by A.EmployeeShiftHistoryId"
                        presentEmpData = DB.selectAllData(presentQuerry)
                        todayPresent = len(presentEmpData)
                        absentQuerry = "Select F.EmpId FROM BaseLocation AS G, EmployeeShiftHistory AS H, ShiftMaster AS I, EmployeeRegistration AS F left join DatasetEncodings AS J on (F.EmpId=J.EmpId) where F.EmpId NOT IN (select A.EmpId from ActivityDetails as A,BaseLocation as C,ShiftMaster as D where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + extractDate + "' and E.LicKey='" + LicKey + "') and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' group by A.EmployeeShiftHistoryId) and F.LicKey='" + LicKey + "' and F.IsActive=1 and F.IsDelete=0 and G.BaseLocationId=F.BaseLocationId and H.StartDate='" + extractDate + "' and F.EmpId=H.EmpId and H.ShiftMasterId=I.ShiftMasterId and I.ShiftMasterId='" + str(
                            ShiftMasterId) + "' and G.BaseLocationId='" + str(locationID) + "' GROUP BY F.EmpId"
                        absentEmpData = DB.selectAllData(absentQuerry)
                        todayabsent = len(absentEmpData)
                        singleDateDataResponse = {'todayPresent': todayPresent, 'todayabsent': todayabsent,
                                                  'date': extractDate, 'month': month}
                        singleDayWiseData.append(singleDateDataResponse)
                locationwisedata = {'BaseLocationId': locationID, 'LocationName': locationName,
                                    'TotalWeekData': singleDayWiseData}  # ,
                locationArrayData.append(locationwisedata)
            response = {'category': "1", 'message': "Present and Absent Info.", "ResponseData": locationArrayData}
            response = make_response(jsonify(response))
            return response


class LateComingInTimeGraph(Resource):
    def get(self):
        VURS = authVerifyUser.checkAuthenticate()
        if VURS['authenticate'] == "False":
            return VURS
        else:
            LicKey = VURS['LicKey']
            now = datetime.now()
            ADDate = now.strftime('%Y-%m-%d')
            date_obj = datetime.strptime(ADDate, '%Y-%m-%d')
            Sunday = date_obj - timedelta(days=date_obj.isoweekday())
            Saturday = Sunday + timedelta(days=6)
            intimearray = {}
            locationArrayData = []
            locationList = "SELECT A.BaseLocationId,A.LocationName FROM BaseLocation AS A,ShiftMaster AS B  WHERE A.LicKey = '" + LicKey + "' AND A.IsActive = 1  and A.BaseLocationId=B.BaseLocationId GROUP by BaseLocationId"
            rsLoc = DB.selectAllData(locationList)
            for i in range(len(rsLoc)):
                locationID = rsLoc[i]['BaseLocationId']
                locationName = rsLoc[i]['LocationName']
                shiftList = "SELECT ShiftMasterId,ShiftName FROM ShiftMaster WHERE LicKey = '" + LicKey + "' AND BaseLocationId = 0 OR  BaseLocationId = '" + str(
                    locationID) + "'"
                rsShift = DB.selectAllData(shiftList)
                shiftArrayData = []
                for j in range(len(rsShift)):
                    ShiftMasterId = rsShift[j]['ShiftMasterId']
                    ShiftName = rsShift[j]['ShiftName']
                    singleDayWiseData = []
                    for i in range(-1, 7, 1):
                        if i != -1:
                            modified_date = Sunday + timedelta(days=i)
                            if modified_date <= Saturday:
                                nextdate = modified_date
                                nextdate = str(nextdate)
                                var = nextdate.split(' ')
                                extractDate = var[0]
                                extractMonth = extractDate.split('-')
                                month = extractMonth[1]
                                query = "select A.EmpId,convert(D.ShiftMargin,char) AS ShiftMargin from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + extractDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.ShiftMasterId='" + str(
                                    ShiftMasterId) + "' and A.BaseLocationId='" + str(
                                    locationID) + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)<=ShiftMargin)"
                                Intime = DB.selectAllData(query)
                                todayintime = len(Intime)
                                query2 = "select A.EmpId,convert(D.ShiftMargin,char) AS ShiftMargin from ActivityDetails as A, EmployeeRegistration as B, BaseLocation as C, ShiftMaster as D, EmployeeShiftHistory AS F where A.EmployeeShiftHistoryId IN(select E.EmployeeShiftHistoryId from EmployeeShiftHistory as E where E.StartDate='" + extractDate + "' and E.LicKey='" + LicKey + "') and A.EmpId=B.EmpId and A.BaseLocationId=C.BaseLocationId and A.ShiftMasterId=D.ShiftMasterId and A.LicKey='" + LicKey + "' and A.ShiftMasterId='" + str(
                                    ShiftMasterId) + "'  and A.BaseLocationId='" + str(
                                    locationID) + "' group by A.EmployeeShiftHistoryId having (convert(min(A.ADTime),TIME)>ShiftMargin)"
                                Latecoming = DB.selectAllData(query2)
                                countLateEmployee = len(Latecoming)
                                singleDateDataResponse = {'todayintime': todayintime, 'month': month,
                                                          'day': extractDate, 'LateEmployee': countLateEmployee}
                                singleDayWiseData.append(singleDateDataResponse)
                    # shiftwisedata = {'ShiftMasterId': ShiftMasterId, 'ShiftName': ShiftName,'ResponseData': singleDayWiseData}
                    # shiftArrayData.append(shiftwisedata)
                locationwisedata = {'BaseLocationId': locationID, 'LocationName': locationName,
                                    'TotalWeekData': singleDayWiseData}  # ,'shiftList': shiftArrayData
                locationArrayData.append(locationwisedata)
            response = {'category': "1", 'message': "Latecoming and Intime Employee Info",
                        "ResponseData": locationArrayData}
            response = make_response(jsonify(response))
            return response


# GET USER ACCESS TOKEN
class RcAPIUsersession(Resource):
    def post(self):
        requestData = request.get_json()
        if not requestData: return {'status': 1001, 'message': "Request parameter require."}
        if len(requestData) > 1: return {'status': 1002, 'message': "Too many request parameters."}
        licKey = ''
        if 'licKey' in requestData:
            licKey = requestData['licKey']
        if (licKey.isspace() == True or licKey == ''):
            response = {'status': 1003, 'message': "parameters are missing. Please provide them."}
        else:
            licKey = licKey.strip()
            apiQuery = "SELECT * from apiusersession where LicKey='" + licKey + "' "
            apiData = DB.selectAllData(apiQuery)

            if len(apiData) > 0:
                response = {"errorNo": "0", 'status': 2000, 'message': "Api User Session Details.",
                            'responseData': apiData}
            else:
                response = {"errorNo": "1", 'status': 3000, 'message': "Data not found !"}
        response = make_response(jsonify(response))
        return response

    # Multi Camera List


class CameraList(Resource):
    def get(self):
        verifiedUser = authVerifyUser.checkAuthenticate()
        if verifiedUser['authenticate'] == "False":
            return verifiedUser
        else:
            licKey = verifiedUser['LicKey']
            requestData = request.get_json()
            if requestData:  return {'status': 1001, "errorNo": "1", 'message': "Too many request parameters."}
            if (licKey.isspace() == True or licKey == ''):
                response = {'status': 1002, "errorNo": "1", 'message': "parameters are missing. Please provide them."}

            else:
                multiCameraQuery = "select * from Camera ORDER BY CameraId ASc"
                multiCamera = DB.selectAllData(multiCameraQuery)
                if len(multiCamera) > 0:
                    response = {"status": 2000, 'errorNo': "0", 'message': "List  of cameras.",
                                'responseData': multiCamera}
                else:
                    response = {"status": 3000, 'errorNo': "1", 'message': "No data available !"}
            response = make_response(jsonify(response))
            return response


# API URL
api.add_resource(Welcomedash, '/')
api.add_resource(RcAPILogin, '/login')
api.add_resource(RcAPIDashboardSEC, '/dashboard')
api.add_resource(RcAPIAbsentPresentLocationAndShiftWise, '/present-absent-location-shift-wise')
api.add_resource(RcAPIDashboardLateComingShiftwise, '/latecoming-intime-location-shift-wise')
api.add_resource(RcAPIPresentEmployee, '/present-employee')
api.add_resource(RcAPIAbsentEmployee, '/absent-employee')
api.add_resource(RcAPILateComing, '/latecoming')
api.add_resource(RcAPIRegistration, '/registration')
api.add_resource(RcAPIEMailVarification, '/email-send/<string:MasterId>')
# NEW(ShiftWise-Requirements)
api.add_resource(ShiftWiseDashboardCount, '/shift-wise-total-count')
api.add_resource(ShiftWiseAbsentEmployee, '/shift-wise-absent-report')
api.add_resource(AbsentPresentGraph, '/total-absent-present-graph')
api.add_resource(LateComingInTimeGraph, '/total-latecoming-intime-graph')

# EMPLOYEE
api.add_resource(RcAPIActiveMultiEmployee, '/employees')
api.add_resource(RcAPIMultiEmployee, '/allemployees')
api.add_resource(RcAPIEmployeeVerify, '/employee-verify/<string:MasterId>')
api.add_resource(RcAPIEmployee, '/employee/<string:MasterId>')
api.add_resource(RcAPIEmployeeInfo, '/employee-info/<string:MasterId>')
api.add_resource(RcAPIRestoreEmployeeProfile, '/restore-employee-profile/<string:MasterId>')
api.add_resource(RcAPIEmployeeStatus, '/employee-status/<string:MasterId>')
api.add_resource(RcAPIDeleteStatus, '/employee-temp-delete/<string:MasterId>')
api.add_resource(RcAPIDeleteEmployee, '/employee-permanent-delete')
api.add_resource(RcAPIEmployeeCSVUpload, '/employee-bulk-upload')
api.add_resource(RcAPIDeletedEmployeeList, '/delete-employees-list')
# LOCATIONS
api.add_resource(RcAPIMultiLocation, '/locations')
api.add_resource(RcAPILocation, '/location/<string:MasterId>')
# PROFILE
api.add_resource(RcAPIProfile, '/profile')
api.add_resource(RcAPIUpdateProfile, '/profile-info')
api.add_resource(RcAPIAdminProfile, '/admin-profile')
api.add_resource(RcAPIUserProfile, '/user-profile')
api.add_resource(RcAPIChangePassword, '/change-password')
api.add_resource(RcAPIOldPassword, '/password-verify')
api.add_resource(RcAPIDeleteEmployeeImage, '/delete-emp-image')
# ENROLLMENT
api.add_resource(RcAPIGetMultipleEnroll, '/get-enrolls')
api.add_resource(RcAPIEnroll, '/enroll/<string:MasterId>')
api.add_resource(RcAPIEnrollEmployeeDetails, '/enroll-emp-details/<string:MasterId>')
api.add_resource(RcAPIDeleteEnrolldEmployee, '/delete-enroll-employee/<string:MasterId>')
# REPORT
api.add_resource(RcAPIDailyReport, '/daily-report')
api.add_resource(RcAPIRecentReport, '/recent-report')
api.add_resource(RcAPIAllActivityReport, '/allactivity-report')
api.add_resource(RcAPISingleTimesheetDelete, '/single-timesheet-delete')
api.add_resource(RcAPISingleTimesheetSwapping, '/single-timesheet-move')
api.add_resource(RcAPIDailyRecentImages, '/recentimages/<string:MasterId>')
api.add_resource(RcAPISingleTimesheet, '/single-timesheet/<string:MasterId>')
api.add_resource(RcAPIUserReport, '/user-report')
api.add_resource(RcAPICheckInOut, '/checkinout')
api.add_resource(RcAPICheckInOutDetails, '/checkinoutdetails')
api.add_resource(RcAPIAttendanceInfo, '/attendance-info')
api.add_resource(RcAPIMonthlyListHourWiseReport, '/monthly-report-hourwise')
api.add_resource(RcAPIMonthlySummaryReport, '/monthly-summary-report')
api.add_resource(RcAPIMonthlyReportHourWise, '/monthly-report-hour-wise')
api.add_resource(RcAPIMonthlyReportDaywise, '/monthly-report-day-wise')
api.add_resource(RcAPIMonthlyCornJob, '/month-clone')
api.add_resource(ShiftWiseDailyReport, '/shift-wise-daily-report')
# CAMERA
api.add_resource(RcAPIMultipleCameraList, '/cameras')
api.add_resource(RcAPICameraDetails, '/camera/<string:MasterId>')
api.add_resource(RcAPIOrganizationDetails, '/organization-details')
api.add_resource(RcAPICountryDetails, '/country-details')
# ASSIGN SHIFT
api.add_resource(RcAPIEmployeeShiftHistory, '/assignshift/<string:MasterId>')
api.add_resource(RcAPIGetEmployeeShiftHistory, '/get-employee-shift-history')
api.add_resource(RcAPIGetMultiShifthistory, '/employee-shift-mapping')
api.add_resource(RcAPIEmployeeShiftList, '/employee-shift-list/<string:MasterId>')
api.add_resource(RcAPIGetShiftsLocationWise, '/get-shift-locationwise/<string:MasterId>')
api.add_resource(RcAPIEmployeeListLocationWise, '/get-employee-locationwise/<string:MasterId>')
# SHIFT
api.add_resource(RcAPIGetMultiShift, '/shifts')
api.add_resource(RcAPIShift, '/shift/<string:MasterId>')
# HOLIDAY
api.add_resource(RcAPIMultiHoliday, '/holidays')
api.add_resource(RcAPIHoliday, '/holiday/<string:MasterId>')
api.add_resource(RcAPIHolidayStatus, '/holiday-status/<string:MasterId>')
# LEAVE
api.add_resource(RcAPIMultiLeave, '/leaves')
api.add_resource(RcAPILeave, '/leave/<string:MasterId>')
api.add_resource(RcAPILeaveStatus, '/leave-status')
# COMPOFF LEAVE
api.add_resource(RcAPIMultiCompoffleave, '/compoffleaves')
api.add_resource(RcAPICompoffleave, '/compoffleave/<string:MasterId>')
api.add_resource(RcAPICompOffLeaveStatus, '/compoff-leave-status')
# WEEKEND DETAILS
api.add_resource(RcAPIGetWeekendDetails, '/get-weekends')
api.add_resource(RcAPIWeekendDetails, '/weekends')
api.add_resource(RcAPIWeekendLocation, '/weekend-location')
api.add_resource(RcAPIWeekendShift, '/weekend-shift')
api.add_resource(RcAPIWeekendShiftDetails, '/weekend-shiftdetails')
api.add_resource(RcAPIGetMultiWeekendDetails, '/weekenddetails')
api.add_resource(RcAPIWeekendDays, '/weekenddays')
# Add,update,get & delete USER
api.add_resource(RcAPIGetMultiUserDetails, '/userdetails')
api.add_resource(RcAPIGetLocationWiseMultiUserDetails, '/location-wise-userdetails/<string:MasterId>')
api.add_resource(RcAPIUserStatus, '/user-status/<string:MasterId>')
api.add_resource(RcAPIUserDetails, '/userdetail/<string:MasterId>')
api.add_resource(RcAPIGetUser, '/get-user/<string:MasterId>')
# USER ACCESS
api.add_resource(RcAPIGetUserPrivelegeDetails, '/user-privelege-details')
api.add_resource(RcAPIGetUserPrivelegeSubMenu, '/user-privelege-submenu')
api.add_resource(RcAPIUserAccess, '/user-access/<string:MasterId>/<string:MenuId>/<string:SubMenuId>')
api.add_resource(RcAPIMenu, '/menu')
api.add_resource(RcAPISubmenu, '/submenu/<string:MasterId>')
# user Profile
api.add_resource(RcAPIUserChangePassword, '/user-change-password')
api.add_resource(RcAPIUserInfo, '/user-Info')
api.add_resource(RcAPIUserOldPassword, '/user-password-verify')
api.add_resource(RcAPIUserPageAccess, '/get-user-privelege')
# Language
api.add_resource(RcAPILanguage, '/language')
api.add_resource(RcAPISelectLanguage, '/select-language')
# Zoho
api.add_resource(RcAPZOHODataList, '/zoho-list')
api.add_resource(RcAPZOHORequest, '/zoho-request/<string:MasterId>')
api.add_resource(RcAPIMonthlySummeryList, '/monthly-summery-list')
api.add_resource(RcAPIUserHistory, '/UserHistory/<string:MasterId>')
# Services for middleware
api.add_resource(RcServicesInsertActivityDetails, '/insert-activity-details')
api.add_resource(RcServicesGetEncodingsSets, '/get-encodings-sets')
api.add_resource(RcAPIMonthlyClone, '/monthly-clone')
# Geofence Area
api.add_resource(RcAPIMultiGeofenceArea, '/geofenceareas')
api.add_resource(RcAPIGeofenceArea, '/geofencearea/<string:MasterId>')
api.add_resource(RcAPIGeofenceCheckMeOut, '/geofence-check-me-out/<string:MasterId>')
# Mobile Api
api.add_resource(RcAPIMobileLocationList, '/mobilelocationlist')
api.add_resource(RcAPIMobileShiftList, '/mobileshiftlist')
api.add_resource(RcAPIMobileDashboard, '/mobiledashboard')
api.add_resource(RcAPIMobLocationShiftEmployees, '/location-shift-employees')
api.add_resource(RcAPIMobilePresentEmployee, '/mobile-present-employee')
api.add_resource(RcAPIMobileLateComing, '/mobile-latecoming')
api.add_resource(RcAPIMobileAbsentEmployee, '/mobile-absent-employee')
api.add_resource(RcAPIMobileUserPrivilegeDetails, '/mobile-userprivilege-details')
api.add_resource(RcAPIMobileUpdateProfile, '/mobile-profile-info')
api.add_resource(RcAPIMobileAdminProfile, '/mobile-organization-logo')
api.add_resource(RcAPIMobileForgotPassword, '/mobile-forgot-password')
api.add_resource(RcAPIMobileResetPassword, '/mobile-reset-password')
# Mobile-Report
api.add_resource(RcAPIMobileSingleTimesheet, '/mobile-single-timesheet/<string:MasterId>')
api.add_resource(RcAPIMobileAllActivityReport, '/mobile-allactivity-report')
api.add_resource(RcAPIMobileAttendanceInfo, '/mobile-attendance-info')
api.add_resource(RcAPIMobileMonthlyReportDaywise, '/mobile-monthly-report-day-wise')
api.add_resource(RcAPIMobileMonthlyReportHourWise, '/mobile-monthly-report-hour-wise')
api.add_resource(RcAPIMobileEnroll, '/mobile-enroll/<string:MasterId>')

# Mobile-PDF AND EXCEL Generation
api.add_resource(RcAPIMultiEmployeeExcel, '/employees-excel')
api.add_resource(RcAPIMultiEmployeePdf, '/employees-pdf')
api.add_resource(RcAPIMobileGetMultiShiftPDF, '/shifts-pdf')
api.add_resource(RcAPIMobileMultiShiftExcel, '/shifts-excel')
api.add_resource(RcAPIMobileGetMultiShiftMappingPDF, '/shift-mapping-pdf')
api.add_resource(RcAPIMobileGetMultiShiftMappingEXCEL, '/shift-mapping-excel')
api.add_resource(RcAPIMobileGetMultiUserDetailsPDF, '/users-pdf')
api.add_resource(RcAPIMobileGetMultiUserDetailsExcel, '/users-excel')
api.add_resource(RcAPILocationExcel, '/locations-excel')
api.add_resource(RcAPILocationPdf, '/locations-pdf')
api.add_resource(RcAPICompoffPdf, '/compoffleaves-pdf')
api.add_resource(RcAPICompoffExcel, '/compoffleaves-excel')
api.add_resource(RcAPILeavePdf, '/leaves-pdf')
api.add_resource(RcAPILeaveExcel, '/leaves-excel')
api.add_resource(RcAPIMobileRecentReportPdf, '/recent-report-pdf')
api.add_resource(RcAPIMobileRecentReportExcel, '/recent-report-excel')
api.add_resource(RcAPIMobileDailyReportPdf, '/daily-report-pdf')
api.add_resource(RcAPIMobileDailyReportExcel, '/daily-report-excel')
api.add_resource(RcAPIHolidayPdf, '/holidays-pdf')
api.add_resource(RcAPIHolidayExcel, '/holidays-excel')
api.add_resource(RcAPIGeofenceAreaExcel, '/geofenceareas-excel')
api.add_resource(RcAPIGeofencePdf, '/geofenceareas-pdf')
# PrameetCode
api.add_resource(RcAPIGetEncodings, '/get-encodings')
api.add_resource(RcAPIInsertActivityDetails, '/insert-activity-details')
# API Documents
api.add_resource(RcAPIMultiAPICreateDocument, '/api-documents')
api.add_resource(RcAPICreateDocument, '/api-document/<string:MasterId>')

# By IN_OI01_052 Dt-19-01-21
api.add_resource(RcAPIProjects, '/projects')
api.add_resource(RcAPIModules, '/modules')
api.add_resource(RcAPIGetModules, '/get-modules/<string:MasterId>')
api.add_resource(RcAPIGetApiDocuments, '/api-documents/<string:MasterId>')
api.add_resource(RcAPITempDeleteDocument, '/document-temp-delete/<string:MasterId>')
api.add_resource(RcAPIPermanentDeleteDocument, '/document-permanent-delete/<string:MasterId>')
api.add_resource(RcAPIDocumentStatus, '/document-status/<string:MasterId>')
api.add_resource(RcAPIFCMTokenList, '/fcmmessage/<string:MasterId>')
# User API Documents
# By IN_OI01_052 Dt-21-01-21
api.add_resource(RcAPIUserProjects, '/user-projects')
api.add_resource(RcAPIUserModules, '/user-modules')
api.add_resource(RcAPIGetUserModules, '/get-user-modules/<string:MasterId>')
api.add_resource(RcAPIUserApiDocuments, '/user-api-documents/<string:MasterId>')
api.add_resource(RcAPIUserDocument, '/user-single-apidocuments/<string:MasterId>')
api.add_resource(RcAPILogout, '/logout')
# NEW API FOR WEB
api.add_resource(RcAPIMultiEmployeeRestore, '/restore-multiemp')
api.add_resource(RcAPIMultiEmployeeDelete, '/permanent-multiemp-delete')
# For mobile Notification
api.add_resource(RcAPINotification, '/notification/<string:MasterId>')
api.add_resource(RcAPIMultiNotification, '/notification')
api.add_resource(RcAPIUserListLocationWise, '/get-user-locationwise/<string:MasterId>')
api.add_resource(RcAPIGetEmployeeShiftMapping, '/get-employee-shift-mapping')
# BackendServiceAPI
api.add_resource(ReverseLog, '/reverselog')
api.add_resource(RcAPIUsersession, '/get-usersession')
api.add_resource(CameraList, '/camera-details')
# new enterprise api
api.add_resource(AddUpdateCamera, '/enterprise-camera/<string:MasterId>')
api.add_resource(ActiveDeactiveCamera, '/enterprise-camera-status/<string:MasterId>')
api.add_resource(EnterpriseCameraList, '/enterprise-camera-list')
api.add_resource(DailyIncidentReport, '/daily-incident-report')
api.add_resource(RecentIncidentReport, '/recent-incident-report')
api.add_resource(ThresholdPoints, '/insert-threshold')
api.add_resource(ContactTracing, '/contact-tracing')
api.add_resource(ThresholdtReport, '/threshold-details')
api.add_resource(LoadIncidentActivity, '/insert-incident-activity')
# api.add_resource(RcAPIGetEmployeeShiftMapping, '/get-employee-shift-mapping')
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5018, debug=True)
