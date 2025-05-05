# plugins\example\p_catchat.py
# __version__ = "1.0.0"

import aiohttp
import asyncio
import logging
import re
import os
import json
from plugin_base import Plugin
from api.send import send_msg

logger = logging.getLogger("bot")

class P_catchatPlugin(Plugin):  
    def __init__(self, bot):
        logger.info("p_cat_chat 插件正在初始化...")
        self.bot = bot
        self.api_url = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek API URL
        self.api_key = "sk-"  # 填写你的 DeepSeek API 密钥
        self.history_file = "C:/Users/Administrator/Desktop/chat_history.txt"  # 用于保存历史记录的文件路径
        
        # 确保历史记录文件存在
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump({}, f)  # 初始化为空字典

    def load_history(self, user_id):
        """加载指定用户的对话历史"""
        try:
            with open(self.history_file, 'r') as f:
                history_data = json.load(f)
            return history_data.get(str(user_id), [])
        except Exception as e:
            logger.error(f"加载历史记录出错: {e}")
            return []

    def save_history(self, user_id, messages):
        """保存指定用户的对话历史"""
        try:
            with open(self.history_file, 'r') as f:
                history_data = json.load(f)
        except Exception:
            history_data = {}

        # 保存最新的消息历史（最多50条）
        history_data[str(user_id)] = messages[-50:]
        with open(self.history_file, 'w') as f:
            json.dump(history_data, f)

    async def on_message(self, message):
        try:
            raw_message = message['raw_message']
            user_id = message['user_id']
            message_type = message.get('message_type', '')
            group_id = message.get('group_id', '')  # 获取群聊 ID

            # 匹配 @猫猫 命令
            match = re.match(r"。\s*(.*)", raw_message)
            if match:
                input_text = match.group(1)
                logger.info(f"匹配到 用户 消息，输入文本: {input_text}")

                # 加载用户的对话历史
                messages = self.load_history(user_id)
                
                # 始终加入角色设定
                messages.insert(0, {
                    "role": "system",
                    "content": (
                        ""  # 此处添加对 AI 的角色设定
                    )
                })

                messages.append({"role": "user", "content": input_text})
                
                # 调用 DeepSeek API 获取响应内容
                response_text = await self.chat_with_gpt(messages)  # 异步调用 DeepSeek API
                
                # 清理响应文本
                cleaned_text = await self.clean_response_text(response_text)
                
                # 将模型回复添加到对话历史
                messages.append({"role": "assistant", "content": cleaned_text})
                
                # 保存更新后的对话历史
                self.save_history(user_id, messages)
                
                # 发送消息到群聊或私聊
                if group_id:
                    logger.info(f"发送消息到群聊 {group_id}")
                    send_msg(self.bot.base_url, message_type, group_id, cleaned_text, self.bot.token)
                else:
                    logger.info(f"发送消息到用户 {user_id}")
                    send_msg(self.bot.base_url, message_type, user_id, cleaned_text, self.bot.token)

        except Exception as e:
            logger.exception("处理消息时出错")

    async def chat_with_gpt(self, messages):
        """与 DeepSeek 模型交互"""
        # 设置超时配置，增加超时时间到 30 秒
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "model": "deepseek-chat",  # 使用 DeepSeek-V3 模型
                "messages": messages
            }

            try:
                # 连接 API 服务器
                logger.info("正在连接 API 服务器...")
                async with session.post(self.api_url, headers=headers, json=data) as resp:
                    logger.info("已连接 API 服务器")

                    # 每秒更新日志，显示连接状态
                    start_time = asyncio.get_event_loop().time()
                    while True:
                        elapsed_time = int(asyncio.get_event_loop().time() - start_time)
                        logger.info(f"持续连接中... 已等待 {elapsed_time} 秒")

                        # 尝试读取响应内容
                        try:
                            response_data = await resp.json()
                            logger.info("已收到响应")
                            return response_data.get("choices", [{}])[0].get("message", {}).get("content", "没有收到有效的聊天回复")
                        except aiohttp.ContentTypeError:
                            # 如果响应不是 JSON 格式，继续等待
                            await asyncio.sleep(1)
                        except json.JSONDecodeError:
                            # 如果响应是无效的 JSON，继续等待
                            await asyncio.sleep(1)
                        except Exception as e:
                            logger.error(f"解析响应时出错: {e}")
                            return "啊哦，服务器繁忙？那就请稍后再试吧😘"

            except asyncio.TimeoutError:
                logger.error("请求超时，请检查网络连接或联系 API 提供方。")
                return "请求超时啦！稍后再试吧。"
            except aiohttp.ClientError as e:
                logger.error(f"网络请求失败: {e}")
                return "网络连接失败，请检查网络设置。"
            except Exception as e:
                logger.exception("未知错误发生")
                return "发生未知错误😮，请稍后再试。"

    async def clean_response_text(self, response_text: str) -> str:
        """清理 DeepSeek 的响应文本"""
        # 如果响应文本是 JSON 格式，提取 content 字段
        if response_text.startswith("{") and response_text.endswith("}"):
            try:
                response_data = json.loads(response_text)
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    return response_data["choices"][0]["message"]["content"]
            except json.JSONDecodeError:
                pass
        
        # 如果响应文本是纯文本，直接返回
        return response_text.strip()