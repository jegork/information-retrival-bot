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

To test the bot, open frontend/index.html

### DialoGPT

DialoGPT can be run and tested using the text-generative-model/train_dialogpt.ipynb in a code cell at the end.

### Rasa

To compile Rasa server use:
```bash
cd rasa
rasa train
```

To run Rasa server using command line use (from the rasa folder):
```bash
rasa shell
```

## Todo
- [x] Add FastAPI server for translation
- [x] Make Rasa custom action to fetch results from server
- [x] Add message for "no results found"
- [ ] Add buttons for interior and city choice
- [ ] Write tests
- [x] Create idea for what the bot is going to search for
- [ ] Create related Rasa conversations
- [ ] Add Rasa filtering dialogues
- [x] Make Rasa out-of-scope case and hook up DialoGPT model
- [x] Make Docker images
- [x] Write frontend with UI
- [ ] Better clean input data for DialoGPT
- [ ] Add data for DialoGPT
- [ ] Retrain DialoGPT
- [ ] Add tokenizer to DialoGPT repository
- [ ] Code cleanup
- [ ] Handle wrong inputs in form
- [x] Add requirements.txt