# plugins/example/p_priv_tts.py
#__version__ = "1.0.0"
import os
import logging
import asyncio

import torch
import numpy as np
import ChatTTS
import sounddevice as sd

from plugin_base import Plugin

# 日志配置
logger = logging.getLogger("p_priv_tts")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class P_priv_ttsPlugin(Plugin):
    def __init__(self, bot):
        self.bot = bot
        logger.info("p_priv_tts 插件初始化中... v1.0.3")

        # 初始化 TTS 引擎
        self.chat = ChatTTS.Chat()
        self.chat.load(compile=True)

        # 加载本地女性说话人嵌入 (.pth 格式)
        spk_path = os.path.join(os.path.dirname(__file__), "female_spk.pth")    # 没有也没关系
        try:
            loaded = torch.load(spk_path, map_location="cpu")
            # 如果是字典，则提取 spk_emb 字段或第一个值
            if isinstance(loaded, dict):
                if "spk_emb" in loaded:
                    spk_val = loaded["spk_emb"]
                else:
                    spk_val = list(loaded.values())[0]
            else:
                spk_val = loaded
            # Tensor 转为 numpy
            if isinstance(spk_val, torch.Tensor):
                spk_val = spk_val.cpu().numpy()
            # 确保类型正确（str 或 numpy 数组）
            if isinstance(spk_val, np.ndarray) or isinstance(spk_val, str):
                self.spk = spk_val
                logger.info(f"成功加载 female_spk.pth，类型: {type(spk_val)}")
            else:
                raise TypeError(f"不支持的 spk_emb 类型: {type(spk_val)}")
        except Exception as e:
            logger.error(f"加载 female_spk.pth 失败：{e}，将使用随机说话人", exc_info=True)
            self.spk = self.chat.sample_random_speaker()

        # 使用系统默认输出设备
        sd.default.device = None

    async def on_message(self, message):
        # 仅处理私聊且来自指定 QQ
        if message.get("message_type") != "private":
            return
        if str(message.get("user_id", "")) != "2302827468":     #此处填写需要语音复述的QQ号
            return

        text = message.get("raw_message", "").strip()
        if not text:
            logger.warning("收到空文本，跳过 TTS")
            return

        logger.info(f"收到私聊：{text}")
        loop = asyncio.get_event_loop()
        try:
            # 合成
            wavs = await loop.run_in_executor(
                None,
                lambda: self.chat.infer(
                    [text],
                    params_infer_code=ChatTTS.Chat.InferCodeParams(spk_emb=self.spk)
                )
            )
            if not wavs:
                logger.error("TTS 未生成音频")
                return

            # 播放
            audio = wavs[0]
            logger.info("开始播放语音")
            await loop.run_in_executor(
                None,
                lambda: (sd.play(audio, samplerate=24000), sd.wait())
            )
            logger.info("播放完成")

        except Exception:
            logger.exception("p_priv_tts 插件执行异常")

    async def send_private_msg(self, user_id, message):
        """
        使用 OneBot API 发送私聊消息
        """
        try:
            await self.bot.call_api('send_private_msg', {
                'user_id': int(user_id),
                'message': message
            })
            logger.info(f"已发送私聊消息给 {user_id}")
        except Exception as e:
            logger.error(f"发送私聊消息时出错: {e}")
