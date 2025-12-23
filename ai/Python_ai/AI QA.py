from ollama import Client

messages = []
client=Client()

while True:
    user_input = input("Q: ")
    if '/bye' in user_input.lower():
        client.delete(model='qwen3:8b')
        break
    messages.append({'role': 'user', 'content': user_input})

    response = client.chat(model='qwen3:8b', messages=messages, stream=True)
    assistant_response = "" 
    print("A: ", end='', flush=True)
    for chunk in response:
        content = chunk['message']['content']
        print(content, end='', flush=True)
        assistant_response += content
    print()

    messages.append({'role': 'assistant', 'content': assistant_response})