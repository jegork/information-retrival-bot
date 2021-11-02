# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
import os
import sqlite3
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from transformers import AutoTokenizer, AutoModelForCausalLM


class GenerateText(Action):

    def __init__(self):
        if os.path.exists('models/dialogpt-ir-bot'):
            self.model = AutoModelForCausalLM.from_pretrained("models/dialogpt-ir-bot")
            self.tokenizer = AutoTokenizer.from_pretrained("models/dialogpt-ir-bot")
        else:
            self.model = AutoModelForCausalLM.from_pretrained("jegorkitskerkin/dialogpt-ir-bot")
            self.tokenizer = AutoTokenizer.from_pretrained("jegorkitskerkin/dialogpt-ir-bot")

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
        min_rooms = tracker.get_slot('min_rooms')
        min_area = tracker.get_slot('min_area')

        cur = self.conn.cursor()

        cur.execute("SELECT * FROM housing WHERE city = ? AND price >= ? AND price <= ? AND rooms >= ? AND area >= ?",
                    (city, min_price, max_price, min_rooms, min_area))

        rows = cur.fetchall()

        if len(rows) == 0:
            dispatcher.utter_message(text='Sorry! No results found! Please try again.')

            return [
                SlotSet('max_price', None),
                SlotSet('min_price', None),
                SlotSet('city', None),
                SlotSet('min_rooms', None),
                SlotSet('min_area', None)
            ]

        dispatcher.utter_message(text=
                                 f'Found {len(rows)} properties' if len(rows) <= 10
                                 else f'Found {len(rows)} properties, showing first 10'
                                 )

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

        return [
            SlotSet('max_price', None),
            SlotSet('min_price', None),
            SlotSet('city', None),
            SlotSet('min_rooms', None),
            SlotSet('min_area', None)
        ]
