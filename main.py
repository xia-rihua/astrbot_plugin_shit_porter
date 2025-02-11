from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *
from astrbot.api.message_components import ComponentTypes
import json

@register("转发", "DUAAAA", "一个简单的 转发 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.recent_messages = []  # 缓存最近的消息

    async def load(self):
        # 加载最近的消息
        try:
            with open('_conf_schema.json', 'r', encoding='utf-8') as f:
                conf = json.load(f)
            self.forward_type = conf['forward_type']
            self.forward_id = conf['forward_id']
        except FileNotFoundError:
            self.forward_type = None
            self.forward_id = None

        # 从配置文件读取最近的消息
        try:
            self.recent_messages = await self.context.db.load_recent_messages()
        except Exception as e:
            logger.error(f"加载最近的消息失败：{e}")
            self.recent_messages = []

    async def save(self):
        # 保存最近的消息
        try:
            await self.context.db.save_recent_messages(self.recent_messages)
            with open('_conf_schema.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'forward_type': self.forward_type,
                    'forward_id': self.forward_id
                }, f)
        except Exception as e:
            logger.error(f"保存最近的消息失败：{e}")

    @command("转发")
    async def forward(self, event: AstrMessageEvent):
        if event.message.chain:
            # 根据配置自动转发
            if self.forward_type == '群聊':
                # 转发到群聊
                forward_chain = [
                    ComponentTypes["forward"].build(event.message.chain),
                    ComponentTypes["at"].build(self.forward_id),
                ]
                await event.context.send_message_chain(forward_chain)
            elif self.forward_type == '私聊':
                # 转发到私聊
                forward_chain = [
                    ComponentTypes["forward"].build(event.message.chain),
                ]
                await event.context.send_message_chain(forward_chain)
            else:
                yield event.plain_result("未知转发类型")
        else:
            yield event.plain_result("没有可以转发的消息。")

    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        # 将消息添加到最近的消息列表
        self.recent_messages.append(event)
        self.recent_messages = self.recent_messages[-5:]  # 只保留最近5条消息
        await self.save()

    @event_message_type(EventMessageType.PRIVATE_MESSAGE)
    async def on_private_message(self, event: AstrMessageEvent):
        # 将消息添加到最近的消息列表
        self.recent_messages.append(event)
        self.recent_messages = self.recent_messages[-5:]  # 只保留最近5条消息
        await self.save()
