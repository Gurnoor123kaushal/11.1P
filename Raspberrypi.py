import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import tkinter as tk
import threading

# MQTT broker and topic details
broker = "broker.hivemq.com"
topic = "Home/SensorData"

# GPIO setup
alert_pin = 17  # Change this to the GPIO pin you want to use
GPIO.setmode(GPIO.BCM)
GPIO.setup(alert_pin, GPIO.OUT)
GPIO.output(alert_pin, GPIO.LOW)  # Set pin to LOW initially

# Temperature threshold
TEMP_THRESHOLD = 30.0  # Adjust this to your desired threshold

# GUI setup
root = tk.Tk()
root.title("Sensor Monitoring")
root.geometry("400x400")  # Adjusted for additional sensor data

# Create labels to display sensor values
temperature_label = tk.Label(root, text="Temperature: -- C", font=("Helvetica", 14))
temperature_label.pack()

humidity_label = tk.Label(root, text="Humidity: -- %", font=("Helvetica", 14))
humidity_label.pack()

light_level_label = tk.Label(root, text="Light: -- lx", font=("Helvetica", 14))
light_level_label.pack()

soil_moisture_label = tk.Label(root, text="Soil Moisture: -- %", font=("Helvetica", 14))
soil_moisture_label.pack()

co2_level_label = tk.Label(root, text="CO₂: -- ppm", font=("Helvetica", 14))
co2_level_label.pack()

smoke_level_label = tk.Label(root, text="Smoke Level: -- %", font=("Helvetica", 14))
smoke_level_label.pack()

# Add a label for alert status
alert_label = tk.Label(root, text="Alert: --", font=("Helvetica", 16))
alert_label.pack()

def on_message(client, userdata, msg):
    data = msg.payload.decode()
    print(f"Received sensor data: {data}")  # Print the raw data for debugging

    try:
        # Parse sensor data assuming it is in the format "Temperature: 25.5, Humidity: 60%, ..."
        parts = data.split(',')
        
        # Find each data point, ensuring to strip extra spaces and parse values correctly
        temperature_str = next((item.split(":")[1].strip() for item in parts if "Temperature" in item), None)
        humidity_str = next((item.split(":")[1].strip() for item in parts if "Humidity" in item), None)
        light_level_str = next((item.split(":")[1].strip() for item in parts if "Light" in item), None)
        soil_moisture_str = next((item.split(":")[1].strip() for item in parts if "Soil Moisture" in item), None)
        co2_level_str = next((item.split(":")[1].strip() for item in parts if "CO₂" in item), None)
        smoke_level_str = next((item.split(":")[1].strip() for item in parts if "Smoke Level" in item), None)

        # Remove '%' symbol or other extra characters before converting to float
        humidity_str = humidity_str.replace('%', '') if humidity_str else None
        soil_moisture_str = soil_moisture_str.replace('%', '') if soil_moisture_str else None
        smoke_level_str = smoke_level_str.replace('%', '') if smoke_level_str else None

        # Convert values to floats if available
        temperature = float(temperature_str) if temperature_str else None
        humidity = float(humidity_str) if humidity_str else None
        light_level = float(light_level_str) if light_level_str else None
        soil_moisture = float(soil_moisture_str) if soil_moisture_str else None
        co2_level = float(co2_level_str) if co2_level_str else None
        smoke_level = float(smoke_level_str) if smoke_level_str else None

        # Update GUI with received values
        if temperature is not None:
            temperature_label.config(text=f"Temperature: {temperature} C")
        if humidity is not None:
            humidity_label.config(text=f"Humidity: {humidity} %")
        if light_level is not None:
            light_level_label.config(text=f"Light: {light_level} lx")
        if soil_moisture is not None:
            soil_moisture_label.config(text=f"Soil Moisture: {soil_moisture} %")
        if co2_level is not None:
            co2_level_label.config(text=f"CO₂: {co2_level} ppm")
        if smoke_level is not None:
            smoke_level_label.config(text=f"Smoke Level: {smoke_level} %")

        # Check if temperature exceeds the threshold and update the GPIO pin
        if temperature is not None and temperature > TEMP_THRESHOLD:
            GPIO.output(alert_pin, GPIO.HIGH)
            alert_label.config(text="Alert: Temperature threshold exceeded!", fg="red")
            print("Temperature threshold exceeded! GPIO pin set to HIGH.")
        else:
            GPIO.output(alert_pin, GPIO.LOW)
            alert_label.config(text="Alert: Temperature is normal.", fg="green")
            print("Temperature below threshold. GPIO pin set to LOW.")
            
    except (ValueError, IndexError) as e:
        print(f"Error parsing sensor data: {e}")
        alert_label.config(text="Error parsing data!", fg="orange")

# Initialize MQTT client
client = mqtt.Client()
client.connect(broker, 1883)

# Assign callback function
client.on_message = on_message

# Subscribe to the topic
client.subscribe(topic)

# Start listening for incoming messages
print("Listening for sensor data...")

def run_mqtt():
    client.loop_forever()

mqtt_thread = threading.Thread(target=run_mqtt)
mqtt_thread.daemon = True
mqtt_thread.start()

# Run the GUI
root.mainloop()

# Clean up GPIO when GUI window is closed
GPIO.cleanup()
