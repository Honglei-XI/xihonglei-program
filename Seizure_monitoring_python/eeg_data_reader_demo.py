import mne
import numpy as np
import time
import json
import os

def read_eeg_file(edf_file_path, window_size=1.0, step_size=0.5):
    """
    读取EEG文件并实时输出数据
    
    参数:
        edf_file_path: EDF文件路径
        window_size: 每次读取的时间窗口大小（秒）
        step_size: 每步移动的时间（秒）
    """
    print(f"正在读取EDF文件: {edf_file_path}")
    
    # 使用MNE库读取EDF文件
    raw = mne.io.read_raw_edf(edf_file_path, preload=True)
    
    # 获取基本信息
    n_channels = len(raw.ch_names)
    sampling_freq = raw.info['sfreq']
    duration = raw.times[-1]
    
    print(f"文件信息:")
    print(f"- 通道数: {n_channels}")
    print(f"- 采样率: {sampling_freq} Hz")
    print(f"- 记录时长: {duration:.2f} 秒")
    print(f"- 通道名称: {raw.ch_names}")
    
    # 获取所有数据
    data, times = raw[:, :]
    
    # 计算总步数
    total_steps = int((duration - window_size) / step_size) + 1
    
    print("\n开始模拟实时数据输出...")
    print("=" * 80)
    
    # 模拟实时数据流
    for step in range(min(10, total_steps)):  # 只显示前10个时间窗口作为演示
        # 计算当前时间窗口
        current_time = step * step_size
        start_idx = int(current_time * sampling_freq)
        end_idx = int((current_time + window_size) * sampling_freq)
        
        # 确保索引在有效范围内
        end_idx = min(end_idx, len(times))
        
        print(f"\n时间窗口 {step+1}/{total_steps}: {current_time:.2f}s - {current_time + window_size:.2f}s")
        
        # 提取当前窗口的数据
        window_data = {}
        for i in range(n_channels):
            channel_name = raw.ch_names[i]
            channel_data = data[i, start_idx:end_idx]
            
            # 计算一些基本统计信息
            mean_val = np.mean(channel_data)
            std_val = np.std(channel_data)
            min_val = np.min(channel_data)
            max_val = np.max(channel_data)
            
            # 只显示前5个数据点作为示例
            sample_data = channel_data[:5].tolist()
            
            window_data[channel_name] = {
                "mean": float(mean_val),
                "std": float(std_val),
                "min": float(min_val),
                "max": float(max_val),
                "sample_data": sample_data,
                "data_length": len(channel_data)
            }
        
        # 创建可以发送给Java后端的JSON数据
        output_data = {
            "timestamp": current_time,
            "window_size": window_size,
            "channels": raw.ch_names,
            "sampling_rate": sampling_freq,
            "data": window_data
        }
        
        # 输出JSON格式的数据（这就是可以发送给Java后端的格式）
        print("数据格式示例 (JSON):")
        print(json.dumps(output_data, indent=2)[:500] + "...\n")  # 只显示前500个字符
        
        # 输出原始数据格式
        print("原始数据格式 (Numpy数组):")
        for i in range(min(3, n_channels)):  # 只显示前3个通道作为示例
            channel_name = raw.ch_names[i]
            channel_data = data[i, start_idx:end_idx]
            print(f"通道 {i+1} ({channel_name}): 形状={channel_data.shape}, 类型={channel_data.dtype}")
            print(f"  前5个数据点: {channel_data[:5]}")
            print(f"  数据范围: {np.min(channel_data)} 到 {np.max(channel_data)}")
            print()
        
        # 模拟实时处理的延迟
        time.sleep(0.5)
    
    print("=" * 80)
    print("演示完成。实际应用中，您可以将上述JSON格式的数据发送给Java后端。")
    
    # 返回一个完整的数据样本，用于进一步分析
    return {
        "raw": raw,
        "data": data,
        "times": times,
        "sample_output": output_data
    }

def analyze_seizure_data(edf_file_path, seizure_start, seizure_end):
    """
    分析发作期间的数据
    
    参数:
        edf_file_path: EDF文件路径
        seizure_start: 发作开始时间（秒）
        seizure_end: 发作结束时间（秒）
    """
    print(f"\n分析发作期间的数据...")
    
    # 读取EDF文件
    raw = mne.io.read_raw_edf(edf_file_path, preload=True)
    sampling_freq = raw.info['sfreq']
    
    # 获取发作前、发作中和发作后的数据
    before_seizure_start = max(0, seizure_start - 10)  # 发作前10秒
    after_seizure_end = min(raw.times[-1], seizure_end + 10)  # 发作后10秒
    
    # 获取数据
    data, times = raw[:, :]
    
    # 计算索引
    before_idx_start = int(before_seizure_start * sampling_freq)
    before_idx_end = int(seizure_start * sampling_freq)
    seizure_idx_start = before_idx_end
    seizure_idx_end = int(seizure_end * sampling_freq)
    after_idx_start = seizure_idx_end
    after_idx_end = int(after_seizure_end * sampling_freq)
    
    # 分析每个阶段的数据
    stages = [
        ("发作前", data[:, before_idx_start:before_idx_end]),
        ("发作中", data[:, seizure_idx_start:seizure_idx_end]),
        ("发作后", data[:, after_idx_start:after_idx_end])
    ]
    
    for stage_name, stage_data in stages:
        print(f"\n{stage_name}数据分析:")
        
        # 计算每个通道的统计信息
        for i in range(min(5, len(raw.ch_names))):  # 只分析前5个通道
            channel_data = stage_data[i]
            mean_val = np.mean(channel_data)
            std_val = np.std(channel_data)
            min_val = np.min(channel_data)
            max_val = np.max(channel_data)
            
            print(f"通道 {i+1} ({raw.ch_names[i]}):")
            print(f"  均值: {mean_val:.4f}")
            print(f"  标准差: {std_val:.4f}")
            print(f"  最小值: {min_val:.4f}")
            print(f"  最大值: {max_val:.4f}")
            print(f"  波动范围: {max_val - min_val:.4f}")
    
    print("\n发作数据分析完成。")

if __name__ == "__main__":
    # 设置EDF文件路径
    edf_file = r"e:\Code\jisheeeg\data\chb01\chb01_03.edf"
    
    # 读取并显示数据格式
    result = read_eeg_file(edf_file, window_size=1.0, step_size=0.5)
    
    # 分析发作期间的数据（根据chb01-summary.txt中的信息）
    seizure_start = 2996  # 秒
    seizure_end = 3036    # 秒
    analyze_seizure_data(edf_file, seizure_start, seizure_end)
    
    print("\n如果要将数据发送给Java后端，您可以使用以下方法:")
    print("1. 使用HTTP请求（如requests库）")
    print("2. 使用WebSocket进行实时通信")
    print("3. 使用消息队列（如RabbitMQ、Kafka）")
    print("4. 将数据写入共享文件或数据库")