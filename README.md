# Bing每日一图插件

## 插件简介

Bing每日一图插件是一个专为聊天机器人设计的实用工具，能够自动获取微软Bing搜索引擎的每日精选图片及相关信息。插件支持多种分辨率选择、图片压缩和多语言显示，让用户能够轻松欣赏高质量的每日壁纸。

## 功能特点
每日精选图片：自动获取Bing每日精选的高质量壁纸

多分辨率支持：支持1366、1920、3840及UHD超高清分辨率

多语言显示：支持中文、英语、日语等多种语言的信息展示

智能缓存机制：1小时缓存减少API请求，提高响应速度

图片压缩功能：自动压缩大尺寸图片，节省带宽

历史图片浏览：支持查看最近7天的精选图片

## 安装方法
将插件文件夹 bing_daily_image_plugin 放入您聊天机器人的 plugins 目录

确保已安装以下依赖：

pip install requests pillow

重启聊天机器人服务以加载插件

## 配置说明
插件的配置文件为 config.toml，位于插件根目录下：

[plugin]
name = "bing_daily_image_plugin"
version = "1.0.0"

[components]
enable_bing_image = true  # 是否启用插件功能

[api]
resolution = "UHD"   # 图片分辨率 (1366,1920,3840,UHD)
language = "zh-CN"   # 语言区域 (zh-CN, en-US, ja-JP等)

[image]
compress_image = true     # 是否压缩大尺寸图片
max_image_size = 4194304  # 最大图片大小(字节)，默认4MB
## 使用方法
在聊天窗口中输入以下任意关键词即可触发插件：

#每日一图, bing壁纸, 必应图片, #bingdaily
可选参数
索引号：指定要查看的历史图片（0=今天, 1=昨天...最多7天前）

#每日一图 1   // 查看昨天的图片
语言代码：指定返回信息的语言

#每日一图 en-US   // 使用英语显示信息
返回内容
插件将返回以下信息：

Bing每日精选图片

图片标题和版权描述

图片详情链接（如有）

示例返回：

🌟 Bing 每日精选图片 🌟

挪威斯瓦尔巴群岛的北极光

© naturepl.com/Steven Kazlowski/DanitaDelimont.com

🔗 图片详情: https://www.bing.com/th?id=OHR.AuroraNorway_ZH-CN...
## 注意事项
插件使用公开的Bing图片API https://bing.biturl.top，请确保网络畅通

图片缓存存储在 cache/bing_daily_image 目录，定期清理可释放空间

压缩功能依赖Pillow库，请确保已正确安装

建议将max_image_size设置为适合您平台的值（默认为4MB）

## 使用效果

![003052ECC904FAA0FBE0C75B9974EBE0](https://github.com/user-attachments/assets/f99ffb38-5c71-49ce-a698-1016ccda1dba)


## 技术支持
如有任何问题或建议，请联系：全民制作人：ikun两年半
许可证：GPL-3.0

