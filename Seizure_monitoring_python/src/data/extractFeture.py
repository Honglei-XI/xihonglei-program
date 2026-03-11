import numpy as np
import tqdm
import mne
from scipy.signal import welch, stft, iirnotch
from scipy.stats import skew, kurtosis, entropy
from scipy.spatial.distance import euclidean
from scipy.ndimage import gaussian_filter1d
from sklearn.decomposition import PCA

# 非线性动力学特征计算
def calculate_approximate_entropy(signal, m=2, r=0.2):
    """
    计算近似熵
    """
    n = len(signal)
    if n < m + 1:
        return 0
    
    # 构建嵌入向量
    def _phi(m):
        x = np.array([signal[i:i+m] for i in range(n - m + 1)])
        C = []
        for i in range(len(x)):
            # 计算与其他向量的距离
            d = np.max(np.abs(x - x[i]), axis=1)
            # 计算在阈值内的比例
            C.append(np.sum(d < r * np.std(signal)) / (len(x) - 1))
        return np.mean(np.log(C))
    
    return _phi(m) - _phi(m + 1)

def calculate_sample_entropy(signal, m=2, r=0.2):
    """
    计算样本熵
    """
    n = len(signal)
    if n < m + 1:
        return 0
    
    # 构建嵌入向量
    def _phi(m):
        x = np.array([signal[i:i+m] for i in range(n - m + 1)])
        C = []
        for i in range(len(x)):
            # 计算与其他向量的距离
            d = np.max(np.abs(x - x[i]), axis=1)
            # 计算在阈值内的比例
            C.append(np.sum(d < r * np.std(signal)) - 1)  # 减去自身
        C = np.array(C) / (len(x) - 1)
        return C[C > 0]
    
    phi_m = _phi(m)
    phi_m1 = _phi(m + 1)
    
    if len(phi_m) == 0 or len(phi_m1) == 0:
        return 0
    
    return -np.log(np.mean(phi_m1) / np.mean(phi_m))

def calculate_fractal_dimension(signal):
    """
    计算分形维数（使用Higuchi方法）
    """
    n = len(signal)
    if n < 4:
        return 1
    
    k_max = min(10, n // 2)
    L = []
    
    for k in range(1, k_max + 1):
        Lk = 0
        for m in range(k):
            # 计算子序列长度
            N = len(signal[m::k])
            if N < 2:
                continue
            # 计算子序列的长度
            Lk += np.sum(np.abs(np.diff(signal[m::k])))
            Lk /= (N - 1)
        Lk *= (n - 1) / (k * N)
        L.append(Lk)
    
    if len(L) < 2:
        return 1
    
    # 线性回归计算分形维数
    log_k = np.log(np.arange(1, k_max + 1))
    log_L = np.log(L)
    
    # 计算线性回归斜率
    if np.std(log_k) == 0:
        return 1
    
    slope = np.cov(log_k, log_L)[0, 1] / np.var(log_k)
    return 1 - slope

# 小波变换特征（暂时禁用）
def extract_wavelet_features(data, fs):
    """
    提取小波变换特征
    """
    # 由于scipy版本兼容性问题，暂时返回空特征
    return []

# 高级统计特征
def extract_advanced_statistics(signal):
    """
    提取高级统计特征（扩展版，增加到 20 个特征）
    """
    # 标准化信号
    signal = (signal - np.mean(signal)) / np.std(signal)
    
    features = []
    
    # 基础统计特征
    features.extend([
        np.mean(signal),
        np.std(signal),
        skew(signal),
        kurtosis(signal)
    ])
    
    # 能量相关特征
    features.append(np.mean(signal**2))  # 平均能量
    
    # 零交叉率
    zero_crossings = np.sum(np.abs(np.diff(np.sign(signal)))) / (2 * len(signal))
    features.append(zero_crossings)
    
    # 添加更多高级统计特征
    # 四分位数特征
    q25 = np.percentile(signal, 25)
    q50 = np.percentile(signal, 50)
    q75 = np.percentile(signal, 75)
    iqr = q75 - q25
    features.extend([q25, q50, q75, iqr])
    
    # 绝对偏差特征
    mad = np.mean(np.abs(signal - np.mean(signal)))  # 平均绝对偏差
    features.append(mad)
    
    # 方差特征
    variance = np.var(signal)
    features.append(variance)
    
    # 峰值特征
    peak = np.max(np.abs(signal))
    features.append(peak)
    
    # 均方根特征
    rms = np.sqrt(np.mean(signal**2))
    features.append(rms)
    
    # 波形因子
    waveform_factor = rms / np.mean(np.abs(signal)) if np.mean(np.abs(signal)) > 0 else 0
    features.append(waveform_factor)
    
    # 脉冲因子
    impulse_factor = peak / np.mean(np.abs(signal)) if np.mean(np.abs(signal)) > 0 else 0
    features.append(impulse_factor)
    
    # 峰值因子
    crest_factor = peak / rms if rms > 0 else 0
    features.append(crest_factor)
    
    # 裕度因子
    margin_factor = peak / (np.mean(np.sqrt(np.abs(signal)))**2) if np.mean(np.sqrt(np.abs(signal))) > 0 else 0
    features.append(margin_factor)
    
    # 峰峰值
    peak_to_peak = np.max(signal) - np.min(signal)
    features.append(peak_to_peak)
    
    # 峰峰值比率
    peak_to_peak_ratio = peak_to_peak / np.mean(np.abs(signal)) if np.mean(np.abs(signal)) > 0 else 0
    features.append(peak_to_peak_ratio)
    
    return features

# 频率域高级特征
def extract_advanced_frequency_features(data, fs):
    """
    提取高级频率域特征（扩展版，增加到 30 个特征）
    """
    # 计算功率谱密度（使用更小的 nperseg 加快计算）
    f, Pxx = welch(data, fs, nperseg=64)
    
    features = []
    
    # 保留 10 个主要频段的相对功率
    freq_bands = {
        'delta1': (0.5, 2),
        'delta2': (2, 4),
        'theta': (4, 8),
        'alpha1': (8, 10),
        'alpha2': (10, 13),
        'beta1': (13, 20),
        'beta2': (20, 30),
        'gamma1': (30, 40),
        'gamma2': (40, 50),
        'high_gamma': (50, 80)
    }
    
    total_power = np.sum(Pxx)
    if total_power > 0:
        for band, (fmin, fmax) in freq_bands.items():
            band_mask = (f >= fmin) & (f <= fmax)
            if np.any(band_mask):
                band_ratio = np.sum(Pxx[band_mask]) / total_power
                features.append(band_ratio)
            else:
                features.append(0)
    else:
        features.extend([0] * 10)
    
    # 添加频谱熵特征
    if total_power > 0:
        normalized_psd = Pxx / total_power
        spectral_entropy = entropy(normalized_psd)
        features.append(spectral_entropy)
    else:
        features.append(0)
    
    # 添加频谱质心特征
    if total_power > 0:
        spectral_centroid = np.sum(f * Pxx) / total_power
        features.append(spectral_centroid)
    else:
        features.append(0)
    
    # 添加频谱带宽特征
    if total_power > 0:
        spectral_bandwidth = np.sqrt(np.sum(((f - features[-1])**2) * Pxx) / total_power)
        features.append(spectral_bandwidth)
    else:
        features.append(0)
    
    # 添加频谱平坦度特征
    if total_power > 0:
        geometric_mean = np.exp(np.mean(np.log(Pxx + 1e-10)))
        spectral_flatness = geometric_mean / np.mean(Pxx)
        features.append(spectral_flatness)
    else:
        features.append(0)
    
    # 添加频谱滚降特征
    if total_power > 0:
        cumulative_power = np.cumsum(Pxx)
        rolloff_idx = np.where(cumulative_power >= 0.85 * total_power)[0]
        if len(rolloff_idx) > 0:
            spectral_rolloff = f[rolloff_idx[0]]
        else:
            spectral_rolloff = f[-1]
        features.append(spectral_rolloff)
    else:
        features.append(0)
    
    # 添加主频率特征
    if total_power > 0:
        dominant_freq_idx = np.argmax(Pxx)
        dominant_freq = f[dominant_freq_idx]
        features.append(dominant_freq)
    else:
        features.append(0)
    
    # 添加主频率功率特征
    if total_power > 0:
        dominant_power = Pxx[dominant_freq_idx] if total_power > 0 else 0
        features.append(dominant_power)
    else:
        features.append(0)
    
    # 添加频谱斜率特征
    if len(f) > 1:
        spectral_slope = np.polyfit(f[:10], Pxx[:10], 1)[0]
        features.append(spectral_slope)
    else:
        features.append(0)
    
    # 添加频谱峰度特征
    if total_power > 0:
        normalized_psd = Pxx / total_power
        spectral_kurtosis = kurtosis(normalized_psd)
        features.append(spectral_kurtosis)
    else:
        features.append(0)
    
    # 添加频谱偏度特征
    if total_power > 0:
        normalized_psd = Pxx / total_power
        spectral_skewness = skew(normalized_psd)
        features.append(spectral_skewness)
    else:
        features.append(0)
    
    return features

# 跨通道特征
def extract_cross_channel_features(channels_data):
    """
    提取跨通道特征
    """
    features = []
    n_channels = channels_data.shape[0]
    
    if n_channels > 1:
        # 通道间相关性
        corr_matrix = np.corrcoef(channels_data)
        features.extend(corr_matrix[np.triu_indices(n_channels, 1)])
        
        # 通道间协方差
        cov_matrix = np.cov(channels_data)
        features.extend(cov_matrix[np.triu_indices(n_channels, 1)])
        
        # 通道间差异
        for i in range(n_channels):
            for j in range(i + 1, n_channels):
                features.append(np.mean(np.abs(channels_data[i] - channels_data[j])))
        
        # PCA分析
        try:
            pca = PCA(n_components=min(5, n_channels))
            pca.fit(channels_data.T)
            features.extend(pca.explained_variance_ratio_)
        except:
            pass
    
    return features

# 主特征提取函数
def extract_basic_features(signal):
    """
    提取基础特征（扩展版，增加到 20 个特征）
    """
    # 标准化信号
    signal = (signal - np.mean(signal)) / np.std(signal)
    
    # 计算基础统计特征（扩展到 20 个）
    mean = np.mean(signal)
    std = np.std(signal)
    skewness = skew(signal)
    kurt = kurtosis(signal)
    zero_crossings = np.sum(np.abs(np.diff(np.sign(signal)))) / (2 * len(signal))
    energy = np.mean(signal**2)
    
    # 添加更多统计特征
    median = np.median(signal)
    variance = np.var(signal)
    min_val = np.min(signal)
    max_val = np.max(signal)
    range_val = max_val - min_val
    rms = np.sqrt(np.mean(signal**2))
    peak_to_peak = max_val - min_val
    crest_factor = max_val / rms if rms > 0 else 0
    impulse_factor = max_val / np.mean(np.abs(signal)) if np.mean(np.abs(signal)) > 0 else 0
    margin_factor = max_val / (np.mean(np.sqrt(np.abs(signal)))**2) if np.mean(np.sqrt(np.abs(signal))) > 0 else 0
    shape_factor = rms / np.mean(np.abs(signal)) if np.mean(np.abs(signal)) > 0 else 0
    clearance_factor = max_val / (np.mean(np.abs(signal))**(1/3)) if np.mean(np.abs(signal)) > 0 else 0
    
    return [mean, std, skewness, kurt, zero_crossings, energy, median, variance, min_val, max_val, 
            range_val, rms, peak_to_peak, crest_factor, impulse_factor, margin_factor, shape_factor, clearance_factor]

def extract_advanced_features(data, fs, window_length_sec=3):
    """
    使用短时傅里叶变换（STFT）从 EEG 数据中提取高级特征。

    :param data: EEG 信号数据。
    :param fs: 采样频率。
    :param window_length_sec: STFT的每个窗口长度（秒）。
    :return: 从 STFT 提取的特征。
    """

    # 执行 STFT
    f, t, Zxx = stft(data, fs, nperseg=window_length_sec*fs)
    
    # 从 STFT 提取特征
    power = np.mean(np.abs(Zxx)**2, axis=1)  # 每个频率下的平均功率

    # 计算不同频段的功率
    freq_bands = {
        'delta': (0.5, 4),
        'theta': (4, 8),
        'alpha': (8, 13),
        'beta': (13, 30),
        'gamma': (30, 50)
    }
    
    band_powers = []
    for band, (fmin, fmax) in freq_bands.items():
        band_mask = (f >= fmin) & (f <= fmax)
        if np.any(band_mask):
            band_power = np.mean(power[band_mask])
        else:
            band_power = 0
        band_powers.append(band_power)

    # 提取高级频率特征
    freq_features = extract_advanced_frequency_features(data, fs)
    
    # 提取小波特征
    wavelet_features = extract_wavelet_features(data, fs)
    
    # 提取高级统计特征
    stat_features = extract_advanced_statistics(data)

    return np.concatenate([power, band_powers, freq_features, wavelet_features, stat_features])

def calculate_psd(data, fs, nperseg=256):
    """
    计算功率谱密度
    """
    f, Pxx = welch(data, fs, nperseg=nperseg)
    return f, Pxx

def preprocess_and_extract_features_mne_with_timestamps(file_name):
    """
    使用 mne 库预处理 EEG 数据，并提取基础和高级特征。
    在每个特征数组的开头加入对应的时间戳。
    """

    # 加载数据
    raw = mne.io.read_raw_edf(file_name, preload=True)

    # 1. 重参考：使用公共平均参考
    raw.set_eeg_reference('average', projection=True)
    raw.apply_proj()

    # 2. 伪迹去除：简化处理，禁用ICA以提高速度
    # 注释掉ICA处理，显著提高速度
    # try:
    #     # 运行ICA
    #     ica = mne.preprocessing.ICA(n_components=20, random_state=42)
    #     ica.fit(raw)
    #     
    #     # 自动检测并移除与眼动相关的成分
    #     eog_indices, eog_scores = ica.find_bads_eog(raw, ch_name=None)
    #     if eog_indices:
    #         ica.exclude = eog_indices
    #         raw = ica.apply(raw)
    #         print(f"已移除 {len(eog_indices)} 个眼动伪迹成分")
    # except Exception as e:
    #     print(f"ICA处理失败: {str(e)}")

    # 3. 滤波
    # 陷波滤波：去除50Hz电源噪声
    raw.notch_filter(50.0, fir_design='firwin')
    
    # 带通滤波：1-50Hz
    raw.filter(1., 50., fir_design='firwin')

    # 4. 选择 EEG 通道
    raw.pick_types(meg=False, eeg=True, eog=False)
    
    # 只保留部分通道以加快分析速度（例如前8个通道）
    n_channels = len(raw.ch_names)
    if n_channels > 8:
        # 只保留前8个通道
        raw.pick_channels(raw.ch_names[:8])
        print(f"只保留前8个通道，加快分析速度")

    # 5. 下采样：如果采样率过高，降低到256Hz
    sfreq = raw.info['sfreq']
    if sfreq > 256:
        raw.resample(256)
        print(f"已将采样率从 {sfreq}Hz 下采样到 256Hz")
        sfreq = 256

    # 6. 定义短时间窗口的参数
    window_length = 3  # 窗口长度（秒）
    window_samples = int(window_length * sfreq)

    # 7. 初始化一个空列表来存储特征和时间戳
    features_with_timestamps = []

    # 8. 遍历每个窗口中的数据
    for start in range(0, len(raw.times), window_samples):
        end = start + window_samples
        if end > len(raw.times):
            break

        # 提取并预处理这个窗口中的数据
        window_data, times = raw[:, start:end]
        window_data = np.squeeze(window_data)

        # 获取窗口的开始时间戳
        timestamp = raw.times[start]

        # 9. 为每个通道的每个窗口提取特征
        for channel_data in window_data:
            # 计算功率谱密度（增加采样点数以获得更多特征）
            f, psd = calculate_psd(channel_data, sfreq, nperseg=256)  # 增加采样点数
            
            # 只保留 0-50Hz 的频率范围
            freq_mask = f <= 50
            f = f[freq_mask]
            psd = psd[freq_mask]
            
            # 提取基础特征（扩展版）
            basic_features = extract_basic_features(channel_data)
            
            # 提取高级特征（扩展版）
            fft_features = extract_advanced_frequency_features(channel_data, sfreq)
            stat_features = extract_advanced_statistics(channel_data)
            
            # 计算需要保留的功率谱点数量
            # 目标：1（时间戳）+ 18（基础特征）+ 30（频率特征）+ 20（统计特征）+ PSD特征 = 128
            target_psd_features = 128 - (1 + len(basic_features) + len(fft_features) + len(stat_features))
            
            # 如果PSD特征数量不足，增加采样点数
            if len(psd) < target_psd_features:
                # 重新计算PSD，使用更大的nperseg
                new_nperseg = min(1024, len(channel_data) // 4)
                f, psd = calculate_psd(channel_data, sfreq, nperseg=new_nperseg)
                freq_mask = f <= 50
                f = f[freq_mask]
                psd = psd[freq_mask]
            
            # 如果PSD特征数量仍然不足，使用插值
            if len(psd) < target_psd_features:
                # 使用线性插值增加PSD点数
                from scipy import interpolate
                x_old = np.linspace(0, 1, len(psd))
                x_new = np.linspace(0, 1, target_psd_features)
                f_new = np.linspace(f[0], f[-1], target_psd_features)
                psd_new = interpolate.interp1d(x_old, psd, kind='linear', fill_value='extrapolate')(x_new)
                psd = psd_new
            elif len(psd) > target_psd_features:
                # 如果PSD特征数量过多，均匀采样
                step = max(1, len(psd) // target_psd_features)
                psd = psd[::step][:target_psd_features]
            
            # 组合所有特征
            combined_features = np.concatenate([[timestamp], basic_features, fft_features, stat_features, psd])
            features_with_timestamps.append(combined_features)

    # 10. 提取跨通道特征（如果有多通道）
    if len(features_with_timestamps) > 1:
        # 这里可以实现跨通道特征提取
        pass

    return np.array(features_with_timestamps)

#("data/chb01/chb01_03.edf")