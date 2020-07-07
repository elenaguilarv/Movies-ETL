# Movies-ETL
Module: Peform an ETL on three datasets (two csv and one json file) to create an SQL database of movies. The datasets include Wikipedia profiles, Kaggle and ratings. 

## Challenge
Instructions: Write a Python script that performs all three ETL steps on the Wikipedia and Kaggle data. Utilize the code already created but leave out any code that performs exploratory data analysis. Add code to handle potentially unforeseen errors due to changes in the underlying data.

### Goals
- Create an automated ETL pipeline
- Extract data from multiple sources
- Transform the data using pandas and regular expressions
- Load new data in PostgreSQL

## Assumptions
- Create a list of movies by filtering with the following requirements: IMDB link and Director. A code statement to exclude shows (using "no. of episodes") is also included. 

- The data is cleaned by comparing the formatting of the columns and values between the different datasets. Regular expressions, functions and else-if statements are used to create new categories (alternate titles), column names, and to make the data uniform overall (parse dollars for box office values, parse budget values, release dates, running time, etc.)

- try-except block example is used for imdb_id string format assuming there could be another format to this column value that might have been missed in the large dataset. These blocks can be used throughout the code to avoid potential errors that can arise from for loops running and finding outliers in the data as it runs.

- Wikipedia data is dropped significantly when analyzing the competing data columns (box office, title, release date, production company, run time, language) and Kaggle data is used because it is more readable and descriptive.

- Though the data is cleaned extensively, there are still null values and redundant information in the data compiled. This could play a role in how the data is read and extracted by those who use it.
