# information-retrival-bot

## Running

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
- [ ] Add FastAPI server for translation and serving the search results
- [ ] Make custom action to fetch results from server
- [ ] Write tests
- [ ] Update Rasa conversations
- [ ] Make Rasa out-of-scope case and hook up DialoGPT model
- [ ] Make Docker images
- [x] Write frontend with UI
- [ ] Clean input data for DialoGPT better
- [ ] Transition notebooks code into .py files
- [ ] Add requirements.txt