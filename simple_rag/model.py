"""
This module provides a `RAGModelHandler` class for using pre-trained text generation models with Retrieval Augmented Generation (RAG).

The `RAGModelHandler` class simplifies the process of loading, initializing, and using
a text generation model from the `transformers` library, incorporating external context for improved responses.
It provides methods for preprocessing prompts, generating text, and maintaining a chat history.

The module also includes basic logging functionality to provide information about
the model's initialization and usage.

Example usage:
model_handler = RAGModelHandler("meta-llama/Llama-3.2-1B-Instruct")
output = model_handler.predict("What is the capital of France?", context=["The capital of France is Paris."])
"""

import torch
import logging
from transformers import pipeline

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RAGModelHandler:
    """
    Handles the loading, initialization, and usage of a text generation model with RAG.

    This class uses the `transformers` library to load and initialize a pre-trained
    text generation model. It provides methods for preprocessing prompts,
    generating text, and maintaining a chat history, while incorporating external context.

    Attributes:
        pipe (transformers.Pipeline): The text generation pipeline.
        chat_history (list): A list of previous interactions in the chat.

    Args:
        model_id (str): The identifier of the pre-trained model to use.
        max_new_tokens (int): The maximum number of new tokens to generate. Defaults to 600.
        max_length (int): The maximum length of the generated text. Defaults to 600.

    Methods:
        clear_history(self): Clears the chat history.
        preprocess_prompt(self, prompt_text, context): Preprocesses the prompt and adds it to the chat history.
        predict(self, prompt_text, context): Generates text based on the prompt, context, and chat history.
    """
    def __init__(self, model_id, max_new_tokens=600, max_length=600) -> None:
        """
        Initializes the RAGModelHandler with the specified model and parameters.

        Args:
            model_id (str): The identifier of the pre-trained model to use.
            max_new_tokens (int): The maximum number of new tokens to generate. Defaults to 600.
            max_length (int): The maximum length of the generated text. Defaults to 600.
        """
        logger.info(f'Initializing model {model_id}.')
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

    def preprocess_prompt(self, prompt_text: str, context: list[str]) -> None:
        """
        Preprocesses the prompt by incorporating context and adding it to the chat history.

        Args:
            prompt_text (str): The user's prompt text.
            context (list[str]): A list of strings representing the external context.
        """
        prompt: dict ={
            'role': 'user',
            'content': f'Given context listed:{" ".join(context)} Answer based on the context. '
                       f'{prompt_text}',
        }
        self.chat_history.append(prompt)
        logger.info('%s has been added to chat history.', prompt)

    def predict(self, prompt_text: str, context: list[str]) -> str:
        """
        Generates text based on the prompt, context, and chat history.

        Args:
            prompt_text (str): The user's prompt text.
            context (list[str]): A list of strings representing the external context.

        Returns:
            str: The generated text response.
        """
        self.preprocess_prompt(prompt_text, context)
        try:
            output: dict = self.pipe(self.chat_history)[0]['generated_text'][-1]
        except Exception as e:
            logger.error(f"Error during text generation: {e}")
            return "Sorry, I encountered an error while processing your request."
        self.chat_history.append(output)
        logger.info('%s has been added to chat history.', output)
        return output['content']
