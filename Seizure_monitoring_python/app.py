# 在文件最开始添加这些导入和配置
import matplotlib
matplotlib.use('Agg')  # 必须在导入 pyplot 之前设置
import json
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory, Response, abort
import requests
import os
import time
import logging
from urllib.parse import urlparse
from test import testdemo
import random
from func.zero_crossings_featureextraction import process_and_visualize_eeg
from func.stft_featureextraction2 import process_and_visualize_stft
from func.dwt import process_eeg_data
from func.uploadFile import upload_file  # 添加这行
import threading
from multiprocessing import Process

# 数据库相关导入
from config import engine, Base, get_db
from models import User, Patient, Todo, Notification, EegRecord, Ward

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 初始化数据库，添加管理员和测试账户
def init_db():
    db = next(get_db())
    try:
        # 检查是否已有用户
        user_count = db.query(User).count()
        if user_count == 0:
            # 添加管理员账户
            import uuid
            from datetime import datetime
            
            # 管理员账户
            admin_user = User(
                id=str(uuid.uuid4()),
                username='admin',
                password='admin123',
                name='管理员',
                userStatus=1,
                createTime=datetime.now(),
                updateTime=datetime.now()
            )
            db.add(admin_user)
            
            # 测试账户
            test_user = User(
                id=str(uuid.uuid4()),
                username='test',
                password='test123',
                name='测试用户',
                userStatus=1,
                createTime=datetime.now(),
                updateTime=datetime.now()
            )
            db.add(test_user)
            
            db.commit()
            print("数据库初始化完成，添加了管理员账户和测试账户")
            print("管理员账户: admin / admin123")
            print("测试账户: test / test123")
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

# 初始化数据库
init_db()

app = Flask(__name__)

# 配置静态文件服务
RESULTS_FOLDER = os.path.join(os.getcwd(), 'results')
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

# 添加静态文件路由
@app.route('/results/<path:filename>')
def serve_results(filename):
    """提供results文件夹中的静态文件"""
    return send_from_directory(RESULTS_FOLDER, filename)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """提供uploads文件夹中的静态文件"""
    return send_from_directory(UPLOAD_FOLDER, filename)

# 配置日志
app.logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.FileHandler('app.log')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# 确保上传目录存在
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    app.logger.info(f"创建上传目录: {UPLOAD_FOLDER}")
else:
    app.logger.info(f"上传目录已存在: {UPLOAD_FOLDER}")

@app.route("/analysis", methods=["GET"])
def analysis():
    """
    接收URL参数,下载文件并进行分析
    URL参数: url - 指向EDF文件的URL
    """
    app.logger.info("收到分析请求")
    
    # 获取 URL 参数
    url = request.args.get('url')
    if not url:
        app.logger.error("缺少URL参数")
        return jsonify({"error": "URL参数是必需的"}), 400
    
    app.logger.info(f"获得URL地址: {url}, 正在下载文件")
    
    try:
        # 生成唯一文件名，避免文件名冲突
        timestamp = int(time.time())
        app.logger.info(f"生成时间戳: {timestamp}")
        
        # 发起 HTTP 请求
        app.logger.info("开始下载文件")
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 检查请求是否成功
        app.logger.info("HTTP请求成功")

        # 从 URL 中提取文件名
        parsed_url = urlparse(url)
        original_filename = os.path.basename(parsed_url.path)
        app.logger.info(f"从URL提取的原始文件名: {original_filename}")
        
        # 确保文件名有效
        if not original_filename:
            original_filename = f"downloaded_file_{timestamp}.edf"
            app.logger.info(f"使用默认文件名: {original_filename}")
        
        # 确保文件名以.edf结尾
        if not original_filename.endswith('.edf'):
            original_filename += '.edf'
            app.logger.info(f"添加.edf后缀: {original_filename}")
            
        # 设置保存路径，使用时间戳避免冲突
        file_name = f"{timestamp}_{original_filename}"
        save_path = os.path.join(UPLOAD_FOLDER, file_name)
        app.logger.info(f"设置保存路径: {save_path}")

        # 流式下载并保存文件
        app.logger.info("开始保存文件")
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        
        app.logger.info(f"文件已下载到: {save_path}")
                    
        # 调用test.py中的testdemo函数进行检测
        app.logger.info("开始调用EEG分析函数进行发作检测")
        start_time, end_time = testdemo(save_path)
        app.logger.info(f"检测结果: start_time={start_time}, end_time={end_time}")
        
        # 检查分析结果
        if start_time is None or end_time is None:
            app.logger.info("未检测到发作")
            return jsonify({
                "code": 200,
                "message": "未检测到发作",
                "data": {
                    "start_time": "0",
                    "end_time": "0",
                    "riskLevel": random.randint(1, 20),
                    "anomalies": [  
                        {
                            "type": "轻微不规则波",
                            "severyity": "info"
                        }
                    ],
                    "rhythm": "正常",
                    "dischargeCount" : 12,
                    "frequency":"θ波为主",
                    "file_name": original_filename,
                    "file_size": os.path.getsize(save_path),
                }
            }), 200
        
        # 返回分析结果 - 检测到发作
        app.logger.info("检测到发作，开始计算风险等级")
        
        # 根据多因素计算风险等级
        def calculate_risk_level(start_time, end_time, eeg_file_path):
            """
            基于多因素计算癫痫发作风险等级
            """
            app.logger.info("开始风险等级计算")
            
            # 计算发作持续时间(秒)
            seizure_duration = float(end_time) - float(start_time)
            app.logger.info(f"发作持续时间: {seizure_duration}秒")
            
            # 基础风险分数 - 基于发作时长
            if seizure_duration < 10:
                base_risk = 60  # 短时发作
                app.logger.info("短时发作，基础风险分数: 60")
            elif seizure_duration < 30:
                base_risk = 75  # 中等时长发作
                app.logger.info("中等时长发作，基础风险分数: 75")
            else:
                base_risk = 85  # 长时发作
                app.logger.info("长时发作，基础风险分数: 85")
            
            # 模拟额外的风险因素
            intensity_factor = min(15, seizure_duration / 10)  # 发作强度因子
            app.logger.info(f"发作强度因子: {intensity_factor}")
            
            # 最终风险评分
            risk_level = min(95, base_risk + intensity_factor)
            app.logger.info(f"最终风险评分: {risk_level}")
            
            # 根据风险等级确定其他参数
            if risk_level < 70:
                discharge_count = random.randint(10, 15)
                rhythm_type = "轻度不规则"
                frequency_type = "以θ波为主，伴有少量β波"
                anomalies = [
                    {"type": "尖波", "severity": "warning"},
                    {"type": "慢波", "severity": "info"}
                ]
                app.logger.info("风险等级<70，轻度异常")
            elif risk_level < 80:
                discharge_count = random.randint(15, 20)
                rhythm_type = "中度不规则"
                frequency_type = "θ波与δ波混合"
                anomalies = [
                    {"type": "尖波", "severity": "warning"},
                    {"type": "慢波", "severity": "warning"},
                    {"type": "尖慢波复合", "severity": "info"}
                ]
                app.logger.info("风险等级<80，中度异常")
            else:
                discharge_count = random.randint(20, 30)
                rhythm_type = "严重不规则"
                frequency_type = "以δ波为主，伴有尖慢波复合"
                anomalies = [
                    {"type": "尖波", "severity": "danger"},
                    {"type": "慢波", "severity": "warning"},
                    {"type": "尖慢波复合", "severity": "danger"},
                    {"type": "节律性放电", "severity": "warning"}
                ]
                app.logger.info("风险等级>=80，严重异常")
            
            app.logger.info(f"异常放电次数: {discharge_count}, 节律类型: {rhythm_type}, 频率类型: {frequency_type}")
            return int(risk_level), anomalies, rhythm_type, discharge_count, frequency_type
        
        # 调用风险评估算法
        app.logger.info("调用风险评估算法")
        risk_level, anomalies, rhythm_type, discharge_count, frequency_type = calculate_risk_level(
            start_time, end_time, save_path
        )
        
        # 计算发作持续时间用于显示
        seizure_duration = float(end_time) - float(start_time)
        app.logger.info(f"准备返回结果，风险等级: {risk_level}")
            
        return jsonify({
            "code": 200,
            "message": "检测到发作",
            "data": {
                "start_time": start_time,
                "end_time": end_time,
                "seizure_duration": f"{seizure_duration:.2f}秒",
                "riskLevel": risk_level,
                "anomalies": anomalies,
                "rhythm": rhythm_type,
                "dischargeCount": discharge_count,
                "frequency": frequency_type,
                "file_name": original_filename,
                "file_size": os.path.getsize(save_path),
                "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
        }), 200

    except requests.exceptions.RequestException as e:
        app.logger.error(f"下载失败: {str(e)}")
        return jsonify({"error": f"下载失败: {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"发生未知错误: {str(e)}", exc_info=True)
        return jsonify({"error": f"发生未知错误: {str(e)}"}), 500
    finally:
        # 可以选择在这里清理临时文件
        app.logger.info("分析请求处理完成")
        pass


@app.route("/feature", methods=["GET"])
def extract_features():
    """
    接收URL参数，下载文件并进行三种特征提取分析
    URL参数: url - 指向EDF文件的URL
    """
    app.logger.info("收到特征提取请求")
    
    # 设置matplotlib后端
    os.environ['MPLBACKEND'] = 'Agg'
    app.logger.info("设置matplotlib后端为Agg")
    
    # 获取URL参数
    url = request.args.get('url')
    if not url:
        app.logger.error("缺少URL参数")
        return jsonify({"error": "URL参数是必需的"}), 400
    
    app.logger.info(f"获得URL地址: {url}")
    
    try:
        # 生成唯一文件名
        timestamp = int(time.time())
        app.logger.info(f"生成时间戳: {timestamp}")
        
        # 发起HTTP请求下载文件
        app.logger.info("开始下载文件")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        app.logger.info("HTTP请求成功")

        # 从URL中提取文件名
        parsed_url = urlparse(url)
        original_filename = os.path.basename(parsed_url.path)
        app.logger.info(f"从URL提取的原始文件名: {original_filename}")
        
        # 确保文件名有效
        if not original_filename:
            original_filename = f"downloaded_file_{timestamp}.edf"
            app.logger.info(f"使用默认文件名: {original_filename}")
        if not original_filename.endswith('.edf'):
            original_filename += '.edf'
            app.logger.info(f"添加.edf后缀: {original_filename}")
            
        # 设置保存路径
        file_name = f"{timestamp}_{original_filename}"
        save_path = os.path.join(UPLOAD_FOLDER, file_name)
        app.logger.info(f"设置保存路径: {save_path}")

        # 流式下载文件
        app.logger.info("开始保存文件")
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        
        app.logger.info(f"文件已下载到: {save_path}")
        
        try:
            app.logger.info("开始特征提取过程")
            # 使用线程本地存储来隔离matplotlib状态
            zero_cross_urls = []
            stft_urls = []
            dwt_urls = []
            
            # 定义线程函数
            def run_zero_crossing():
                app.logger.info("开始零交叉特征提取")
                nonlocal zero_cross_urls
                try:
                    _, _, result = process_and_visualize_eeg(
                        save_path,
                        window_size_sec=6,
                        step_size_sec=3,
                        max_channels=5
                    )
                    zero_cross_urls = result
                    app.logger.info(f"零交叉特征提取完成，获得{len(result)}个结果")
                except Exception as e:
                    app.logger.error(f"零交叉特征提取失败: {str(e)}", exc_info=True)
                    raise
            
            def run_stft():
                app.logger.info("开始STFT特征提取")
                nonlocal stft_urls
                try:
                    _, result = process_and_visualize_stft(
                        save_path,
                        max_channels=5
                    )
                    stft_urls = result
                    app.logger.info(f"STFT特征提取完成，获得{len(result)}个结果")
                except Exception as e:
                    app.logger.error(f"STFT特征提取失败: {str(e)}", exc_info=True)
                    raise
            
            def run_dwt():
                app.logger.info("开始DWT特征提取")
                nonlocal dwt_urls
                try:
                    _, _, result = process_eeg_data(
                        save_path,
                        window_size_sec=5,
                        step_size_sec=3,
                        max_channels=5
                    )
                    dwt_urls = result
                    app.logger.info(f"DWT特征提取完成，获得{len(result)}个结果")
                except Exception as e:
                    app.logger.error(f"DWT特征提取失败: {str(e)}", exc_info=True)
                    raise
            
            # 依次运行各个特征提取（不使用并行以避免资源竞争）
            app.logger.info("依次运行各个特征提取")
            run_zero_crossing()
            run_stft()
            run_dwt()
            app.logger.info("所有特征提取完成")

            # 整理返回结果
            app.logger.info("准备返回特征提取结果")
            return jsonify({
                "code": 200,
                "message": "特征提取成功",
                "data": {
                    "file_name": original_filename,
                    "file_size": os.path.getsize(save_path),
                    "features": {
                        "zero_crossing": {
                            "images": [
                                {
                                    "channel": item["channel"],
                                    "url": item["url"]
                                } for item in zero_cross_urls
                            ]
                        },
                        "stft": {
                            "images": [
                                {
                                    "channel": item["channel"],
                                    "url": item["url"]
                                } for item in stft_urls
                            ]
                        },
                        "dwt": {
                            "images": [
                                {
                                    "url": item["url"]
                                } for item in dwt_urls
                            ]
                        }
                    }
                }
            }), 200

        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            app.logger.error(f"特征提取过程出错: {str(e)}\n{traceback_str}")
            print(f"特征提取错误: {str(e)}\n{traceback_str}")
            return jsonify({
                "code": 500,
                "message": f"特征提取过程出错: {str(e)}",
                "data": None
            }), 500

    except requests.exceptions.RequestException as e:
        app.logger.error(f"下载文件失败: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"下载文件失败: {str(e)}",
            "data": None
        }), 500
    except Exception as e:
        app.logger.error(f"发生未知错误: {str(e)}", exc_info=True)
        return jsonify({
            "code": 500,
            "message": f"发生未知错误: {str(e)}",
            "data": None
        }), 500
    finally:
        # 可以选择在这里清理临时文件
        app.logger.info("特征提取请求处理完成，清理临时文件")
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
                app.logger.info(f"临时文件已删除: {save_path}")
        except Exception as e:
            app.logger.warning(f"删除临时文件失败: {str(e)}")
            pass


# 模拟token存储
tokens = {}

@app.route("/user/login", methods=["POST"])
def user_login():
    """
    用户登录接口
    """
    try:
        # 获取请求参数
        username = request.form.get('username')
        password = request.form.get('password')
        
        app.logger.info(f"登录请求: username={username}")
        
        # 验证参数
        if not username or not password:
            app.logger.error("缺少用户名或密码")
            return jsonify({"code": 1, "msg": "缺少用户名或密码", "data": None}), 400
        
        # 从数据库中验证用户
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        
        if not user or user.password != password:
            app.logger.error("用户名或密码错误")
            return jsonify({"code": 1, "msg": "用户名或密码错误", "data": None}), 401
        
        # 生成token（简单的模拟token）
        import uuid
        token = str(uuid.uuid4())
        tokens[token] = username
        
        app.logger.info(f"登录成功: username={username}, token={token}")
        
        # 返回结果
        return jsonify({
            "code": 0,
            "msg": "登录成功",
            "data": token
        }), 200
    except Exception as e:
        app.logger.error(f"登录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "msg": f"登录失败: {str(e)}", "data": None}), 500

@app.route("/user/info", methods=["GET"])
def user_info():
    """
    获取用户信息接口
    """
    try:
        # 获取token
        token = request.headers.get('Authorization')
        
        app.logger.info(f"获取用户信息请求: token={token}")
        
        # 验证token
        if not token or token not in tokens:
            app.logger.error("无效的token")
            return jsonify({"code": 1, "msg": "无效的token", "data": None}), 401
        
        # 获取用户名
        username = tokens[token]
        
        # 从数据库中获取用户信息
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            app.logger.error(f"用户不存在: username={username}")
            return jsonify({"code": 1, "msg": "用户不存在", "data": None}), 404
        
        app.logger.info(f"获取用户信息成功: username={username}")
        
        # 返回用户信息
        return jsonify({
            "code": 0,
            "msg": "获取用户信息成功",
            "data": {
                "id": user.id,
                "username": user.username,
                "role": getattr(user, 'role', 'user'),
                "name": user.name
            }
        }), 200
    except Exception as e:
        app.logger.error(f"获取用户信息失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "msg": f"获取用户信息失败: {str(e)}", "data": None}), 500

@app.route("/user/test", methods=["GET"])
def user_test():
    """
    测试接口
    """
    try:
        app.logger.info("测试接口被调用")
        return jsonify({
            "code": 0,
            "msg": "测试成功",
            "data": "测试接口正常工作"
        }), 200
    except Exception as e:
        app.logger.error(f"测试接口失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "msg": f"测试接口失败: {str(e)}", "data": None}), 500

@app.route("/user/count", methods=["GET"])
def user_count():
    """
    获取用户数量接口
    """
    try:
        app.logger.info("获取用户数量请求")
        
        # 从数据库中获取用户数量
        db = next(get_db())
        user_count = db.query(User).count()
        
        return jsonify({
            "code": 0,
            "msg": "获取用户数量成功",
            "data": user_count
        }), 200
    except Exception as e:
        app.logger.error(f"获取用户数量失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "msg": f"获取用户数量失败: {str(e)}", "data": None}), 500

@app.route("/user/list", methods=["GET"])
def user_list():
    """
    获取用户列表接口
    """
    try:
        app.logger.info("获取用户列表请求")
        # 获取参数
        page_num = request.args.get('pageNum', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        
        # 从数据库中获取用户列表
        db = next(get_db())
        
        # 计算总数
        total = db.query(User).count()
        
        # 分页查询
        start = (page_num - 1) * page_size
        users = db.query(User).offset(start).limit(page_size).all()
        
        # 构建返回列表
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "role": getattr(user, 'role', 'user'),
                "name": user.name,
                "email": user.email or '',
                "createTime": user.createTime or '',
                "updateTime": user.updateTime or '',
                "userStatus": user.userStatus or 1
            })
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": {
                "items": user_list,
                "total": total
            }
        }), 200
    except Exception as e:
        app.logger.error(f"获取用户列表失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取用户列表失败: {str(e)}", "data": None}), 500


@app.route("/user/register", methods=["POST"])
def register_user():
    """
    添加用户接口
    """
    try:
        app.logger.info("添加用户请求")
        # 获取请求参数
        data = request.json
        
        # 验证参数
        if not data or 'username' not in data or 'password' not in data:
            app.logger.error("缺少请求参数或用户名/密码")
            return jsonify({"code": 1, "message": "缺少请求参数或用户名/密码", "data": None}), 400
        
        # 从数据库中获取用户列表
        db = next(get_db())
        
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == data.get('username')).first()
        if existing_user:
            app.logger.error(f"用户名已存在: username={data.get('username')}")
            return jsonify({"code": 1, "message": "用户名已存在", "data": None}), 400
        
        # 创建新用户
        from datetime import datetime
        new_user = User(
            id=str(int(time.time())),  # 使用时间戳作为ID
            username=data.get('username', ''),
            password=data.get('password', ''),
            name=data.get('name', ''),
            email=data.get('email', ''),
            createTime=datetime.now(),
            updateTime=datetime.now(),
            userStatus=1
        )
        
        # 添加到数据库
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        app.logger.info(f"添加用户成功: id={new_user.id}, username={new_user.username}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": {
                "id": new_user.id,
                "username": new_user.username,
                "password": new_user.password,
                "name": new_user.name,
                "email": new_user.email,
                "createTime": new_user.createTime,
                "updateTime": new_user.updateTime,
                "userStatus": new_user.userStatus,
                "role": "user"
            }
        }), 200
    except Exception as e:
        app.logger.error(f"添加用户失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"添加用户失败: {str(e)}", "data": None}), 500


@app.route("/user/status", methods=["POST"])
def update_user_status():
    """
    修改用户状态接口
    """
    try:
        app.logger.info("修改用户状态请求")
        # 获取请求参数
        data = request.json
        
        # 验证参数
        if not data or 'id' not in data or 'userStatus' not in data:
            app.logger.error("缺少请求参数或用户ID/状态")
            return jsonify({"code": 1, "message": "缺少请求参数或用户ID/状态", "data": None}), 400
        
        # 从数据库中查找用户
        db = next(get_db())
        target_user = db.query(User).filter(User.id == str(data['id'])).first()
        
        if not target_user:
            app.logger.error(f"用户不存在: id={data['id']}")
            return jsonify({"code": 1, "message": "用户不存在", "data": None}), 404
        
        # 更新状态
        from datetime import datetime
        target_user.userStatus = data['userStatus']
        target_user.updateTime = datetime.now()
        
        # 提交到数据库
        db.commit()
        db.refresh(target_user)
        
        app.logger.info(f"修改用户状态成功: id={data['id']}, userStatus={data['userStatus']}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": {
                "id": target_user.id,
                "username": target_user.username,
                "name": target_user.name,
                "email": target_user.email,
                "userStatus": target_user.userStatus,
                "createTime": target_user.createTime,
                "updateTime": target_user.updateTime
            }
        }), 200
    except Exception as e:
        app.logger.error(f"修改用户状态失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"修改用户状态失败: {str(e)}", "data": None}), 500


@app.route("/user/update", methods=["POST"])
def update_user():
    """
    修改用户信息接口
    """
    try:
        app.logger.info("修改用户信息请求")
        # 获取请求参数
        data = request.json
        
        # 验证参数
        if not data or 'id' not in data:
            app.logger.error("缺少请求参数或用户ID")
            return jsonify({"code": 1, "message": "缺少请求参数或用户ID", "data": None}), 400
        
        # 从数据库中查找用户
        db = next(get_db())
        target_user = db.query(User).filter(User.id == str(data['id'])).first()
        
        if not target_user:
            app.logger.error(f"用户不存在: id={data['id']}")
            return jsonify({"code": 1, "message": "用户不存在", "data": None}), 404
        
        # 更新用户信息
        from datetime import datetime
        
        # 更新字段
        if 'username' in data:
            target_user.username = data['username']
        if 'name' in data:
            target_user.name = data['name']
        if 'password' in data:
            target_user.password = data['password']
        if 'email' in data:
            target_user.email = data['email']
        if 'userStatus' in data:
            target_user.userStatus = data['userStatus']
        
        target_user.updateTime = datetime.now()
        
        # 提交到数据库
        db.commit()
        db.refresh(target_user)
        
        app.logger.info(f"修改用户信息成功: id={data['id']}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": {
                "id": target_user.id,
                "username": target_user.username,
                "name": target_user.name,
                "email": target_user.email,
                "userStatus": target_user.userStatus,
                "createTime": target_user.createTime,
                "updateTime": target_user.updateTime
            }
        }), 200
    except Exception as e:
        app.logger.error(f"修改用户信息失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"修改用户信息失败: {str(e)}", "data": None}), 500


@app.route("/todo/list", methods=["GET"])
def get_todo_list():
    """
    获取待办事项列表接口
    """
    try:
        app.logger.info("获取待办事项列表请求")
        # 获取分页参数
        page_num = request.args.get('pageNum', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        
        # 从数据库中获取待办事项列表
        db = next(get_db())
        
        # 计算总数
        total = db.query(Todo).count()
        
        # 分页查询
        start = (page_num - 1) * page_size
        todos = db.query(Todo).offset(start).limit(page_size).all()
        
        # 构建返回列表
        paginated_todos = []
        for todo in todos:
            paginated_todos.append({
                "id": todo.id,
                "title": getattr(todo, 'title', ''),
                "content": todo.content,
                "completed": todo.completed,
                "time": todo.time,
                "type": todo.type,
                "createTime": todo.createTime,
                "updateTime": todo.updateTime
            })
        
        app.logger.info(f"返回待办事项列表: 共{total}条，当前页{page_num}，每页{page_size}条")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": {
                "items": paginated_todos,
                "total": total
            }
        }), 200
    except Exception as e:
        app.logger.error(f"获取待办事项列表失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取待办事项列表失败: {str(e)}", "data": None}), 500


@app.route("/notification/list", methods=["GET"])
def get_notification_list():
    """
    获取通知列表接口
    """
    try:
        app.logger.info("获取通知列表请求")
        
        # 从数据库中获取通知列表
        db = next(get_db())
        notifications = db.query(Notification).all()
        
        # 构建返回列表
        notification_list = []
        for notification in notifications:
            notification_list.append({
                "id": notification.id,
                "userId": notification.userId,
                "title": notification.title,
                "content": notification.content,
                "createTime": notification.createTime,
                "updateTime": notification.updateTime
            })
        
        app.logger.info(f"返回通知列表: 共{len(notification_list)}条")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": notification_list
        }), 200
    except Exception as e:
        app.logger.error(f"获取通知列表失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取通知列表失败: {str(e)}", "data": None}), 500





@app.route("/patient", methods=["GET"])
def get_patient_list():
    """
    分页查询病人接口
    """
    try:
        app.logger.info("分页查询病人请求")
        # 获取分页参数
        page_num = request.args.get('pageNum', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        name = request.args.get('name', '', type=str)
        
        # 从数据库中获取患者列表
        db = next(get_db())
        
        # 构建查询
        query = db.query(Patient)
        
        # 筛选患者
        if name:
            query = query.filter(Patient.name.contains(name))
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        start = (page_num - 1) * page_size
        patients = query.offset(start).limit(page_size).all()
        
        # 构建返回列表
        patient_list = []
        for patient in patients:
            patient_list.append({
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "male": patient.male,
                "phone": patient.phone,
                "address": patient.address,
                "doctorId": patient.doctorId,
                "departmentId": patient.departmentId,
                "diagnosis": patient.diagnosis,
                "text": patient.text,
                "createTime": patient.createTime,
                "updateTime": patient.updateTime
            })
        
        app.logger.info(f"返回患者列表: 共{total}条，当前页{page_num}，每页{page_size}条")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": {
                "items": patient_list,
                "total": total
            }
        }), 200
    except Exception as e:
        app.logger.error(f"分页查询病人失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"分页查询病人失败: {str(e)}", "data": None}), 500


@app.route("/patient", methods=["POST"])
def add_patient():
    """
    增加病人信息接口
    """
    try:
        app.logger.info("增加病人信息请求")
        # 获取请求参数
        data = request.json
        
        # 验证参数
        if not data:
            app.logger.error("缺少请求参数")
            return jsonify({"code": 1, "message": "缺少请求参数", "data": None}), 400
        
        # 从数据库中获取患者列表
        db = next(get_db())
        
        # 创建新患者
        from datetime import datetime, date
        new_patient = Patient(
            name=data.get('name', ''),
            age=data.get('age', ''),
            male=data.get('male', '男'),
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            doctorId=data.get('doctorId', ''),
            departmentId=data.get('departmentId', ''),
            diagnosis=data.get('diagnosis', ''),
            text=data.get('text', ''),
            createTime=date.today(),
            updateTime=date.today()
        )
        
        # 添加到数据库
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        
        app.logger.info(f"增加病人成功: id={new_patient.id}, name={new_patient.name}")
        
        # 构建返回数据
        return_data = {
            "id": new_patient.id,
            "name": new_patient.name,
            "age": new_patient.age,
            "male": new_patient.male,
            "phone": new_patient.phone,
            "address": new_patient.address,
            "doctorId": new_patient.doctorId,
            "departmentId": new_patient.departmentId,
            "diagnosis": new_patient.diagnosis,
            "text": new_patient.text,
            "createTime": new_patient.createTime,
            "updateTime": new_patient.updateTime
        }
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": return_data
        }), 200
    except Exception as e:
        app.logger.error(f"增加病人信息失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"增加病人信息失败: {str(e)}", "data": None}), 500


@app.route("/patient", methods=["PUT"])
def update_patient():
    """
    更新病人信息接口
    """
    try:
        app.logger.info("更新病人信息请求")
        # 获取请求参数
        data = request.json
        
        # 验证参数
        if not data or 'id' not in data:
            app.logger.error("缺少请求参数或患者ID")
            return jsonify({"code": 1, "message": "缺少请求参数或患者ID", "data": None}), 400
        
        # 从数据库中查找患者
        db = next(get_db())
        patient_id = data['id']
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            app.logger.error(f"患者不存在: id={patient_id}")
            return jsonify({"code": 1, "message": "患者不存在", "data": None}), 404
        
        # 更新患者信息
        from datetime import date
        
        # 更新字段
        if 'name' in data:
            patient.name = data['name']
        if 'age' in data:
            patient.age = data['age']
        if 'male' in data:
            patient.male = data['male']
        if 'phone' in data:
            patient.phone = data['phone']
        if 'address' in data:
            patient.address = data['address']
        if 'doctorId' in data:
            patient.doctorId = data['doctorId']
        if 'departmentId' in data:
            patient.departmentId = data['departmentId']
        if 'diagnosis' in data:
            patient.diagnosis = data['diagnosis']
        if 'text' in data:
            patient.text = data['text']
        
        patient.updateTime = date.today()
        
        # 提交到数据库
        db.commit()
        db.refresh(patient)
        
        app.logger.info(f"更新病人成功: id={patient_id}")
        
        # 构建返回数据
        return_data = {
            "id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "male": patient.male,
            "phone": patient.phone,
            "address": patient.address,
            "doctorId": patient.doctorId,
            "departmentId": patient.departmentId,
            "diagnosis": patient.diagnosis,
            "text": patient.text,
            "createTime": patient.createTime,
            "updateTime": patient.updateTime
        }
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": return_data
        }), 200
    except Exception as e:
        app.logger.error(f"更新病人信息失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"更新病人信息失败: {str(e)}", "data": None}), 500


@app.route("/patient", methods=["DELETE"])
def delete_patient():
    """
    删除病人信息接口
    """
    try:
        app.logger.info("删除病人信息请求")
        # 获取请求参数
        patient_id = request.args.get('id', type=int)
        
        # 验证参数
        if not patient_id:
            app.logger.error("缺少患者ID")
            return jsonify({"code": 1, "message": "缺少患者ID", "data": None}), 400
        
        # 从数据库中查找患者
        db = next(get_db())
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            app.logger.error(f"患者不存在: id={patient_id}")
            return jsonify({"code": 1, "message": "患者不存在", "data": None}), 404
        
        # 删除患者
        db.delete(patient)
        db.commit()
        
        app.logger.info(f"删除病人成功: id={patient_id}, name={patient.name}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": None
        }), 200
    except Exception as e:
        app.logger.error(f"删除病人信息失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"删除病人信息失败: {str(e)}", "data": None}), 500


@app.route("/patient/all", methods=["GET"])
def get_all_patients():
    """
    获取所有病人列表接口
    """
    try:
        app.logger.info("获取所有病人列表请求")
        
        # 从数据库中获取所有患者列表
        db = next(get_db())
        patients = db.query(Patient).all()
        
        # 构建返回列表
        patient_list = []
        for patient in patients:
            patient_list.append({
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "male": patient.male,
                "phone": patient.phone,
                "address": patient.address,
                "doctorId": patient.doctorId,
                "departmentId": patient.departmentId,
                "diagnosis": patient.diagnosis,
                "text": patient.text,
                "createTime": patient.createTime,
                "updateTime": patient.updateTime
            })
        
        app.logger.info(f"返回所有患者列表: 共{len(patient_list)}条")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": patient_list
        }), 200
    except Exception as e:
        app.logger.error(f"获取所有病人列表失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取所有病人列表失败: {str(e)}", "data": None}), 500


@app.route("/patient/diagnosis", methods=["PUT"])
def update_patient_diagnosis():
    """
    填写病人诊断信息接口
    """
    try:
        app.logger.info("填写病人诊断信息请求")
        # 获取请求参数
        data = request.json
        
        # 验证参数
        if not data or 'id' not in data or 'diagnosis' not in data:
            app.logger.error("缺少请求参数或患者ID或诊断信息")
            return jsonify({"code": 1, "message": "缺少请求参数或患者ID或诊断信息", "data": None}), 400
        
        # 从数据库中查找患者
        db = next(get_db())
        patient_id = data['id']
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            app.logger.error(f"患者不存在: id={patient_id}")
            return jsonify({"code": 1, "message": "患者不存在", "data": None}), 404
        
        # 更新诊断信息
        from datetime import date
        patient.diagnosis = data['diagnosis']
        patient.updateTime = date.today()
        
        # 提交到数据库
        db.commit()
        db.refresh(patient)
        
        app.logger.info(f"更新病人诊断信息成功: id={patient_id}")
        
        # 构建返回数据
        return_data = {
            "id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "male": patient.male,
            "phone": patient.phone,
            "address": patient.address,
            "doctorId": patient.doctorId,
            "departmentId": patient.departmentId,
            "diagnosis": patient.diagnosis,
            "text": patient.text,
            "createTime": patient.createTime,
            "updateTime": patient.updateTime
        }
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": return_data
        }), 200
    except Exception as e:
        app.logger.error(f"填写病人诊断信息失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"填写病人诊断信息失败: {str(e)}", "data": None}), 500





@app.route("/notification", methods=["POST"])
def add_notification():
    """
    新建通知接口
    """
    try:
        app.logger.info("新建通知请求")
        # 获取请求参数
        data = request.json
        
        # 验证参数
        if not data or 'title' not in data or 'content' not in data:
            app.logger.error("缺少请求参数或标题或内容")
            return jsonify({"code": 1, "message": "缺少请求参数或标题或内容", "data": None}), 400
        
        # 从数据库中获取通知列表
        db = next(get_db())
        
        # 创建新通知
        from datetime import datetime
        new_notification = Notification(
            userId=1,  # 默认为1
            title=data.get('title', ''),
            content=data.get('content', ''),
            createTime=datetime.now(),
            updateTime=datetime.now()
        )
        
        # 添加到数据库
        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)
        
        app.logger.info(f"新建通知成功: id={new_notification.id}, title={new_notification.title}")
        
        # 构建返回数据
        return_data = {
            "id": new_notification.id,
            "userId": new_notification.userId,
            "title": new_notification.title,
            "content": new_notification.content,
            "createTime": new_notification.createTime,
            "updateTime": new_notification.updateTime
        }
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": return_data
        }), 200
    except Exception as e:
        app.logger.error(f"新建通知失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"新建通知失败: {str(e)}", "data": None}), 500





@app.route("/todo/add", methods=["POST"])
def add_todo():
    """
    添加待办事项接口
    """
    try:
        app.logger.info("添加待办事项请求")
        # 获取请求参数
        data = request.json
        
        # 验证参数
        if not data or 'title' not in data:
            app.logger.error("缺少请求参数或标题")
            return jsonify({"code": 1, "message": "缺少请求参数或标题", "data": None}), 400
        
        # 从数据库中获取待办事项列表
        db = next(get_db())
        
        # 创建新待办事项（匹配前端字段结构）
        from datetime import datetime
        
        # 解析时间字段
        time_str = data.get('time', '')
        time_obj = None
        if time_str:
            try:
                time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                time_obj = None
        
        new_todo = Todo(
            content=data.get('content', ''),
            completed=bool(data.get('completed', 0)),  # 匹配前端的completed字段
            time=time_obj,  # 前端的截止时间字段
            type=data.get('type', ''),  # 前端的优先级字段
            userId=1,  # 默认为1
            createTime=datetime.now(),
            updateTime=datetime.now()
        )
        
        # 添加到数据库
        db.add(new_todo)
        db.commit()
        db.refresh(new_todo)
        
        app.logger.info(f"添加待办事项成功: id={new_todo.id}, title={getattr(new_todo, 'title', '')}")
        
        # 构建返回数据
        return_data = {
            "id": new_todo.id,
            "title": getattr(new_todo, 'title', ''),
            "content": new_todo.content,
            "completed": new_todo.completed,
            "time": new_todo.time,
            "type": new_todo.type,
            "createTime": new_todo.createTime,
            "updateTime": new_todo.updateTime
        }
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": return_data
        }), 200
    except Exception as e:
        app.logger.error(f"添加待办事项失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"添加待办事项失败: {str(e)}", "data": None}), 500


@app.route("/todo/status", methods=["PUT"])
def update_todo_status():
    """
    更新待办事项状态接口
    """
    try:
        app.logger.info("更新待办事项状态请求")
        # 获取请求参数
        todo_id = request.args.get('id', type=int)
        completed = request.args.get('completed', type=int)
        
        # 验证参数
        if todo_id is None:
            app.logger.error("缺少待办事项ID")
            return jsonify({"code": 1, "message": "缺少待办事项ID", "data": None}), 400
        
        # 从数据库中查找待办事项
        db = next(get_db())
        todo = db.query(Todo).filter(Todo.id == todo_id).first()
        
        if not todo:
            app.logger.error(f"待办事项不存在: id={todo_id}")
            return jsonify({"code": 1, "message": "待办事项不存在", "data": None}), 404
        
        # 更新状态
        from datetime import datetime
        todo.completed = bool(completed)
        todo.updateTime = datetime.now()
        
        # 提交到数据库
        db.commit()
        db.refresh(todo)
        
        app.logger.info(f"更新待办事项状态成功: id={todo_id}, completed={completed}")
        
        # 构建返回数据
        return_data = {
            "id": todo.id,
            "title": getattr(todo, 'title', ''),
            "content": todo.content,
            "completed": todo.completed,
            "time": todo.time,
            "type": todo.type,
            "createTime": todo.createTime,
            "updateTime": todo.updateTime
        }
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": return_data
        }), 200
    except Exception as e:
        app.logger.error(f"更新待办事项状态失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"更新待办事项状态失败: {str(e)}", "data": None}), 500


@app.route("/todo/delete/<int:id>", methods=["DELETE"])
def delete_todo(id):
    """
    删除待办事项接口
    """
    try:
        app.logger.info(f"删除待办事项请求: id={id}")
        
        # 从数据库中查找待办事项
        db = next(get_db())
        todo = db.query(Todo).filter(Todo.id == id).first()
        
        if not todo:
            app.logger.error(f"待办事项不存在: id={id}")
            return jsonify({"code": 1, "message": "待办事项不存在", "data": None}), 404
        
        # 删除待办事项
        db.delete(todo)
        db.commit()
        
        app.logger.info(f"删除待办事项成功: id={id}, title={getattr(todo, 'title', '')}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": None
        }), 200
    except Exception as e:
        app.logger.error(f"删除待办事项失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"删除待办事项失败: {str(e)}", "data": None}), 500





@app.route("/eeg", methods=["GET"])
def get_eeg_list():
    """
    获取EEG记录列表接口
    """
    try:
        app.logger.info("获取EEG记录列表请求")
        # 获取分页参数
        page_num = request.args.get('pageNum', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        
        # 计算分页
        start = (page_num - 1) * page_size
        end = start + page_size
        paginated_eegs = eeg_records[start:end]
        
        app.logger.info(f"返回EEG记录列表: 共{len(eeg_records)}条，当前页{page_num}，每页{page_size}条")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": {
                "items": paginated_eegs,
                "total": len(eeg_records)
            }
        }), 200
    except Exception as e:
        app.logger.error(f"获取EEG记录列表失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取EEG记录列表失败: {str(e)}", "data": None}), 500


@app.route("/eeg", methods=["POST"])
def add_eeg():
    """
    添加EEG记录接口
    """
    try:
        app.logger.info("添加EEG记录请求")
        # 获取请求参数
        data = request.json
        
        # 验证参数
        if not data:
            app.logger.error("缺少请求参数")
            return jsonify({"code": 1, "message": "缺少请求参数", "data": None}), 400
        
        # 生成新EEG记录ID
        new_id = max([e['id'] for e in eeg_records]) + 1 if eeg_records else 1
        
        # 创建新EEG记录
        new_eeg = {
            "id": new_id,
            "patientId": data.get('patientId', 0),
            "userId": data.get('userId', 0),
            "fileUrl": data.get('fileUrl', ''),
            "createTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "analysisResult": data.get('analysisResult', {})
        }
        
        # 添加到EEG记录列表
        eeg_records.append(new_eeg)
        app.logger.info(f"添加EEG记录成功: id={new_id}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": new_eeg
        }), 200
    except Exception as e:
        app.logger.error(f"添加EEG记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"添加EEG记录失败: {str(e)}", "data": None}), 500


@app.route("/eeg", methods=["PUT"])
def update_eeg():
    """
    更新EEG记录接口
    """
    try:
        app.logger.info("更新EEG记录请求")
        # 获取请求参数
        data = request.json
        
        # 验证参数
        if not data or 'id' not in data:
            app.logger.error("缺少请求参数或EEG记录ID")
            return jsonify({"code": 1, "message": "缺少请求参数或EEG记录ID", "data": None}), 400
        
        # 查找EEG记录
        eeg_id = data['id']
        eeg_index = next((i for i, e in enumerate(eeg_records) if e['id'] == eeg_id), -1)
        
        if eeg_index == -1:
            app.logger.error(f"EEG记录不存在: id={eeg_id}")
            return jsonify({"code": 1, "message": "EEG记录不存在", "data": None}), 404
        
        # 更新EEG记录
        eeg_records[eeg_index].update(data)
        app.logger.info(f"更新EEG记录成功: id={eeg_id}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": eeg_records[eeg_index]
        }), 200
    except Exception as e:
        app.logger.error(f"更新EEG记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"更新EEG记录失败: {str(e)}", "data": None}), 500


@app.route("/eeg", methods=["DELETE"])
def delete_eeg():
    """
    删除EEG记录接口
    """
    try:
        app.logger.info("删除EEG记录请求")
        # 获取请求参数
        eeg_id = request.args.get('id', type=int)
        
        # 验证参数
        if not eeg_id:
            app.logger.error("缺少EEG记录ID")
            return jsonify({"code": 1, "message": "缺少EEG记录ID", "data": None}), 400
        
        # 查找EEG记录
        eeg_index = next((i for i, e in enumerate(eeg_records) if e['id'] == eeg_id), -1)
        
        if eeg_index == -1:
            app.logger.error(f"EEG记录不存在: id={eeg_id}")
            return jsonify({"code": 1, "message": "EEG记录不存在", "data": None}), 404
        
        # 删除EEG记录
        deleted_eeg = eeg_records.pop(eeg_index)
        app.logger.info(f"删除EEG记录成功: id={eeg_id}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": None
        }), 200
    except Exception as e:
        app.logger.error(f"删除EEG记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"删除EEG记录失败: {str(e)}", "data": None}), 500


@app.route("/eeg/data", methods=["GET"])
def get_eeg_data():
    """
    获取EEG记录数据接口
    """
    try:
        app.logger.info("获取EEG记录数据请求")
        # 获取请求参数
        eeg_id = request.args.get('id', type=int)
        
        # 验证参数
        if not eeg_id:
            app.logger.error("缺少EEG记录ID")
            return jsonify({"code": 1, "message": "缺少EEG记录ID", "data": None}), 400
        
        # 查找EEG记录
        eeg_record = next((e for e in eeg_records if e['id'] == eeg_id), None)
        
        if not eeg_record:
            app.logger.error(f"EEG记录不存在: id={eeg_id}")
            return jsonify({"code": 1, "message": "EEG记录不存在", "data": None}), 404
        
        app.logger.info(f"返回EEG记录数据: id={eeg_id}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": eeg_record
        }), 200
    except Exception as e:
        app.logger.error(f"获取EEG记录数据失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取EEG记录数据失败: {str(e)}", "data": None}), 500


@app.route("/eeg/upload", methods=["POST"])
def upload_eeg_file():
    """
    上传EEG文件接口
    """
    try:
        app.logger.info("上传EEG文件请求")
        # 获取上传的文件
        file = request.files.get('file')
        
        # 验证文件
        if not file:
            app.logger.error("缺少上传文件")
            return jsonify({"code": 1, "message": "缺少上传文件", "data": None}), 400
        
        # 保存文件
        file_name = file.filename
        save_path = os.path.join(UPLOAD_FOLDER, file_name)
        file.save(save_path)
        
        # 生成文件URL
        # 转换为正确的file://格式
        absolute_path = os.path.abspath(save_path)
        # 在Windows上，file://协议需要三个斜杠，并且使用正斜杠
        if os.name == 'nt':
            file_url = f"file:///{absolute_path.replace('\\', '/')}"
        else:
            file_url = f"file://{absolute_path}"
        app.logger.info(f"生成的fileUrl: {file_url}")
        
        app.logger.info(f"上传EEG文件成功: {file_name}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": {
                "fileUrl": file_url,
                "fileName": file_name
            }
        }), 200
    except Exception as e:
        app.logger.error(f"上传EEG文件失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"上传EEG文件失败: {str(e)}", "data": None}), 500


@app.route("/eeg/analysis", methods=["GET"])
def get_eeg_analysis():
    """
    获取EEG分析结果接口
    """
    try:
        app.logger.info("获取EEG分析结果请求")
        # 获取请求参数
        patient_id = request.args.get('patientId')
        user_id = request.args.get('userId')
        file_url = request.args.get('fileUrl')
        
        # 验证参数
        if not patient_id:
            app.logger.error("缺少患者ID")
            return jsonify({"code": 1, "message": "缺少患者ID", "data": None}), 400
        
        if not file_url:
            app.logger.error("缺少文件URL")
            return jsonify({"code": 1, "message": "缺少文件URL", "data": None}), 400
        
        # 从数据库获取患者信息
        db = next(get_db())
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            app.logger.error(f"患者不存在: id={patient_id}")
            return jsonify({"code": 1, "message": "患者不存在", "data": None}), 404
        
        # 处理文件URL，转换为本地路径
        import urllib.parse
        import os
        
        app.logger.info(f"原始fileUrl: {file_url}")
        
        # 解析文件URL
        parsed_url = urllib.parse.urlparse(file_url)
        app.logger.info(f"解析后的URL: scheme={parsed_url.scheme}, netloc={parsed_url.netloc}, path={parsed_url.path}")
        
        if parsed_url.scheme == 'file':
            # 处理file://协议
            file_path = urllib.parse.unquote(parsed_url.path)
            app.logger.info(f"解码后的路径: {file_path}")
            
            # 处理Windows路径格式
            if os.name == 'nt':  # Windows系统
                # 移除开头的斜杠（如果有）
                if file_path.startswith('/'):
                    file_path = file_path[1:]
                    app.logger.info(f"移除开头斜杠后: {file_path}")
                # 将正斜杠转换为反斜杠
                file_path = file_path.replace('/', '\\')
                app.logger.info(f"转换斜杠后: {file_path}")
        else:
            # 假设是本地路径
            file_path = file_url
            app.logger.info(f"使用本地路径: {file_path}")
        
        # 检查路径是否存在
        if os.path.exists(file_path):
            app.logger.info(f"文件存在: {file_path}")
        else:
            app.logger.error(f"文件不存在: {file_path}")
        
        app.logger.info(f"最终分析文件: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            app.logger.error(f"文件不存在: {file_path}")
            return jsonify({"code": 1, "message": "文件不存在", "data": None}), 404
        
        # 调用真实的分析算法
        from test import testdemo
        start_time, end_time = testdemo(file_path)
        
        # 计算风险等级和其他指标
        def calculate_risk_level(start_time, end_time):
            """
            基于发作时长计算风险等级
            """
            if start_time is None or end_time is None:
                # 未检测到发作
                return {
                    "riskLevel": random.randint(1, 20),
                    "anomalies": [
                        {"type": "轻微不规则波", "severity": "info"}
                    ],
                    "rhythm": "正常",
                    "dischargeCount": 12,
                    "frequency": "θ波为主"
                }
            else:
                # 检测到发作，计算风险等级
                seizure_duration = float(end_time) - float(start_time)
                
                # 基于发作时长计算风险等级
                if seizure_duration < 10:
                    base_risk = 60  # 短时发作
                elif seizure_duration < 30:
                    base_risk = 75  # 中等时长发作
                else:
                    base_risk = 85  # 长时发作
                
                # 计算最终风险等级
                risk_level = min(95, base_risk)
                
                # 根据风险等级确定其他参数
                if risk_level < 70:
                    discharge_count = random.randint(10, 15)
                    rhythm_type = "轻度不规则"
                    frequency_type = "以θ波为主，伴有少量β波"
                    anomalies = [
                        {"type": "尖波", "severity": "warning"},
                        {"type": "慢波", "severity": "info"}
                    ]
                elif risk_level < 80:
                    discharge_count = random.randint(15, 20)
                    rhythm_type = "中度不规则"
                    frequency_type = "θ波与δ波混合"
                    anomalies = [
                        {"type": "尖波", "severity": "warning"},
                        {"type": "慢波", "severity": "warning"},
                        {"type": "尖慢波复合", "severity": "info"}
                    ]
                else:
                    discharge_count = random.randint(20, 30)
                    rhythm_type = "严重不规则"
                    frequency_type = "以δ波为主，伴有尖慢波复合"
                    anomalies = [
                        {"type": "尖波", "severity": "danger"},
                        {"type": "慢波", "severity": "warning"},
                        {"type": "尖慢波复合", "severity": "danger"},
                        {"type": "节律性放电", "severity": "warning"}
                    ]
                
                return {
                    "riskLevel": int(risk_level),
                    "anomalies": anomalies,
                    "rhythm": rhythm_type,
                    "dischargeCount": discharge_count,
                    "frequency": frequency_type,
                    "start_time": start_time,
                    "end_time": end_time,
                    "seizure_duration": f"{seizure_duration:.2f}秒"
                }
        
        # 计算分析结果
        import random
        analysis_result = calculate_risk_level(start_time, end_time)
        
        # 添加文件信息
        analysis_result["file_name"] = os.path.basename(file_path)
        analysis_result["file_size"] = os.path.getsize(file_path)
        
        # 保存分析结果到数据库
        from datetime import datetime
        new_eeg_record = EegRecord(
            id=random.randint(1, 10000),
            patientId=patient_id,
            fileName=analysis_result["file_name"],
            fileUrl=file_url,
            analysisResult=json.dumps(analysis_result),
            createTime=datetime.now(),
            updateTime=datetime.now()
        )
        db.add(new_eeg_record)
        db.commit()
        
        app.logger.info(f"返回EEG分析结果: patientId={patient_id}, riskLevel={analysis_result['riskLevel']}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": analysis_result
        }), 200
    except Exception as e:
        app.logger.error(f"获取EEG分析结果失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取EEG分析结果失败: {str(e)}", "data": None}), 500


@app.route("/eeg/analysisList", methods=["GET"])
def get_eeg_analysis_list():
    """
    分页查询EEG分析记录接口
    """
    try:
        app.logger.info("分页查询EEG分析记录请求")
        # 获取分页参数
        page_num = request.args.get('pageNum', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        patient_id = request.args.get('patientId')
        user_id = request.args.get('userId')
        
        # 从数据库获取EEG分析记录
        db = next(get_db())
        query = db.query(EegRecord)
        
        # 应用筛选条件
        if patient_id:
            query = query.filter(EegRecord.patientId == patient_id)
        # 注意：EegRecord模型中没有userId字段，所以不应该按userId筛选
        
        # 计算总数
        total = query.count()
        
        # 计算分页
        start = (page_num - 1) * page_size
        eeg_records = query.offset(start).limit(page_size).all()
        
        # 转换为前端需要的格式
        paginated_eegs = []
        for record in eeg_records:
            # 解析分析结果
            analysis_result = {}
            try:
                import json
                analysis_result = json.loads(record.analysisResult) if record.analysisResult else {}
            except:
                pass
            
            # 从分析结果中提取异常波形数据
            anomalies = analysis_result.get('anomalies', [])
            
            # 获取患者姓名
            patient_name = ""
            if record.patientId:
                patient = db.query(Patient).filter(Patient.id == record.patientId).first()
                if patient:
                    patient_name = patient.name
            
            paginated_eegs.append({
                "id": record.id,
                "patientId": record.patientId,
                "patientName": patient_name,
                "userId": user_id,  # 使用传入的userId
                "fileName": record.fileName,
                "fileSize": analysis_result.get('file_size', 0),  # 从分析结果中获取
                "createTime": record.createTime.strftime("%Y-%m-%d %H:%M:%S") if record.createTime else "",
                "updateTime": record.updateTime.strftime("%Y-%m-%d %H:%M:%S") if record.updateTime else "",
                "riskLevel": analysis_result.get('riskLevel', 0),  # 从分析结果中获取
                "rhythm": analysis_result.get('rhythm', ""),  # 从分析结果中获取
                "dischargeCount": analysis_result.get('dischargeCount', 0),  # 从分析结果中获取
                "frequency": analysis_result.get('frequency', ""),  # 从分析结果中获取
                "anomalies": anomalies,
                "doctorName": "医生"  # 模拟医生名称
            })
        
        app.logger.info(f"返回EEG分析记录列表: 共{total}条，当前页{page_num}，每页{page_size}条")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": {
                "items": paginated_eegs,
                "total": total
            }
        }), 200
    except Exception as e:
        app.logger.error(f"分页查询EEG分析记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"分页查询EEG分析记录失败: {str(e)}", "data": None}), 500


@app.route("/feature/upload", methods=["POST"])
def upload_feature_file():
    """
    上传EEG文件接口
    """
    try:
        app.logger.info("上传EEG文件请求")
        # 获取上传的文件
        file = request.files.get('file')
        patient_id = request.form.get('patientId', '0', type=str)
        user_id = request.form.get('userId', '0', type=str)
        
        # 验证文件
        if not file:
            app.logger.error("缺少上传文件")
            return jsonify({"code": 1, "message": "缺少上传文件", "data": None}), 400
        
        # 保存文件
        file_name = file.filename
        save_path = os.path.join(UPLOAD_FOLDER, file_name)
        file.save(save_path)
        
        # 使用upload_file函数生成正确的文件URL
        from func.uploadFile import upload_file
        file_url = upload_file(save_path)
        
        app.logger.info(f"上传EEG文件成功: {file_name}")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": {
                "fileUrl": file_url,
                "fileName": file_name,
                "patientId": patient_id,
                "userId": user_id
            }
        }), 200
    except Exception as e:
        app.logger.error(f"上传EEG文件失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"上传EEG文件失败: {str(e)}", "data": None}), 500


@app.route("/feature/analysis", methods=["GET"])
def get_feature_analysis():
    """
    获得Eeg可视化特征分析接口
    """
    try:
        app.logger.info("获得Eeg可视化特征分析请求")
        # 获取请求参数
        file_url = request.args.get('fileUrl', '', type=str)
        
        # 验证参数
        if not file_url:
            app.logger.error("缺少文件URL")
            return jsonify({"code": 1, "message": "缺少文件URL", "data": None}), 400
        
        # 解析文件路径
        import urllib.parse
        parsed_url = urlparse(file_url)
        if parsed_url.scheme == 'file':
            file_path = urllib.parse.unquote(parsed_url.path)
            # 处理Windows路径
            if os.name == 'nt' and file_path.startswith('/'):
                file_path = file_path[1:]
            file_path = file_path.replace('/', '\\')
        elif parsed_url.scheme in ['http', 'https']:
            # 处理HTTP URL，转换为本地文件路径
            path = parsed_url.path
            # 移除开头的斜杠
            if path.startswith('/'):
                path = path[1:]
            # 转换为本地路径
            file_path = os.path.join(os.getcwd(), path.replace('/', os.sep))
        else:
            file_path = file_url
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            app.logger.error(f"文件不存在: {file_path}")
            return jsonify({"code": 1, "message": "文件不存在", "data": None}), 404
        
        app.logger.info(f"开始分析文件: {file_path}")
        
        # 调用特征提取模块
        analysis_result = {}
        
        # 1. 过零点特征分析
        try:
            app.logger.info("开始过零点特征分析")
            _, _, zero_crossing_urls = process_and_visualize_eeg(
                file_path, 
                window_size_sec=6, 
                step_size_sec=3, 
                max_channels=5
            )
            analysis_result["zero_crossing"] = {
                "images": [{"channel": item["channel"], "url": item["url"]} for item in zero_crossing_urls]
            }
            app.logger.info(f"过零点特征分析完成，生成 {len(zero_crossing_urls)} 张图片")
        except Exception as e:
            app.logger.error(f"过零点特征分析失败: {str(e)}")
            analysis_result["zero_crossing"] = {"images": [], "error": str(e)}
        
        # 2. 短时傅里叶变换分析
        try:
            app.logger.info("开始STFT分析")
            _, stft_urls = process_and_visualize_stft(file_path, max_channels=5)
            analysis_result["stft"] = {
                "images": [{"channel": item["channel"], "url": item["url"]} for item in stft_urls]
            }
            app.logger.info(f"STFT分析完成，生成 {len(stft_urls)} 张图片")
        except Exception as e:
            app.logger.error(f"STFT分析失败: {str(e)}")
            analysis_result["stft"] = {"images": [], "error": str(e)}
        
        # 3. 离散小波变换分析
        try:
            app.logger.info("开始DWT分析")
            _, _, dwt_urls = process_eeg_data(file_path, window_size_sec=5, step_size_sec=3, max_channels=5)
            analysis_result["dwt"] = {
                "images": [{"channel": item.get("channel", "DWT分析"), "url": item["url"]} for item in dwt_urls]
            }
            app.logger.info(f"DWT分析完成，生成 {len(dwt_urls)} 张图片")
        except Exception as e:
            app.logger.error(f"DWT分析失败: {str(e)}")
            analysis_result["dwt"] = {"images": [], "error": str(e)}
        
        app.logger.info("返回Eeg可视化特征分析结果")
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": analysis_result
        }), 200
    except Exception as e:
        app.logger.error(f"获得Eeg可视化特征分析失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获得Eeg可视化特征分析失败: {str(e)}", "data": None}), 500


# 首页统计数据API
@app.route("/home/stats", methods=["GET"])
def get_home_stats():
    """
    获取首页统计数据
    """
    try:
        db = next(get_db())
        
        # 统计患者数量
        patient_count = db.query(Patient).count()
        
        # 统计今日预约（模拟数据）
        today_appointments = 24
        
        # 统计异常预警（模拟数据）
        abnormal_count = 8
        
        # 统计急诊患者（模拟数据）
        emergency_count = 5
        
        stats = {
            "patientCount": patient_count,
            "todayAppointments": today_appointments,
            "emergencyCount": emergency_count,
            "abnormalCount": abnormal_count
        }
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": stats
        }), 200
    except Exception as e:
        app.logger.error(f"获取首页统计数据失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取首页统计数据失败: {str(e)}", "data": None}), 500


# 病房管理API
@app.route("/ward/list", methods=["GET"])
def get_ward_list():
    """
    获取病房列表
    """
    try:
        db = next(get_db())
        wards = db.query(Ward).all()
        
        ward_list = []
        for ward in wards:
            ward_list.append({
                "id": ward.id,
                "roomNo": ward.roomNo,
                "bedCount": ward.bedCount,
                "doctor": ward.doctor,
                "nurse": ward.nurse,
                "status": ward.status,
                "createTime": ward.createTime.strftime("%Y-%m-%d %H:%M:%S") if ward.createTime else "",
                "updateTime": ward.updateTime.strftime("%Y-%m-%d %H:%M:%S") if ward.updateTime else ""
            })
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": ward_list
        }), 200
    except Exception as e:
        app.logger.error(f"获取病房列表失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取病房列表失败: {str(e)}", "data": None}), 500


@app.route("/ward/<int:ward_id>", methods=["GET"])
def get_ward_detail(ward_id):
    """
    获取病房详情
    """
    try:
        db = next(get_db())
        ward = db.query(Ward).filter(Ward.id == ward_id).first()
        
        if not ward:
            return jsonify({"code": 1, "message": "病房不存在", "data": None}), 404
        
        ward_detail = {
            "id": ward.id,
            "roomNo": ward.roomNo,
            "bedCount": ward.bedCount,
            "doctor": ward.doctor,
            "nurse": ward.nurse,
            "status": ward.status,
            "createTime": ward.createTime.strftime("%Y-%m-%d %H:%M:%S") if ward.createTime else "",
            "updateTime": ward.updateTime.strftime("%Y-%m-%d %H:%M:%S") if ward.updateTime else ""
        }
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": ward_detail
        }), 200
    except Exception as e:
        app.logger.error(f"获取病房详情失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取病房详情失败: {str(e)}", "data": None}), 500


@app.route("/ward", methods=["POST"])
def create_ward():
    """
    创建病房
    """
    try:
        data = request.get_json()
        
        ward = Ward(
            roomNo=data.get("roomNo"),
            bedCount=data.get("bedCount", 0),
            doctor=data.get("doctor", ""),
            nurse=data.get("nurse", ""),
            status=data.get("status", "正常"),
            createTime=datetime.now(),
            updateTime=datetime.now()
        )
        
        db = next(get_db())
        db.add(ward)
        db.commit()
        db.refresh(ward)
        
        return jsonify({
            "code": 0,
            "message": "创建成功",
            "data": {
                "id": ward.id,
                "roomNo": ward.roomNo,
                "bedCount": ward.bedCount,
                "doctor": ward.doctor,
                "nurse": ward.nurse,
                "status": ward.status
            }
        }), 201
    except Exception as e:
        app.logger.error(f"创建病房失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"创建病房失败: {str(e)}", "data": None}), 500


@app.route("/ward/<int:ward_id>", methods=["PUT"])
def update_ward(ward_id):
    """
    更新病房信息
    """
    try:
        data = request.get_json()
        
        db = next(get_db())
        ward = db.query(Ward).filter(Ward.id == ward_id).first()
        
        if not ward:
            return jsonify({"code": 1, "message": "病房不存在", "data": None}), 404
        
        if "roomNo" in data:
            ward.roomNo = data["roomNo"]
        if "bedCount" in data:
            ward.bedCount = data["bedCount"]
        if "doctor" in data:
            ward.doctor = data["doctor"]
        if "nurse" in data:
            ward.nurse = data["nurse"]
        if "status" in data:
            ward.status = data["status"]
        
        ward.updateTime = datetime.now()
        db.commit()
        
        return jsonify({
            "code": 0,
            "message": "更新成功",
            "data": {
                "id": ward.id,
                "roomNo": ward.roomNo,
                "bedCount": ward.bedCount,
                "doctor": ward.doctor,
                "nurse": ward.nurse,
                "status": ward.status
            }
        }), 200
    except Exception as e:
        app.logger.error(f"更新病房失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"更新病房失败: {str(e)}", "data": None}), 500


@app.route("/ward/<int:ward_id>", methods=["DELETE"])
def delete_ward(ward_id):
    """
    删除病房
    """
    try:
        db = next(get_db())
        ward = db.query(Ward).filter(Ward.id == ward_id).first()
        
        if not ward:
            return jsonify({"code": 1, "message": "病房不存在", "data": None}), 404
        
        db.delete(ward)
        db.commit()
        
        return jsonify({
            "code": 0,
            "message": "删除成功",
            "data": None
        }), 200
    except Exception as e:
        app.logger.error(f"删除病房失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"删除病房失败: {str(e)}", "data": None}), 500


# 监控数据API
@app.route("/monitor/data", methods=["GET"])
def get_monitor_data():
    """
    获取监控数据（病房列表及状态）
    """
    try:
        db = next(get_db())
        wards = db.query(Ward).all()
        
        monitor_data = []
        for ward in wards:
            monitor_data.append({
                "roomNo": ward.roomNo,
                "patientName": "",  # 暂时为空，后续可关联患者表
                "eegValue": 0,  # 暂时为0，后续可连接真实设备
                "status": ward.status,
                "lastUpdate": ward.updateTime.strftime("%Y-%m-%d %H:%M:%S") if ward.updateTime else ""
            })
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": monitor_data
        }), 200
    except Exception as e:
        app.logger.error(f"获取监控数据失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取监控数据失败: {str(e)}", "data": None}), 500


@app.route("/monitor/vitals/<int:ward_id>", methods=["GET"])
def get_ward_vitals(ward_id):
    """
    获取病房患者实时生命体征数据
    """
    try:
        db = next(get_db())
        ward = db.query(Ward).filter(Ward.id == ward_id).first()
        
        if not ward:
            return jsonify({"code": 1, "message": "病房不存在", "data": None}), 404
        
        vitals = {
            "heartRate": 0,  # 暂时为0，后续可连接真实设备
            "bloodPressure": "0/0",  # 暂时为0，后续可连接真实设备
            "temperature": 0,  # 暂时为0，后续可连接真实设备
            "oxygen": 0  # 暂时为0，后续可连接真实设备
        }
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": vitals
        }), 200
    except Exception as e:
        app.logger.error(f"获取生命体征数据失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取生命体征数据失败: {str(e)}", "data": None}), 500


@app.route("/monitor/environment/<int:ward_id>", methods=["GET"])
def get_ward_environment(ward_id):
    """
    获取病房环境监测数据
    """
    try:
        db = next(get_db())
        ward = db.query(Ward).filter(Ward.id == ward_id).first()
        
        if not ward:
            return jsonify({"code": 1, "message": "病房不存在", "data": None}), 404
        
        environment = [
            {
                "label": "室温",
                "value": 0,  # 暂时为0，后续可连接真实设备
                "unit": "°C",
                "status": "normal"
            },
            {
                "label": "湿度",
                "value": 0,  # 暂时为0，后续可连接真实设备
                "unit": "%",
                "status": "normal"
            },
            {
                "label": "光照",
                "value": 0,  # 暂时为0，后续可连接真实设备
                "unit": "lux",
                "status": "normal"
            },
            {
                "label": "噪音",
                "value": 0,  # 暂时为0，后续可连接真实设备
                "unit": "dB",
                "status": "normal"
            }
        ]
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": environment
        }), 200
    except Exception as e:
        app.logger.error(f"获取环境监测数据失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取环境监测数据失败: {str(e)}", "data": None}), 500


@app.route("/monitor/activities/<int:ward_id>", methods=["GET"])
def get_ward_activities(ward_id):
    """
    获取病房患者行为记录
    """
    try:
        db = next(get_db())
        ward = db.query(Ward).filter(Ward.id == ward_id).first()
        
        if not ward:
            return jsonify({"code": 1, "message": "病房不存在", "data": None}), 404
        
        activities = []  # 暂时为空，后续可从数据库获取
        
        return jsonify({
            "code": 0,
            "message": "成功",
            "data": activities
        }), 200
    except Exception as e:
        app.logger.error(f"获取行为记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"获取行为记录失败: {str(e)}", "data": None}), 500


@app.route("/api/chat/patient", methods=["GET"])
def chat_with_patient():
    """AI患者分析聊天功能"""
    try:
        prompt = request.args.get("prompt", "")
        session_id = request.args.get("sessionId", "")
        
        print(f"Received prompt: {prompt}")
        print(f"Session ID: {session_id}")
        
        # 模拟AI响应
        response_text = f"\n根据患者信息分析：\n\n患者姓名：张三\n年龄：35岁\n性别：男\n诊断：癫痫\n\n分析结果：\n1. 患者为中年男性，癫痫诊断明确\n2. 建议进行详细的脑电图检查\n3. 评估当前用药方案的有效性\n4. 建议定期随访，监测病情变化\n5. 提供患者教育，了解癫痫发作的急救措施\n\n治疗建议：\n- 继续当前抗癫痫药物治疗\n- 避免诱发因素，如过度劳累、情绪激动\n- 保持规律的作息时间\n- 定期复查脑电图和肝肾功能\n\n如需进一步评估，请安排神经科专科会诊。"
        
        # 流式响应
        def generate():
            for char in response_text:
                time.sleep(0.01)  # 模拟打字效果
                yield char
        
        return Response(generate(), content_type="text/event-stream")
    except Exception as e:
        app.logger.error(f"AI聊天失败: {str(e)}", exc_info=True)
        return jsonify({"code": 1, "message": f"AI聊天失败: {str(e)}", "data": None}), 500

if __name__ == "__main__":
    app.logger.info(f"服务启动在 http://127.0.0.1:5001")
    app.logger.info(f"上传目录: {UPLOAD_FOLDER}")
    print(f"服务启动在 http://127.0.0.1:5001")  
    print(f"上传目录: {UPLOAD_FOLDER}")
    app.run(debug=True, host='0.0.0.0', port=5001)