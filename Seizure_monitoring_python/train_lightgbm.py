import joblib
import numpy as np
import os
import lightgbm as lgb
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from src.data.loaddata import load_data, load_dataX
from src.data.extractFeture import preprocess_and_extract_features_mne_with_timestamps


def train_lightgbm_model():
    """
    训练LightGBM模型用于癫痫发作检测
    """
    try:
        print("开始加载数据...")
        
        # 加载数据
        subject_id = 1
        base_path = "data"
        all_X, all_y = load_data(subject_id, base_path)
        
        # 合并所有数据
        X = np.vstack(all_X)
        y = np.hstack(all_y)
        print(f"数据加载完成，X形状: {X.shape}, y形状: {y.shape}")
        
        # 处理类别不平衡问题
        print("处理类别不平衡问题...")
        smote = SMOTE(random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X, y)
        print(f"SMOTE处理后，X形状: {X_resampled.shape}, y形状: {y_resampled.shape}")
        
        # 分割训练集和测试集
        print("分割训练集和测试集...")
        X_train, X_test, y_train, y_test = train_test_split(
            X_resampled, y_resampled, test_size=0.2, random_state=42
        )
        print(f"训练集: {X_train.shape}, 测试集: {X_test.shape}")
        
        # 配置LightGBM参数
        print("配置LightGBM参数...")
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'learning_rate': 0.05,
            'max_depth': 6,
            'num_leaves': 31,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': 0,
            'random_state': 42
        }
        
        # 训练模型
        print("开始训练LightGBM模型...")
        lgb_train = lgb.Dataset(X_train, y_train)
        lgb_test = lgb.Dataset(X_test, y_test, reference=lgb_train)
        
        model = lgb.train(
            params,
            lgb_train,
            num_boost_round=1000,
            valid_sets=[lgb_train, lgb_test],
            valid_names=['train', 'test'],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50),
                lgb.log_evaluation(period=100)
            ]
        )
        
        # 评估模型
        print("评估模型性能...")
        y_pred = model.predict(X_test, num_iteration=model.best_iteration)
        y_pred_binary = [1 if x > 0.5 else 0 for x in y_pred]
        
        accuracy = accuracy_score(y_test, y_pred_binary)
        f1 = f1_score(y_test, y_pred_binary)
        
        print(f"模型准确率: {accuracy:.4f}")
        print(f"模型F1分数: {f1:.4f}")
        
        # 保存模型
        model_path = r'lightgbm_model.joblib'
        joblib.dump(model, model_path)
        print(f"模型保存成功: {model_path}")
        
        return model_path
        
    except Exception as e:
        print(f"训练过程中出现错误: {str(e)}")
        return None


# 测试代码，仅在直接运行此文件时执行
if __name__ == "__main__":
    model_path = train_lightgbm_model()
    if model_path:
        print(f"训练完成，模型保存路径: {model_path}")
    else:
        print("训练失败")
