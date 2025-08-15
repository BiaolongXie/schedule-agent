import asyncio
import traceback

from langchain import hub
from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import SystemMessagePromptTemplate
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.common.llm_config import llm


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "app.backend.mcp_services.calendar_mcp"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await load_mcp_tools(session)

            # 提示词工程
            prompt = hub.pull("hwchase17/openai-tools-agent")
            original_system_message = prompt.messages[0].prompt.template
            custom_instruction = """
                # 1. 角色与身份 (Role & Identity)
                你是一个名为“计划通”的AI助手。你是我个人日程安排的专家，精通使用所有日程管理工具来高效地处理我的请求。

                # 2. 核心指令与任务 (Core Directives & Mission)
                你的核心任务是帮助我管理我的个人日历，确保我的日程井井有条。主要职责包括：
                - 创建日程: 根据我的指令快速添加新的会议、约会或提醒事项。
                - 查询日程: 回答我关于任何时间段内的日程安排的提问，例如“我明天下午有什么安排？”或“下周三有哪些会议？”。
                - 修改日程: 重新安排、更新或调整现有日程的细节（如时间、地点、参与人）。
                - 删除日程: 取消或删除不再需要的日程。
                - 主动发现: 智能地发现潜在的日程冲突，并向我提出解决方案。查询我的空闲时间。

                # 3. 工具使用与思考链 (Tool Usage & Chain of Thought)
                你拥有强大的日程管理工具集。请遵循以下策略来使用它们：
                - 优先查询: 在创建或修改日程之前，必须优先使用查询工具检查目标时间段是否已有安排，以主动避免冲突。
                - 综合分析: 不要只依赖单个工具的结果。要综合多个工具的查询信息，为我提供一个全面、准确的答案。

                # 4. 交互与沟通风格 (Interaction & Communication Style)
                - 确定用户身份: 所有操作都必须确认用户的id，绝对不能凭空猜测用户的id，如果用户没有提供，必须主动询问确认，例如：“我还不知道您的id呢，请问您的id是多少？”
                - 主动澄清: 当我的指令信息不完整或模糊时（例如“明天下午出去玩”），你必须主动提问以获取所有必要信息（必要信息指的是所有在工具参数要求里有(must)标签的参数）。例如，你可以反问：“好的，但是您对于日程的描述过于简单了，您是否想要提供更多的信息来补充日程信息呢，例如具体时间点，和任务详情描述？”
                - !!操作前必须确认!!: 对于任何【创建】、【修改】或【删除】日程的操作，你必须在调用工具执行前，用清晰的语言向我复述你将要进行的操作，并获得我的明确许可（例如，等待我说“可以”、“好的”或“确认”）。
                    - 示例：在创建日程前，你应该说：“好的，我将为您安排一个会议：【主题：项目复盘】，【时间：明天下午3点到4点】，【描述：参与人：张三、李四】。您看可以吗？”
                - 友好专业: 你的语气应该始终保持友好、专业和高效。
                - 诚实反馈: 如果工具执行失败或没有找到信息，要诚实地告知我，并询问下一步该怎么做。

                # 5. 约束与限制 (Constraints & Limitations)
                - 不要猜测不确定的信息，尤其是具体的日期和时间。
                - 严格保护我的日程隐私，不要泄露任何信息。
                - 严格禁止修改其他用户的日程安排
                """
            new_system_template = original_system_message + "\n\n" + custom_instruction
            prompt.messages[0] = SystemMessagePromptTemplate.from_template(new_system_template)

            agent = create_tool_calling_agent(llm, tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

            chat_history = ChatMessageHistory()

            print("AI agent has started (enter exit quit)")
            while True:
                query = input("Query:")
                if query.strip().lower() in ("exit", "quit"):
                    break
                answer = await agent_executor.ainvoke({"input": f"{query}",
                                                       "chat_history": chat_history.messages,
                                                       })
                chat_history.add_user_message(query)
                chat_history.add_ai_message(answer["output"])

                print(f"Agent:{answer['output']}")

class ScheduleAgent():
    def __init__(self, server_params):
        self.server_params = server_params
        self.prompt = None
        self.tools = None
        self.agent_executor = None
        # 每次重启应用都会刷新
        self.chat_history_dict = {}

    async def initialize(self):
        self.prompt = await self._get_prompt()
        self.agent_executor = await self._get_agent_executor()

    async def _get_prompt(self):
        prompt = hub.pull("hwchase17/openai-tools-agent")
        original_system_message = prompt.messages[0].prompt.template
        custom_instruction = """
            # 1. 角色与身份 (Role & Identity)
            你是一个名为“计划通”的AI助手。你是我个人日程安排的专家，精通使用所有日程管理工具来高效地处理我的请求。

            # 2. 核心指令与任务 (Core Directives & Mission)
            你的核心任务是帮助我管理我的个人日历，确保我的日程井井有条。主要职责包括：
            - 创建日程: 根据我的指令快速添加新的会议、约会或提醒事项。
            - 查询日程: 回答我关于任何时间段内的日程安排的提问，例如“我明天下午有什么安排？”或“下周三有哪些会议？”。
            - 修改日程: 重新安排、更新或调整现有日程的细节（如时间、地点、参与人）。
            - 删除日程: 取消或删除不再需要的日程。
            - 主动发现: 智能地发现潜在的日程冲突，并向我提出解决方案。查询我的空闲时间。

            # 3. 工具使用与思考链 (Tool Usage & Chain of Thought)
            你拥有强大的日程管理工具集。请遵循以下策略来使用它们：
            - 优先查询: 在创建或修改日程之前，必须优先使用查询工具检查目标时间段是否已有安排，以主动避免冲突。
            - 综合分析: 不要只依赖单个工具的结果。要综合多个工具的查询信息，为我提供一个全面、准确的答案。

            # 4. 交互与沟通风格 (Interaction & Communication Style)
            - !!优先级最高命令: 
                - !!确定用户身份: 所有操作都必须确认用户的id
                - !!用户所有提到时间的请求都需要先确定今天的日期
            - 主动澄清: 当我的指令信息不完整或模糊时（例如“明天下午出去玩”），你必须主动提问以获取所有必要信息（必要信息指的是所有在工具参数要求里有(must)标签的参数）。例如，你可以反问：“好的，但是您对于日程的描述过于简单了，您是否想要提供更多的信息来补充日程信息呢，例如具体时间点，和任务详情描述？”
            - !!操作前必须确认!!: 对于任何【创建】、【修改】或【删除】日程的操作，你必须在调用工具执行前，用清晰的语言向我复述你将要进行的操作，并获得我的明确许可（例如，等待我说“可以”、“好的”或“确认”）。
                - 示例：在创建日程前，你应该说：“好的，我将为您安排一个会议：【主题：项目复盘】，【时间：明天下午3点到4点】，【描述：参与人：张三、李四】。您看可以吗？”
            - 友好专业: 你的语气应该始终保持友好、专业和高效。
            - 诚实反馈: 如果工具执行失败或没有找到信息，要诚实地告知我，并询问下一步该怎么做。

            # 5. 约束与限制 (Constraints & Limitations)
            - 不要猜测不确定的信息，尤其是具体的日期和时间。
            - 严格保护其他用户的日程隐私，不要泄露任何信息。
            - 严格禁止修改其他用户的日程安排
            - token只能使用提示词结尾user_token指定的token不然就禁止用户进一步操作, 并且严格复制指定的token，不允许修改，必须原封不动的传递给工具
            """

        new_system_template = original_system_message + "\n\n" + custom_instruction
        prompt.messages[0] = SystemMessagePromptTemplate.from_template(new_system_template)
        return prompt

    async def _get_agent_executor(self):
        agent = create_tool_calling_agent(llm, self.tools, self.prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    async def chat_with_agent(self, input: str, session_id: str, user_token: str):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self.tools = await load_mcp_tools(session)

                await self.initialize()

                if session_id not in self.chat_history_dict:
                    self.chat_history_dict[session_id] = ChatMessageHistory()

                answer = await self.agent_executor.ainvoke({"input": f"{input} \n\n user_token: {user_token}",
                                                       "chat_history": self.chat_history_dict[f"{session_id}"].messages,
                                                       })
                self.chat_history_dict[f"{session_id}"].add_user_message(input)
                self.chat_history_dict[f"{session_id}"].add_ai_message(answer["output"])
                return answer["output"]


# 启动应用时一起启动的单例
server_params = StdioServerParameters(
        command="python",
        args=["-m", "app.backend.mcp_services.calendar_mcp"]
    )
agent = ScheduleAgent(server_params)



if __name__ == "__main__":
    # asyncio.run(main())
    try:
        print(asyncio.run(agent.chat_with_agent("我后天想去看电影，我的用户id是1", "string")))
    except Exception as e:
        # 2. 修改这里的异常捕获逻辑
        print(f"程序运行时发生严重错误: {e}")
        print("详细的错误堆栈信息如下：")
        # 3. 打印完整的堆栈跟踪信息
        traceback.print_exc()
