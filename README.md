# information-retrival-bot

## Running

```bash
docker-compose up --build
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
- [ ] Serve the search results with FastAPI
- [ ] Make Rasa custom action to fetch results from server
- [ ] Write tests
- [ ] Create idea for what the bot is going to search for
- [ ] Create related Rasa conversations
- [x] Make Rasa out-of-scope case and hook up DialoGPT model
- [x] Make Docker images
- [x] Write frontend with UI
- [ ] Clean input data for DialoGPT better
- [x] Add requirements.txt