import joblib
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score,f1_score
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from src.data.loaddata import load_data, load_dataX

subject_id = 1
base_path = "data"
all_X,all_y = load_data(subject_id,base_path)

# 合并 all_X 和 all_y
X = np.vstack(all_X)
y = np.concatenate(all_y)

# 初始化 SMOTE 实例
smote = SMOTE()
# 分割的数据集

# 应用 SMOTE 过采样
X_resampled, y_resampled = smote.fit_resample(X, y)

# 训练决策树分类器
clf = DecisionTreeClassifier(random_state=0)
clf.fit(X_resampled, y_resampled)
joblib.dump(clf, 'e:\\python project\\CHB-MIT-data-preprocessing-and-prediction-main\\decision_tree_model2.joblib')
# 对测试集进行预测
# y_pred = clf.predict(X_test)
#
# # 评估模型
# accuracy = accuracy_score(y_test, y_pred)
# print("Accuracy:", accuracy)
#
# # 计算 F1 分数
# f1 = f1_score(y_test, y_pred)
# print(f"F1 分数: {f1}")