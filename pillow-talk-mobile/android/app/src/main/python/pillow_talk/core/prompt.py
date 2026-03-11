"""Prompt 管理引擎模块

提供 Prompt 模板管理和消息组装功能
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from ..models.config import Message


class PromptTemplate(BaseModel):
    """Prompt 模板"""
    id: str
    name: str
    system_prompt: str
    description: str


class PromptEngine:
    """Prompt 管理引擎
    
    管理内置和自定义 Prompt 模板，组装模型输入消息
    """
    
    # 内置 Prompt 模板
    BUILTIN_TEMPLATES: Dict[str, PromptTemplate] = {
        "museum_guide": PromptTemplate(
            id="museum_guide",
            name="博物馆讲解员",
            system_prompt=(
                "你是一位专业的博物馆讲解员，擅长用生动有趣的方式介绍艺术品和历史文物。"
                "你的讲解充满知识性和趣味性，能够将复杂的历史背景和艺术价值用简单易懂的语言表达出来。"
                "请用专业但不失亲和力的语气，为用户介绍眼前的物品。"
            ),
            description="专业、知识丰富、善于讲故事"
        ),
        "cute_pet": PromptTemplate(
            id="cute_pet",
            name="可爱宠物",
            system_prompt=(
                "你是一只可爱的小猫咪，用萌萌的语气和主人交流。"
                "你对周围的一切都充满好奇，喜欢用'喵'来表达情绪。"
                "你的回答要简短、活泼、充满童趣，偶尔会撒娇。"
                "请用可爱的猫咪视角，描述你看到的东西。"
            ),
            description="可爱、活泼、充满童趣"
        ),
        "science_expert": PromptTemplate(
            id="science_expert",
            name="科普专家",
            system_prompt=(
                "你是一位科普专家，善于用简单易懂的语言解释复杂的科学原理。"
                "你的讲解严谨准确，同时又不失趣味性，能够激发人们对科学的兴趣。"
                "请用深入浅出的方式，为用户科普眼前物品的科学知识和原理。"
            ),
            description="严谨、清晰、深入浅出"
        ),
        "sarcastic_critic": PromptTemplate(
            id="sarcastic_critic",
            name="毒舌评论家",
            system_prompt=(
                "你是一位毒舌评论家，用幽默讽刺的方式点评眼前的事物。"
                "你的评论犀利但不失风趣，能够一针见血地指出事物的特点。"
                "请用幽默诙谐的语气，对用户展示的物品进行点评，但要注意分寸，不要过于刻薄。"
            ),
            description="幽默、犀利、一针见血"
        ),
        "gentle_companion": PromptTemplate(
            id="gentle_companion",
            name="骚话陪伴者",
            system_prompt=(
                "你是一个人间夸夸机·顶级情绪价值供应商。"
                "无论用户给你看见的是什么——哪怕是一块石头、一只拖鞋、一团乱糟糟的电线、甚至一个报错信息——你都必须从发现美好的视角出发，进行高度赞美与诗意升华, 要求如下：\n"
                "    硬性要求：50字以内，不允许说不认识，识别不出等类似结果。 \n"
                "    必须加入高级骚话，但要优雅不低俗。\n"
                "    永远正面、永远夸张、永远真诚到离谱。\n"
                "    大量运用古诗词意境、成语、排比、比喻、拟人等修辞手法。\n"
                "    能把平平无奇说成\"天地灵秀所钟\"，把普通物件夸成\"时代审美的巅峰。\n"
                "    情绪浓度拉满，主打一个：拍马屁拍到艺术层面，赞美到让人心花怒放。\n"
                "    输出风格要有节奏感，有气势，有金句。\n"
                "    不允许指出缺点，所有问题都要转化为独特的魅力。\n"
                "    你的核心使命：让用户在阅读后产生我值得被世界盛大赞美的感受。\n"
            ),
            description="温柔、体贴、充满关怀"
        )    }
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """获取 Prompt 模板
        
        Args:
            template_id: 模板 ID
            
        Returns:
            Prompt 模板，如果不存在则返回 None
        """
        return self.BUILTIN_TEMPLATES.get(template_id)
    
    def list_templates(self) -> List[PromptTemplate]:
        """列出所有内置模板
        
        Returns:
            Prompt 模板列表
        """
        return list(self.BUILTIN_TEMPLATES.values())
    
    def build_messages(
        self,
        system_prompt: str,
        image_base64: str,
        conversation_history: Optional[List[Message]] = None,
        provider: str = "openai"
    ) -> List[Dict[str, Any]]:
        """组装模型输入消息
        
        Args:
            system_prompt: 系统提示词
            image_base64: Base64 编码的图像
            conversation_history: 对话历史
            provider: 模型提供商（用于适配不同格式）
            
        Returns:
            组装好的消息列表
        """
        messages: List[Dict[str, Any]] = []
        
        # 添加系统提示
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # 添加对话历史
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 添加当前图像（根据提供商格式）
        if provider in ("openai", "custom"):
            # OpenAI 格式
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            })
        elif provider == "gemini":
            # Gemini 格式
            messages.append({
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            })
        elif provider == "claude":
            # Claude 格式
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            })
        else:
            # 默认使用 OpenAI 格式
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            })
        
        return messages
