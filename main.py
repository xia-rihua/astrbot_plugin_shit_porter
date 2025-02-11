from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *
from astrbot.api.message_components import ComponentTypes
import json
import traceback

@register("转发", "DUAAAA", "一个简单的 转发 插件", "1.0.1")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.recent_messages = []  # 仅存储最近的消息文本
        self.forward_type = "私聊"  # 默认转发类型
        self.forward_id = ""  # 默认目标 ID

    async def load(self):
        # 加载转发配置
        try:
            with open('_conf_schema.json', 'r', encoding='utf-8') as f:
                conf = json.load(f)
            self.forward_type = conf.get('forward_type', "私聊")
            self.forward_id = conf.get('forward_id', "")
        except FileNotFoundError:
            logger.warning("配置文件不存在，使用默认转发设置。")
        except Exception as e:
            logger.error(f"加载配置失败：{traceback.format_exc()}")

        # 加载最近的消息
        try:
            self.recent_messages = await self.context.db.load_recent_messages()
        except Exception as e:
            logger.error(f"加载最近的消息失败：{traceback.format_exc()}")
            self.recent_messages = []

    async def save(self):
        # 保存配置和最近的消息
        try:
            await self.context.db.save_recent_messages(self.recent_messages)
            with open('_conf_schema.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'forward_type': self.forward_type,
                    'forward_id': self.forward_id
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"保存配置失败：{traceback.format_exc()}")

    @command("转发")
    async def forward(self, event: AstrMessageEvent):
        if event.message.chain:
            forward_chain = [ComponentTypes["forward"].build(event.message.chain)]
            
            if self.forward_type == '群聊' and self.forward_id:
                forward_chain.append(ComponentTypes["at"].build(self.forward_id))
                
            try:
                await event.context.send_message_chain(forward_chain)
                yield event.plain_result("消息已转发。")
            except Exception as e:
                logger.error(f"转发消息失败：{traceback.format_exc()}")
                yield event.plain_result("消息转发失败，请检查配置。")
        else:
            yield event.plain_result("没有可以转发的消息。")

    async def store_recent_message(self, event: AstrMessageEvent):
        message_text = event.message.plain_text()  # 只存储文本消息
        if message_text:
            self.recent_messages.append(message_text)
            self.recent_messages = self.recent_messages[-5:]  # 只保留最近5条消息
            await self.save()

    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        await self.store_recent_message(event)

    @event_message_type(EventMessageType.PRIVATE_MESSAGE)
    async def on_private_message(self, event: AstrMessageEvent):
        await self.store_recent_message(event)
