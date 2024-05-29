from flask import Flask, render_template, request, jsonify
#import pymysql
import matplotlib.pyplot as plt
import io
import base64
from gtts import gTTS
import os
app = Flask(__name__)
'''db = pymysql.connect(host="localhost", user="root", password="1234", database="tea_farm")
cursor = db.cursor()'''


UPLOAD_FOLDER = 'uploads'
OUTPUT_DIRECTORY = 'audio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_DIRECTORY):
    os.makedirs(OUTPUT_DIRECTORY)

# Text for pest and disease
pest_text = '''tea mosquito bugs,to get rid,spray with neem oil and garlic,use sticky traps, and trap crops like castor . Expect results in 2 to 4 weeks.চা মশার বাগ, পরিত্রাণ পেতে, নিম তেল এবং রসুন দিয়ে স্প্রে করুন, আঠালো ফাঁদ ব্যবহার করুন এবং ক্যাস্টরের মতো ফসল ফাঁদ করুন। 2-4 সপ্তাহের মধ্যে ফলাফল আশা করুন।'''
disease_text = '''Detected Disease: Brown Blight is a fungal disease To treat it spray a mix of baking soda, water and apply organic mulch to keep soil healthy.ব্রাউন ব্লাইট একটি ছত্রাকজনিত রোগের চিকিৎসার জন্য বেকিং সোডা, পানির মিশ্রণ স্প্রে করুন এবং মাটি সুস্থ রাখতে জৈব মালচ প্রয়োগ করুন'''
# Dictionary to store sensor data
sensor_data = {
    'temperature': None,
    'humidity': None,
    'irValue': None,
    'distance': None
}

@app.route('/home')
def home():
    return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    pest_filename = None
    disease_filename = None
    pest_audio_file = "pest.mp3"
    disease_audio_file = "disease.mp3"
    
    if request.method == 'POST':
        if 'pest_file' in request.files:
            pest_file = request.files['pest_file']
            if pest_file.filename != '':
                pest_filename = pest_file.filename
                pest_file.save(os.path.join(UPLOAD_FOLDER, pest_filename))
                tts_pest = gTTS(text=pest_text, lang='en', slow=False)
                tts_pest.save(os.path.join(OUTPUT_DIRECTORY, pest_audio_file))

        if 'disease_file' in request.files:
            disease_file = request.files['disease_file']
            if disease_file.filename != '':
                disease_filename = disease_file.filename
                disease_file.save(os.path.join(UPLOAD_FOLDER, disease_filename))
                tts_disease = gTTS(text=disease_text, lang='en', slow=False)
                tts_disease.save(os.path.join(OUTPUT_DIRECTORY, disease_audio_file))

    return render_template('index.html', pest_filename=pest_filename, disease_filename=disease_filename, pest_audio_file=pest_audio_file, disease_audio_file=disease_audio_file)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/audio/<filename>')
def audio_file(filename):
    return send_from_directory(OUTPUT_DIRECTORY, filename)

@app.route('/sensors')
def sensors():
    return render_template('sensors.html', sensor_data=sensor_data)

@app.route('/zones')
def zones():
    return render_template('zones.html')


@app.route('/activity-log')
def activity_log():
    return 0
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
    cursor.execute(sql, val) # type: ignore
    db.commit() # type: ignore
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


