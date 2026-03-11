import joblib
import numpy as np
import os
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from src.data.loaddata import load_data, load_dataX
from src.data.extractFeture import preprocess_and_extract_features_mne_with_timestamps

def testdemo(file_path):
    """
    分析EDF文件并预测发作时间
    
    Args:
        file_path: EDF文件路径
        
    Returns:
        tuple: (发作开始时间, 发作结束时间) 或 (None, None)
    """
    try:
        # 特征提取
        X = preprocess_and_extract_features_mne_with_timestamps(file_path)
        X = X[:, 1:]  # 去除时间戳列
        
        # 直接加载指定路径的模型文件
        model_path = r'lightgbm_model_multi_dataset.joblib'
        clf = joblib.load(model_path)
        print(f"成功加载模型: {model_path}")
            
        # 使用模型进行预测
        predictions = clf.predict(X)
        
        # 分析预测结果
        time = 0
        a = 0  # 连续预测为1的计数
        b = 0  # 连续预测为0的计数
        flag = False  # 是否处于发作状态
        startTime = []
        endTime = []
        
        for prediction in predictions:
            time += 1
            if flag:  # 当前处于发作状态
                if prediction == 0:
                    b += 1
                else:
                    b = 0
                if b == 5:  # 连续5次预测为0，认为发作结束
                    flag = False
                    endTime.append(time - 5)
            else:  # 当前不处于发作状态
                if prediction == 1:
                    a += 1
                else:
                    a = 0
                if a == 5:  # 连续5次预测为1，认为发作开始
                    flag = True
                    startTime.append(time - 5)
        
        # 处理结果
        if len(startTime) > 0 and len(endTime) > 0:
            start_time = startTime[0] * 3600 / 27600
            end_time = endTime[0] * 3600 / 27600
            print(f"病症发作时间：{start_time} 结束时间：{end_time}")
            print("startTime:", startTime)
            print("endTime:", endTime)
            return start_time, end_time
        else:
            print("未检测到发作时间")
            print("startTime:", startTime)
            print("endTime:", endTime)
            return None, None
            
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        return None, None

# 测试代码，仅在直接运行此文件时执行
if __name__ == "__main__":
    # 示例文件路径
    test_file_path = 'data/chb01/chb01_03.edf'
    
    # 测试函数
    start, end = testdemo(test_file_path)
    
    if start is not None and end is not None:
        print(f"测试结果 - 发作开始时间: {start}, 发作结束时间: {end}")
    else:
        print("测试未检测到发作或发生错误")


