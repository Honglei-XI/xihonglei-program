import os
import glob
import numpy as np
from src.data.extractFeture import preprocess_and_extract_features_mne_with_timestamps
from src.data.extractTarget import extractTarget


def load_bonn_dataset(base_path):
    """
    加载Bonn数据集
    
    Args:
        base_path: Bonn数据集的基本路径
        
    Returns:
        tuple: (特征数组, 标签数组)
    """
    try:
        print("加载Bonn数据集...")
        
        # Bonn数据集的类别文件夹
        classes = ['Z', 'O', 'N', 'F', 'S']  # 正常、其他、正常、焦点发作、全身性发作
        
        all_X = []
        all_y = []
        
        for cls_idx, cls in enumerate(classes):
            # 构建类别文件夹路径
            class_path = os.path.join(base_path, cls)
            
            # 查找所有.edf文件
            edf_files = glob.glob(os.path.join(class_path, '*.edf'))
            
            for edf_file in edf_files:
                try:
                    # 提取特征
                    X = preprocess_and_extract_features_mne_with_timestamps(edf_file)
                    X = X[:, 1:]  # 去除时间戳列
                    
                    # 根据类别设置标签
                    # 0: 正常, 1: 发作
                    if cls in ['F', 'S']:
                        y = np.ones(len(X))  # 发作
                    else:
                        y = np.zeros(len(X))  # 正常
                    
                    all_X.append(X)
                    all_y.append(y)
                    print(f"  处理文件: {os.path.basename(edf_file)}, 类别: {cls}, 样本数: {len(X)}")
                    
                except Exception as e:
                    print(f"  处理文件 {os.path.basename(edf_file)} 时出错: {str(e)}")
                    continue
        
        # 合并数据
        if all_X:
            X = np.vstack(all_X)
            y = np.hstack(all_y)
            print(f"Bonn数据集加载完成，X形状: {X.shape}, y形状: {y.shape}")
            return X, y
        else:
            print("Bonn数据集加载失败，未找到有效文件")
            return None, None
            
    except Exception as e:
        print(f"加载Bonn数据集时出错: {str(e)}")
        return None, None


def load_tusz_dataset(base_path):
    """
    加载TUSZ数据集
    
    Args:
        base_path: TUSZ数据集的基本路径
        
    Returns:
        tuple: (特征数组, 标签数组)
    """
    try:
        print("加载TUSZ数据集...")
        
        all_X = []
        all_y = []
        
        # 递归查找所有.edf文件
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith('.edf'):
                    edf_file = os.path.join(root, file)
                    
                    try:
                        # 提取特征
                        X = preprocess_and_extract_features_mne_with_timestamps(edf_file)
                        X = X[:, 1:]  # 去除时间戳列
                        
                        # 尝试从文件名或路径中获取标签
                        # 这里需要根据TUSZ数据集的具体结构进行调整
                        # 简单示例：如果路径中包含'seizure'则标记为发作
                        is_seizure = 'seizure' in root.lower() or 'sz' in file.lower()
                        y = np.ones(len(X)) if is_seizure else np.zeros(len(X))
                        
                        all_X.append(X)
                        all_y.append(y)
                        print(f"  处理文件: {os.path.basename(edf_file)}, 发作: {is_seizure}, 样本数: {len(X)}")
                        
                    except Exception as e:
                        print(f"  处理文件 {os.path.basename(edf_file)} 时出错: {str(e)}")
                        continue
        
        # 合并数据
        if all_X:
            X = np.vstack(all_X)
            y = np.hstack(all_y)
            print(f"TUSZ数据集加载完成，X形状: {X.shape}, y形状: {y.shape}")
            return X, y
        else:
            print("TUSZ数据集加载失败，未找到有效文件")
            return None, None
            
    except Exception as e:
        print(f"加载TUSZ数据集时出错: {str(e)}")
        return None, None


def load_barcelona_dataset(base_path):
    """
    加载Barcelona数据集
    
    Args:
        base_path: Barcelona数据集的基本路径
        
    Returns:
        tuple: (特征数组, 标签数组)
    """
    try:
        print("加载Barcelona数据集...")
        
        all_X = []
        all_y = []
        
        # 查找所有.edf文件
        edf_files = glob.glob(os.path.join(base_path, '**/*.edf'), recursive=True)
        
        for edf_file in edf_files:
            try:
                # 提取特征
                X = preprocess_and_extract_features_mne_with_timestamps(edf_file)
                X = X[:, 1:]  # 去除时间戳列
                
                # 尝试从文件名或路径中获取标签
                # 这里需要根据Barcelona数据集的具体结构进行调整
                is_seizure = 'seizure' in edf_file.lower() or 'sz' in edf_file.lower()
                y = np.ones(len(X)) if is_seizure else np.zeros(len(X))
                
                all_X.append(X)
                all_y.append(y)
                print(f"  处理文件: {os.path.basename(edf_file)}, 发作: {is_seizure}, 样本数: {len(X)}")
                
            except Exception as e:
                print(f"  处理文件 {os.path.basename(edf_file)} 时出错: {str(e)}")
                continue
        
        # 合并数据
        if all_X:
            X = np.vstack(all_X)
            y = np.hstack(all_y)
            print(f"Barcelona数据集加载完成，X形状: {X.shape}, y形状: {y.shape}")
            return X, y
        else:
            print("Barcelona数据集加载失败，未找到有效文件")
            return None, None
            
    except Exception as e:
        print(f"加载Barcelona数据集时出错: {str(e)}")
        return None, None


def load_freiburg_dataset(base_path):
    """
    加载Freiburg数据集
    
    Args:
        base_path: Freiburg数据集的基本路径
        
    Returns:
        tuple: (特征数组, 标签数组)
    """
    try:
        print("加载Freiburg数据集...")
        
        all_X = []
        all_y = []
        
        # 查找所有.edf文件
        edf_files = glob.glob(os.path.join(base_path, '**/*.edf'), recursive=True)
        
        for edf_file in edf_files:
            try:
                # 提取特征
                X = preprocess_and_extract_features_mne_with_timestamps(edf_file)
                X = X[:, 1:]  # 去除时间戳列
                
                # 尝试从文件名或路径中获取标签
                # 这里需要根据Freiburg数据集的具体结构进行调整
                is_seizure = 'seizure' in edf_file.lower() or 'sz' in edf_file.lower()
                y = np.ones(len(X)) if is_seizure else np.zeros(len(X))
                
                all_X.append(X)
                all_y.append(y)
                print(f"  处理文件: {os.path.basename(edf_file)}, 发作: {is_seizure}, 样本数: {len(X)}")
                
            except Exception as e:
                print(f"  处理文件 {os.path.basename(edf_file)} 时出错: {str(e)}")
                continue
        
        # 合并数据
        if all_X:
            X = np.vstack(all_X)
            y = np.hstack(all_y)
            print(f"Freiburg数据集加载完成，X形状: {X.shape}, y形状: {y.shape}")
            return X, y
        else:
            print("Freiburg数据集加载失败，未找到有效文件")
            return None, None
            
    except Exception as e:
        print(f"加载Freiburg数据集时出错: {str(e)}")
        return None, None


def load_all_datasets(datasets_config):
    """
    加载所有配置的数据集
    
    Args:
        datasets_config: 数据集配置字典，格式如下：
            {
                'bonn': '/path/to/bonn',
                'tusz': '/path/to/tusz',
                'barcelona': '/path/to/barcelona',
                'freiburg': '/path/to/freiburg'
            }
            
    Returns:
        tuple: (合并的特征数组, 合并的标签数组)
    """
    try:
        all_X = []
        all_y = []
        
        # 加载Bonn数据集
        if 'bonn' in datasets_config and datasets_config['bonn']:
            X_bonn, y_bonn = load_bonn_dataset(datasets_config['bonn'])
            if X_bonn is not None and y_bonn is not None:
                all_X.append(X_bonn)
                all_y.append(y_bonn)
        
        # 加载TUSZ数据集
        if 'tusz' in datasets_config and datasets_config['tusz']:
            X_tusz, y_tusz = load_tusz_dataset(datasets_config['tusz'])
            if X_tusz is not None and y_tusz is not None:
                all_X.append(X_tusz)
                all_y.append(y_tusz)
        
        # 加载Barcelona数据集
        if 'barcelona' in datasets_config and datasets_config['barcelona']:
            X_barcelona, y_barcelona = load_barcelona_dataset(datasets_config['barcelona'])
            if X_barcelona is not None and y_barcelona is not None:
                all_X.append(X_barcelona)
                all_y.append(y_barcelona)
        
        # 加载Freiburg数据集
        if 'freiburg' in datasets_config and datasets_config['freiburg']:
            X_freiburg, y_freiburg = load_freiburg_dataset(datasets_config['freiburg'])
            if X_freiburg is not None and y_freiburg is not None:
                all_X.append(X_freiburg)
                all_y.append(y_freiburg)
        
        # 合并所有数据
        if all_X:
            X = np.vstack(all_X)
            y = np.hstack(all_y)
            print(f"\n所有数据集加载完成，总样本数: {len(y)}")
            print(f"发作样本数: {int(np.sum(y))}, 正常样本数: {int(len(y) - np.sum(y))}")
            return X, y
        else:
            print("所有数据集加载失败，未找到有效文件")
            return None, None
            
    except Exception as e:
        print(f"加载所有数据集时出错: {str(e)}")
        return None, None
