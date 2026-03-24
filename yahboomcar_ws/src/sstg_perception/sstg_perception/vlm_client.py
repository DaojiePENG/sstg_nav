"""
阿里云百炼 VLM 客户端 - 调用 qwen-vl-plus 进行图像理解
"""

import json
import base64
from pathlib import Path
from typing import Dict, Optional, List
import requests
from dataclasses import dataclass
import time


@dataclass
class VLMResponse:
    """VLM 响应数据"""
    success: bool
    content: str
    error: Optional[str] = None
    tokens_used: Optional[Dict] = None


class VLMClient:
    """
    阿里云百炼 VLM 客户端
    
    支持模型：
    - qwen-vl-plus：高精度视觉理解
    - qwen-vl-max：最高精度（可选）
    """
    
    def __init__(self, api_key: str,
                 base_url: str = 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                 model: str = 'qwen-vl-plus',
                 timeout: float = 30.0):
        """
        初始化 VLM 客户端
        
        Args:
            api_key: 阿里云 API Key
            base_url: 基础 URL
            model: 使用的模型
            timeout: 请求超时时间
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        self.logger_func = print
    
    def set_logger(self, logger_func) -> None:
        """设置日志函数"""
        self.logger_func = logger_func
    
    def call_semantic_annotation(self, image_path: str,
                                 prompt: Optional[str] = None) -> VLMResponse:
        """
        调用 VLM 进行语义标注
        
        Args:
            image_path: 图像文件路径
            prompt: 自定义提示词（如为 None 使用默认提示词）
        
        Returns:
            VLMResponse 对象
        """
        if not Path(image_path).exists():
            return VLMResponse(
                success=False,
                content='',
                error=f'Image file not found: {image_path}'
            )
        
        if prompt is None:
            prompt = self._get_default_prompt()
        
        # 将图像编码为 base64
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            return VLMResponse(
                success=False,
                content='',
                error=f'Failed to read image: {e}'
            )
        
        # 构建请求体
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image',
                            'image': f'data:image/jpeg;base64,{image_data}'
                        },
                        {
                            'type': 'text',
                            'text': prompt
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                return VLMResponse(
                    success=False,
                    content='',
                    error=f'API Error: {response.status_code} - {response.text}'
                )
            
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                return VLMResponse(
                    success=False,
                    content='',
                    error='Invalid API response'
                )
            
            content = result['choices'][0]['message']['content']
            tokens_used = result.get('usage', {})
            
            return VLMResponse(
                success=True,
                content=content,
                tokens_used=tokens_used
            )
        
        except requests.exceptions.Timeout:
            return VLMResponse(
                success=False,
                content='',
                error=f'Request timeout after {self.timeout}s'
            )
        except Exception as e:
            return VLMResponse(
                success=False,
                content='',
                error=f'Request failed: {str(e)}'
            )
    
    def batch_annotate(self, image_paths: List[str],
                      prompt: Optional[str] = None,
                      delay_between_calls: float = 1.0) -> List[VLMResponse]:
        """
        批量标注图像
        
        Args:
            image_paths: 图像路径列表
            prompt: 提示词
            delay_between_calls: 调用之间的延迟
        
        Returns:
            VLMResponse 列表
        """
        results = []
        for idx, path in enumerate(image_paths):
            self.logger_func(f'Annotating {idx+1}/{len(image_paths)}: {Path(path).name}')
            response = self.call_semantic_annotation(path, prompt)
            results.append(response)
            
            if idx < len(image_paths) - 1:
                time.sleep(delay_between_calls)
        
        return results
    
    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """请分析这张房间图像，并以 JSON 格式返回以下信息（确保返回有效的 JSON）：

{
  "room_type": "环境类型（如：客厅、卧室、厨房、卫生间等）",
  "confidence": 0.95,
  "objects": [
    {
      "name": "物品名称",
      "position": "位置（上/下/左/右/中心/前景/背景）",
      "quantity": 1,
      "confidence": 0.95
    }
  ],
  "description": "房间的简要描述"
}

注意：必须返回有效的 JSON 格式，不要包含代码块标记或其他文本。"""
    
    def test_connection(self) -> bool:
        """测试 API 连接"""
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': 'Hello, test message'
                }
            ]
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=self.headers,
                json=payload,
                timeout=10.0
            )
            return response.status_code == 200
        except:
            return False


class VLMClientWithRetry(VLMClient):
    """支持重试的 VLM 客户端"""
    
    def __init__(self, *args, max_retries: int = 3,
                 retry_delay: float = 2.0, **kwargs):
        """
        初始化带重试的 VLM 客户端
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def call_semantic_annotation(self, image_path: str,
                                 prompt: Optional[str] = None) -> VLMResponse:
        """带重试的语义标注调用"""
        for attempt in range(self.max_retries):
            response = super().call_semantic_annotation(image_path, prompt)
            
            if response.success:
                return response
            
            if attempt < self.max_retries - 1:
                self.logger_func(
                    f'Retry {attempt+1}/{self.max_retries-1} after {self.retry_delay}s: {response.error}'
                )
                time.sleep(self.retry_delay)
        
        return response
