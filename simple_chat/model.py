"""
This module provides a `ModelHandler` class for using pre-trained text generation models.

The `ModelHandler` class simplifies the process of loading, initializing, and using
a text generation model from the `transformers` library. It provides methods
for preprocessing prompts, generating text, and maintaining a chat history.

The module also includes basic logging functionality to provide information about
the model's initialization and usage.

Example usage:
model_handler = ModelHandler("meta-llama/Llama-3.2-1B-Instruct")
output = model_handler.predict("What is the capital of France?")
"""
import logging
import torch
from transformers import pipeline

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ModelHandler:
    """
    Handles the loading, initialization, and usage of a text generation model.

    This class uses the `transformers` library to load and initialize a pre-trained
    text generation model. It provides methods for preprocessing prompts,
    generating text, and maintaining a chat history.

    Attributes:
        pipe (transformers.Pipeline): The text generation pipeline.
        chat_history (list): A list of previous interactions in the chat.

    Args:
        model_id (str): The identifier of the pre-trained model to use.
        max_new_tokens (int): The maximum number of new tokens to generate.
        max_length (int): The maximum length of the generated text.

    Methods:
        preprocess_prompt(self, prompt_text): Preprocesses the prompt and adds it to the chat history.
        predict(self, prompt_text): Generates text based on the prompt and chat history.

    """
    def __init__(self, model_id, max_new_tokens=600, max_length=600) -> None:
        logger.info('Initializing model %s.', model_id)
        device: str = "cuda:0" if torch.cuda.is_available() else "cpu"
        logger.info('Model will be initialized on %s.', device)
        self.pipe = pipeline(
            "text-generation",
            model=model_id,
            device=device,
            max_new_tokens=max_new_tokens,
            max_length=max_length,
        )
        logger.info('Model %s has been initialized.', model_id)
        self.chat_history: list[dict] = []

    def clear_history(self) -> None:
        """Clears the chat history."""
        self.chat_history = []
        logger.info("Chat history cleared.")

    def preprocess_prompt(self, prompt_text: str) -> None:
        """Preprocesses the prompt and adds it to the chat history.

                Args:
                    prompt_text (str): The prompt text.
        """
        prompt: dict ={'role': 'user', 'content': prompt_text}
        self.chat_history.append(prompt)
        logger.info('%s has been added to chat history.', prompt)

    def predict(self, prompt_text: str) -> str:
        """Generates text based on the prompt and chat history.

                Args:
                    prompt_text (str): The prompt text.

                Returns:
                    str: The generated text.
        """
        self.preprocess_prompt(prompt_text)
        try:
            output: dict = self.pipe(self.chat_history)[0]['generated_text'][-1]
        except Exception as e:
            logger.error("Error during text generation: %s", e)
            return "Sorry, I encountered an error while processing your request."
        self.chat_history.append(output)
        logger.info('%s has been added to chat history.', output)
        return output['content']
