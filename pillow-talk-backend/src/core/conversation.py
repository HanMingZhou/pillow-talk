"""对话管理模块

提供多轮对话上下文管理功能
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict
from ..models.config import Message, Conversation
from ..utils.exceptions import ConversationNotFoundError


class ConversationManager:
    """对话管理器
    
    管理多轮对话的上下文和生命周期
    """
    
    def __init__(self, cache_ttl: int = 1800, max_history: int = 10):
        """初始化对话管理器
        
        Args:
            cache_ttl: 对话缓存过期时间（秒），默认 30 分钟
            max_history: 最大对话历史轮数，默认 10 轮
        """
        self.conversations: Dict[str, Conversation] = {}
        self.cache_ttl = cache_ttl
        self.max_history = max_history
    
    def create_conversation(self) -> str:
        """创建新对话
        
        Returns:
            对话 ID（UUID 格式）
        """
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = Conversation(
            conversation_id=conversation_id,
            messages=[],
            created_at=datetime.now(),
            last_activity=datetime.now(),
            max_history=self.max_history
        )
        return conversation_id
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> None:
        """添加消息到对话历史
        
        Args:
            conversation_id: 对话 ID
            role: 消息角色（user/assistant/system）
            content: 消息内容
            
        Raises:
            ConversationNotFoundError: 对话不存在时
        """
        if conversation_id not in self.conversations:
            raise ConversationNotFoundError(
                f"Conversation {conversation_id} not found or expired"
            )
        
        conversation = self.conversations[conversation_id]
        
        # 添加新消息
        conversation.messages.append(
            Message(
                role=role,
                content=content,
                timestamp=datetime.now()
            )
        )
        
        # 更新最后活动时间
        conversation.last_activity = datetime.now()
        
        # 保持最近 N 轮对话（每轮包含 user 和 assistant 两条消息）
        max_messages = conversation.max_history * 2
        if len(conversation.messages) > max_messages:
            # 保留系统消息（如果有）和最近的消息
            system_messages = [msg for msg in conversation.messages if msg.role == "system"]
            recent_messages = conversation.messages[-max_messages:]
            conversation.messages = system_messages + recent_messages
    
    def get_history(self, conversation_id: str) -> List[Message]:
        """获取对话历史
        
        Args:
            conversation_id: 对话 ID
            
        Returns:
            对话历史消息列表
        """
        if conversation_id not in self.conversations:
            return []
        
        return self.conversations[conversation_id].messages
    
    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """获取对话对象
        
        Args:
            conversation_id: 对话 ID
            
        Returns:
            对话对象，如果不存在则返回 None
        """
        return self.conversations.get(conversation_id)
    
    def conversation_exists(self, conversation_id: str) -> bool:
        """检查对话是否存在
        
        Args:
            conversation_id: 对话 ID
            
        Returns:
            对话是否存在
        """
        return conversation_id in self.conversations
    
    def cleanup_expired(self) -> int:
        """清理过期对话
        
        Returns:
            清理的对话数量
        """
        now = datetime.now()
        expired_ids = [
            cid for cid, conv in self.conversations.items()
            if (now - conv.last_activity).total_seconds() > self.cache_ttl
        ]
        
        for cid in expired_ids:
            del self.conversations[cid]
        
        return len(expired_ids)
    
    def get_active_conversations_count(self) -> int:
        """获取活跃对话数量
        
        Returns:
            活跃对话数量
        """
        return len(self.conversations)
