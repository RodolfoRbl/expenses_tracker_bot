from openai import OpenAI


class AIClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_response(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        """
        Generate a response from the OpenAI API based on the given prompt.
        """
        try:
            response = self.client.responses.create(model=model, input=prompt)
            return response.output_text.strip()
        except Exception as e:
            print(f"Error while calling OpenAI API: {e}")
