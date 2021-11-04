# information-retrival-bot

## Build

```bash
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build
```

## Run

From the root directory:
```bash
docker-compose up
```

The UI is available at http://localhost:8000/

## DialoGPT

DialoGPT can be run and tested using the ``text-generative-model/train_dialogpt.ipynb`` in a code cell at the end.

## Todo
- [x] Add FastAPI server for translation
- [x] Make Rasa custom action to fetch results from server
- [x] Add message for "no results found"
- [ ] Add buttons for interior and city choice
- [ ] Write test stories
- [ ] Write FastAPI tests
- [x] Create idea for what the bot is going to search for
- [x] Create related Rasa conversations
- [x] Add Rasa filtering dialogues
- [x] Make Rasa out-of-scope case and hook up DialoGPT model
- [x] Make Docker images
- [x] Write frontend with UI
- [x] Better clean input data for DialoGPT
- [x] Add data for DialoGPT
- [x] Retrain DialoGPT
- [x] Add tokenizer to DialoGPT repository
- [ ] Code cleanup
- [x] Handle wrong inputs in form
- [x] Add requirements.txt