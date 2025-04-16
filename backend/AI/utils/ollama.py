"""Ollama模型工具"""

import os
import platform
import subprocess
import sys
import requests
import time
from typing import List, Optional
import questionary
from colorama import Fore, Style
from loguru import logger

# 常量
OLLAMA_SERVER_URL = "http://localhost:11434"
OLLAMA_API_MODELS_ENDPOINT = f"{OLLAMA_SERVER_URL}/api/tags"
OLLAMA_DOWNLOAD_URL = {
    "darwin": "https://ollama.com/download/darwin",     # macOS
    "win32": "https://ollama.com/download/windows",     # Windows
    "linux": "https://ollama.com/download/linux"        # Linux
}
INSTALLATION_INSTRUCTIONS = {
    "darwin": "curl -fsSL https://ollama.com/install.sh | sh",
    "win32": "# 从 https://ollama.com/download/windows 下载并运行安装程序",
    "linux": "curl -fsSL https://ollama.com/install.sh | sh"
}


def is_ollama_installed() -> bool:
    """检查系统是否安装了Ollama"""
    system = platform.system().lower()
    
    if system == "darwin" or system == "linux":  # macOS 或 Linux
        try:
            result = subprocess.run(["which", "ollama"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
            return result.returncode == 0
        except Exception:
            return False
    elif system == "win32":  # Windows
        try:
            result = subprocess.run(["where", "ollama"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True,
                                   shell=True)
            return result.returncode == 0
        except Exception:
            return False
    else:
        return False  # 不支持的操作系统


def is_ollama_server_running() -> bool:
    """检查Ollama服务器是否正在运行"""
    try:
        response = requests.get(OLLAMA_API_MODELS_ENDPOINT, timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_locally_available_models() -> List[str]:
    """获取已本地下载的模型列表"""
    if not is_ollama_server_running():
        return []
    
    try:
        response = requests.get(OLLAMA_API_MODELS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data['models']] if 'models' in data else []
        return []
    except requests.RequestException:
        return []


def start_ollama_server() -> bool:
    """如果Ollama服务器未运行，则启动它"""
    if is_ollama_server_running():
        logger.info(f"{Fore.GREEN}Ollama服务器已经在运行。{Style.RESET_ALL}")
        return True
    
    system = platform.system().lower()
    
    try:
        if system == "darwin" or system == "linux":  # macOS 或 Linux
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
        elif system == "windows":  # Windows
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           shell=True)
        else:
            logger.error(f"{Fore.RED}不支持的操作系统: {system}{Style.RESET_ALL}")
            return False
        
        # 等待服务器启动
        for _ in range(10):  # 尝试10秒
            if is_ollama_server_running():
                logger.info(f"{Fore.GREEN}Ollama服务器成功启动。{Style.RESET_ALL}")
                return True
            time.sleep(1)
        
        logger.error(f"{Fore.RED}启动Ollama服务器失败。等待服务器可用超时。{Style.RESET_ALL}")
        return False
    except Exception as e:
        logger.error(f"{Fore.RED}启动Ollama服务器时出错: {e}{Style.RESET_ALL}")
        return False


def install_ollama() -> bool:
    """在系统上安装Ollama"""
    system = platform.system().lower()
    if system not in OLLAMA_DOWNLOAD_URL:
        logger.error(f"{Fore.RED}不支持自动安装的操作系统: {system}{Style.RESET_ALL}")
        logger.info(f"请访问 https://ollama.com/download 手动安装Ollama。")
        return False
    
    if system == "darwin":  # macOS
        logger.info(f"{Fore.YELLOW}Mac版Ollama可作为应用程序下载。{Style.RESET_ALL}")
        
        # 默认首先为macOS用户提供应用程序下载
        if questionary.confirm("您想下载Ollama应用程序吗？", default=True).ask():
            try:
                import webbrowser
                webbrowser.open(OLLAMA_DOWNLOAD_URL["darwin"])
                logger.info(f"{Fore.YELLOW}请下载并安装应用程序，然后重启此程序。{Style.RESET_ALL}")
                logger.info(f"{Fore.CYAN}安装后，您可能需要先打开一次Ollama应用程序。{Style.RESET_ALL}")
                
                # 询问是否要在安装后继续
                if questionary.confirm("您是否已安装Ollama应用程序并至少打开过一次？", default=False).ask():
                    # 检查是否现在已安装
                    if is_ollama_installed() and start_ollama_server():
                        logger.info(f"{Fore.GREEN}Ollama现在已正确安装并运行！{Style.RESET_ALL}")
                        return True
                    else:
                        logger.error(f"{Fore.RED}未检测到Ollama安装。请在安装Ollama后重启此应用程序。{Style.RESET_ALL}")
                        return False
                return False
            except Exception as e:
                logger.error(f"{Fore.RED}打开浏览器失败: {e}{Style.RESET_ALL}")
                return False
        else:
            # 仅作为高级用户的备选方案提供命令行安装
            if questionary.confirm("您想尝试命令行安装吗？（适用于高级用户）", default=False).ask():
                logger.info(f"{Fore.YELLOW}尝试命令行安装...{Style.RESET_ALL}")
                try:
                    install_process = subprocess.run(
                        ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        text=True
                    )
                    
                    if install_process.returncode == 0:
                        logger.info(f"{Fore.GREEN}通过命令行成功安装Ollama。{Style.RESET_ALL}")
                        return True
                    else:
                        logger.error(f"{Fore.RED}命令行安装失败。请改用应用程序下载方法。{Style.RESET_ALL}")
                        return False
                except Exception as e:
                    logger.error(f"{Fore.RED}命令行安装过程中出错: {e}{Style.RESET_ALL}")
                    return False
            return False
    elif system == "linux":  # Linux
        logger.info(f"{Fore.YELLOW}正在安装Ollama...{Style.RESET_ALL}")
        try:
            # 作为单个命令运行安装命令
            install_process = subprocess.run(
                ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            if install_process.returncode == 0:
                logger.info(f"{Fore.GREEN}Ollama安装成功。{Style.RESET_ALL}")
                return True
            else:
                logger.error(f"{Fore.RED}安装Ollama失败。错误: {install_process.stderr}{Style.RESET_ALL}")
                return False
        except Exception as e:
            logger.error(f"{Fore.RED}Ollama安装过程中出错: {e}{Style.RESET_ALL}")
            return False
    elif system == "win32":  # Windows
        logger.info(f"{Fore.YELLOW}Windows不支持自动安装。{Style.RESET_ALL}")
        logger.info(f"请从以下地址下载并安装Ollama: {OLLAMA_DOWNLOAD_URL['win32']}")
        
        # 询问是否要打开下载页面
        if questionary.confirm("您想在浏览器中打开Ollama下载页面吗？").ask():
            try:
                import webbrowser
                webbrowser.open(OLLAMA_DOWNLOAD_URL['win32'])
                logger.info(f"{Fore.YELLOW}安装后，请重启此应用程序。{Style.RESET_ALL}")
                
                # 询问是否要在安装后继续
                if questionary.confirm("您是否已安装Ollama？", default=False).ask():
                    # 检查是否现在已安装
                    if is_ollama_installed() and start_ollama_server():
                        logger.info(f"{Fore.GREEN}Ollama现在已正确安装并运行！{Style.RESET_ALL}")
                        return True
                    else:
                        logger.error(f"{Fore.RED}未检测到Ollama安装。请在安装Ollama后重启此应用程序。{Style.RESET_ALL}")
                        return False
            except Exception as e:
                logger.error(f"{Fore.RED}打开浏览器失败: {e}{Style.RESET_ALL}")
        return False
    
    return False


def download_model(model_name: str) -> bool:
    """下载Ollama模型"""
    if not is_ollama_server_running():
        if not start_ollama_server():
            return False
    
    logger.info(f"{Fore.YELLOW}正在下载模型 {model_name}...{Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}这可能需要一些时间，取决于您的网络速度和模型大小。{Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}下载在后台进行。请耐心等待...{Style.RESET_ALL}")
    
    try:
        # 使用Ollama CLI下载模型
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,  # 将stderr重定向到stdout以捕获所有输出
            text=True,
            bufsize=1,  # 行缓冲
            universal_newlines=True
        )
        
        # 向用户显示一些进度
        logger.info(f"{Fore.CYAN}下载进度:{Style.RESET_ALL}")
        
        # 用于跟踪进度
        last_percentage = 0
        last_phase = ""
        bar_length = 40
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output = output.strip()
                # 处理进度输出
                if "pulling" in output.lower():
                    try:
                        # 提取百分比
                        percentage = int(output.split("%")[0].split()[-1])
                        if percentage != last_percentage:
                            # 创建进度条
                            filled_length = int(bar_length * percentage / 100)
                            bar = '=' * filled_length + '-' * (bar_length - filled_length)
                            logger.info(f"\r[{bar}] {percentage}%", end='')
                            last_percentage = percentage
                    except:
                        pass
                elif "verifying" in output.lower():
                    if "verifying" != last_phase:
                        logger.info("\n验证模型完整性...")
                        last_phase = "verifying"
                elif "writing" in output.lower():
                    if "writing" != last_phase:
                        logger.info("\n写入模型文件...")
                        last_phase = "writing"
        
        if process.returncode == 0:
            logger.info(f"\n{Fore.GREEN}模型 {model_name} 下载成功！{Style.RESET_ALL}")
            return True
        else:
            logger.error(f"\n{Fore.RED}下载模型 {model_name} 失败。{Style.RESET_ALL}")
            return False
    except Exception as e:
        logger.error(f"{Fore.RED}下载模型时出错: {e}{Style.RESET_ALL}")
        return False


def ensure_ollama_and_model(model_name: str) -> bool:
    """确保Ollama已安装并运行，且指定的模型可用"""
    # 检查Ollama是否已安装
    if not is_ollama_installed():
        logger.info(f"{Fore.YELLOW}未检测到Ollama安装。{Style.RESET_ALL}")
        if not install_ollama():
            return False
    
    # 检查Ollama服务器是否正在运行
    if not is_ollama_server_running():
        logger.info(f"{Fore.YELLOW}Ollama服务器未运行。尝试启动...{Style.RESET_ALL}")
        if not start_ollama_server():
            return False
    
    # 检查模型是否已下载
    available_models = get_locally_available_models()
    if model_name not in available_models:
        logger.info(f"{Fore.YELLOW}模型 {model_name} 未找到。开始下载...{Style.RESET_ALL}")
        if not download_model(model_name):
            return False
    
    return True


def delete_model(model_name: str) -> bool:
    """删除Ollama模型"""
    if not is_ollama_server_running():
        logger.error(f"{Fore.RED}Ollama服务器未运行。{Style.RESET_ALL}")
        return False
    
    try:
        process = subprocess.run(
            ["ollama", "rm", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode == 0:
            logger.info(f"{Fore.GREEN}成功删除模型 {model_name}。{Style.RESET_ALL}")
            return True
        else:
            logger.error(f"{Fore.RED}删除模型 {model_name} 失败。错误: {process.stderr}{Style.RESET_ALL}")
            return False
    except Exception as e:
        logger.error(f"{Fore.RED}删除模型时出错: {e}{Style.RESET_ALL}")
        return False 