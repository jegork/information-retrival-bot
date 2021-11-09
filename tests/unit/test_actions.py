from unittest.mock import Mock, MagicMock

import pytest

from rasa_ai.actions.actions import GenerateText, GetHousing, ValidateHousingForm


@pytest.mark.asyncio
async def test_generate_text():
    generate_text = GenerateText()

    mock_dispatcher = Mock()
    mock_tracker = Mock()
    mock_domain = Mock()

    mock_tracker.latest_message = {'text': 'i love red roses'}

    run = await generate_text.run(mock_dispatcher, mock_tracker, mock_domain)

    mock_dispatcher.utter_message.assert_called_once()

    assert run == []


@pytest.mark.asyncio
async def test_get_housing_one_result():
    mock_conn = Mock()
    mock_cur = Mock()

    mock_conn.cursor.return_value = mock_cur

    mock_cur.fetchall = Mock(return_value=[])

    get_housing = GetHousing(conn=mock_conn)

    mock_dispatcher = Mock()
    mock_tracker = Mock()

    slots = {
        'housing_city': 'Tilburg',
        'max_price': '1500',
        'min_price': '1000',
        'min_rooms': 1,
        'min_area': 100
    }

    mock_tracker.get_slot.side_effect = lambda x: slots[x]

    run = await get_housing.run(mock_dispatcher, mock_tracker, Mock())

    mock_conn.cursor.assert_called_once()
    mock_cur.execute.assert_called_once()
    mock_cur.fetchall.assert_called_once()
    mock_cur.close.assert_called_once()

    mock_dispatcher.utter_message.assert_called_once()

    for s in slots.keys():
        assert mock_tracker.get_slot.called_once_with(s)

    assert isinstance(run, list)
    assert len(run) == 5

    for r in run:
        assert r['event'] == 'slot'
        assert r['name'] in slots.keys()
        assert r['value'] is None


@pytest.mark.asyncio
async def test_get_housing_ten_result():
    mock_conn = Mock()
    mock_cur = Mock()

    mock_conn.cursor.return_value = mock_cur

    mock_cur.fetchall = Mock(return_value=[MagicMock() for _ in range(5)])

    get_housing = GetHousing(conn=mock_conn)

    mock_dispatcher = Mock()
    mock_tracker = Mock()

    mock_dispatcher.utter_message = Mock()

    slots = {
        'housing_city': 'Tilburg',
        'max_price': '1500',
        'min_price': '1000',
        'min_rooms': 1,
        'min_area': 100
    }

    mock_tracker.get_slot.side_effect = lambda x: slots[x]

    run = await get_housing.run(mock_dispatcher, mock_tracker, Mock())

    mock_conn.cursor.assert_called_once()
    mock_cur.execute.assert_called_once()
    mock_cur.fetchall.assert_called_once()
    mock_cur.close.assert_called_once()

    assert mock_dispatcher.utter_message.call_count == 6

    for s in slots.keys():
        assert mock_tracker.get_slot.called_once_with(s)

    assert isinstance(run, list)
    assert len(run) == 5

    for r in run:
        assert r['event'] == 'slot'
        assert r['name'] in slots.keys()
        assert r['value'] is None


def test_validate_housing_form_city_1():
    validate_housing_form = ValidateHousingForm()
    mock_dispatcher = Mock()
    mock_tracker = Mock()
    mock_domain = Mock()

    mock_tracker.get_slot.side_effect = lambda x: 'housing_city' if x == 'requested_slot' else None
    validated_slots = validate_housing_form.validate_housing_city('Tilburg', mock_dispatcher, mock_tracker, mock_domain)

    assert isinstance(validated_slots, dict)
    assert validated_slots['housing_city'] == 'Tilburg'


def test_validate_housing_form_city_2():
    validate_housing_form = ValidateHousingForm()
    mock_dispatcher = Mock()
    mock_tracker = Mock()
    mock_domain = Mock()

    mock_tracker.get_slot.side_effect = lambda x: 'housing_city' if x == 'requested_slot' else None
    validated_slots = validate_housing_form.validate_housing_city('amsterdam', mock_dispatcher, mock_tracker,
                                                                  mock_domain)

    assert isinstance(validated_slots, dict)
    assert validated_slots['housing_city'] == 'Amsterdam'


def test_validate_housing_form_city_3():
    validate_housing_form = ValidateHousingForm()
    mock_dispatcher = Mock()
    mock_tracker = Mock()
    mock_domain = Mock()

    mock_tracker.get_slot.side_effect = lambda x: 'housing_city' if x == 'requested_slot' else None
    validated_slots = validate_housing_form.validate_housing_city('Prague', mock_dispatcher, mock_tracker, mock_domain)
    mock_dispatcher.utter_message.assert_called_once()

    assert isinstance(validated_slots, dict)
    assert validated_slots['housing_city'] is None


def test_validate_housing_form_city_4():
    validate_housing_form = ValidateHousingForm()
    mock_dispatcher = Mock()
    mock_tracker = Mock()
    mock_domain = Mock()

    mock_tracker.get_slot.side_effect = lambda x: 'housing_city' if x == 'requested_slot' else None
    validated_slots = validate_housing_form.validate_housing_city('london', mock_dispatcher, mock_tracker, mock_domain)
    mock_dispatcher.utter_message.assert_called_once()

    assert isinstance(validated_slots, dict)
    assert validated_slots['housing_city'] is None


def test_validate_max_price_fail():
    validate_housing_form = ValidateHousingForm()
    mock_dispatcher = Mock()
    mock_tracker = Mock()
    mock_domain = Mock()

    mock_tracker.get_slot.side_effect = lambda x: 2000 if 'min_price' else None

    validate_housing_form.validate_max_price(1000, mock_dispatcher, mock_tracker, mock_domain)

    mock_dispatcher.utter_message.assert_called_once_with('Maximal price cannot be lower than minimal price.')


def test_validate_min_price_fail():
    validate_housing_form = ValidateHousingForm()
    mock_dispatcher = Mock()
    mock_tracker = Mock()
    mock_domain = Mock()

    mock_tracker.get_slot.side_effect = lambda x: 1000 if 'max_price' else None

    validate_housing_form.validate_min_price(2000, mock_dispatcher, mock_tracker, mock_domain)

    mock_dispatcher.utter_message.assert_called_once_with('Minimal price cannot be larger than maximal price.')


def test_validate_min_price_pass():
    validate_housing_form = ValidateHousingForm()
    mock_dispatcher = Mock()
    mock_tracker = Mock()
    mock_domain = Mock()

    mock_tracker.get_slot.side_effect = lambda x: 2000 if 'max_price' else None

    validate_housing_form.validate_min_price(1000, mock_dispatcher, mock_tracker, mock_domain)

    mock_dispatcher.utter_message.assert_not_called()


def test_validate_max_price_pass():
    validate_housing_form = ValidateHousingForm()
    mock_dispatcher = Mock()
    mock_tracker = Mock()
    mock_domain = Mock()

    mock_tracker.get_slot.side_effect = lambda x: 1000 if 'min_price' else None

    validate_housing_form.validate_max_price(2000, mock_dispatcher, mock_tracker, mock_domain)

    mock_dispatcher.utter_message.assert_not_called()
