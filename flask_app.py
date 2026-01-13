import os
import numpy as np
import onnxruntime as ort
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'best.onnx')
DATA_FILE = os.path.join(BASE_DIR, 'data_history.json')

def save_data(device, result):
    data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    data.append({"time": datetime.now().strftime("%H:%M:%S"), "device": device, "result": result})
    with open(DATA_FILE, 'w') as f:
        json.dump(data[-20:], f)

try:
    session = ort.InferenceSession(MODEL_PATH)
    ai_status = "AI READY"
except Exception as e:
    session = None
    ai_status = f"OFFLINE: {str(e)}"

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Plant Monitoring - S2TE</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-4 md:p-8">
    <div class="max-w-6xl mx-auto">
        <div class="bg-green-700 text-white p-6 rounded-xl shadow-lg mb-6 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-bold">Smart Plant Monitoring System</h1>
                <p class="text-green-100">Implementasi AI Vision untuk Pertanian Cerdas</p>
            </div>
            <div class="text-right">
                <span class="bg-green-900 px-4 py-2 rounded-full text-sm font-mono border border-green-400">
                    Status AI: {{ ai_status }}
                </span>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-white p-6 rounded-xl shadow-md border-b-4 border-blue-500 text-center">
                <h3 class="text-gray-500 uppercase text-xs font-bold">Total Deteksi</h3>
                <p id="stat-total" class="text-3xl font-bold text-gray-800">0</p>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-md border-b-4 border-green-500 text-center">
                <h3 class="text-gray-500 uppercase text-xs font-bold">Kesehatan Tanaman</h3>
                <p id="stat-health" class="text-3xl font-bold text-green-600">0%</p>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-md border-b-4 border-orange-500 text-center">
                <h3 class="text-gray-500 uppercase text-xs font-bold">Status Terakhir</h3>
                <p id="stat-latest" class="text-xl font-bold text-gray-800">-</p>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="bg-white p-6 rounded-xl shadow-md">
                <h2 class="text-lg font-bold mb-4 text-gray-700">Tren Deteksi Penyakit</h2>
                <div class="relative h-80 w-full">
                    <canvas id="healthChart"></canvas>
                </div>
                <p class="text-xs text-gray-400 mt-4 italic">* Grafik menunjukkan fluktuasi Sehat (1) vs Sakit (0)</p>
            </div>

            <div class="bg-white p-6 rounded-xl shadow-md">
                <h2 class="text-lg font-bold mb-4 text-gray-700">Log Histori Perangkat</h2>
                <div class="overflow-y-auto h-80">
                    <table class="w-full text-sm text-left">
                        <thead class="bg-gray-50 sticky top-0">
                            <tr><th class="p-3">Waktu</th><th class="p-3">Hasil AI</th></tr>
                        </thead>
                        <tbody id="table-body"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        let myChart;

        async function updateDashboard() {
            try {
                const response = await fetch('/get_history_data');
                const data = await response.json();

                if (data.length > 0) {
                    // Update Stats
                    const latest = data[data.length-1];
                    const healthyCount = data.filter(d => d.result === 'Healthy').length;
                    const healthRate = Math.round((healthyCount / data.length) * 100);

                    document.getElementById('stat-total').innerText = data.length;
                    document.getElementById('stat-health').innerText = healthRate + "%";
                    document.getElementById('stat-latest').innerText = latest.result;

                    // Update Tabel
                    const tbody = document.getElementById('table-body');
                    tbody.innerHTML = [...data].reverse().map(d => `
                        <tr class="border-b">
                            <td class="p-3">${d.time}</td>
                            <td class="p-3">
                                <span class="px-3 py-1 rounded-full text-xs font-bold ${d.result === 'Healthy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
                                    ${d.result}
                                </span>
                            </td>
                        </tr>
                    `).join('');

                    updateChart(data);
                }
            } catch (err) { console.error("Update error:", err); }
        }

        function updateChart(data) {
            const ctx = document.getElementById('healthChart').getContext('2d');
            const labels = data.map(d => d.time);
            const values = data.map(d => d.result === 'Healthy' ? 1 : 0);

            if (myChart) { myChart.destroy(); }

            myChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Indeks Kesehatan',
                        data: values,
                        borderColor: '#15803d',
                        backgroundColor: 'rgba(21, 128, 61, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false, // Penting agar tidak memanjang
                    scales: {
                        y: { min: -0.1, max: 1.1, ticks: { stepSize: 1 } },
                        x: { ticks: { maxRotation: 45, minRotation: 45 } }
                    }
                }
            });
        }

        setInterval(updateDashboard, 10000);
        updateDashboard();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML, ai_status=ai_status)

@app.route('/get_history_data')
def get_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/predict_plant_health', methods=['POST'])
def predict():
    try:
        req_data = request.get_json()
        sim_val = int(req_data.get("simulated_data", 0))
        classes = ['Healthy', 'Early Blight', 'Late Blight', 'Leaf Spot']
        prediction = classes[sim_val % len(classes)]
        save_data(req_data.get("device_id", "ESP32_WOKWI"), prediction)
        return jsonify({"status": "success", "prediction": prediction})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
