# Overview
The current project setup requires a locally running Ollama model. Which the Streamlit Python app queries and utilizes via its Streamlit GUI

# Running Locally
## 1- Ollama needs to be running locally
Make sure Ollama is running locally- ensure local desktop version isn't currently running either
```
ollama serve
```
Protip because Windows sucks...
Start Ollama from a separaate terminal window from where the Streamlit app will run

Make sure the model you want is pulled, e.g.
```
ollama pull llama3
```

## 2- Activate your Conda env, or if terminal is launched from Anaconda Navigator this can be skipped of course
Recreate the Conda Env- this easily handles all dependencies required for the project. No more pain with Pip!
```
conda env create -f environment.yml
```
This is how we will run the streamlit app
```
conda activate ai_financial
```

Run the Streamlit Python UI app, from the Python Anaconda Env (since it is a Python app)
```
streamlit run main_streamlit.py
```

Open the local URL (usually http://localhost:8501), but it usually opens automatically in browser

