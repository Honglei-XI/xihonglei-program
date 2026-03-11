import joblib
import numpy as np
import os
import lightgbm as lgb
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from src.data.multi_dataset_loader import load_all_datasets


def train_lightgbm_multi_dataset():
    """
    使用多个数据集训练LightGBM模型用于癫痫发作检测
    """
    try:
        print("开始加载多个数据集...")
        
        # 数据集配置
        # 注意：请根据实际情况修改这些路径
        datasets_config = {
            'bonn': 'data/bonn',  # Bonn数据集路径
            'tusz': 'data/tusz',  # TUSZ数据集路径
            'barcelona': 'data/barcelona',  # Barcelona数据集路径
            'freiburg': 'data/freiburg'  # Freiburg数据集路径
        }
        
        # 加载所有数据集
        X, y = load_all_datasets(datasets_config)
        
        # 如果外部数据集加载失败，使用CHB-MIT数据集
        if X is None or y is None:
            print("外部数据集加载失败，使用CHB-MIT数据集...")
            from src.data.loaddata import load_data
            
            # 加载CHB-MIT数据集
            subject_id = 1
            base_path = "data"
            all_X, all_y = load_data(subject_id, base_path)
            
            # 合并所有数据
            X = np.vstack(all_X)
            y = np.hstack(all_y)
            print(f"CHB-MIT数据集加载完成，X形状: {X.shape}, y形状: {y.shape}")
        
        print(f"数据加载完成，X形状: {X.shape}, y形状: {y.shape}")
        
        # 处理类别不平衡问题
        print("处理类别不平衡问题...")
        smote = SMOTE(random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X, y)
        print(f"SMOTE处理后，X形状: {X_resampled.shape}, y形状: {y_resampled.shape}")
        print(f"SMOTE处理后，发作样本数: {int(np.sum(y_resampled))}, 正常样本数: {int(len(y_resampled) - np.sum(y_resampled))}")
        
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
            'max_depth': 8,
            'num_leaves': 63,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': 0,
            'random_state': 42,
            'is_unbalance': False,  # 由于我们已经使用SMOTE处理了不平衡问题
            'scale_pos_weight': 1.0  # 由于我们已经使用SMOTE处理了不平衡问题
        }
        
        # 训练模型
        print("开始训练LightGBM模型...")
        lgb_train = lgb.Dataset(X_train, y_train)
        lgb_test = lgb.Dataset(X_test, y_test, reference=lgb_train)
        
        model = lgb.train(
            params,
            lgb_train,
            num_boost_round=2000,
            valid_sets=[lgb_train, lgb_test],
            valid_names=['train', 'test'],
            callbacks=[
                lgb.early_stopping(stopping_rounds=100),
                lgb.log_evaluation(period=200)
            ]
        )
        
        # 评估模型
        print("评估模型性能...")
        y_pred = model.predict(X_test, num_iteration=model.best_iteration)
        y_pred_binary = [1 if x > 0.5 else 0 for x in y_pred]
        
        accuracy = accuracy_score(y_test, y_pred_binary)
        f1 = f1_score(y_test, y_pred_binary)
        precision = precision_score(y_test, y_pred_binary)
        recall = recall_score(y_test, y_pred_binary)
        
        print(f"模型准确率: {accuracy:.4f}")
        print(f"模型F1分数: {f1:.4f}")
        print(f"模型精确率: {precision:.4f}")
        print(f"模型召回率: {recall:.4f}")
        
        # 保存模型
        model_path = r'lightgbm_model_multi_dataset.joblib'
        joblib.dump(model, model_path)
        print(f"模型保存成功: {model_path}")
        
        # 保存训练配置和结果
        training_info = {
            'datasets': list(datasets_config.keys()),
            'original_data_shape': (X.shape, y.shape),
            'resampled_data_shape': (X_resampled.shape, y_resampled.shape),
            'test_size': 0.2,
            'model_params': params,
            'best_iteration': model.best_iteration,
            'metrics': {
                'accuracy': accuracy,
                'f1_score': f1,
                'precision': precision,
                'recall': recall
            }
        }
        
        info_path = r'training_info_multi_dataset.json'
        import json
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(training_info, f, indent=2, ensure_ascii=False)
        print(f"训练信息保存成功: {info_path}")
        
        return model_path
        
    except Exception as e:
        print(f"训练过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# 测试代码，仅在直接运行此文件时执行
if __name__ == "__main__":
    model_path = train_lightgbm_multi_dataset()
    if model_path:
        print(f"\n训练完成，模型保存路径: {model_path}")
    else:
        print("\n训练失败")
