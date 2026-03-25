@app.route('/eeg/data', methods=['GET'])
def get_eeg_data():
    """获取指定时间范围的EEG数据"""
    edf_file = r"e:\Code\jisheeeg\data\chb01\chb01_03.edf"
    
    # 获取请求参数
    start_time = float(request.args.get('start_time', 0))
    window_size = float(request.args.get('window_size', 1.0))
    
    # 使用MNE库读取EDF文件
    raw = mne.io.read_raw_edf(edf_file, preload=True)
    sampling_freq = raw.info['sfreq']
    
    # 计算索引
    start_idx = int(start_time * sampling_freq)
    end_idx = int((start_time + window_size) * sampling_freq)
    
    # 获取数据
    data, times = raw[:, start_idx:end_idx]
    
    # 构建返回数据
    response_data = {
        "timestamp": start_time,
        "window_size": window_size,
        "channels": raw.ch_names,
        "sampling_rate": float(sampling_freq),
        "data": {}
    }
    
    # 处理每个通道的数据
    for i, channel_name in enumerate(raw.ch_names):
        channel_data = data[i].tolist()
        response_data["data"][channel_name] = {
            "mean": float(np.mean(data[i])),
            "std": float(np.std(data[i])),
            "min": float(np.min(data[i])),
            "max": float(np.max(data[i])),
            "data": channel_data
        }
    
    return jsonify(response_data)