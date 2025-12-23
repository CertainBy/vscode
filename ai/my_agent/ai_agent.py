from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import ollama
from mcp import ClientSession
from mcp.client.sse import sse_client

# MCP 服务器地址
MCP_SERVER_URL = "http://localhost:8000/sse"
# Ollama 模型
OLLAMA_MODEL = 'qwen3:8b'

app = FastAPI(title="MCP Agent API")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义请求数据模型
class ChatRequest(BaseModel):
    prompt: str

async def chat_with_agent(user_prompt: str) -> str:
    """
    连接 MCP 服务器，协调 Ollama，并返回最终结果字符串。
    """
    print(f"🌉 Agent: 收到请求 '{user_prompt}'，正在连接 MCP: {MCP_SERVER_URL}...")
    
    try:
        # 1. 建立 SSE 连接
        async with sse_client(MCP_SERVER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                # 2. 握手并获取工具
                await session.initialize()
                tools_list = await session.list_tools()
                print(f"✅ Agent: MCP 连接成功，获取到工具: {[t.name for t in tools_list.tools]}")

                # 3. 转换工具格式
                ollama_tools = []
                for tool in tools_list.tools:
                    ollama_tools.append({
                        'type': 'function',
                        'function': {
                            'name': tool.name,
                            'description': tool.description,
                            'parameters': tool.inputSchema
                        }
                    })

                # 4. 开始对话逻辑
                messages = [{'role': 'user', 'content': user_prompt}]

                response = ollama.chat(model=OLLAMA_MODEL, messages=messages, tools=ollama_tools)

                # 检查是否需要调用工具
                if response['message'].get('tool_calls'):
                    print("🤖 Agent: AI 决定调用远程工具...")
                    
                    # 将 AI 的决定加入历史
                    messages.append(response['message'])

                    for tool_call in response['message']['tool_calls']:
                        fn_name = tool_call['function']['name']
                        fn_args = tool_call['function']['arguments']
                        print(f"🌐 Agent: 发送工具调用请求 -> {fn_name}")

                        # 通过 MCP 协议调用远程工具
                        result = await session.call_tool(fn_name, arguments=fn_args)
                        tool_output = result.content[0].text
                        print(f"📩 Agent: 收到工具结果 <- {tool_output}")

                        # 将工具结果加入历史
                        messages.append({'role': 'tool', 'content': tool_output})

                    # 第二次询问 Ollama，获取最终回答
                    final_response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
                    return final_response['message']['content']
                else:
                    # 不需要工具，直接返回回答
                    return response['message']['content']

    except Exception as e:
        print(f"❌ Agent Error: {e}")
        raise e

# 定义 API 接口
@app.post("/agent/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        ai_response = await chat_with_agent(request.prompt)
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 注意监听 8001 端口，避免和 MCP Server (8000) 冲突
    print("🚀 Agent 正在启动，监听端口 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)