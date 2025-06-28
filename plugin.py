"""
 Copyright (C) 2025 全民制作人：ikun两年半
 SPDX-License-Identifier: GPL-3.0-or-later
 """


import os
import base64
import json
import time
from pathlib import Path
from io import BytesIO
from typing import Tuple, Type, List
from src.common.logger import get_logger
from src.plugin_system import (
    BasePlugin, register_plugin, BaseAction,
    ComponentInfo, ActionActivationType, ChatMode
)
from src.plugin_system.base.config_types import ConfigField
import requests
import asyncio
from functools import partial

logger = get_logger("bing_daily_image_action")

@register_plugin
class BingDailyImagePlugin(BasePlugin):
    """Bing每日一图插件
    提供微软Bing精选的每日壁纸图片及相关说明
    """

    plugin_name = "bing_daily_image_plugin"
    plugin_description = "获取微软Bing每日精选图片并显示相关信息"
    plugin_version = "1.0.0"
    plugin_author = "全民制作人：ikun两年半"
    enable_plugin = True
    config_file_name = "config.toml"

    config_section_descriptions = {
        "plugin": "插件基本配置",
        "components": "组件启用控制",
        "api": "API相关配置",
        "image": "图片处理配置",
    }

    config_schema = {
        "plugin": {
            "config_version": ConfigField(type=str, default="1.0.0", description="配置文件版本号"),
        },
        "components": {
            "enable_bing_image": ConfigField(type=bool, default=True, description="启用Bing每日一图功能"),
        },
        "api": {
            "resolution": ConfigField(type=str, default="1920", description="图片分辨率(如1366,1920,3840,UHD)", choices=["1366", "1920", "3840", "UHD"]),
            "language": ConfigField(type=str, default="zh-CN", description="语言区域", choices=["zh-CN", "en-US", "ja-JP"]),
        },
        "image": {
            "compress_image": ConfigField(type=bool, default=True, description="是否压缩大尺寸图片"),
            "max_image_size": ConfigField(type=int, default=2097152, description="图片最大字节数(默认2MB)"),
        },
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        components = []
        if self.get_config("components.enable_bing_image", True):
            components.append((BingDailyImageAction.get_action_info(), BingDailyImageAction))
        return components

class BingDailyImageAction(BaseAction):
    """Bing每日一图功能"""
    action_name = "bing_daily_image"
    action_description = "获取微软Bing精选每日图片"
    
    focus_activation_type = ActionActivationType.KEYWORD
    normal_activation_type = ActionActivationType.KEYWORD
    mode_enable = ChatMode.ALL
    parallel_action = False
    
    activation_keywords = ["#每日一图", "bing壁纸", "必应图片", "#bingdaily"]
    keyword_case_sensitive = False

    associated_types = ["text", "image"]
    
    action_require = ["当用户需要获取每日精选图片时调用", "当用户发送相关关键词时调用"]
    action_parameters = {
        "index": "0表示今天的图片，1表示昨天的图片，最多7",
        "language": "语言区域代码，如zh-CN，默认自动选择"
    }

    API_URL = "https://bing.biturl.top"
    CACHE_DIR = Path("cache/bing_daily_image")
    CACHE_FILE = CACHE_DIR / "daily_image.json"
    CACHE_EXPIRE = 3600  # 1小时缓存

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cfg = getattr(self, "global_config", None) or kwargs.get("global_config", {}) or {}
        self.api_cfg = cfg.get("api", {})
        self.image_cfg = cfg.get("image", {})

    async def get_daily_image_data(self, index=0):
        """获取Bing每日一图数据"""
        cache_key = f"daily_image_{index}_{self.api_cfg.get('language','zh-CN')}"
        
        # 检查缓存
        if self.CACHE_FILE.exists():
            mtime = self.CACHE_FILE.stat().st_mtime
            if time.time() - mtime < self.CACHE_EXPIRE:
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    if cache_key in cache_data:
                        return cache_data[cache_key]

        # 构建API请求参数
        params = {
            "format": "json",
            "index": index,
            "resolution": self.api_cfg.get("resolution", "1920"),
            "mkt": self.api_cfg.get("language", "zh-CN")
        }

        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(
                None,
                partial(
                    requests.get,
                    self.API_URL,
                    params=params,
                    timeout=15
                )
            )
            resp.raise_for_status()
            data = resp.json()
            
            # 更新缓存
            cache_data = {}
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    try:
                        cache_data = json.load(f)
                    except json.JSONDecodeError:
                        pass
            
            cache_data[cache_key] = data
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return data
        except Exception as e:
            logger.error(f"获取Bing图片数据失败: {e}")
            return None

    async def download_image(self, url):
        """下载图片并返回base64编码"""
        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(
                None,
                partial(
                    requests.get,
                    url,
                    timeout=15
                )
            )
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode("utf-8")
        except Exception as e:
            logger.error(f"下载图片失败: {e} - URL: {url}")
            return None

    async def compress_image(self, img_bytes):
        """压缩图片（如果需要）"""
        from PIL import Image  # 仅在需要时导入
        
        try:
            if not self.image_cfg.get("compress_image", True):
                return img_bytes
                
            max_size = self.image_cfg.get("max_image_size", 2097152)
            if len(img_bytes) <= max_size:
                return img_bytes
                
            img = Image.open(BytesIO(img_bytes))
            if img.mode == 'RGBA':
                img = img.convert('RGB')
                
            # 调整质量因数
            quality = 85
            img_format = "JPEG"
            
            while quality > 50 and len(img_bytes) > max_size:
                buffer = BytesIO()
                img.save(buffer, format=img_format, quality=quality)
                img_bytes = buffer.getvalue()
                quality -= 5
                
            # 如果仍超出限制，调整尺寸
            if len(img_bytes) > max_size:
                new_width = int(img.width * 0.8)
                new_height = int(img.height * 0.8)
                img = img.resize((new_width, new_height))
                buffer = BytesIO()
                img.save(buffer, format=img_format, quality=quality)
                img_bytes = buffer.getvalue()
                
            return img_bytes
        except Exception as e:
            logger.error(f"图片压缩失败: {e}")
            return img_bytes

    async def execute(self) -> Tuple[bool, str]:
        try:
            # 从用户消息提取参数（如果有）
            user_input = self.action_data.get("query", "")
            index = 0
            language = self.api_cfg.get("language", "zh-CN")
            
            # 尝试解析用户输入
            if user_input:
                parts = user_input.split()
                for part in parts:
                    try:
                        i = int(part)
                        if 0 <= i <= 7:
                            index = i
                            break
                    except ValueError:
                        pass
            
            logger.info(f"获取Bing每日图片: 索引={index}, 语言={language}")
            
            # 获取图片数据
            image_data = await self.get_daily_image_data(index)
            if not image_data:
                return False, "获取图片信息失败，请稍后重试"
            
            # 下载图片
            file_url = image_data.get("url", "")
            if not file_url:
                return False, "图片地址不存在"
                
            base64_img = await self.download_image(file_url)
            if not base64_img:
                return False, "下载图片失败"
            
            # 发送文字描述
            title = image_data.get("title", "")
            description = image_data.get("copyright", "")
            
            response_text = "🌟 Bing 每日精选图片 🌟\n"
            if title:
                response_text += f"\n{title}\n"
            if description:
                response_text += f"\n{description}"
            
            await self.send_text(response_text)
            
            # 发送图片
            await self.send_image(base64_img)
            
            # 添加版权信息
            copyright_link = image_data.get("copyright_link", "")
            if copyright_link:
                await self.send_text(f"🔗 图片详情: {copyright_link}")
            
            return True, "Bing每日图片发送成功"
        except Exception as e:
            logger.exception(f"处理Bing图片失败: {e}")
            return False, "获取每日图片时出错"
