import os
import random
import sqlite3
from typing import Any, Text, Dict, List
import logging

from rasa_sdk import Action, Tracker, FormValidationAction, ActionExecutionRejection
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)


class GenerateText(Action):

    def __init__(self):
        if os.path.exists('/app/models/dialogpt-ir-bot'):
            logger.info('Models exist')
            self.model = AutoModelForCausalLM.from_pretrained("/app/models/dialogpt-ir-bot")
            self.tokenizer = AutoTokenizer.from_pretrained("/app/models/dialogpt-ir-bot")
        else:
            logger.info('Downloading models')
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

    def __init__(self, conn=None) -> None:
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        if conn is None:
            self.conn = sqlite3.connect('/app/actions/data/housing.db')
            logger.info('connected to db')
        else:
            self.conn = conn

        self.conn.row_factory = dict_factory

    def __del__(self) -> None:
        self.conn.close()

    def name(self) -> Text:
        return "action_get_housing"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[
        Dict[Text, Any]]:

        city = tracker.get_slot('housing_city')
        max_price = tracker.get_slot('max_price')
        min_price = tracker.get_slot('min_price')
        min_rooms = tracker.get_slot('min_rooms')
        min_area = tracker.get_slot('min_area')

        cur = self.conn.cursor()

        cur.execute("SELECT * FROM housing WHERE city = ? AND price >= ? AND price <= ? AND rooms >= ? AND area >= ?",
                    (city, min_price, max_price, min_rooms, min_area))

        rows = cur.fetchall()
        cur.close()

        if len(rows) == 0:
            dispatcher.utter_message(text='Sorry! No results found! Please try again.')

            return [
                SlotSet('max_price', None),
                SlotSet('min_price', None),
                SlotSet('housing_city', None),
                SlotSet('min_rooms', None),
                SlotSet('min_area', None)
            ]

        dispatcher.utter_message(text=
                                 f'Found {len(rows)} properties' if len(rows) <= 10
                                 else f'Found {len(rows)} properties, showing first 10'
                                 )

        for row in rows[:10]:
            msg = f"""\
            Price: € {row['price']}
            Area: {row['area']} m2
            Rooms: {row['rooms']}
            Interior: {row['interior']}
            Location: {row['location']}\
            """

            data = {
                'title': row['title'],
                'text': msg,
                'link': row['link'],
            }

            dispatcher.utter_message(json_message=data)

        return [
            SlotSet('max_price', None),
            SlotSet('min_price', None),
            SlotSet('housing_city', None),
            SlotSet('min_rooms', None),
            SlotSet('min_area', None)
        ]


class ValidateHousingForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_housing_form"

    async def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: "DomainDict",
    ) -> List[Text]:

        return ['housing_city', 'min_price', 'max_price', 'min_area', 'min_rooms']

    async def extract_housing_city(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # TODO: write tests
        if tracker.get_slot('requested_slot') == 'housing_city':
            if tracker.latest_message['intent']['name'] == 'tell_city':
                value = tracker.latest_message['entities'][0]['value']
                return {'housing_city': value}
            else:
                dispatcher.utter_message(template='utter_this_is_wrong')
                return {'housing_city': None}
        else:
            return {}

    async def extract_min_price(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # TODO: write tests
        if tracker.get_slot('requested_slot') == 'min_price':
            if tracker.latest_message['intent']['name'] == 'tell_number':
                value = tracker.latest_message['entities'][0]['value']
                return {'min_price': int(float(value))}
            else:
                dispatcher.utter_message(template='utter_this_is_wrong')
                return {'min_price': None}
        else:
            return {}

    async def extract_max_price(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # TODO: write tests
        if tracker.get_slot('requested_slot') == 'max_price':
            if tracker.latest_message['intent']['name'] == 'tell_number':
                value = tracker.latest_message['entities'][0]['value']
                return {'max_price': int(float(value))}
            else:
                dispatcher.utter_message(template='utter_this_is_wrong')
                return {'max_price': None}
        else:
            return {}

    async def extract_min_area(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # TODO: write tests
        if tracker.get_slot('requested_slot') == 'min_area':
            if tracker.latest_message['intent']['name'] == 'tell_number':
                value = tracker.latest_message['entities'][0]['value']
                return {'min_area': int(float(value))}
            else:
                dispatcher.utter_message(template='utter_this_is_wrong')
                return {'min_area': None}
        else:
            return {}

    async def extract_min_rooms(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # TODO: write tests
        if tracker.get_slot('requested_slot') == 'min_rooms':
            if tracker.latest_message['intent']['name'] == 'tell_number':
                value = tracker.latest_message['entities'][0]['value']
                return {'min_rooms': int(float(value))}
            else:
                dispatcher.utter_message(template='utter_this_is_wrong')
                return {'min_rooms': None}
        else:
            return {}

    def validate_housing_city(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain) -> \
            Dict[
                Text, Any]:
        if slot_value is None:
            return {'housing_city': None}

        def cap_each(string):
            list_of_words = string.split(" ")

            for word in list_of_words:
                list_of_words[list_of_words.index(word)] = word.capitalize()

            return " ".join(list_of_words)

        # TODO: get cities from database
        cities_list = ['Amsterdam', 'Rotterdam', 'Eindhoven', 'Utrecht', 'Haarlem', 'Groningen',
                       'Leiden', 'Breda', 'Maastricht', 'Amstelveen', 'Arnhem', 'Almere', 'Delft',
                       'Tilburg', 'Hilversum', 'Zwolle', 'Enschede', 'Amersfoort', 'Zaandam',
                       'Heerlen', 'Dordrecht', 'Apeldoorn', 'Bussum', 'Nijmegen', 'Roermond',
                       'Deventer', 'Leeuwarden', 'Alkmaar']

        _city = cap_each(str(slot_value))
        if _city in cities_list:
            return {'housing_city': _city}
        else:
            dispatcher.utter_message(text=f"City should be one of the following: {', '.join(cities_list)}")
            return {'housing_city': None}

    def validate_min_price(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain) -> Dict[Text, Any]:
        if slot_value is None:
            return {'min_price': None}

        max_price = tracker.get_slot('max_price')

        if max_price is not None and max_price < slot_value:
            dispatcher.utter_message('Minimal price cannot be larger than maximal price.')
            return {'min_price': None}
        else:
            return {'min_price': slot_value}

    def validate_max_price(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain) -> Dict[Text, Any]:
        if slot_value is None:
            return {'max_price': None}

        min_price = tracker.get_slot('min_price')

        if min_price is not None and min_price > slot_value:
            dispatcher.utter_message('Maximal price cannot be lower than minimal price.')
            return {'max_price': None}
        else:
            return {'max_price': slot_value}

    def validate_min_rooms(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain) -> Dict[Text, Any]:

        return {'min_rooms': slot_value}

    def validate_min_area(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain) -> Dict[Text, Any]:

        return {'min_area': slot_value}