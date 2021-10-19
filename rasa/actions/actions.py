# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
from typing import Any, Text, Dict, List
#
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from transformers import AutoTokenizer, AutoModelForCausalLM
class GenerateText(Action):

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
        self.model = AutoModelForCausalLM.from_pretrained("jegorkitskerkin/dialogpt-twitter-ubuntu")

    def name(self) -> Text:
        return "action_dialogpt"

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        new_user_input_ids = self.tokenizer.encode(tracker.latest_message['text'] + self.tokenizer.eos_token, return_tensors='pt')

        chat_history_ids = self.model.generate(
            new_user_input_ids, max_length=1000, 
            pad_token_id=self.tokenizer.eos_token_id,
            min_length=16,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            do_sample=True,
            top_k=50,
            top_p=0.9,
            temperature = 0.6,
            device='cpu'
        )

        generated_text = self.tokenizer.decode(chat_history_ids[:, new_user_input_ids.shape[-1]:][0], skip_special_tokens=True)

        dispatcher.utter_message(text=generated_text)

        return []