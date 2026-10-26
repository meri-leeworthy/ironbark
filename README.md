# Ironbark Technical Task

Finds the closest road for a given light

## Running the code

I used [uv](https://docs.astral.sh/uv/) for package/project management, so:

```sh
git clone https://github.com/meri-leeworthy/ironbark.git
cd ironbark
uv run main.py
```

Otherwise:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Key assumptions

The code is written to be have ok performance assuming a higher volume of data with the samples given as representative of that data:
- Coordinates are expected to be around Melbourne region for purposes of projecting to metric CRS
- I assume for simplicity there are no zero-length line segments
- Lights are always Point and roads are always LineString

## AI use

I use agents in my regular workflow, but was concerned that this would make it hard to evaluate my work for such a small task, so I decided to work primarily by hand with some chatbot assistance. I consulted Claude for some questions about geopandas and other libraries, to work through some syntax bugs, and to get feedback in a final code review. My hand-written notes working through the problem are at `notes.md`.
