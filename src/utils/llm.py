from openai import OpenAI, RateLimitError


class AIClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key, max_retries=0, timeout=4)

    def generate_response(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        """
        Generate a response from the OpenAI API based on the given prompt.
        """
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "developer", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content.strip()
        except RateLimitError:
            return None
        except Exception as e:
            print("Error from OpenAI request:", e)
            return None
