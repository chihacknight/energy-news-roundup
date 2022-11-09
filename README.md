# Energy News Roundup Scraping

Chi Hack Night scraping project for energy news information
We scraped daily email digests from energynews.us ranging back all the way to 2013

## Setup
First install the base package requirements 
```pip install -r requirements.txt```

Then download the required natural language toolkit data 
```python3 nltk-setup.py```

Finally, download the required core english web for `spacy`
```python3 -m spacy download en```

## Running the script
To run the script run the following in the project directory:
`
python3 scrape.py
`
## Output
The library of digests will be converted into a [csv file](digestItems.csv)

## Topic Modeling
We also ran all the blurbs through a topic modeling program.
This helps determine how much certain words are used with each other.
Check it out in the [jupyter notebook](topic_modeling.ipynb)