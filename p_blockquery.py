# plugins/example/p_blockquery.py
# __version__ = '1.1.0'

import re
import datetime
import asyncio
import aiosqlite
import logging
from plugin_base import Plugin
from api.send import send_msg

logger = logging.getLogger('bot')
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 世界映射
WORLD_NAME_MAP = {
    "主世界": "minecraft:overworld",
    "末地": "minecraft:the_end",
    "下界": "minecraft:the_nether"
}
# 动作映射
ACTION_MAP = {
    0: "破坏",
    1: "放置",
    2: "使用"
}

class P_blockqueryPlugin(Plugin):
    def __init__(self, bot):
        logger.info('p_blockquery 插件初始化...')
        self.bot = bot
        self.db_path = 'database.db'  # 设置实际路径，不更改需把数据库放在插件同级目录
        asyncio.create_task(self._ensure_tables())

    async def _ensure_tables(self):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                for tbl in ('levels','blocks','materials','users'):
                    cur = await db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                        (tbl,)
                    )
                    if not await cur.fetchone():
                        logger.warning(f"数据库缺少表: {tbl}")
        except Exception as e:
            logger.error(f"检查数据库表时失败: {e}")

    async def on_message(self, message):
        raw = message.get('raw_message','').strip()
        group_id = message.get('group_id')
        if not group_id:
            return
        #获取关键词
        m = re.match(
            r'^查询-(主世界|末地|下界)-方块-(具体|范围)-\((-?\d+),(-?\d+),(-?\d+)\)(?:,(\d+))?$',
            raw
        )
        if not m:
            return

        world_ch, mode, xs, ys, zs, rs = m.groups()
        x,y,z = map(int,(xs,ys,zs))
        radius = int(rs) if rs else None
        if mode=='具体' and radius:
            mode='范围'

        reply = await self._build_reply(world_ch, mode, x, y, z, radius)
        send_msg(
            self.bot.base_url,
            message.get('message_type','group'),
            group_id,
            reply,
            self.bot.token
        )

    async def _build_reply(self, world_ch, mode, x, y, z, radius):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                # 获取 world_id
                cur = await db.execute(
                    "SELECT id FROM levels WHERE name=?",
                    (WORLD_NAME_MAP[world_ch],)
                )
                row = await cur.fetchone()
                if not row:
                    return f"未找到世界「{world_ch}」对应的记录。"
                world_id = row['id']

                # 具体模式：历史记录
                if mode == '具体':
                    cur = await db.execute(
                        "SELECT time,type,user,action FROM blocks "
                        "WHERE level=? AND x=? AND y=? AND z=? ORDER BY time DESC",
                        (world_id, x, y, z)
                    )
                    rows = await cur.fetchall()
                    if not rows:
                        return f"在坐标 ({x},{y},{z}) 未找到任何方块记录。"
                    lines = [f"📋 坐标 ({x},{y},{z}) 历史记录（共{len(rows)}条）："]
                    for r in rows:
                        dt = datetime.datetime.fromtimestamp(r['time']/1000)
                        cur2 = await db.execute(
                            "SELECT name FROM materials WHERE id=?", (r['type'],)
                        )
                        mat = await cur2.fetchone()
                        cur3 = await db.execute(
                            "SELECT name FROM users WHERE id=?", (r['user'],)
                        )
                        usr = await cur3.fetchone()
                        action_desc = ACTION_MAP.get(r['action'], f"未知({r['action']})")
                        lines.append(
                            f"[{dt:%Y-%m-%d %H:%M:%S}] {mat['name'] if mat else '未知材质'} — "
                            f"玩家 {usr['name'] if usr else '未知玩家'} — 动作: {action_desc}"
                        )
                    return "\n".join(lines)

                # 范围模式
                if radius is None:
                    return "范围查询需要指定半径，例如：…,(radius)"
                cur = await db.execute(
                    "SELECT x,y,z,time,type,user,action FROM blocks "
                    "WHERE level=? AND x BETWEEN ? AND ? AND y BETWEEN ? AND ? AND z BETWEEN ? AND ? "
                    "ORDER BY time DESC LIMIT 100",
                    (world_id, x-radius, x+radius, y-radius, y+radius, z-radius, z+radius)
                )
                rows = await cur.fetchall()
                if not rows:
                    return f"在范围 ±{radius} 内未找到任何方块记录。"
                lines = [f"🔍 范围查询 ({x},{y},{z}) ±{radius} 共{len(rows)}条："]
                for r in rows:
                    dt = datetime.datetime.fromtimestamp(r['time']/1000)
                    cur2 = await db.execute(
                        "SELECT name FROM materials WHERE id=?", (r['type'],)
                    )
                    mat = await cur2.fetchone()
                    cur3 = await db.execute(
                        "SELECT name FROM users WHERE id=?", (r['user'],)
                    )
                    usr = await cur3.fetchone()
                    action_desc = ACTION_MAP.get(r['action'], f"未知({r['action']})")
                    lines.append(
                        f"[{dt:%Y-%m-%d %H:%M:%S}] 坐标({r['x']},{r['y']},{r['z']}) — "
                        f"{mat['name'] if mat else '未知材质'} — 玩家 {usr['name'] if usr else '未知玩家'} — 动作: {action_desc}"
                    )
                return "\n".join(lines)
        except Exception as e:
            logger.exception(f"构建回复时出错: {e}")
            return "查询执行失败，请检查日志。"


def setup(bot):
    return P_blockqueryPlugin(bot)