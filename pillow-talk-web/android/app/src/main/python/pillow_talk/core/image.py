"""图像预处理模块

提供图像压缩、格式转换和编码功能
"""
import base64
import io
from PIL import Image
from ..utils.exceptions import ImageProcessingError


class ImagePreprocessor:
    """图像预处理器
    
    负责图像的压缩、格式转换和 Base64 编码
    """
    
    def __init__(self, max_size_mb: float = 1.0, quality: int = 85):
        """初始化图像预处理器
        
        Args:
            max_size_mb: 最大图像大小（MB）
            quality: JPEG 压缩质量（1-100）
        """
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.quality = quality
    
    async def process(self, image_data: bytes) -> str:
        """处理图像并返回 Base64 编码
        
        Args:
            image_data: 原始图像数据
            
        Returns:
            Base64 编码的图像字符串
            
        Raises:
            ImageProcessingError: 图像处理失败时
        """
        try:
            # 打开图像
            image = Image.open(io.BytesIO(image_data))
            
            # 转换为 RGB（处理 RGBA、P 等格式）
            if image.mode not in ("RGB", "L"):
                if image.mode == "RGBA":
                    # 创建白色背景
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])  # 使用 alpha 通道作为 mask
                    image = background
                else:
                    image = image.convert("RGB")
            
            # 压缩图像
            output = io.BytesIO()
            quality = self.quality
            
            # 逐步降低质量直到满足大小要求
            while True:
                output.seek(0)
                output.truncate()
                image.save(output, format="JPEG", quality=quality, optimize=True)
                
                if output.tell() <= self.max_size_bytes or quality <= 50:
                    break
                
                quality -= 5
            
            # Base64 编码
            output.seek(0)
            encoded = base64.b64encode(output.read()).decode("utf-8")
            
            return encoded
            
        except Exception as e:
            raise ImageProcessingError(f"Failed to process image: {str(e)}")
    
    def validate_image(self, image_data: bytes) -> bool:
        """验证图像是否有效
        
        Args:
            image_data: 图像数据
            
        Returns:
            图像是否有效
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            image.verify()
            return True
        except Exception:
            return False
    
    @staticmethod
    def decode_base64(base64_str: str) -> bytes:
        """解码 Base64 字符串为图像数据
        
        Args:
            base64_str: Base64 编码的字符串
            
        Returns:
            图像数据字节
            
        Raises:
            ImageProcessingError: 解码失败时
        """
        try:
            # 移除可能的 data URL 前缀
            if base64_str.startswith("data:image"):
                base64_str = base64_str.split(",", 1)[1] if "," in base64_str else base64_str
            
            return base64.b64decode(base64_str)
        except Exception as e:
            raise ImageProcessingError(f"Failed to decode base64 image: {str(e)}")
