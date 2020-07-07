# Challenge: Write a Python script that performs all three ETL steps on the Wikipedia and Kaggle data.

# import dependencies 
import pandas as pd
import json
import numpy as np
import re
from sqlalchemy import create_engine
from config import db_password
import time

# Set file path directory
movies_dir = 'C:/Users/User1/Desktop/Movies-ETL'

# Read Kaggle Data and Ratings
kaggle_metadata = pd.read_csv('movies_metadata.csv', low_memory=False)
ratings = pd.read_csv('ratings.csv')

# Open file in the directory
wiki_data = f"/wikipedia.movies.json"

# Create autotomated pipeline for the three datasets
def three_pipeline(wiki_data, kaggle_metadata, ratings):
# Open and load Wikipedia Json file
    with open(f'{movies_dir}(wiki_data)', mode='r') as file:
        wiki_movies_raw = json.load(file)
    
    # Create a list of the movies following the requirements
    wiki_movies = [movie for movie in wiki_movies_raw
               if ('Director' in movie or 'Directed by' in movie)
               and 'imdb_link' in movie
               and 'No. of episodes' not in movie]

# Create a function to clean data
def clean_movie(movie):
    movie_copy = dict(movie) #create a non-destructive copy
    alt_titles = {} # make an empty dict for the alt titles
    
# Loop through a list of alt title keys
    for key in ['Also known as','Arabic','Cantonese','Chinese','French',
                'Hangul','Hebrew','Hepburn','Japanese','Literally',
                'Mandarin','McCune–Reischauer','Original title','Polish',
                'Revised Romanization','Romanized','Russian',
                'Simplified','Traditional','Yiddish']:  
    
# If so- remove key-value pair and add to the alt titles dict  
        if key in movie:
            alt_titles[key] = movie[key]
            movie.pop(key)
            
# After looping through every key- add alt titles dict to movie object            
    if len(alt_titles) > 0:
        movie['alt_titles'] = alt_titles

    # merge column names
    def change_column_name(old_name, new_name):
        if old_name in movie:
            movie[new_name] = movie.pop(old_name)
    change_column_name('Adaptation by', 'Writer(s)')
    change_column_name('Country of origin', 'Country')        
    change_column_name('Directed by', 'Director')
    change_column_name('Distributed by', 'Distributor')
    change_column_name('Edited by', 'Editor(s)')
    change_column_name('Length', 'Running time')
    change_column_name('Original release', 'Release date')
    change_column_name('Music by', 'Composer(s)')
    change_column_name('Produced by', 'Producer(s)')
    change_column_name('Producer', 'Producer(s)')
    change_column_name('Productioncompanies ', 'Production company(s)')
    change_column_name('Productioncompany ', 'Production company(s)')
    change_column_name('Released', 'Release Date')
    change_column_name('Release Date', 'Release date')
    change_column_name('Screen story by', 'Writer(s)')
    change_column_name('Screenplay by', 'Writer(s)')
    change_column_name('Story by', 'Writer(s)')
    change_column_name('Theme music composer', 'Composer(s)')
    change_column_name('Written by', 'Writer(s)')
        
    return movie

    # Create clean movie list and rename it into the existing DataFrame
    clean_movies = [clean_movie(movie) for movie in wiki_movies]
    wiki_movies_df = pd.DataFrame(clean_movies)
    
    # This code is to drop duplicates split in two format at the end counts IMDB regular expression 
    # Used try and except block as example for potential unforeseen errors
try:
    wiki_movies_df['imdb_id'] = wiki_movies_df['imdb_link'].str.extract(r'(tt\d{7})')
    wiki_movies_df.drop_duplicates(subset='imdb_id', inplace=True)
except:
    wiki_movies_df
    
    # Clean code more to get a list of columns with less than 90% null values to trim dataset and onto DataFrame
    wiki_columns_to_keep = [column for column in wiki_movies_df.columns if wiki_movies_df[column].isnull().sum() < len(wiki_movies_df) * 0.9]
    wiki_movies_df = wiki_movies_df[wiki_columns_to_keep]

    # Create variable and Drop NA values from Box Office
    box_office = wiki_movies_df['Box office'].dropna() 

    # Find non-strings
    box_office = box_office.apply(lambda x: ' '.join(x) if type(x) == list else x)

    # Pattern match 1 string for box office ($123.4 million/billion)
    form_one = r"\$\s*\d+.?\d*\s*[mb]ill?ion"

    # Pattern match 2 string for box office ($123,456,789)
    form_two = r"\$\s*\d{1,3}(?:[,\.]\d{3})+(?!\s[mb]illion)"

    # Create regular expression to get all values
    box_office = box_office.str.replace(r'\$.*[-—–](?![a-z])', '$', regex=True)

    # Compare the variables in both forms
    matches_form_one = box_office.str.contains(form_one, flags=re.IGNORECASE)
    matches_form_two = box_office.str.contains(form_two, flags=re.IGNORECASE)

    # Extract and update box office values using function that loops through the different string formats
    def parse_dollars(s):
        # if s is not a string, return NaN
        if type(s) != str:
            return np.nan

        # if input is of the form $###.# million
        if re.match(r'\$\s*\d+\.?\d*\s*milli?on', s, flags=re.IGNORECASE):

            # remove dollar sign and " million"
            s = re.sub('\$|\s|[a-zA-Z]','', s)

            # convert to float and multiply by a million
            value = float(s) * 10**6

            # return value
            return value

        # if input is of the form $###.# billion
        elif re.match(r'\$\s*\d+\.?\d*\s*billi?on', s, flags=re.IGNORECASE):

            # remove dollar sign and " billion"
            s = re.sub('\$|\s|[a-zA-Z]','', s)

            # convert to float and multiply by a billion
            value = float(s) * 10**9

            # return value
            return value

        # if input is of the form $###,###,###
        elif re.match(r'\$\s*\d{1,3}(?:[,\.]\d{3})+(?!\s[mb]illion)', s, flags=re.IGNORECASE):

            # remove dollar sign and commas
            s = re.sub('\$|,','', s)

            # convert to float
            value = float(s)

            # return value
            return value

        # otherwise, return NaN
        else:
            return np.nan


    # Extract values from box office
    wiki_movies_df['box_office'] = box_office.str.extract(f'({form_one}|{form_two})', flags=re.IGNORECASE)[0].apply(parse_dollars)

    # Drop temporary box office column
    wiki_movies_df.drop('Box office', axis=1, inplace=True)

    # PARSE BUDGET: create variable and drop NA values
    budget = wiki_movies_df['Budget'].dropna()
    # Convert list into strings
    budget = budget.map(lambda x: ' '.join(x) if type(x) == list else x)
    # Remove values that are between dollar sign and hypen
    budget = budget.str.replace(r'\$.*[-—–](?![a-z])', '$', regex=True)
    # Compare or parse the budget/box office values
    matches_form_one = budget.str.contains(form_one, flags=re.IGNORECASE)
    matches_form_two = budget.str.contains(form_two, flags=re.IGNORECASE)
    budget = budget.str.replace(r'\[\d+\]\s*', '')

    # PARSE RELEASE DATE:
    # Parse release date with similar pattern
    release_date = wiki_movies_df['Release date'].dropna().apply(lambda x: ' '.join(x) if type(x) == list else x)
    date_form_one = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s[123]\d,\s\d{4}"
    date_form_two = r"\d{4}.[01]\d.[123]\d"
    date_form_three = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}"
    date_form_four = r"\d{4}"
    wiki_movies_df['release_date'] = pd.to_datetime(release_date.str.extract(f'({date_form_one}|{date_form_two}|{date_form_three}|{date_form_four})')[0], infer_datetime_format=True)

    # PARSE RUNNING TIME:
    running_time = wiki_movies_df['Running time'].dropna().apply(lambda x: ' '.join(x) if type(x) == list else x)
    running_time_extract = running_time.str.extract(r'(\d+)\s*ho?u?r?s?\s*(\d*)|(\d+)\s*m')
    running_time_extract = running_time_extract.apply(lambda col: pd.to_numeric(col, errors='coerce')).fillna(0)
    wiki_movies_df['running_time'] = running_time_extract.apply(lambda row: row[0]*60 + row[1] if row[2] == 0 else row[2], axis=1)
    wiki_movies_df.drop('Running time', axis=1, inplace=True)

    # Keep rows where adult column is false, setting data types to kaggle metadata
    kaggle_metadata = kaggle_metadata[kaggle_metadata['adult'] == 'False'].drop('adult',axis='columns')
    kaggle_metadata['video'] = kaggle_metadata['video'] == 'True'
    kaggle_metadata['budget'] = kaggle_metadata['budget'].astype(int)
    kaggle_metadata['id'] = pd.to_numeric(kaggle_metadata['id'], errors='raise')
    kaggle_metadata['popularity'] = pd.to_numeric(kaggle_metadata['popularity'], errors='raise')
    kaggle_metadata['release_date'] = pd.to_datetime(kaggle_metadata['release_date'])

    # Ratings Data
    ratings.info(null_counts=True)
    pd.to_datetime(ratings['timestamp'], unit='s')
    ratings['timestamp'] = pd.to_datetime(ratings['timestamp'], unit='s')

    # Merge together
    movies_df = pd.merge(wiki_movies_df, kaggle_metadata, on='imdb_id', suffixes=['_wiki','_kaggle'])

    # Redundant columns list below and charted
    # Competing data: box office/revenue, title, release date, production company, release date, run time, language
    # Wiki                     Movielens                Resolution
    #--------------------------------------------------------------------------
    #1 title_wiki               title_kaggle            drop Wikipedia titles
    #2 running_time             runtime                 keep kaggle, fill in zeros with Wiki data
    #3 budget_wiki              budget_kaggle           keep kaggle, fill in zeros with Wiki data
    #4 box_office               revenue                 keep kaggle, fill in zeros with Wiki data
    #5 release_date_wiki        release_date_kaggle     drop wikipedia release date
    #6 Language                 original_language       drop Wikipedia languages
    #7 Production company(s)    production_companies    drop Wikipedia prod company

    movies_df.drop(columns=['title_wiki','release_date_wiki','Language','Production company(s)'], inplace=True)

    # Function to fill in data for column pair and drop redundant column
    def fill_missing_kaggle_data(df, kaggle_column, wiki_column):
        df[kaggle_column] = df.apply(
            lambda row: row[wiki_column] if row[kaggle_column] == 0 else row[kaggle_column]
            , axis=1)
        df.drop(columns=wiki_column, inplace=True)

        # Run the functions for column pairs filled in with zeros
    fill_missing_kaggle_data(movies_df, 'runtime', 'running_time')
    fill_missing_kaggle_data(movies_df, 'budget_kaggle', 'budget_wiki')
    fill_missing_kaggle_data(movies_df, 'revenue', 'box_office')

    # Reorder the rows using loc
    movies_df = movies_df.loc[:, ['imdb_id','id','title_kaggle','original_title','tagline','belongs_to_collection','url','imdb_link',
                           'runtime','budget_kaggle','revenue','release_date_kaggle','popularity','vote_average','vote_count',
                           'genres','original_language','overview','spoken_languages','Country',
                           'production_companies','production_countries','Distributor',
                           'Producer(s)','Director','Starring','Cinematography','Editor(s)','Writer(s)','Composer(s)','Based on'
                          ]]

    # Rename the columns
    movies_df.rename({'id':'kaggle_id',
                      'title_kaggle':'title',
                      'url':'wikipedia_url',
                      'budget_kaggle':'budget',
                      'release_date_kaggle':'release_date',
                      'Country':'country',
                      'Distributor':'distributor',
                      'Producer(s)':'producers',
                      'Director':'director',
                      'Starring':'starring',
                      'Cinematography':'cinematography',
                      'Editor(s)':'editors',
                      'Writer(s)':'writers',
                      'Composer(s)':'composers',
                      'Based on':'based_on'
                     }, axis='columns', inplace=True)

    rating_counts = ratings.groupby(['movieId','rating'], as_index=False).count() \
                    .rename({'userId':'count'}, axis=1) \
                    .pivot(index='movieId',columns='rating', values='count')
    rating_counts.columns = ['rating_' + str(col) for col in rating_counts.columns]

    # Join DataFrames using a left merge
    movies_with_ratings_df = pd.merge(movies_df, rating_counts, left_on='kaggle_id', right_index=True, how='left')
    movies_with_ratings_df[rating_counts.columns] = movies_with_ratings_df[rating_counts.columns].fillna(0)

    # Load Data
    db_string = f"postgres://postgres:{db_password}@127.0.0.1:5432/movie_data"
    engine = create_engine(db_string)
    movies_df.to_sql(name='movies', con=engine, if_exists="replace")

rows_imported = 0
# get the start_time from time.time()
start_time = time.time()
for data in pd.read_csv(f'{movies_dir}/ratings.csv', chunksize=1000000):
    print(f'importing rows {rows_imported} to {rows_imported + len(data)}...', end='')
    data.to_sql(name='ratings', con=engine, if_exists='append')
    rows_imported += len(data)

    # add elapsed time to final print out
    print(f'Done. {time.time() - start_time} total seconds elapsed')