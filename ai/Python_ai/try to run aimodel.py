from ollama import chat
from ollama import ChatResponse

response: ChatResponse = chat(model='qwen3:8b', messages=[
  {
    'role': 'user',
    'content': 'Who are you?',
  },
])
print(response['message']['content'])
#or access fields directly from the response object
#print(response.message.content)