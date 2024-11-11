import threading
import numpy as np
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import tkinter as tk
import cv2

# GPIO and light sensor setup
light_sensor_pin = 18  # Change to the GPIO pin connected to your light sensor (LDR)
GPIO.setmode(GPIO.BCM)
GPIO.setup(light_sensor_pin, GPIO.IN)  # Read from the GPIO pin

# MQTT setup
broker = "broker.hivemq.com"
topic = "Home/SensorData"

# Temperature threshold
TEMP_THRESHOLD = 30.0

# GPIO setup for alert
alert_pin = 17
GPIO.setup(alert_pin, GPIO.OUT)
GPIO.output(alert_pin, GPIO.LOW)  # Set pin to LOW initially

# GUI setup
root = tk.Tk()
root.title("Sensor Monitoring System")
root.geometry("800x600")  # Larger window size

# Create labels for displaying data
temperature_label = tk.Label(root, text="Temperature: -- C", font=("Helvetica", 16))
temperature_label.pack()

humidity_label = tk.Label(root, text="Humidity: -- %", font=("Helvetica", 16))
humidity_label.pack()

smoke_level_label = tk.Label(root, text="Smoke Level: -- %", font=("Helvetica", 16))
smoke_level_label.pack()

light_level_label = tk.Label(root, text="Light Level: --", font=("Helvetica", 16))
light_level_label.pack()

alert_label = tk.Label(root, text="Alert: --", font=("Helvetica", 16))
alert_label.pack()

# Function to read light sensor data
def read_light_sensor():
    # Simulating the light sensor reading (can be replaced with real analog-to-digital conversion)
    light_level = GPIO.input(light_sensor_pin)
    light_level_percentage = 100 if light_level == GPIO.HIGH else 0
    return light_level_percentage

# MQTT Callback function
def on_message(client, userdata, msg):
    data = msg.payload.decode()
    print(f"Received sensor data: {data}")

    try:
        parts = data.split(',')
        
        temperature_str = next((item.split(":")[1].strip() for item in parts if "Temperature" in item), None)
        humidity_str = next((item.split(":")[1].strip() for item in parts if "Humidity" in item), None)
        smoke_level_str = next((item.split(":")[1].strip() for item in parts if "Smoke Level" in item), None)

        temperature = float(temperature_str) if temperature_str else None
        humidity = float(humidity_str) if humidity_str else None
        smoke_level = float(smoke_level_str) if smoke_level_str else None

        # Update labels in GUI
        if temperature is not None:
            temperature_label.config(text=f"Temperature: {temperature} C")
        if humidity is not None:
            humidity_label.config(text=f"Humidity: {humidity} %")
        if smoke_level is not None:
            smoke_level_label.config(text=f"Smoke Level: {smoke_level} %")

        # Light sensor data
        light_level = read_light_sensor()
        light_level_label.config(text=f"Light Level: {light_level}%")
        
        # Alert handling for temperature threshold
        if temperature is not None and temperature > TEMP_THRESHOLD:
            GPIO.output(alert_pin, GPIO.HIGH)
            alert_label.config(text="Alert: Temperature threshold exceeded!", fg="red")
        else:
            GPIO.output(alert_pin, GPIO.LOW)
            alert_label.config(text="Alert: Temperature is normal.", fg="green")
            
    except (ValueError, IndexError) as e:
        print(f"Error parsing sensor data: {e}")
        alert_label.config(text="Error parsing data!", fg="orange")

# Initialize MQTT client
client = mqtt.Client()
client.connect(broker, 1883)

# Assign callback function for MQTT
client.on_message = on_message
client.subscribe(topic)

# Start MQTT listener in a separate thread
def run_mqtt():
    client.loop_forever()

mqtt_thread = threading.Thread(target=run_mqtt)
mqtt_thread.daemon = True
mqtt_thread.start()

# OpenCV Setup for Object Detection
classNames = []
classFile = "/home/pi/Desktop/Object_Detection_Files/coco.names"
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

configPath = "/home/pi/Desktop/Object_Detection_Files/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "/home/pi/Desktop/Object_Detection_Files/frozen_inference_graph.pb"

net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Function for object detection
def getObjects(img, thres, nms, draw=True, objects=[]):
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    if len(objects) == 0: objects = classNames
    objectInfo = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in objects:
                objectInfo.append([box, className])
                if draw:
                    cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                    cv2.putText(img, classNames[classId - 1].upper(), (box[0] + 10, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(img, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
    return img, objectInfo

# Function to capture video and display object detection
def capture_video():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    while True:
        success, img = cap.read()
        result, objectInfo = getObjects(img, 0.45, 0.2)
        cv2.imshow("Output", img)
        cv2.waitKey(1)

# Start video capture in a separate thread
video_thread = threading.Thread(target=capture_video)
video_thread.daemon = True
video_thread.start()

# Run GUI
root.mainloop()

# Clean up GPIO when GUI window is closed
GPIO.cleanup()
