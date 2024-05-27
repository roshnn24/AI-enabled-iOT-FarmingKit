from flask import Flask, render_template, request, jsonify
import pymysql
import matplotlib.pyplot as plt
import io
import base64
app = Flask(__name__)
db = pymysql.connect(host="localhost", user="root", password="1234", database="tea_farm")
cursor = db.cursor()
# Dictionary to store sensor data
sensor_data = {
    'temperature': None,
    'humidity': None,
    'irValue': None,
    'distance': None
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/sensors')
def sensors():
    return render_template('sensors.html', sensor_data=sensor_data)

@app.route('/zones')
def zones():
    return render_template('zones.html')


@app.route('/activity-log')
def activity_log():
    # Fetch data for IR value distribution plot
    cursor.execute("SELECT ir_value FROM sensor_data")
    ir_values = cursor.fetchall()
    count_0 = ir_values.count((0,))
    count_1 = ir_values.count((1,))
    labels = ['Pest Swarm Detected', 'No Pest Swarm Detected']
    sizes = [count_0, count_1]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.title('IR Value Distribution')
    plt.axis('equal')
    ir_buffer = io.BytesIO()
    plt.savefig(ir_buffer, format='png')
    ir_buffer.seek(0)
    ir_plot_data = base64.b64encode(ir_buffer.getvalue()).decode('utf-8')
    plt.close()

    # Fetch data for average closeness of pests plot
    cursor.execute("SELECT timestamp, distance FROM sensor_data WHERE distance < 500")
    data = cursor.fetchall()
    timestamps = [row[0] for row in data]
    distances = [row[1] for row in data]
    average_distance = sum(distances) / len(distances)
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, distances, marker='o', linestyle='-')
    plt.xlabel('Timestamp')
    plt.ylabel('Distance (cm)')
    plt.title('Average Closeness of Pests over Time')
    plt.xticks(rotation=45)
    plt.grid(True)
    distance_buffer = io.BytesIO()
    plt.savefig(distance_buffer, format='png')
    distance_buffer.seek(0)
    distance_plot_data = base64.b64encode(distance_buffer.getvalue()).decode('utf-8')
    plt.close()

    return render_template('activity-log.html', ir_plot_data=ir_plot_data, distance_plot_data=distance_plot_data)

@app.route('/sensor-data', methods=['POST'])
def update_sensor_data():
    global sensor_data
    data = request.get_json()
    sensor_data['temperature'] = data.get('temperature')
    sensor_data['humidity'] = data.get('humidity')
    sensor_data['irValue'] = data.get('irValue')
    sensor_data['distance'] = data.get('distance')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    ir_value = data.get('irValue')
    distance = data.get('distance')
    sql = "INSERT INTO sensor_data (temperature, humidity, ir_value, distance) VALUES (%s, %s, %s, %s)"
    val = (temperature, humidity, ir_value, distance)
    cursor.execute(sql, val)
    db.commit()
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
