# plugins\example\p_drawcat.py
# __version__ = "1.0.0"

from plugin_base import Plugin  # 假设你有一个插件基类
import logging
import re
import requests
import io
import base64
from PIL import Image
from api.send import send_group_image_msg, send_group_msg  # 使用 send_group_image_msg 发送图片
import asyncio  # 用于异步任务管理

logger = logging.getLogger("bot")


class P_drawcatPlugin(Plugin):
    def __init__(self, bot):
        logger.info("DrawCat 插件正在初始化...")
        self.bot = bot
        # Stable Diffusion API 配置
        self.api_url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
        self.auth = ("账号", "密码")  # 替换为你的用户名和密码
        self.is_busy = False  # 用于标记是否有任务正在进行

    async def on_message(self, message):
        raw_message = message['raw_message']
        group_id = message.get('group_id')  # 获取群聊 ID

        # 使用正则表达式匹配“画图猫猫”关键词，可修改
        match = re.match(r"画图猫猫 (.+)", raw_message)
        if match:
            prompt = match.group(1)  # 提取提示词
            logger.info(f"匹配到提示词: {prompt}")

            try:
                # 检查是否有任务正在进行
                if self.is_busy:
                    # 如果有任务正在进行，回复提示信息
                    await self.send_group_msg(group_id, "别急喵已经有别的画正在画了，给点时间喵")
                else:
                    # 如果没有任务正在进行，标记为忙碌状态
                    self.is_busy = True

                    # 发送桌面上的忙碌状态图片
                    whwh_image_path = r""  # 忙碌状态图片的目录
                    await self.send_image_to_group(group_id, whwh_image_path)

                    # 调用生成图片的函数
                    image_path = await self.generate_image(prompt)
                    if image_path:
                        # 发送生成的图片到群聊
                        await self.send_image_to_group(group_id, image_path)
                    else:
                        logger.error("图片生成失败，未发送图片")

                    # 任务完成后，标记为空闲状态
                    self.is_busy = False
            except Exception as e:
                logger.error(f"生成图片时出错: {e}")
                # 任务完成后，标记为空闲状态
                self.is_busy = False
        else:
            logger.info("未匹配到“画图猫猫”关键词")

    async def generate_image(self, prompt):
        """
        调用 Stable Diffusion API 生成图片
        """
        # 请求数据
        data = {
            "prompt": prompt
        }

        try:
            # 发送 POST 请求
            response = requests.post(self.api_url, json=data, auth=self.auth)
            if response.status_code == 200:
                logger.info("生成成功！")
                # 解析响应数据
                response_data = response.json()
                # 保存生成的图片
                for i, image_data in enumerate(response_data['images']):
                    image = Image.open(io.BytesIO(base64.b64decode(image_data.split(",", 1)[0])))
                    image_path = r'C:\Users\Administrator\Desktop\output_{i}.png'   # 输出目录
                    image.save(image_path)
                    logger.info(f"图片保存成功: {image_path}")
                    return image_path
            else:
                logger.error("生成失败！")
                logger.error(response.text)
        except Exception as e:
            logger.error(f"调用 API 时出错: {e}")
        return None

    async def send_image_to_group(self, group_id, image_path):
        """
        发送图片到群聊
        """
        try:
            # 使用 send_group_image_msg 发送图片
            send_group_image_msg(self.bot.base_url, group_id, f"file:///{image_path}", summary="生成的图片如下：", token=self.bot.token)
            logger.info(f"图片已发送至群聊 {group_id}")
        except Exception as e:
            logger.error(f"发送图片时出错: {e}")

    async def send_group_msg(self, group_id, message):
        """
        发送文本消息到群聊
        """
        try:
            send_group_msg(self.bot.base_url, group_id, message, token=self.bot.token)
            logger.info(f"文本消息已发送至群聊 {group_id}")
        except Exception as e:
            logger.error(f"发送文本消息时出错: {e}")