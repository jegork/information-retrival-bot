import os
import random
import sqlite3
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction, ActionExecutionRejection
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from transformers import AutoTokenizer, AutoModelForCausalLM


class GenerateText(Action):

    def __init__(self):
        if os.path.exists('/app/models/dialogpt-ir-bot'):
            print('Models exist')
            self.model = AutoModelForCausalLM.from_pretrained("/app/models/dialogpt-ir-bot")
            self.tokenizer = AutoTokenizer.from_pretrained("/app/models/dialogpt-ir-bot")
        else:
            print('Downloading models')
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
        city = tracker.get_slot('housing_city')
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
                SlotSet('housing_city', None),
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
            SlotSet('housing_city', None),
            SlotSet('min_rooms', None),
            SlotSet('min_area', None)
        ]


class ValidateHousingForm(FormValidationAction):
    @staticmethod
    def cap_each(string):
        list_of_words = string.split(" ")

        for word in list_of_words:
            list_of_words[list_of_words.index(word)] = word.capitalize()

        return " ".join(list_of_words)

    def name(self) -> Text:
        return "validate_housing_form"

    async def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: "DomainDict",
    ) -> List[Text]:
        slot_list = ['housing_city']
        slots_mapped_in_domain.remove('housing_city')
        random.shuffle(slots_mapped_in_domain)
        slot_list.extend(slots_mapped_in_domain)

        return slot_list

    def validate_housing_city(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain) -> \
            Dict[
                Text, Any]:
        if str(tracker.get_slot('requested_slot')) == 'housing_city':

            # TODO: get cities from database
            cities_list = ['Amsterdam', 'Rotterdam', 'Eindhoven', 'Utrecht', 'Haarlem', 'Groningen',
                           'Leiden', 'Breda', 'Maastricht', 'Amstelveen', 'Arnhem', 'Almere', 'Delft',
                           'Tilburg', 'Hilversum', 'Zwolle', 'Enschede', 'Amersfoort', 'Zaandam',
                           'Heerlen', 'Dordrecht', 'Apeldoorn', 'Bussum', 'Nijmegen', 'Roermond',
                           'Deventer', 'Leeuwarden', 'Alkmaar']

            _city = self.cap_each(str(slot_value))
            if _city in cities_list:
                return {'housing_city': _city}
            else:
                dispatcher.utter_message(text=f"City should be one of the following: {', '.join(cities_list)}")
                return {'housing_city': None}
        else:
            dispatcher.utter_message(text='Error! Aborting!!!')
            raise ActionExecutionRejection(self.name())

    def validate_min_price(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain) -> Dict[Text, Any]:
        slot_value = float(slot_value)

        return {'min_price': str(int(slot_value))}

    def validate_max_price(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain) -> Dict[Text, Any]:
        slot_value = float(slot_value)

        return {'max_price': str(int(slot_value))}

    def validate_min_rooms(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain) -> Dict[Text, Any]:
        slot_value = float(slot_value)

        return {'min_rooms': str(int(slot_value))}

    def validate_min_area(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain) -> Dict[Text, Any]:
        slot_value = float(slot_value)

        return {'min_area': str(int(slot_value))}