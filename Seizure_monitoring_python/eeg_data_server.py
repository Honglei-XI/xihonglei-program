"""
实时渲染EEG动态数据 --Echarts
"""
import mne
import numpy as np
import time
import json
import os
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # 添加这一行
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'eeg-secret-key'
CORS(app)  # 添加这一行，启用CORS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')  # 修改这一行

# 全局变量，用于控制数据流
streaming = False
stream_thread = None
@app.route('/eeg/stream/start', methods=['POST', 'OPTIONS'])  # 添加OPTIONS方法支持
def start_streaming():
    """开始实时数据流"""
    # 处理预检请求
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
        
    global streaming, stream_thread
    
    if streaming:
        return jsonify({"status": "error", "message": "数据流已经在运行中"})
    
    # 获取请求参数
    data = request.json or {}
    window_size = float(data.get('window_size', 1.0))
    step_size = float(data.get('step_size', 0.5))
    
    # 启动数据流线程
    streaming = True
    stream_thread = threading.Thread(
        target=stream_eeg_data,
        args=(window_size, step_size)
    )
    stream_thread.daemon = True
    stream_thread.start()
    
    return jsonify({"status": "success", "message": "数据流已启动"})

@app.route('/eeg/stream/stop', methods=['POST', 'OPTIONS'])  # 添加OPTIONS方法支持
def stop_streaming():
    """停止实时数据流"""
    # 处理预检请求
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
        
    global streaming
    
    if not streaming:
        return jsonify({"status": "error", "message": "数据流未运行"})
    
    streaming = False
    return jsonify({"status": "success", "message": "数据流已停止"})

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    print('客户端已连接')
    emit('connection_response', {'status': 'connected'})
    
    # 自动启动数据流
    global streaming, stream_thread
    if not streaming:
        streaming = True
        stream_thread = threading.Thread(
            target=stream_eeg_data,
            args=(5, 5)  # 默认窗口大小和步长
        )
        stream_thread.daemon = True
        stream_thread.start()
        print('数据流自动启动')

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    print('客户端已断开连接')
    # 断开连接时停止数据流
    global streaming, stream_thread
    if streaming:
        streaming = False
        if stream_thread and stream_thread.is_alive():
            stream_thread.join(timeout=1.0)  # 等待线程结束
        stream_thread = None
        print('数据流已停止')

def stream_eeg_data(window_size, step_size):
    """实时流式传输EEG数据的线程函数"""
    global streaming, stream_thread
    
    try:
        edf_file = r"e:\Code\jisheeeg\data\chb01\chb01_03.edf"
        
        # 使用MNE库读取EDF文件
        raw = mne.io.read_raw_edf(edf_file, preload=True)
        
        # 获取基本信息
        sampling_freq = raw.info['sfreq']
        duration = raw.times[-1]
        
        # 获取所有数据并应用滤波器
        raw.filter(l_freq=1, h_freq=50)  # 添加带通滤波器
        data, times = raw[:, :]
        
        # 对数据进行锐化处理
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]]) / 9.0
        
        sharpened_data = np.zeros_like(data)
        for i in range(len(data)):
            # 对每个通道进行锐化
            channel_data = data[i].reshape(1, -1)
            # 使用卷积进行锐化
            sharpened_data[i] = np.convolve(channel_data[0], kernel[1], mode='same')
        
        data = sharpened_data
        
        # 计算总步数
        total_steps = int((duration - window_size) / step_size) + 1
        
        # 模拟实时数据流
        step = 0
        while streaming and step < total_steps:
            # 计算当前时间窗口
            current_time = step * step_size
            start_idx = int(current_time * sampling_freq)
            end_idx = int((current_time + window_size) * sampling_freq)
            
            # 确保索引在有效范围内
            if end_idx >= len(times):
                break
            
            # 提取当前窗口的数据
            window_data = {}
            for i, channel_name in enumerate(raw.ch_names):
                channel_data = data[i, start_idx:end_idx]
                
                # 对数据进行归一化处理
                channel_mean = np.mean(channel_data)
                channel_std = np.std(channel_data)
                if channel_std != 0:
                    normalized_data = (channel_data - channel_mean) / channel_std
                else:
                    normalized_data = channel_data - channel_mean
                    
                # 将数据缩放到合适的范围
                scaled_data = normalized_data * 75  # 增加缩放因子以突出锐化效果
                
                window_data[channel_name] = scaled_data.tolist()
            
            # 创建要发送的数据包
            output_data = {
                "timestamp": float(current_time),
                "window_size": float(window_size),
                "channels": raw.ch_names,
                "data": window_data,
                "is_seizure": 2996 <= current_time <= 3036
            }
            
            # 通过WebSocket发送数据
            socketio.emit('eeg_data', output_data)
            
            # 控制发送速度
            time.sleep(step_size / 2)
            step += 1
        
        # 发送流结束通知
        socketio.emit('eeg_stream_end', {"message": "数据流结束"})
    finally:
        # 确保在任何情况下都重置状态
        streaming = False
        stream_thread = None

if __name__ == '__main__':
    print("EEG数据服务器启动在 http://localhost:5000")
    # 确保安装了eventlet
    import eventlet
    eventlet.monkey_patch()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)