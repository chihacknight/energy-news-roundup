# Energy News Roundup Scraping

Chi Hack Night scraping project for energy news information

## Setup
First install the base package requirements 
```pip install -r requirements.txt```

Then download the required natural language toolkit data 
```python3 nltk-setup.py```

Finally, download the required core english web for `spacy`
```python3 -m spacy download en```

## Running the script
To run the script run the following in the project directory:
```bash
python3 scrape.py
```
## Output
The library of digests will be converted into a [csv file](digestItems.csv)