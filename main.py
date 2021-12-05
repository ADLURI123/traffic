from flask import Flask
import cv2
import numpy as np
import time
import pyrebase

app = Flask(__name__)

config = {
    "apiKey": "AIzaSyDuo1XxvB4Z7id_W7NmC84N5hDui74iv8Q",
    "authDomain": "trafficheatmap-329015.firebaseapp.com",
    "databaseURL": "https://trafficheatmap-329015-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "trafficheatmap-329015",
    "storageBucket": "trafficheatmap-329015.appspot.com",
    "messagingSenderId": "326976030499",
    "appId": "1:326976030499:web:33b9200e0ddfa44d74ae96",
    "measurementId": "G-ZP4XVWEJ5V",
    "serviceAccount": "ServiceAccountKey.json"
}

firebase_storage = pyrebase.initialize_app(config)
storage = firebase_storage.storage()
db = firebase_storage.database()


@app.route('/<int:rid>/<rdate>/<rtime>')
def home(rid, rdate, rtime):
    cap = cv2.VideoCapture("https://firebasestorage.googleapis.com/v0/b/trafficheatmap-329015.appspot.com/o/Recordings%2F" + str(rid) + "%2F" + rdate + "%2F" + rtime + ".mp4?alt=media&token=c567d077-249e-4a23-a9ba-cf592ed12b3f")
    offset = 6
    left_counter = 0
    right_counter = 0
    left_speed_sum = 0
    right_speed_sum = 0
    avg_left_speed = 0
    avg_right_speed = 0
    min_height = 80
    min_width = 80
    algo = cv2.bgsegm.createBackgroundSubtractorMOG()
    coord = [[25, 550], [1200, 550], [0, 650], [1250, 650]]
    dist = 2
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    seconds = int(frames / fps)


    while (cap.isOpened()):
        ret, frame1 = cap.read()
        try:
            grey = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(grey, (3, 3), 5)
            img_sub = algo.apply(blur)
            dilat = cv2.dilate(img_sub, np.ones((5, 5)))
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            dilatada = cv2.morphologyEx(dilat, cv2.MORPH_CLOSE, kernel)
            dilatada = cv2.morphologyEx(dilatada, cv2.MORPH_CLOSE, kernel)
            counterShape, h = cv2.findContours(dilatada, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            def center_handle(x, y, w, h):
                x1 = int(w / 2)
                y1 = int(h / 2)
                cx = x + x1
                cy = y + y1
                return cx, cy

            detect = []

            for (i, c) in enumerate(counterShape):
                (x, y, w, h) = cv2.boundingRect(c)
                validate_counter = (w >= min_width) and (h >= min_height)
                if not validate_counter:
                    continue
                center = center_handle(x, y, w, h)
                detect.append(center)
                for (x, y) in detect:
                    # left
                    if y < (coord[0][1] + offset) and y > (coord[0][1] - offset) and x < 650:
                        left_counter += 1
                        left_tim1 = time.time()
                    if y < (coord[2][1] + offset) and y > (coord[2][1] - offset) and x < 650:
                        left_tim2 = time.time()
                        left_speed_sum += dist / ((left_tim2 - left_tim1))
                    # right
                    if y < (coord[0][1] + offset) and y > (coord[0][1] - offset) and x >= 650:
                        right_counter += 1
                        right_tim2 = time.time()
                        right_speed_sum += dist / ((right_tim2 - right_tim1))
                    if y < (coord[2][1] + offset) and y > (coord[2][1] - offset) and x >= 650:
                        right_tim1 = time.time()
                    detect.remove((x, y))

        except Exception as e:
            break

    if (left_counter != 0):
        avg_left_speed = (left_speed_sum * 3.6) / left_counter
    if (right_counter != 0):
        avg_right_speed = (right_speed_sum * 3.6) / right_counter
    cap.release()
    avg_left_speed = round(avg_left_speed,2)
    avg_right_speed = round(avg_right_speed,2)
    data = {"left count": left_counter,"right count": right_counter,"left speed": avg_left_speed,"right speed": avg_right_speed,"time" : seconds}
    db.child(str(rid)+"-"+rdate+"-"+rtime).set(data)
    return str("Left count : " + str (left_counter) +" Right count : "+str(right_counter)+ " Left speed : "+str(avg_left_speed) +" Right speed : "+str(avg_right_speed)+" time : "+str(seconds))
if __name__ == "__main__":
    app.run()


