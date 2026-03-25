import os
import uuid

# 配置选项：设置为True使用本地文件系统，设置为False使用七牛云
USE_LOCAL_FILE_SYSTEM = True

# 七牛云配置信息（仅在USE_LOCAL_FILE_SYSTEM=False时使用）
access_key = 'tmoRxAnYOPtcI5k2_5qceLe4nX6-ABYW-PT1PaRj'
secret_key = 'k9-pw8JUBNCWQASOnG28trE7DdLhzlGM7DAmQRtT'
bucket_name = 'epilepsy-detect'
domain = 'http:st2f6c92m.hb-bkt.clouddn.com'

def upload_file(local_file):
    """
    上传文件函数，根据配置选择使用本地文件系统还是七牛云
    
    Args:
        local_file: 本地文件路径
        
    Returns:
        str: 文件的访问URL
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(local_file):
            print(f"文件不存在: {local_file}")
            return None
        
        # 根据配置选择上传方式
        if USE_LOCAL_FILE_SYSTEM:
            # 使用本地文件系统，生成HTTP URL
            abs_path = os.path.abspath(local_file)
            # 生成相对于项目根目录的路径
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rel_path = os.path.relpath(abs_path, project_root)
            # 生成HTTP URL
            file_url = f"http://localhost:5001/{rel_path.replace(os.sep, '/')}"
            print(f"本地文件HTTP URL: {file_url}")
            return file_url
        else:
            # 使用七牛云
            try:
                from qiniu import Auth, put_data, put_file
                import qiniu.config
                
                # 构建鉴权对象
                q = Auth(access_key, secret_key)
                
                # 生成随机文件名
                file_ext = os.path.splitext(local_file)[1]
                key = f"{str(uuid.uuid4())}{file_ext}"
                
                # 生成上传凭证
                token = q.upload_token(bucket_name, key, 3600)
                
                # 上传文件
                ret, info = put_file(token, key, local_file, version='v2')
                
                if info.status_code == 200:
                    # 生成访问链接
                    file_url = f"{domain}/{key}"
                    print(f"七牛云文件URL: {file_url}")
                    return file_url
                else:
                    print(f"七牛云上传失败: {info}")
                    return None
            except ImportError:
                print("七牛云模块未安装，使用本地文件系统作为替代")
                # 回退到本地文件系统
                file_url = f"file://{os.path.abspath(local_file)}"
                print(f"本地文件路径: {file_url}")
                return file_url
    except Exception as e:
        print(f"处理文件出错: {str(e)}")
        return None

if __name__ == '__main__':
    local_file = 'E:/Code/medicine-care/EegFunc/miResult/mi_distribution.png'
    upload_file(local_file)
