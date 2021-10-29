# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
import os
import sqlite3
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from transformers import AutoTokenizer, AutoModelForCausalLM


class GenerateText(Action):

    def __init__(self):
        if os.path.exists('models/dialogpt-twitter-ubuntu'):
            self.model = AutoModelForCausalLM.from_pretrained("models/dialogpt-twitter-ubuntu")
            self.tokenizer = AutoTokenizer.from_pretrained("models/dialogpt-twitter-ubuntu")
        else:
            self.model = AutoModelForCausalLM.from_pretrained("jegorkitskerkin/dialogpt-twitter-ubuntu")
            self.tokenizer = AutoTokenizer.from_pretrained("jegorkitskerkin/dialogpt-twitter-ubuntu")

    def name(self) -> Text:
        return "action_dialogpt"

    async def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        new_user_input_ids = self.tokenizer.encode(tracker.latest_message['text'] + self.tokenizer.eos_token,
                                                   return_tensors='pt')

        chat_history_ids = self.model.generate(
            new_user_input_ids,
            max_length=1000,
            pad_token_id=self.tokenizer.eos_token_id,
            min_length=24,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            do_sample=True,
            # top_k=50,
            top_p=0.85,
            # temperature=0.6,
            device='cpu'
        )

        generated_text = self.tokenizer.decode(chat_history_ids[:, new_user_input_ids.shape[-1]:][0],
                                               skip_special_tokens=True)
        generated_text = generated_text.strip()

        dispatcher.utter_message(text=generated_text)

        return []


class GetHousing(Action):

    def __init__(self) -> None:
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        self.conn = sqlite3.connect('/app/actions/data/housing.db')
        self.conn.row_factory = dict_factory

    def __del__(self) -> None:
        self.conn.close()

    def name(self) -> Text:
        return "action_get_housing"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[
        Dict[Text, Any]]:

        max_price = tracker.get_slot('max_price')
        min_price = tracker.get_slot('min_price')
        city = tracker.get_slot('city')

        cur = self.conn.cursor()

        cur.execute("SELECT * FROM housing WHERE city = ? AND price >= ? AND price <= ?", (city, min_price, max_price))

        rows = cur.fetchall()

        if len(rows) == 0:
            dispatcher.utter_message(text='Sorry! No results found! Please try again.')

            return []

        dispatcher.utter_message(text=f'Found {len(rows)} properties' if len(rows) <= 10 else
            f'Found {len(rows)} properties, showing first 10')

        for row in rows[:10]:
            msg = f"""
            <a href="{row['link']}">{row['title']}</a>
            Price: € {row['price']}
            Area: {row['area']} m2
            Rooms: {row['rooms']}
            Interior: {row['interior']}
            Location: {row['location']}
            """

            dispatcher.utter_message(text=msg, attachment=row['link'])

        cur.close()

        return []
