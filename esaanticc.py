import os
import sys
import json
import datetime
import platform

from typing import List

from alibabacloud_esa20240910.client import Client as ESA20240910Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_esa20240910 import models as esa20240910_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


def load_config():
    """
    加载配置文件
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "esa_config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}\n请创建配置文件或检查路径。")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # 验证必需字段
    required_fields = ["access_key_id", "access_key_secret", "site_id", "rule_id", "load_threshold"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"配置文件中缺少必需字段: {field}")
    
    return config


def get_shield_record_file():
    """
    获取盾牌记录文件的完整路径
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "esa.txt")


def record_shield_enabled():
    """
    记录开盾时间到文件
    """
    try:
        file_path = get_shield_record_file()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(current_time)
        print(f"开盾时间已记录: {current_time}")
        return True
    except Exception as e:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 记录开盾时间失败: {e}")
        return False


def has_recent_shield_record(minutes=15):
    """
    检查是否有最近的开盾记录
    
    参数:
        minutes (int): 时间窗口（分钟），默认为15分钟
    
    返回:
        bool: 如果存在且在时间窗口内返回True，否则返回False
    """
    try:
        file_path = get_shield_record_file()
        if not os.path.exists(file_path):
            return False
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        if not content:
            return False
        
        # 解析记录的时间
        record_time = datetime.datetime.strptime(content, "%Y-%m-%d %H:%M:%S")
        current_time = datetime.datetime.now()
        
        # 计算时间差（分钟）
        time_diff = (current_time - record_time).total_seconds() / 60.0
        
        if time_diff <= minutes:
            return True
        else:
            return False
    except Exception as e:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 检查开盾记录失败: {e}")
        return False


def clear_shield_record():
    """
    清空开盾记录文件
    """
    try:
        file_path = get_shield_record_file()
        if os.path.exists(file_path):
            os.remove(file_path)
            print("开盾记录已清空")
            return True
        return True  # 文件不存在也视为成功
    except Exception as e:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 清空开盾记录失败: {e}")
        return False


def check_load_and_enable_rule(config=None):
    """
    检查系统负载并在负载超过阈值时启用 WAF 规则
    
    参数:
        config (dict): 配置字典，如果为None则自动加载配置文件
    """
    if config is None:
        config = load_config()
    
    # 从配置中获取参数
    load_threshold = config.get('load_threshold', 80.0)
    shield_record_window_minutes = config.get('shield_record_window_minutes', 15)
    
    # 检查当前操作系统是否支持 os.getloadavg()
    system = platform.system()
    if system not in ["Linux", "Darwin", "Unix"]:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 当前系统 {system} 不支持负载监控，跳过检查")
        return False
    
    try:
        # 获取系统负载平均值 (1分钟, 5分钟, 15分钟)
        load_avg = os.getloadavg()
        load_1min = load_avg[0]
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if load_1min > load_threshold:
            # 负载超过阈值，需要检查是否已有最近的开盾记录
            if has_recent_shield_record(minutes=shield_record_window_minutes):
                print(f"{current_time} 检测到CPU负载{load_1min:.2f}，超过阈值{load_threshold}，但已有最近的开盾记录，跳过重复执行")
                return True
            else:
                print(f"{current_time} 检测到CPU负载{load_1min:.2f}，超过阈值{load_threshold}，执行开盾策略")
                
                # 启用 WAF 规则
                success = Sample.enable_waf_rule(enabled=True)
                
                if success:
                    print(f"{current_time} 调用API开盾成功")
                    # 记录开盾时间
                    record_shield_enabled()
                    return True
                else:
                    print(f"{current_time} 调用API开盾失败")
                    return False
        else:
            # 负载正常，检查是否需要自动关盾
            print(f"{current_time} 检测到CPU负载{load_1min:.2f}，未超过阈值{load_threshold}")
            
            # 检查是否有开盾记录
            try:
                file_path = get_shield_record_file()
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    
                    if content:
                        # 解析记录的时间
                        record_time = datetime.datetime.strptime(content, "%Y-%m-%d %H:%M:%S")
                        current_time_dt = datetime.datetime.now()
                        time_diff = (current_time_dt - record_time).total_seconds() / 60.0
                        
                        if time_diff > shield_record_window_minutes:
                            print(f"{current_time} 检测到开盾记录已超过{shield_record_window_minutes}分钟({time_diff:.1f}分钟)，执行关盾策略")
                            
                            # 禁用 WAF 规则
                            success = Sample.enable_waf_rule(enabled=False)
                            
                            if success:
                                print(f"{current_time} 调用API关盾成功")
                                clear_shield_record()
                                return True
                            else:
                                print(f"{current_time} 调用API关盾失败")
                                return False
                        else:
                            print(f"{current_time} 开盾记录仍在有效期内({time_diff:.1f}分钟)，无需操作")
                            return True
                    else:
                        # 文件存在但内容为空
                        clear_shield_record()
                        return True
                else:
                    # 无开盾记录，无需操作
                    return True
            except Exception as e:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{current_time} 检查开盾记录时发生错误: {e}")
                return False
            
    except AttributeError:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 当前操作系统不支持 os.getloadavg()")
        return False
    except Exception as e:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} 获取系统负载时发生错误: {e}")
        return False


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> ESA20240910Client:
        """
        使用凭据初始化账号Client
        @return: Client
        @throws Exception
        """
        config_data = load_config()
        access_key_id = config_data.get('access_key_id')
        access_key_secret = config_data.get('access_key_secret')
        endpoint = config_data.get('endpoint', 'esa.cn-hangzhou.aliyuncs.com')
        
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        config.endpoint = endpoint
        return ESA20240910Client(config)

    @staticmethod
    def enable_waf_rule(enabled=True):
        """
        启用或禁用阿里云 ESA WAF 规则
        
        参数:
            enabled (bool): 是否启用规则，默认为 True
        """
        client = Sample.create_client()
        
        # 配置参数
        config_data = load_config()
        site_id = config_data.get('site_id')
        rule_id = config_data.get('rule_id')
        
        # 根据 enabled 参数设置状态
        status = 'on' if enabled else 'off'
        
        update_waf_rule_request = esa20240910_models.UpdateWafRuleRequest(
            site_id=site_id,
            id=rule_id,
            status=status
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = client.update_waf_rule_with_options(update_waf_rule_request, runtime)
            # 成功时只输出一行
            action = "开盾" if enabled else "关盾"
            return True
        except Exception as error:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            action = "开盾" if enabled else "关盾"
            print(f"{current_time} 调用API{action}失败:")
            print(f"  错误信息: {error}")
            if hasattr(error, 'data') and error.data:
                recommend = error.data.get("Recommend")
                if recommend:
                    print(f"  建议: {recommend}")
            return False

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        # 加载配置
        config = load_config()
        
        # 检查系统负载并在需要时启用规则
        success = check_load_and_enable_rule(config=config)
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        # 加载配置
        config = load_config()
        site_id = config.get('site_id')
        rule_id = config.get('rule_id')
        
        client = Sample.create_client()
        update_waf_rule_request = esa20240910_models.UpdateWafRuleRequest(
            site_id=site_id,
            id=rule_id,
            status='on'
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await client.update_waf_rule_with_options_async(update_waf_rule_request, runtime)
            # 成功时只输出一行
            print("已成功调用API接口开盾")
        except Exception as error:
            print(f"Error: {error}")
            if hasattr(error, 'data') and error.data:
                recommend = error.data.get("Recommend")
                if recommend:
                    print(f"Recommend: {recommend}")
            else:
                print("Please configure Alibaba Cloud credentials via environment variables, config file, or ECS RAM role.")
                print("See https://help.aliyun.com/document_detail/378659.html for details.")


if __name__ == '__main__':
    Sample.main(sys.argv[1:])
