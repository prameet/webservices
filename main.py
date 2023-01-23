# IMPORTS
import base64
import os
import time
from datetime import datetime
from decimal import Decimal
import face_recognition
import pymysql
from flask import Flask, request, jsonify, make_response
import logging
from flask_cors import CORS
from flask_restful import Resource, Api
import binascii
import picket
from pytz import timezone
import os.path
from os import path
import cv2
import numpy as np

# GLOBAL VARIABLES
global known_face_encodings
global known_face_names
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
app = Flask(__name__)
CORS(app)
# PREFIX FOR API
api = Api(app, prefix="/V1/API")


# CLASS 'conf' IS FOR DATABASE CONNECTION
class conf():
    @staticmethod
    def connect():
        connection = pymysql.connect(host='localhost', user='root', password='',
                                     db='app_data',
                                     charset='utf8mb4',

                                     cursorclass=pymysql.cursors.DictCursor)

        return connection


# HERE CLASS DB IS DEFINED FOR  SQL CRUD OPERATION
class DB():
    @staticmethod
    # FUNCTION FOR EXECUTION OF GROUP BY SQL QUERRY
    def retrieveData(retriveQuery):
        connection = conf.connect()
        cursor = connection.cursor()
        sqlData = retriveQuery
        try:
            cursor.execute(sqlData)
            rowcount = cursor.fetchall()
            connection.commit()
            cursor.close()
            connection.close()
            return rowcount
        except Exception as e:
            logger.exception('pymysql.Warning in retrive data')
            responseReturn = {"messageType": 'error', "messagetext": e}
            return responseReturn

    # FUNCTION FOR DELETE SINGLE ROW
    def deleteSingleRow(deletequrry):
        connection = conf.connect()
        cursor = connection.cursor()
        sqlData = deletequrry
        try:
            cursor.execute(sqlData)
            connection.commit()
            cursor.close()
            connection.close()
            message = "success"
            responseReturn = {"messageType": 'success', "messagetext": message}
            return responseReturn
        except (pymysql.Error, pymysql.Warning) as e:
            logger.exception('pymysql.Warning in deleteSingleRow data')
            responseReturn = {"messageType": 'error', "messagetext": e}
            return responseReturn

        # FUNCTION FOR UPDATE DATA

    def updateData(updatequrry):
        connection = conf.connect()
        cursor = connection.cursor()
        sqlData = updatequrry

        try:
            cursor.execute(sqlData)
            connection.commit()
            cursor.close()
            connection.close()
            message = "success"
            responseReturn = {"messageType": 'success', "messagetext": message}
            return responseReturn
        except (pymysql.Error, pymysql.Warning) as e:
            logger.exception('pymysql.Warning in updateData data')
            responseReturn = {"messageType": 'error', "messagetext": e}
            return responseReturn

    # FUNCTION FOR DIRECT INSERT DATA
    def insertData(insertqurry):
        connection = conf.connect()
        cursor = connection.cursor()
        sqlData = insertqurry
        try:
            cursor.execute(sqlData)
            connection.commit()
            lastInsertId = cursor.lastrowid
            cursor.close()
            connection.close()
            message = "success"
            responseReturn = {"messageType": 'success',
                              "messagetext": message, 'lastInsertId': lastInsertId}
            return responseReturn
        except (pymysql.Error, pymysql.Warning) as e:
            logger.exception(' pymysql.Warning in fetching data')
            responseReturn = {"messageType": 'error',
                              "messagetext": e, 'lastInsertId': '0'}
            return responseReturn





# CLASS FOR ENROLL EMPLOYEE
class APIEnrollEmplloyee(Resource):
    def check_div(self, base_location, div_id):
        status = False
        QsGetLocationDetails = "SELECT * FROM base_location as BL Where BL.id='" + \
                               base_location + "' AND BL.div_id ='" + div_id + "'"

        RsGetLocationDetails = DB.retrieveData(QsGetLocationDetails)
        if len(RsGetLocationDetails) != 0:
            status = True
        else:
            status = False
        return status

    def post(self):
        req_data = request.get_json()

        if (req_data):
            emp_id = req_data['EmployeeId']
            lic_key = req_data['LicKey']
            emp_name = req_data['EmployeeName']
            div_id = req_data['DivisionID']
            employee_location_id = req_data['EmployeeLocationId']
            div_status = self.check_div(employee_location_id, div_id)
            image_64_encodedata = req_data['SuppliedImageString']

            image_64_encode = bytes(image_64_encodedata, 'utf-8')
            image_64_decode = base64.decodestring(image_64_encode)
            now = datetime.now()
            filename = now.strftime('%Y%m%d%H%M%S')
            savefilefulldirCreate = '../public/face-video/' + \
                                    str(lic_key) + '/' + emp_id
            savefilefulldir = '../public/face-video/' + str(lic_key) + '/' + emp_id + '/' + str(
                filename) + ".png"
            savefilepath = 'public/face-video/' + \
                           str(lic_key) + '/' + emp_id + \
                           '/' + str(filename) + ".png"
            if not os.path.exists(savefilefulldirCreate):
                os.makedirs(savefilefulldirCreate)
            if div_status == True:
                if image_64_encode:
                    # create a writable image and write the decoding result
                    image_result = open(savefilefulldir, 'wb')
                    image_result.write(image_64_decode)
                    known_face_encodings = []
                    name1 = emp_id + "_" + emp_name
                    c1 = face_recognition.load_image_file(savefilefulldir)
                    c2 = face_recognition.face_encodings(c1)
                    if len(c2) > 0:
                        c2 = c2[0]
                    known_face_encodings.append(c2)
                    str_loop = "NULL,'" + emp_id + "','" + emp_name + "','1','" + lic_key + "'" + "," + "'" + str(
                        savefilepath) + "'" + ","
                    n = len(c2)
                    for j in range(len(c2)):
                        if j < 127:
                            str_loop += (str(c2[j])) + ","
                        else:
                            str_loop += str(c2[j])
                    if employee_location_id and div_id:
                        str_loop += "," + employee_location_id + "," + div_id + ""
                    else:
                        str_loop += ",1"

                    if (n > 0):
                        sqlEnrollUser = "INSERT INTO `dataset_encodings`  VALUES (" + \
                                        str_loop + ")"
                        showmessage = DB.insertData(sqlEnrollUser)
                        if showmessage['messageType'] == 'success':
                            category = "1"
                            msg = "Employee enrolled successfully for " + emp_name + "."
                            path = "http://localhost/WEB-Dashboard/" + savefilepath
                            responce = {'category': category,
                                        'message': msg, 'path': path}
                        else:
                            category = "0"
                            msg = "Please check your file again."
                            responce = {'category': category, 'message': msg}
                    else:
                        category = "0"
                        msg = "Please check your file again."
                        responce = {'category': category, 'message': msg}
            else:
                category = "0"
                msg = "Sorry! Wrong division."
                responce = {'category': category, 'message': msg}
        else:
            category = "0"
            msg = "Sorry! Not a valid enrollment"
            responce = {'category': category, 'message': msg}

        return responce

    def is_base64(self, string):
        try:
            base64.decodestring(string)
            return True
        except binascii.Error:
            return False


# CLASS FOR DELETE ENROLLED DATA FOR EMPLOYEE
class APIDeleteEnrollEmplloyee(Resource):
    def post(self):

        req_data = request.get_json()
        if (req_data):

            if 'Employee_Id' in req_data:
                session_lickey = req_data['Lic_key']
                edited_id = req_data['Record_id']
                get_record_query = "SELECT * FROM `dataset_encodings` where ID='" + edited_id + "'"
                result_get_record = DB.retrieveData(get_record_query)
                if len(result_get_record) != 0:
                    FilePath = result_get_record[0]['path']
                    FilePath = "../" + FilePath

                    if path.exists(FilePath):

                        os.remove(FilePath)
                        delete_enroll_statement = "delete from dataset_encodings where ID='" + \
                                                  edited_id + "' and lic_key = '" + session_lickey + "'"

                        showmessage = DB.deleteSingleRow(delete_enroll_statement)
                        if showmessage['messageType'] == 'success':
                            category = "1"
                            msg = "Congratulation! your employee enrolled data deleted successfully."
                            resp = {'category': category, 'message': msg}

                        else:
                            category = "0"
                            msg = "Sorry, something wrong happened."
                            resp = {'category': category, 'message': msg}

                    else:
                        category = "0"
                        msg = "Sorry, file does not exists."
                        resp = {'category': category, 'message': msg}

                else:
                    category = "0"
                    msg = "Sorry, Nothing found to delete."
                    resp = {'category': category, 'message': msg}

                responce_data = make_response(jsonify(resp))

                return responce_data


# CLASS FOR RECOGNITION OF EMPLOYEE
class APIEmpoyeeActivity(Resource):
    def check_geolocation(self, pointAlatitude, pointAlongitude, pointBlatitude, pointBlongitude, pointClatitude,
                          pointClongitude, pointDlatitude, pointDlongitude, userLat, userLong):

        my_fence = picket.Fence()

        my_fence.add_point((pointAlatitude, pointAlongitude))

        my_fence.add_point((pointBlatitude, pointBlongitude))
        my_fence.add_point((pointClatitude, pointClongitude))
        my_fence.add_point((pointDlatitude, pointDlongitude))

        return my_fence.check_point((userLat, userLong))

    def check_div(self, base_location, div_id):

        QsGetLocationDetails = "SELECT * FROM base_location as BL Where BL.id='" + \
                               base_location + "' AND BL.div_id ='" + div_id + "'"

        RsGetLocationDetails = DB.retrieveData(QsGetLocationDetails)
        if len(RsGetLocationDetails) != 0:
            status = True
        else:
            status = False
        return status

    def get_geo_address(self, lat_long):
        from geopy.geocoders import Nominatim
        from geopy.extra.rate_limiter import RateLimiter

        geolocator = Nominatim(user_agent="application")

        reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

        location = reverse((lat_long), language='en', exactly_one=True)

        return location

    def string_to_image(self, base64_string):
        image_data = base64.b64decode(base64_string)
        im_arr = np.frombuffer(image_data, dtype=np.uint8)  # im_arr is one-dim Numpy array
        img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)
        return img

    def post(self):
        request_data = request.get_json()
        if (request_data):
            indian_time_one = timezone('Asia/Kolkata')
            indian_time_now = datetime.now(indian_time_one)
            activity_time = indian_time_now.strftime('%Y-%m-%d %H:%M:%S')
            date = activity_time.split(" ")[0]
            lic_key = request_data['LicKey']
            current_location = request_data['CurrentLocation']
            employee_location_id = request_data['EmployeeLocationId']
            employee_division_id = request_data['DivisionID']
            supplied_image_string = request_data['SuppliedImageString']
            user_type = request_data['UserType']
            user_id = request_data['UserId']

            temporary_detected_image_path = '../public/images/thumb/' + \
                                            str(lic_key) + '/' + str(date)

            if not os.path.exists(temporary_detected_image_path):
                os.makedirs(temporary_detected_image_path)
            current_timestamp = int(time.time())

            string_to_cv2_read_image = self.string_to_image(supplied_image_string)

            net = cv2.dnn.readNetFromCaffe("deploy.prototxt.txt", "res10_300x300_ssd_iter_140000.caffemodel")
            (h, w) = string_to_cv2_read_image.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(string_to_cv2_read_image, (300, 300)), 1.0,
                                         (300, 300), (104.0, 177.0, 123.0))

            net.setInput(blob)
            detections = net.forward()
            employee_names = []
            emp_ids = []
            for i in range(0, detections.shape[2]):
                # print(i)
                confidence = detections[0, 0, i, 2]
                # print(confidence)
                if confidence > 0.5:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    # print(box)
                    (startX, startY, endX, endY) = box.astype("int")

                    text = "{:.2f}%".format(confidence * 100)
                    y = startY - 10 if startY - 10 > 10 else startY + 10
                    cv2.rectangle(string_to_cv2_read_image, (startX, startY), (endX, endY),
                                  (0, 0, 255), 2)
                    cv2.putText(string_to_cv2_read_image, text, (startX, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
                    roi = string_to_cv2_read_image[startY:endY, startX:endX]
                    cv2.imwrite(temporary_detected_image_path + "/" + str(i) + '.png', roi)

                    # print(temporary_detected_image_path + "/" + str(i) + '.png')
                    # calling recognize function to identify the image

                    result = self.recognize(
                        temporary_detected_image_path + "/" + str(i) + '.png', lic_key, user_type, user_id,
                        employee_location_id)

                    emp_id = result[0]
                    # employee_name = result[1]

                    if emp_id != False and emp_id != "unknown" and emp_id != "":

                        file_name = str(current_timestamp) + "_" + str(emp_id) + "_" + str(lic_key)
                        os.rename(temporary_detected_image_path + "/" + str(i) + '.png',
                                  temporary_detected_image_path + "/" + file_name + '.png')
                        # Condition can be applied if an organisation credentials being used for taking attendance or user login
                        query_data = "INSERT INTO activitydetails (id, emp_id, location_id, time, date, employee_location, file_location, lic_key, div_id) VALUES (NULL,'" + str(
                            emp_id) + "','" + employee_location_id + "','" + activity_time + "','" + date + "','" + current_location + "','" + temporary_detected_image_path + "/" + file_name + '.png' + "','" + lic_key + "','" + employee_division_id + "')"
                        show_message = DB.insertData(query_data)
                        if show_message['messageType'] == 'success':
                            message = "Data inserted successfully for the employee or employees."
                            category = "1"

                            resp = {'category': category, 'message': message, "time_post": activity_time}
                            responce_data = make_response(jsonify(resp))
                    else:
                        message = "Did not found a match for the employee or employees."
                        category = "0"
                        resp = {'category': category, 'message': message}
                        os.remove(temporary_detected_image_path + "/" + str(i) + '.png')
                        responce_data = make_response(jsonify(resp))

        else:
            message = "Wrong request data."
            category = "0"
            resp = {'category': category, 'message': message}
            responce_data = make_response(jsonify(resp))
        return responce_data

    # PROCESS RECOGNITION
    def recognize(self, file_stream, lic_key, user_type, user_id, loc_id):
        if user_type != "" and user_type == "admin" or user_type == "userAdmin":
            fetch_data = "all"
        else:
            fetch_data = user_id
        if fetch_data == "all":
            sql = "SELECT * FROM `dataset_encodings` WHERE `lic_key` = '" + \
                  lic_key + "' and `is_active` = 1 and `emp_location`=" + loc_id + ""
        else:
            sql = "SELECT * FROM `dataset_encodings` WHERE `lic_key` = '" + lic_key + "' and EMPID = '" + \
                  fetch_data + "' and `is_active` = 1 and `emp_location`=" + loc_id + ""

        myresult = DB.retrieveData(sql)
        known_face_encodings = []
        known_face_empids = []
        known_names = []
        for x in myresult:
            emp_id = x['emp_id']
            emp_name = x['emp_name']
            str_loop = []

            for j in range(0, 128):
                dataId = 'C' + str(j)

                if j < 127:
                    str_loop.append(float(Decimal(x[dataId])))
                else:
                    str_loop.append(float(Decimal(x[dataId])))
            known_face_encodings.append(str_loop)
            known_face_empids.append(emp_id)
            known_names.append(emp_name)

        frame = face_recognition.load_image_file(file_stream)
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            results = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.48)
            match = None
            if True in results:
                match = known_face_empids[results.index(True)]
                empName = known_names[results.index(True)]
                insert_done = match

            else:
                insert_done = ""
                empName = ""
        result = []

        result.append(insert_done)
        result.append(empName)
        return result


api.add_resource(APIEnrollEmplloyee, '/enroll-employee')
api.add_resource(APIDeleteEnrollEmplloyee, '/delete-enroll')
api.add_resource(APIEmpoyeeActivity, '/mark-attendance')
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
