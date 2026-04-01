import ollama
import time
import json

def test():
    model = "gemma3:1b"
    prompt = "Summarize this: print('hello world')"
    system = "Output JSON only. {'s': 'summary'}"
    
    start = time.time()
    try:
        print(f"Testing {model}...")
        response = ollama.chat(model=model, messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ], format="json")
        end = time.time()
        print(f"Response: {response['message']['content']}")
        print(f"Time taken: {end - start:.2f} seconds")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
