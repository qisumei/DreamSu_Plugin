# DreamSu_Plugin
## 项目概述

本仓库提供了一些单文件插件，用于扩展 QQ 机器人[DreamSu](https://github.com/YeiJ/DreamSu)的功能; 基于Python 3.10。

* **p\_blockquery.py**
  在安装了 GriefLogger 查询 Mod 的 Minecraft 服务器上，读取并查询 GriefLogger 生成的 SQLite 数据库文件（默认 `database.db`），玩家可在 QQ 群中通过 `查询-<世界>-方块-<模式>-(<x>,<y>,<z>)(,半径)` 的格式自主查询服务器上的方块操作记录。

* **p\_catchat.py**
  集成 DeepSeek API，为 QQ 群和私聊提供 AI 聊天交互功能，用户可在消息前加上句号（“。”）触发对话机器人。

* **p\_drawcat.py**
  使用本地部署的 Stable Diffusion 接口，根据 QQ 群中 `画图猫猫 <提示词>` 的格式生成图片，并将图片发送至群聊。

* **p\_priv\_tts.py**
  利用 `ChatTTS` 库，将指定 QQ 号的私聊消息合成并在服务端的音频设备上播放语音（是的，服务端🤣），~~也可以本地部署~~。

---

## 安装与配置

1. **克隆仓库**

   ```bash
   git clone https://github.com/YeiJ/DreamSu.git
   git clone https://github.com/qisumei/DreamSu_Plugin.git
   cd DreamSu_Plugin
   ```

  

2. **安装依赖**
```bash
pip install -r requirements.txt
````

3.  **修改信息**
以下配置项需由使用者根据实际环境进行修改：

- **p_blockquery.py**  
  - 数据库文件路径：`db_path`（默认为插件目录下的 `database.db`），可在插件初始化时传入，位于32行：
    ```bash
    self.db_path = 'database.db'
    ```
- **p_catchat.py**  
  - DeepSeek API 密钥：在脚本中设置 `self.api_key`，位于20行：
    ```bash
    self.api_key = "sk-"
    ```
  - 对话历史文件路径：`history_file`，默认 `C:/Users/Administrator/Desktop/chat_history.txt`，位于21行：
    ```bash
    self.history_file = ""
    ```

- **p_drawcat.py**  
  - Stable Diffusion 接口地址：`api_url`（默认为 `http://127.0.0.1:7860/sdapi/v1/txt2img`），位于23行：
    ```bash
    self.api_url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
    ```
  - API 认证用户名/密码，需自行在SD中设置，位于24行：
    ```bash
    self.auth = ("账号", "密码")
    ```
  - 生成图片保存路径模板：脚本中使用的 `output.png`，可根据需求修改目录和文件名格式，位于85行：
    ```bash
    image_path = ''
    ```

- **p_priv_tts.py**  
  - 目标 QQ 号：在脚本中 `target_user_id`，位于59行：
    ```bash
    if str(message.get("user_id", "")) != "QQ号":
    ```
  - 可选说话人嵌入文件：`female_spk.pth`，放置于插件同级目录；无需时可省略该文件，位于28行：
    ```bash
    spk_path = os.path.join(os.path.dirname(__file__), 'female_spk.pth')
    ```

---

## 使用说明

### 1. BlockQuery (`p_blockquery.py`)

* **命令格式**：

  ```text
  查询-<主世界|末地|下界>-方块-<具体|范围>-(x,y,z)(,半径)
  ```

* **示例**：

  * `查询-主世界-方块-具体-(100,64,-50)`：查询指定坐标的所有历史记录。
  * `查询-下界-方块-范围-(0,100,0),10`：查询范围 ±10 内的最多 100 条记录。

* **输出示例**：

  ```text
  📋 坐标 (100,64,-50) 历史记录（共2条）：
  [2025-05-05 14:23:10] stone — 玩家 Steve — 动作: 放置
  [2025-05-05 13:58:47] chest — 玩家 Alex — 动作: 破坏
  ```

### 2. AI Chat (`p_catchat.py`)

* **触发格式**：在消息开头使用句号 `。`，后接对话内容
* **示例**：

  ```text
  。你好，推荐一下晚餐吃什么？
  ```
* **功能**：机器人将调用 DeepSeek API 并返回 AI 回复。

### 3. DrawCat (`p_drawcat.py`)

* **命令格式**：

  ```text
  画图猫猫 <提示词>
  ```
* **示例**：

  ```text
  画图猫猫 一只戴眼镜的猫在弹钢琴
  ```
* **功能**：调用 Stable Diffusion 接口生成图片，并发送至群聊。

### 4. Private TTS (`p_priv_tts.py`)

* **触发条件**：仅处理来自配置中指定 QQ 号的私聊消息，无需提示词
* **示例**：用户私聊内容：

  ```text
  请将这条消息读出来
  ```
* **功能**：在服务器端播放合成的语音。可通过 `send_private_msg` 方法修改为将音频文件发送给用户（忘记写了😥）。
---

## 贡献与许可
如果您有什么疑问或者修改需要提交，请提交issue。    
本项目采用 **MIT 许可证**，详见 [LICENSE](LICENSE)。
