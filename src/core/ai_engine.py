import json


class AIEngine:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.provider = self.config.get("provider", "openai")
        self.model = self.config.get("model", "gpt-4o-mini")
        self.api_key = self.config.get("api_key", "")

    def match_action(self, user_input: str, actions: list, runtime) -> str | None:
        from core.ai_matchers import get_matcher
        matcher = get_matcher(self.provider)
        return matcher(user_input, actions, runtime, self)

    def _build_prompt(self, user_input: str, actions: list, runtime) -> str:
        prompt = "你是一个互动小说的意图识别助手。\n\n"
        prompt += "【角色】\n"
        for char in runtime.characters.values():
            prompt += f"- {char.name}\n"
        prompt += f"\n【当前状态】\n标签: {runtime.current_label}\n"
        prompt += "\n【可用动作】\n"
        for i, action in enumerate(actions, 1):
            prompt += f"{i}. {action.name} - {action.desc}\n"
        prompt += f"\n【用户输入】\n{user_input}\n\n"
        prompt += "请从可用动作中选择最匹配的一个，只返回动作名称。如果无法匹配，返回 NONE。"
        return prompt

    def _call_openai(self, prompt: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except ImportError:
            raise ImportError("请安装 openai 包: pip install openai")

    def _call_deepseek(self, prompt: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com",
            )
            resp = client.chat.completions.create(
                model=self.model or "deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except ImportError:
            raise ImportError("请安装 openai 包: pip install openai")

    def _call_custom(self, prompt: str) -> str:
        url = self.config.get("url", "")
        if not url:
            raise ValueError("自定义 provider 需要配置 url")
        try:
            import urllib.request
            data = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            }).encode()
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(f"AI API 调用失败: {e}")
