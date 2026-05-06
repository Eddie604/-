import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import time
import os
import json
from datetime import datetime
import random
from typing import Dict, Any, Tuple, Optional

# ===== 配置参数 =====
SCREEN_WIDTH = 3840
SCREEN_HEIGHT = 2160
FONT_PATH = r"D:\江城圆体 700W.ttf"

# ===== 二次元图片API列表（Pixiv镜像、插画网站，随机返回，无标签限制，含R18）=====
IMAGE_APIS = [
    # 1. Pixiv 国内镜像源
    "https://api.likepoems.com/img/pixiv/",
    "https://t.alcy.cc/ycy",
    "https://t.alcy.cc/acg",
    # 2. Pixiv 图片服务（支持R18）
    "https://img.jitsu.top/",
    "https://img.jitsu.top/?sort=r18",
    # 3. 南风二次元随机图
    "https://api.sretna.cn/api/anime.php",
    # 4. 三秋随机二次元
    "https://api.btstu.cn/sjbz/api.php?lx=dongman",
    # 5. 通用随机图片服务
    "https://uapis.cn/api/v1/random/image?category=acg&type=pc",
    # 6. 免费动漫图库
    "https://nekos.best/api/v2/neko",
    "https://api.nekosia.cat/api/v1/images/catgirl",
    # 7. 其他稳定社区 API
    "https://www.dmoe.cc/random.php",
    "https://api.mtyqx.cn/api/random.php?type=302",
    "https://imgapi.xl0408.top/index.php",
    "https://api.obfs.dev/api/acgimg",
]

# 纯净附加源（避免NSFW时启用，但默认主列表已包含，这里作为保底）
SAFE_IMAGE_APIS = [
    "https://api.yimian.xyz/img?type=moe",
    "https://api.btstu.cn/sjbz/api.php?lx=dongman",
]

# ===== 每日一句/诗词API列表 =====
QUOTE_APIS = [
    "https://api.66mz8.com/api/rand.qinghua.php?format=json",  # 情话
    "https://v1.hitokoto.cn",                              # 一言
    "https://v2.jinrishici.com/one.json?client=npm-sdk/1.0", # 今日诗词
    "https://api.7585.net.cn/1/1.json",                     # 经典语录
    "https://api.1314.cool/words/api.php?return=json",      # 古诗词
]

# ===== Pillow 兼容性处理 =====
try:
    RESAMPLE_FILTER = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_FILTER = Image.LANCZOS

# ===== 幻灯片图片保存路径 =====
SLIDESHOW_FOLDER = os.path.join(
    os.getenv('LOCALAPPDATA'),
    'Microsoft',
    'Windows',
    'Themes',
    'DailyWallpapers'
)
os.makedirs(SLIDESHOW_FOLDER, exist_ok=True)

# ===== 字体处理 =====
def get_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        if os.path.exists(FONT_PATH):
            return ImageFont.truetype(FONT_PATH, size)
        else:
            print(f"⚠️ 未找到字体: {FONT_PATH}，尝试使用默认字体")
            fallback_fonts = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simsun.ttc",
                "C:/Windows/Fonts/simhei.ttf",
            ]
            for ff in fallback_fonts:
                if os.path.exists(ff):
                    return ImageFont.truetype(ff, size)
            print("⚠️ 未找到中文字体，将使用默认字体")
            return ImageFont.load_default()
    except Exception as e:
        print(f"⚠️ 加载字体失败: {e}，使用默认字体")
        return ImageFont.load_default()

# ===== 图片获取核心 =====
def try_fetch_image(api_url: str) -> Optional[Image.Image]:
    """从单个API获取图片，支持多种响应格式"""
    try:
        print(f"  🔄 尝试: {api_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        resp = requests.get(api_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"    ❌ 状态码: {resp.status_code}")
            return None

        content_type = resp.headers.get('Content-Type', '').lower()

        # 情况1: 直接返回图片二进制数据
        if 'image' in content_type:
            img = Image.open(BytesIO(resp.content))
            return img

        # 情况2: 返回JSON数据（绝大多数新API）
        if 'json' in content_type or api_url.endswith('.json') or 'api' in api_url:
            try:
                data = resp.json()
            except:
                pass
            else:
                img_url = None

                # ------------------ 新增：特殊 API 的解析 ------------------
                # Nekos.best
                if 'nekos.best' in api_url:
                    if 'results' in data and len(data['results']) > 0:
                        img_url = data['results'][0].get('url')
                # Nekosia.cat
                elif 'nekosia.cat' in api_url:
                    if 'images' in data and len(data['images']) > 0:
                        img_url = data['images'][0].get('url')
                # Pixiv 镜像 (api.likepoems.com) 直接返回图片直链
                elif 'likepoems.com' in api_url:
                    if 'url' in data:
                        img_url = data['url']
                    elif 'imgurl' in data:
                        img_url = data['imgurl']
                # 通用兼容（保留原有的多种格式）
                else:
                    if 'imgurl' in data:
                        img_url = data['imgurl']
                    elif 'url' in data:
                        img_url = data['url']
                    elif 'pic' in data:
                        img_url = data['pic']
                    elif 'img' in data:
                        img_url = data['img']
                    elif 'image' in data:
                        img_url = data['image']
                    elif 'images' in data and isinstance(data['images'], list) and len(data['images']) > 0:
                        img_url = data['images'][0].get('url') or data['images'][0].get('source')
                    elif 'results' in data and isinstance(data['results'], list) and len(data['results']) > 0:
                        img_url = data['results'][0].get('url')
                    # 新增：部分API将图片地址放在data字段里
                    elif 'data' in data:
                        if isinstance(data['data'], str):
                            img_url = data['data']
                        elif isinstance(data['data'], dict):
                            img_url = data['data'].get('url') or data['data'].get('img')

                # 如果提取到了图片直链，则下载
                if img_url:
                    # 处理相对路径
                    if not img_url.startswith('http'):
                        base_url = '/'.join(api_url.split('/')[:3])
                        img_url = base_url + ('' if img_url.startswith('/') else '/') + img_url
                    print(f"    📥 从JSON获取图片URL: {img_url}")
                    img_resp = requests.get(img_url, headers=headers, timeout=10)
                    if img_resp.status_code == 200 and 'image' in img_resp.headers.get('Content-Type', ''):
                        img = Image.open(BytesIO(img_resp.content))
                        return img
                    else:
                        print(f"    ❌ 下载图片失败，状态码: {img_resp.status_code}")
                        return None
                # 无有效img_url则进入后续HTML提取流程

        # 情况3: 返回HTML，尝试从中提取图片链接（兼容老API）
        import re
        img_urls = re.findall(r'https?://[^\s<>"\']+?\.(?:jpg|jpeg|png|gif|bmp|webp)', resp.text)
        if img_urls:
            print(f"    🔍 从HTML提取到 {len(img_urls)} 个图片URL，尝试前两个")
            for img_url in img_urls[:2]:
                try:
                    ir = requests.get(img_url, headers=headers, timeout=8)
                    if ir.status_code == 200 and 'image' in ir.headers.get('Content-Type', ''):
                        img = Image.open(BytesIO(ir.content))
                        return img
                except:
                    continue
        return None

    except Exception as e:
        print(f"    ⚠️ 请求失败: {str(e)[:100]}")
        return None

def fetch_image() -> Optional[Image.Image]:
    print("🖼️ 正在获取二次元图片...")
    for api_url in IMAGE_APIS:
        img = try_fetch_image(api_url)
        if img is not None:
            print(f"✅ 从 {api_url} 获取成功！")
            return img
    print("🟡 主API全部失败，尝试纯净备用源...")
    for api_url in SAFE_IMAGE_APIS:
        img = try_fetch_image(api_url)
        if img is not None:
            print(f"✅ 从备用API {api_url} 获取成功！")
            return img
    print("❌ 所有API均失败，使用内置备用图片...")
    return create_fallback_image()

def create_fallback_image() -> Image.Image:
    try:
        img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), (45, 45, 80))
        draw = ImageDraw.Draw(img)
        for i in range(SCREEN_HEIGHT):
            r = int(45 + (80 - 45) * (i / SCREEN_HEIGHT))
            g = int(45 + (45 - 45) * (i / SCREEN_HEIGHT))
            b = int(80 + (120 - 80) * (i / SCREEN_HEIGHT))
            draw.line([(0, i), (SCREEN_WIDTH, i)], fill=(r, g, b))
        for _ in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 3)
            opacity = random.randint(100, 200)
            draw.ellipse([x - size, y - size, x + size, y + size], fill=(255, 255, 255, opacity))
        font = get_font(40)
        text = "无法获取网络图片"
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text(((SCREEN_WIDTH - (bbox[2] - bbox[0])) // 2, (SCREEN_HEIGHT - (bbox[3] - bbox[1])) // 2 - 20),
                  text, font=font, fill=(255, 255, 255))
        font_small = get_font(20)
        subtext = "请检查网络连接或稍后重试"
        sbbox = draw.textbbox((0, 0), subtext, font=font_small)
        draw.text(((SCREEN_WIDTH - (sbbox[2] - sbbox[0])) // 2, (SCREEN_HEIGHT - (bbox[3] - bbox[1])) // 2 + 30),
                  subtext, font=font_small, fill=(200, 200, 255))
        print("🎨 内置备用图片创建成功！")
        return img
    except Exception as e:
        print(f"❌ 创建备用图片失败: {e}")
        return Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), (70, 130, 180))

# ===== 每日一句/诗词获取 =====
def fetch_quote() -> Dict[str, str]:
    print("📝 正在获取每日一句...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    for api_url in QUOTE_APIS:
        try:
            print(f"  🔄 尝试: {api_url}")
            resp = requests.get(api_url, headers=headers, timeout=5)
            if resp.status_code != 200:
                continue
            data = resp.json()

            quote = ""
            source = ""

            # 今日诗词
            if 'jinrishici' in api_url:
                if 'data' in data:
                    content = data['data'].get('content', '')
                    origin = data['data'].get('origin', {})
                    source = origin.get('title', '') + ' · ' + origin.get('dynasty', '') + ' · ' + origin.get('author', '')
                    quote = content.strip()
                    if quote:
                        print(f"✅ 获取成功: {quote} —— {source}")
                        return {'text': quote, 'source': source}

            # 一言
            if 'hitokoto' in data:
                quote = data['hitokoto']
                source = data.get('from', '未知来源')
                if quote:
                    print(f"✅ 获取成功: {quote} —— {source}")
                    return {'text': quote, 'source': source}

            # 通用格式
            if 'content' in data:
                quote = data['content']
                source = data.get('from', data.get('author', '未知来源'))
            elif 'text' in data:
                quote = data['text']
                source = data.get('source', data.get('from', '未知来源'))
            elif 'msg' in data:
                quote = data['msg']
                source = '网络语录'
            elif 'data' in data and isinstance(data['data'], dict):
                quote = data['data'].get('content', data['data'].get('hitokoto', ''))
                source = data['data'].get('from', '未知')

            if quote:
                print(f"✅ 获取成功: {quote} —— {source}")
                return {'text': quote, 'source': source}
        except Exception as e:
            print(f"    ⚠️ 失败: {e}")
            continue

    print("🟡 所有句子API失败，使用默认句子...")
    return {'text': '长风破浪会有时，直挂云帆济沧海。', 'source': '李白《行路难》'}

# ===== 文字绘制 =====
def draw_text_on_image(img: Image.Image, quote_data: Dict[str, str]) -> Image.Image:
    draw = ImageDraw.Draw(img, 'RGBA')
    now = datetime.now()
    date_str = now.strftime("%Y.%m.%d")
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    full_date = f"{date_str} {weekdays[now.weekday()]}"

    base_size = int(min(img.width, img.height) * 0.04)
    base_size = max(30, min(base_size, 60))
    font_date = get_font(int(base_size * 1.4))
    font_text = get_font(base_size)
    font_source = get_font(int(base_size * 0.8))

    date_bbox = draw.textbbox((0, 0), full_date, font=font_date)
    date_w, date_h = date_bbox[2] - date_bbox[0], date_bbox[3] - date_bbox[1]

    quote_text = quote_data.get('text', 'Error: No Quote')
    text_bbox = draw.textbbox((0, 0), quote_text, font=font_text)
    text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    source_str = f"—— {quote_data.get('source', '')}" if quote_data.get('source') else ""
    if source_str:
        src_bbox = draw.textbbox((0, 0), source_str, font=font_source)
        src_w, src_h = src_bbox[2] - src_bbox[0], src_bbox[3] - src_bbox[1]
    else:
        src_w, src_h = 0, 0

    max_width = img.width * 0.9
    while text_w > max_width and base_size > 20:
        base_size -= 1
        font_text = get_font(base_size)
        text_bbox = draw.textbbox((0, 0), quote_text, font=font_text)
        text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    gap = 20
    total_height = date_h + text_h + (src_h + gap if source_str else 0) + gap
    center_y = int(img.height * 0.45)
    start_y = center_y - total_height // 2
    center_x = img.width // 2

    max_text_w = max(date_w, text_w, src_w)
    padding = 30
    bg_w = max_text_w + padding * 2
    bg_h = total_height + padding * 2
    bg_x = center_x - bg_w // 2
    bg_y = start_y - padding

    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle([bg_x, bg_y, bg_x + bg_w, bg_y + bg_h],
                                   radius=20, fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

    # 文字阴影
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        draw.text((center_x - date_w // 2 + dx, start_y + dy), full_date, font=font_date, fill=(10, 10, 10))
        draw.text((center_x - text_w // 2 + dx, start_y + date_h + gap + dy), quote_text, font=font_text, fill=(10, 10, 10))

    # 主体文字
    draw.text((center_x - date_w // 2, start_y), full_date, font=font_date, fill=(255, 255, 255))
    draw.text((center_x - text_w // 2, start_y + date_h + gap), quote_text, font=font_text, fill=(255, 255, 255))
    if source_str:
        draw.text((center_x - src_w // 2, start_y + date_h + text_h + gap * 2), source_str, font=font_source, fill=(200, 200, 240))

    return img

# ===== 壁纸创建主流程 =====
def create_wallpaper() -> Optional[str]:
    try:
        print("🚀 步骤1: 获取二次元图片...")
        img = fetch_image()
        if img is None:
            return None

        print("🚀 步骤2: 获取每日一句...")
        quote_data = fetch_quote()

        print("🚀 步骤3: 添加每日一句到图片...")
        img = draw_text_on_image(img, quote_data)

        print("🚀 步骤4: 调整图片尺寸...")
        img_ratio = img.width / img.height
        target_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        if img_ratio > target_ratio:
            new_height = SCREEN_HEIGHT
            new_width = int(SCREEN_HEIGHT * img_ratio)
            img = img.resize((new_width, new_height), RESAMPLE_FILTER)
            left = (new_width - SCREEN_WIDTH) // 2
            img = img.crop((left, 0, left + SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            new_width = SCREEN_WIDTH
            new_height = int(SCREEN_WIDTH / img_ratio)
            img = img.resize((new_width, new_height), RESAMPLE_FILTER)
            top = (new_height - SCREEN_HEIGHT) // 2
            img = img.crop((0, top, SCREEN_WIDTH, top + SCREEN_HEIGHT))
        print(f"✅ 图片已调整为: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

        img.info['dpi'] = (96, 96)
        try:
            from PIL import ImageCms
            srgb = ImageCms.createProfile("sRGB")
            img = ImageCms.profileToProfile(img, srgb, srgb, outputMode='RGB')
        except:
            pass

        print("🚀 步骤5: 保存壁纸...")
        filename = f"wallpaper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        save_path = os.path.join(SLIDESHOW_FOLDER, filename)
        img.save(save_path, 'JPEG', quality=95)
        print(f"✅ 壁纸已保存: {save_path}")
        return save_path
    except Exception as e:
        print(f"❌ 创建壁纸失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def cleanup_old_wallpapers(max_count: int = 10):
    try:
        files = [f for f in os.listdir(SLIDESHOW_FOLDER) if f.startswith('wallpaper_') and f.endswith('.jpg')]
        files = sorted(files, key=lambda f: os.path.getmtime(os.path.join(SLIDESHOW_FOLDER, f)), reverse=True)
        for f in files[max_count:]:
            os.remove(os.path.join(SLIDESHOW_FOLDER, f))
            print(f"🗑️ 已删除旧壁纸: {f}")
        print(f"✅ 清理完成，保留最新 {min(max_count, len(files))} 张")
    except Exception as e:
        print(f"⚠️ 清理失败: {e}")

def refresh_windows_wallpaper():
    try:
        import ctypes
        ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, None, 0x0001 | 0x0002)
        print("🔄 已刷新Windows壁纸")
    except Exception as e:
        print(f"⚠️ 刷新失败: {e}")

def main():
    print("=" * 70)
    print("🌟 二次元诗词壁纸生成器 v4.0 (Pixiv镜像版) 🌟")
    print(f"📊 分辨率: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"📁 图片保存: {SLIDESHOW_FOLDER}")
    print(f"🌐 图片API: {len(IMAGE_APIS) + len(SAFE_IMAGE_APIS)} 个")
    print(f"📜 句子API: {len(QUOTE_APIS)} 个（含诗词）")
    print("=" * 70)

    saved_path = create_wallpaper()
    if saved_path:
        cleanup_old_wallpapers(10)
        refresh_windows_wallpaper()
        print("\n🎉 完成！壁纸已更新，建议将幻灯片文件夹设置为此路径：")
        print(f"   {SLIDESHOW_FOLDER}")
    else:
        print("\n❌ 壁纸创建失败")

    print("\n⏱️ 程序执行完毕")
    time.sleep(3)

if __name__ == "__main__":
    main()