"""
- 主要功能：计算脑电信号的过零点特征
- 关键特点：
- 计算信号的零相交次数
- 使用滑动窗口方法进行特征提取
- 去除信号的直流分量
- 可用于分析信号的频率特性
"""
import numpy as np
import matplotlib.pyplot as plt
import mne
import os
import pandas as pd
from datetime import datetime
# 将相对导入改为绝对导入
from func.uploadFile import upload_file

# 读取EEG数据
def read_eeg_data(file_path):
    raw = mne.io.read_raw_edf(file_path, preload=True)
    data = raw.get_data()
    sfreq = raw.info['sfreq']
    channel_names = raw.info['ch_names']
    return data, sfreq, channel_names

#计算信号的零相交次数。
def zero_crossings(signal):
    # 去除直流分量
    signal = signal - np.mean(signal)
    # 计算零相交点
    zero_crossings = np.where(np.diff(np.sign(signal)))[0]
    return len(zero_crossings)

#实现滑动窗口计算零相交次数。参数包括信号、窗口大小和步长。
def zero_crossings_sliding_window(signal, window_size, step_size):
    num_windows = (len(signal) - window_size) // step_size + 1
    crossings_per_window = []

    for i in range(num_windows):
        start = i * step_size
        end = start + window_size
        window = signal[start:end]
        crossings = zero_crossings(window)
        crossings_per_window.append(crossings)

    return np.array(crossings_per_window)

# 创建保存结果的文件夹
def create_results_folder():
    # 创建带有时间戳的文件夹名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 使用项目目录下的results文件夹
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_folder = os.path.join(base_dir, "results", f"zero_crossings_{timestamp}")
    
    # 确保文件夹存在
    os.makedirs(results_folder, exist_ok=True)
    return results_folder

# 处理多通道EEG数据并可视化
def process_and_visualize_eeg(file_path, window_size_sec=6, step_size_sec=3, channels_to_plot=None, max_channels=5):
    # 创建结果文件夹
    results_folder = create_results_folder()
    
    # 读取EEG数据
    data, sfreq, channel_names = read_eeg_data(file_path)
    
    # 转换秒到样本数
    window_size = int(window_size_sec * sfreq)
    step_size = int(step_size_sec * sfreq)
    
    # 如果未指定通道，选择前max_channels个通道
    if channels_to_plot is None:
        channels_to_plot = list(range(min(max_channels, data.shape[0])))
    
    # 存储所有通道的结果和上传的URL
    all_results = {}
    all_uploaded_urls = []
    
    # 处理每个通道
    for ch_idx in channels_to_plot:
        if ch_idx < data.shape[0]:
            channel_name = channel_names[ch_idx] if ch_idx < len(channel_names) else f"Channel {ch_idx}"
            
            # 计算零交叉
            crossings = zero_crossings_sliding_window(data[ch_idx], window_size, step_size)
            all_results[channel_name] = crossings
            
            # 单通道可视化
            plt.figure(figsize=(12, 6))
            plt.plot(crossings, label=f'Zero Crossings - {channel_name}')
            plt.xlabel('Window Index')
            plt.ylabel('Zero Crossings')
            plt.title(f'Zero Crossings in Sliding Windows - {channel_name}')
            plt.legend()
            plt.grid(True)
            
            # 保存单通道图像
            safe_channel_name = channel_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            img_path = os.path.join(results_folder, f"zero_crossings_{safe_channel_name}.png")
            plt.savefig(img_path)
            plt.close()
            
            # 上传图片
            url = upload_file(img_path)
            if url:
                all_uploaded_urls.append({"file": img_path, "url": url, "channel": channel_name})
    
    # 创建多通道对比图
    plt.figure(figsize=(15, 8))
    for ch_name, crossings in all_results.items():
        plt.plot(crossings, label=ch_name)
    
    plt.xlabel('Window Index')
    plt.ylabel('Zero Crossings')
    plt.title('Zero Crossings Comparison Across Channels')
    plt.legend()
    plt.grid(True)
    
    # 保存并上传汇总图
    summary_img_path = os.path.join(results_folder, "zero_crossings_all_channels.png")
    plt.savefig(summary_img_path)
    plt.close()
    
    # 上传汇总图片
    summary_url = upload_file(summary_img_path)
    if summary_url:
        all_uploaded_urls.append({"file": summary_img_path, "url": summary_url, "channel": "汇总图"})
    
    # 打印上传结果
    print(f"共上传了 {len(all_uploaded_urls)} 张图片")
    for item in all_uploaded_urls:
        print(f"通道: {item['channel']}, 文件: {item['file']} -> URL: {item['url']}")
    
    print(f"结果已保存到: {results_folder}")
    return all_results, results_folder, all_uploaded_urls

# 主函数
if __name__ == "__main__":
    # 示例EEG信号
    file_path = 'E:/Code/jisheeeg/data/chb01/chb01_03.edf'
    
    # 处理并可视化EEG数据
    results, folder, uploaded_urls = process_and_visualize_eeg(
        file_path, 
        window_size_sec=6,  # 窗口大小(秒)
        step_size_sec=3,    # 步长(秒)
        max_channels=5      # 最多处理的通道数
    )
    
    print(f"零交叉分析完成，结果保存在: {folder}")
    print(f"所有上传的图片URL:")
    for item in uploaded_urls:
        print(f"通道: {item['channel']} -> {item['url']}")
    
    # 显示所有图像
    plt.show()