# [-- Imports --]
import numpy as np
import pandas as pd
import json
import requests
import time
from datetime import date, datetime, timezone, timedelta
import datetime
import random

# regression tools
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
from scipy import stats

# data scraping tools
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# texting tools
from twilio.rest import Client

# backtesting tools
from itertools import combinations, permutations

# twitter tools
import tweepy

# [-- Data Loading --]
# Inital Data
home_dataframe = pd.read_csv('data/past_home_stats.csv', decimal='.', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0)
away_dataframe = pd.read_csv('data/past_away_stats.csv', decimal='.', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0)

# Manipulated Data
home_manipulated_GF = home_dataframe.copy()
away_manipulated_GF = away_dataframe.copy()
home_manipulated_GA = home_dataframe.copy()
away_manipulated_GA = away_dataframe.copy()

# Current Data
curr_data_home_GF = []
curr_data_home_GA = []
curr_data_away_GF = []
curr_data_away_GA = []

# Final Data
finalDataframe = []

# Backtest Data
backtest_dataframe = pd.read_csv('data/hockey_games.csv', usecols = ['Date', 'Away', 'AwayG', 'Home', 'HomeG'], header = 0)
# backtest_extended_dataframe = pd.read_csv('data/game.csv', usecols = ["date_time_GMT", "away_team_id", "home_team_id", "away_goals", "home_goals", "outcome"], header = 0)
backtest_2021_dataframe = pd.read_csv('data/games2021.csv', usecols = ['Date', 'Visitor' ,'ScoreA','Home','ScoreH','Status'], header = 0)
backtest_2021_2022_dataframe = pd.read_csv('data/games20212022.csv', usecols = ['Date','Start Time (ET)','Visitor','ScoreA','Home','ScoreH','Status'], header = 0)
backtest_odds_2021 = pd.read_csv('data/odds.csv', usecols = ['VH','Team','Final','Open','PuckLine','PuckLineA','OpenOU','OpenOUA','CloseOU','CloseOUA'],  header = 0)
model_data = pd.read_csv('data/modelInputData.csv', usecols = ['Edge','Min Odds Away','Min Odds Home','Max Odds Away','Max Odds Home','Profit','Percentage'], header = 0)

# [-- Inputs --]
gamesPlayed = [3, 10, 23, 30, 40] # how many games played the data should be
# these two should be the same size ^v
weights = [4, 2, 6, 10, 8] # weights for the weighted average

initialMoney = 1000

corrDropValue = 25
regDropValue = 11
cutOffValue = 0.01
correlationCutOff = -0.9 # cut off point for correlation step (anything above/below)

fromSeason = 20222023
thruSeason = 20222023
today = str(date.today())
tomorrow = str(date.today() + timedelta(days=1))
timeToday = today[0:10]
timeTomorrow = tomorrow[0:10]

teamsInNHL = 32

coefficients = [] # coefficients determined in regression step

columns_to_remove_gf = [] # columns that will have to be removed from current data (goals for)
columns_to_remove_ga = [] # columns that will have to be removed from current data (goals against)

client = Client('AC93c09034a467b38c7a2618dd45ecdedb', '4342cd893e4de5be826a3cb5d0387345') # client for texting

api_key = '74a13ca8f52c11c2476a5cc7db5d34d0' # api key for sports betting odds

twitter_auth_keys = {
    'twitter_api_key' : '1aEl9cX94wzMS4Gj3FfuSpDRP',
    'twitter_api_secret' : 'Lrt1LpAEnm3YP4D0UmNKqXGHbOuZKbfchKCUrOWYZK9EIvQQ1u',
    'twitter_access_token' : '1517249140580700161-Nzc22k7cBuSAAFANrhJQMIkyRyGvQV',
    'twitter_access_secret' : 'RV28dFke8XAsheW8xXPyxplRB7IGLz6Adr8GGnZgRmKAo',
    'twitter_bearer_token' : 'AAAAAAAAAAAAAAAAAAAAAEICbwEAAAAAfm%2BDFKXxnABybKD4ibQUfeL0Wg0%3D4p2ljSOtysvLi0J37T9haSK7x6kn3gQZM5ncMuc9g1DsCOBSB1'
}

twitter_auth = tweepy.OAuthHandler(twitter_auth_keys['twitter_api_key'], twitter_auth_keys['twitter_api_secret'])
twitter_auth.set_access_token(twitter_auth_keys['twitter_access_token'], twitter_auth_keys['twitter_access_secret'])

twitter_api = tweepy.API(twitter_auth)
# twitter_api.verify_credentials()

try:
    twitter_api.verify_credentials()
    print("Twitter Authentication OK")
except:
    print("Error during twitter authentication")

odds_response = requests.get(f'https://api.the-odds-api.com/v3/odds/?sport=icehockey_nhl&region=us&mkt=h2h&dateFormat=iso&apiKey={api_key}')
odds_response_scores = requests.get(f'https://api.the-odds-api.com/v4/sports/icehockey_nhl/scores/?apiKey={api_key}&dateFormat=iso')

odds_json = json.loads(odds_response.text) # odds for upcoming games
odds_json_scores = json.loads(odds_response_scores.text) # odds for ongoing scores

simple_json = [] # odds to be cleaned up

textMessage = "" # text to send daily (contains info for todays games)
picks = []

p = True # Whether or not code should be printing status updates.

greetings = ["Good morning, ", "Lines are out 🔻", "Lines are ready 🔻", "Who's ready❗", "Today's games, ", "Let's get after it, "]
score_greetings = ["Update on scores: ", "🕗Latest scores: ", "Currently in the NHL, "]
hashtags = ["#SportsBetting", "#FreePicks", "#FreeBets", "#SportsBettingPicks", "#GamblingTwitter", "#Gambling", "#BettingTwitter", "#FreePlays", "#BettingLocks", "#PicksAllDay", "#SportsBets"]

# website scraping set ups
opts = Options()
opts.add_argument("--headless")
# opts.add_argument("--disable-extensions")
# opts.add_argument("--disable-popup-blocking")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option('useAutomationExtension', False)

cols_to_remove = [ # unnecessary columns for past data evaluation 
    'Team',
    'GP',
    'TOI/GP',
    'W',
    'L',
    'OTL',
    'ROW',
    'Points',
    'Point %',
]

nhl_abbreviations = {
    'ANA' : 'Anaheim Ducks',
    'ARI' : 'Arizona Coyotes',
    'BOS' : 'Boston Bruins',
    'BUF' : 'Buffalo Sabres',
    'CAR' : 'Carolina Hurricanes',
    'CBJ' : 'Columbus Blue Jackets',
    'CGY' : 'Calgary Flames',
    'CHI' : 'Chicago Black Hawks',
    'COL' : 'Colorado Avalanche',
    'DAL' : 'Dallas Stars',
    'DET' : 'Detroit Red Wings',
    'EDM' : 'Edmonton Oilers',
    'FLA' : 'Florida Panthers',
    'LAK' : 'Los Angeles Kings',
    'MIN' : 'Minnesota Wild',
    'MTL' : 'Montreal Canadiens',
    'NJD' : 'Nashville Predators',
    'NYI' : 'New York Islanders',
    'NYR' : 'New York Rangers',
    'OTT' : 'Ottawa Senators',
    'PHI' : 'Philadelphia Flyers',
    'PIT' : 'Pittsburgh Penguins',
    'SEA' : 'Seattle Kraken',
    'SEN' : 'Ottawa Senators',
    'SJS' : 'San Jose Sharks',
    'STL' : 'St. Louis Blues'
}

nhl_twitter_hashtags = {
    'Anaheim Ducks': '#LetsGoDucks',
    'Arizona Coyotes': '#Yotes',
    'Boston Bruins': '#NHLBruins',
    'Buffalo Sabres': '#Sabres',
    'Calgary Flames': '#CofRed',
    'Carolina Hurricanes': '#Redvolution',
    'Chicago Blackhawks': '#Blackhawks',
    'Colorado Avalanche': '#GoAvsGo',
    'Columbus Blue Jackets': '#CBJ',
    'Dallas Stars': '#GoStars',
    'Detroit Red Wings': '#LGRW',
    'Edmonton Oilers': '#LetsGoOilers',
    'Florida Panthers': '#FlaPanthers',
    'Los Angeles Kings': '#GoKingsGo',
    'Minnesota Wild': '#mnwild',
    'Montreal Canadiens': '#GoHabsGo',
    'Nashville Predators': '#Preds',
    'New Jersey Devils': '#NJDevils',
    'New York Islanders': '#Isles',
    'New York Rangers': '#NYR',
    'Ottawa Senators': '#Sens',
    'Philadelphia Flyers': '#LetsGoFlyers',
    'Pittsburgh Penguins': '#LetsGoPens',
    'San Jose Sharks': '#SJSharks',
    'Seattle Kraken': '#SeaKraken',
    'St Louis Blues': '#AllTogetherNowSTL',
    'Tampa Bay Lightning': '#GoBolts',
    'Toronto Maple Leafs': '#TMLtalk',
    'Vancouver Canucks': '#Canucks',
    'Vegas Golden Knights': '#VegasGoesGold',
    'Washington Capitals': '#ALLCAPS',
    'Winnipeg Jets': '#GoJetsGo'
}

# removing unnecessary columns from past data
for col in cols_to_remove:
    home_manipulated_GF.drop(columns = col, inplace = True)
    away_manipulated_GF.drop(columns = col, inplace = True)
    home_manipulated_GA.drop(columns = col, inplace = True)
    away_manipulated_GA.drop(columns = col, inplace = True)

# reset for backtesting
def resetBackTesting():
    print("reseting dataframes for backtesting...")
    global home_dataframe, away_dataframe, home_manipulated_GF, away_manipulated_GF, home_manipulated_GA, away_manipulated_GA, curr_data_home_GF, curr_data_home_GA, curr_data_away_GF, curr_data_away_GA, finalDataframe
    global corrDropValue, regDropValue, cutOffValue, correlationCutOff
    resetBuild()
    # Inital Data
    home_dataframe = pd.read_csv('data/past_home_stats.csv', decimal='.', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0)
    away_dataframe = pd.read_csv('data/past_away_stats.csv', decimal='.', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0)

    # Manipulated Data
    home_manipulated_GF = home_dataframe.copy()
    away_manipulated_GF = away_dataframe.copy()
    home_manipulated_GA = home_dataframe.copy()
    away_manipulated_GA = away_dataframe.copy()

    # Current Data
    curr_data_home_GF = []
    curr_data_home_GA = []
    curr_data_away_GF = []
    curr_data_away_GA = []

    # Final Data
    finalDataframe = []
    
    corrDropValue = 25
    regDropValue = 11
    cutOffValue = 0.01
    
    # removing unnecessary columns from past data
    for col in cols_to_remove:
        home_manipulated_GF.drop(columns = col, inplace = True)
        away_manipulated_GF.drop(columns = col, inplace = True)
        home_manipulated_GA.drop(columns = col, inplace = True)
        away_manipulated_GA.drop(columns = col, inplace = True)


# [-- Current Data Step --]
def currData(fromSeason, thruSeason, today):
    global curr_data_home_GF, curr_data_home_GA, curr_data_away_GF, curr_data_away_GA
    if (p): print("Downloading current data...")
    curr_data_home = []
    curr_data_away = []
    counter = 1
    
    for gps in gamesPlayed:
        # urls to access current data
        urlAway = f"https://www.naturalstattrick.com/teamtable.php?fromseason={fromSeason}&thruseason={thruSeason}&stype=2&sit=5v5&score=all&rate=y&team=all&loc=A&gpf=c&gp={gps}&fd=&td={today}"
        urlHome = f"https://www.naturalstattrick.com/teamtable.php?fromseason={fromSeason}&thruseason={thruSeason}&stype=2&sit=5v5&score=all&rate=y&team=all&loc=H&gpf=c&gp={gps}&fd=&td={today}"

        # setting up the driver to access chrome
        # driver = webdriver.Chrome(ChromeDriverManager().install(), options = opts) # downloads and sets newest chromedriver
        # params = {'behavior': 'allow', 'downloadPath': r'currentData'}
        # driver.execute_cdp_cmd('Page.setDownloadBehavior', params)
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options = opts) # downloads and sets newest chromedriver
        params = {'behavior': 'allow', 'downloadPath': r'currentData'}
        driver.execute_cdp_cmd('Page.setDownloadBehavior', params) # download behaviour set to this directory

        driver.get(urlAway) # driver launches
        
        filterButton = driver.find_element(By.ID, 'colfilterlb')
        filterButton.click()
        buttons = driver.find_elements(By.CSS_SELECTOR, '[class*="\\\\buttonspan"]')

        buttons[7].click()
        buttons[8].click()
        buttons[10].click()
        buttons[12].click()
        buttons[13].click()
        buttons[14].click()
        buttons[15].click()
        buttons[16].click()
        buttons[17].click()

        saveButton = driver.find_elements(By.TAG_NAME, "input")[29] # save button
        saveButton.click()
        time.sleep(3)
        
        curr_data_away.append(pd.read_csv('currentData/games.csv', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0))
        # if (gps == 3):
        #     curr_data_away.append(pd.read_csv('currentData/Team Season Totals - Natural Stat Trick.csv', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0))
        # elif (gps == 5):
        #     curr_data_away.append(pd.read_csv('currentData/Team Season Totals - Natural Stat Trick.csv', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0))
        # elif (gps == 10):
        #     curr_data_away.append(pd.read_csv('currentData/Team Season Totals - Natural Stat Trick.csv', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0))
        # elif (gps == 15):
        #     curr_data_away.append(pd.read_csv('currentData/Team Season Totals - Natural Stat Trick.csv', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0))
        
        if (p): print("(" + str(counter) +  ")" + "done away: " + str(gps) + " games played.") # i.e. (1) done away: 10 games played
        
        driver.close()
        driver.quit()
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options = opts) # downloads and sets newest chromedriver
        params = {'behavior': 'allow', 'downloadPath': r'data'}
        driver.execute_cdp_cmd('Page.setDownloadBehavior', params) # download behaviour set to this directory
        
        driver.get(urlHome)
        
        filterButton = driver.find_element(By.ID, 'colfilterlb')
        filterButton.click()
        buttons = driver.find_elements(By.CSS_SELECTOR, '[class*="\\\\buttonspan"]')

        buttons[7].click()
        buttons[8].click()
        buttons[10].click()
        buttons[12].click()
        buttons[13].click()
        buttons[14].click()
        buttons[15].click()
        buttons[16].click()
        buttons[17].click()

        saveButton = driver.find_elements(By.TAG_NAME, "input")[29] # save button
        saveButton.click()
        time.sleep(3)
        
        curr_data_home.append(pd.read_csv('currentData/games.csv', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0))
        # if (gps == 3):
            
        # elif (gps == 5):
        #     curr_data_home.append(pd.read_csv('currentData/Team Season Totals - Natural Stat Trick.csv', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0))
        # elif (gps == 10):
        #     curr_data_home.append(pd.read_csv('currentData/Team Season Totals - Natural Stat Trick.csv', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0))
        # elif (gps == 15):
        #     curr_data_home.append(pd.read_csv('currentData/Team Season Totals - Natural Stat Trick.csv', usecols = ["Team","GP","TOI/GP","W","L","OTL","ROW","Points","Point %","CF/60","CA/60","CF%","FF/60","FA/60","FF%","SF/60","SA/60","SF%","GF/60","GA/60","GF%","xGF/60","xGA/60","xGF%","SCF/60","SCA/60","SCF%","SCSF/60","SCSA/60","SCSF%","SCGF/60","SCGA/60","SCGF%","SCSH%","SCSV%","HDCF/60","HDCA/60","HDCF%","HDSF/60","HDSA/60","HDSF%","HDGF/60","HDGA/60","HDGF%","HDSH%","HDSV%","MDCF/60","MDCA/60","MDCF%","MDSF/60","MDSA/60","MDSF%","MDGF/60","MDGA/60","MDGF%","MDSH%","MDSV%","LDCF/60","LDCA/60","LDCF%","LDSF/60","LDSA/60","LDSF%","LDGF/60","LDGA/60","LDGF%","LDSH%","LDSV%","SH%","SV%","PDO"], header = 0))
        if (p): print("(" + str(counter) +  ")" + "done home: " + str(gps) + " games played.") # i.e. (2) done home: 10 games played
        counter = counter + 1
        
        driver.close()
        driver.quit()
    
    if (p): print("Uploading current data")
    
    for i in range(0, len(gamesPlayed)):
        curr_data_home_GF.append(curr_data_home[i].copy())
        curr_data_home_GA.append(curr_data_home[i].copy())
        curr_data_away_GF.append(curr_data_away[i].copy())
        curr_data_away_GA.append(curr_data_away[i].copy())
        
    if (p): print("Current data download + upload complete.")
    
    
# cleans up json odds (removes games not on today or if no games ends program)
def cleanOddsJson(bool):
    global simple_json, odds_json
    games_to_remove = []
    
    if (len(odds_json['data']) > 0): # if there are games today
        i = 0
        for game in odds_json['data']: # removes games not on today
            commenceTime = game['commence_time']
            commenceDate = commenceTime.split('T')[0]
            commenceHour = commenceTime.split('T')[1]
            teams = game['teams']
            if (timeToday != commenceDate):
                # check if game is on tomorrow
                if (timeTomorrow != commenceDate):
                    if (p): print(f"Removing game {teams}, game is on the {commenceDate}.")
                    games_to_remove.append(game)
                
    for game in games_to_remove:
        odds_json['data'].remove(game)
              
    if (len(odds_json['data']) == 0):
        textMessage = 'No NHL games today...'
        file = open('/Users/silasnevstad/Desktop/Everything/Programming/Python/BettingModels/Message.txt', 'a')
        file.truncate(0)
        file.write(textMessage)
        file.close()
        print('Code completed (no games).')
        if (bool): exit()
        
    for game in odds_json['data']:
        awayID = 1
        homeID = 0
        teams = game['teams']
        home_team = game['home_team']
        if (len(teams) == 1):
            if (home_team == teams[0]):
                continue
        while (home_team != teams[homeID]):
            awayID = 0
            homeID = 1
        teams.remove(home_team)
        away_team = teams[0]
        if (home_team == 'Montréal Canadiens'):
            home_team = "Montreal Canadiens"
        if (away_team == 'Montréal Canadiens'):
            away_team = "Montreal Canadiens"
        
        siteIdx = 0
        away_odds = game['sites'][siteIdx]['odds']['h2h'][awayID]
        home_odds = game['sites'][siteIdx]['odds']['h2h'][homeID]
        # if away or home odds are 1.0, then use a different site
        while (away_odds == 1.0 or home_odds == 1.0):
            siteIdx += 1
            if (siteIdx == len(game['sites'])):
                break
            away_odds = game['sites'][siteIdx]['odds']['h2h'][awayID]
            home_odds = game['sites'][siteIdx]['odds']['h2h'][homeID]

        if (away_odds == 1.0 or home_odds == 1.0):
            continue
        g = [away_team, home_team, away_odds, home_odds, commenceDate, commenceHour]
        simple_json.append(g)
    
    

# [-- Correlation Step --]
# gets redundant pairs from a dataframe
def get_redundant_pairs(df):
    pairs_to_drop = set()
    cols = df.columns
    for i in range(0, df.shape[1]):
        for j in range(0, i+1):
            pairs_to_drop.add((cols[i], cols[j]))
    return pairs_to_drop

# returns the highest correlation in a data set, given variable to avoid
def highestCorrelation(df, avoid):
    df.drop(columns = avoid, inplace = True)
    corr = df.corr().unstack()
    labels_to_drop = get_redundant_pairs(df)
    corr = corr.drop(labels=labels_to_drop).sort_values(ascending=True)
    return corr[0]

# returns ranked given dataframe by a given value (highest first)
def rankByValue(df, value):
    return df.sort_values(by=[value], ascending=False)

# returns dataframe with new column (percentage * profit)
def multProfitPercentage(df):
    expectedProfits = df.Percentage * df.Profit
    df['Expected Profit'] = expectedProfits
    return df
    
# returns top ten correlations given a value
def rankByCorrelation(df, value):
    corr = df.corr().unstack()
    labels_to_drop = get_redundant_pairs(df)
    corr = corr.drop(labels=labels_to_drop).sort_values(ascending=True)
    return corr
    
# Goals For
def correlationStepGF(df): # determines what data points correlate and then removes them
    global home_manipulated_GF, away_manipulated_GF
    
    for col in df.index: # loops through dataframe
        try:
            col = df.columns[col] # sets col to be the column of dataframe
        except:
            continue
        if (col != 'GF/60'): # GF/60 is what we are looking for (so avoid)
            for column in df.index: # loops through dataframe (so we can compare)
                try:
                    column = df.columns[column]
                except:
                    continue
                if (column != 'GF/60'):
                    if (col != column):
                        # if (p): print(col, column)
                        correlation = df[col].corr(df[column]) # gets correlation between two columns
                        if (correlation > abs(correlationCutOff) or correlation < correlationCutOff):
                            if (p): print("Removing: " + column + " (Correlation: " + str(round(correlation, 4)) + ")")
                            df.drop(columns = column, inplace = True) # drop correlated column
                            columns_to_remove_gf.append(column) # add removed column so we can keep track
                            break
                        
# Goals Against
def correlationStepGA(df): # determines what data points correlate and then removes them
    global home_manipulated_GA, away_manipulated_GA
    
    for col in df.index: # loops through the data frame
        try:
            col = df.columns[col] # sets col to be the column of dataframe
        except:
            continue
        if (col != 'GA/60'): # GA/60 is what we are looking for (so avoid)
            for column in df.index: # loops through dataframe (so we can compare)
                try:
                    column = df.columns[column]
                except:
                    continue
                if (column != 'GA/60'):
                    if (col != column):
                        correlation = df[col].corr(df[column]) # gets correlation between two columns
                        if (correlation > abs(correlationCutOff) or correlation < correlationCutOff):
                            if (p):print("Removing: " + column + " (Correlation: " + str(round(correlation, 4)) + ")")
                            df.drop(columns = column, inplace = True) # drop correlated column
                            columns_to_remove_ga.append(column) # add removed column so we can keep track
                            break
                    
# lowers the correlation cut off by given x amount    
def lowerCutOffBy(x):
    global correlationCutOff
    correlationCutOff = round(correlationCutOff + x, 4)
    

# [-- Regression Step --]
# Goals For
def regressionStepGF(df): # checks the regression of remaining data points and removes highest p-value step by step
    global home_manipulated_GF, away_manipulated_GF, coefficients
    length = len(df.index)
    y = df.loc[:length-1, 'GF/60']
    columns = []
    for col in df:
        if (col != 'GF/60'):
            columns.append(col)
        
    X = pd.DataFrame(np.c_[df[columns[0]], df[columns[1]], df[columns[2]],
                           df[columns[3]], df[columns[4]], df[columns[5]],
                           df[columns[6]], df[columns[7]], df[columns[8]],
                           df[columns[9]]])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.1, random_state=9)
    
    lin_reg_mod = LinearRegression()
    lin_reg_mod.fit(X_train, y_train)
    pred = lin_reg_mod.predict(X_test)
    
    params = np.append(lin_reg_mod.intercept_, lin_reg_mod.coef_)
    newX = np.append(np.ones((len(X_train),1)), X_train, axis=1)
    MSE = (sum((y_test-pred)**2))/(len(newX)-len(newX[0]))
    var_b = MSE*(np.linalg.inv(np.dot(newX.T,newX)).diagonal())
    sd_b = np.sqrt(var_b)
    ts_b = params/ sd_b
    p_values =[2*(1-stats.t.cdf(np.abs(i),(len(newX)-len(newX[0])))) for i in ts_b]
    real_values = p_values[1:]
    
    maximum = max(real_values)
    
    for i, j in enumerate(p_values):
        if j == maximum:
            index = i

    df.drop(columns[index], axis = 1, inplace = True)
    columns_to_remove_gf.append(columns[index])
    
    coefficients = np.copy(params)
    
    if (p): print("Removing: " + columns[index] + " (P-Value: " + str(round(maximum, 4)) + ")")

# Goals Against
def regressionStepGA(df): # checks the regression of remaining data points and removes highest p-value step by step
    global home_manipulated_GA, away_manipulated_GA, coefficients
    length = len(df.index)
    y = df.loc[:length-1, 'GA/60']
    columns = []
    for col in df:
        if (col != 'GA/60'):
            columns.append(col)
        
    X = pd.DataFrame(np.c_[df[columns[0]], df[columns[1]], df[columns[2]],
                           df[columns[3]], df[columns[4]], df[columns[5]],
                           df[columns[6]], df[columns[7]], df[columns[8]],
                           df[columns[9]]])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.1, random_state=9)
    
    lin_reg_mod = LinearRegression()
    lin_reg_mod.fit(X_train, y_train)
    pred = lin_reg_mod.predict(X_test)
    
    X2 = sm.add_constant(X_test)
    est = sm.OLS(y_test, X2)
    
    params = np.append(lin_reg_mod.intercept_, lin_reg_mod.coef_)
    newX = np.append(np.ones((len(X_train),1)), X_train, axis=1)
    MSE = (sum((y_test-pred)**2))/(len(newX)-len(newX[0]))
    var_b = MSE*(np.linalg.inv(np.dot(newX.T,newX)).diagonal())
    sd_b = np.sqrt(var_b)
    ts_b = params/ sd_b
    p_values =[2*(1-stats.t.cdf(np.abs(i),(len(newX)-len(newX[0])))) for i in ts_b]
    real_values = p_values[1:]
    
    maximum = max(real_values)
    
    for i, j in enumerate(p_values):
        if j == maximum:
            index = i
            
    df.drop(columns[index], axis = 1, inplace = True)
    columns_to_remove_ga.append(columns[index])
    
    coefficients = np.copy(params)
    
    if (p): print("Removing: " + columns[index] + " (P-Value: " + str(maximum) + ")")

def removeUnwatedColumns(): # adds columns to be removed to list
    global columns_to_remove_gf, columns_to_remove_ga
    colNames = ['GP', 'W', 'L', 'TOI/GP', 'OTL', 'ROW', 'Points', 'Point %']
    for name in colNames:
        columns_to_remove_gf.append(name);
        columns_to_remove_ga.append(name);
    
def addUnwatedColumns():  # removes columns to be removed from list
    global columns_to_remove_gf, columns_to_remove_ga
    colNames = ['GP', 'W', 'L', 'TOI/GP', 'OTL', 'ROW', 'Points', 'Point %']
    for name in colNames:
        columns_to_remove_gf.remove(name);
        columns_to_remove_ga.remove(name);

# [-- Prediction Step --]
# Goals For
def predictionGF(df): # using current data and coefficients predicts goals for
    global curr_data_home_GF, curr_data_away_GF
    removeUnwatedColumns()
    
    for column in columns_to_remove_gf:
        df.drop(columns = column, inplace = True)
        
    setterArray = []
    
    for i in range(0, teamsInNHL):
        setterArray.append("")
        
    df["Predicted GF"] = setterArray
    coeff = coefficients.tolist()
    df.set_index('Team', inplace = True, drop = True)
    actualGF = df['GF/60']
    df.drop(columns = 'GF/60', axis = 1, inplace = True)
    
    for j in df.itertuples():
        predicted_gf = round(coeff[0] + (coeff[1] * j[1]) + (coeff[2] * j[2]) + (coeff[3] * j[3]) + (coeff[4] * j[4]) + (coeff[5] * j[5]) + (coeff[6] * j[6]) + (coeff[7] * j[7]) + (coeff[8] * j[8]) + (coeff[9] * j[9]) + (coeff[10] * j[10]), 2)
        df.loc[j.Index, 'Predicted GF'] = predicted_gf
    
    df["Actual GF"] = actualGF
    addUnwatedColumns()

# Goals Against
def predictionGA(df): # using current data and coefficients predicts goals against
    global curr_data_home_GA, curr_data_away_GA
    removeUnwatedColumns()
    
    for column in columns_to_remove_ga:
        df.drop(columns = column, inplace = True)
        
    setterArray = []
    
    for i in range(0, teamsInNHL):
        setterArray.append("")
        
    df["Predicted GA"] = setterArray
    coeff = coefficients.tolist()
    df.set_index('Team', inplace = True, drop = True)
    actualGA = df['GA/60']
    df.drop(columns = 'GA/60', axis = 1, inplace = True)
    
    for j in df.itertuples():
        predicted_ga = round(coeff[0] + (coeff[1] * j[1]) + (coeff[2] * j[2]) + (coeff[3] * j[3]) + (coeff[4] * j[4]) + (coeff[5] * j[5]) + (coeff[6] * j[6]) + (coeff[7] * j[7]) + (coeff[8] * j[8]) + (coeff[9] * j[9]) + (coeff[10] * j[10]), 2)
        df.loc[j.Index, 'Predicted GA'] = predicted_ga
    
    df["Actual GA"] = actualGA
    addUnwatedColumns()

# resets values
def resetBuild():
    global coefficients, columns_to_remove_gf, columns_to_remove_ga, correlationCutOff
    coefficients = []
    columns_to_remove_gf = []
    columns_to_remove_ga = []
    correlationCutOff = -0.9
    
# [-- Set Up --]
# building the data to be used when predicting
def buildData():
    global home_manipulated_GF, home_manipulated_GA, away_manipulated_GF, away_manipulated_GA
    global curr_data_home_GF, curr_data_home_GA, curr_data_away_GF, curr_data_away_GA
    global columns_to_remove_gf, columns_to_remove_ga, coefficients
    
    # [ Goals For ]
    # Home
    if (p): print("Correlating home data...")
    while (len(home_manipulated_GF.columns) > corrDropValue):
        correlationStepGF(home_manipulated_GF)
        lowerCutOffBy(cutOffValue)
        
    if (p): print("Regressing home data...")
    while (len(home_manipulated_GF.columns) > regDropValue):
        regressionStepGF(home_manipulated_GF)
    
    for i in range(0, len(gamesPlayed)):
        predictionGF(curr_data_home_GF[i])
    
    resetBuild()
    
    # Away
    if (p): print("Correlating away data...")
    while (len(away_manipulated_GF.columns) > corrDropValue):
        correlationStepGF(away_manipulated_GF)
        lowerCutOffBy(cutOffValue)
        
    if (p): print("Regressing away data...")
    while (len(away_manipulated_GF.columns) > regDropValue):
        regressionStepGF(away_manipulated_GF)
        
    for i in range(0, len(gamesPlayed)):
        predictionGF(curr_data_away_GF[i])
        
    resetBuild()
    
    # [ Goals Against ]
    # Home
    if (p): print("Correlating home data...")
    while (len(home_manipulated_GA.columns) > corrDropValue):
        correlationStepGA(home_manipulated_GA)
        lowerCutOffBy(cutOffValue)
        
    if (p): print("Regressing home data...")
    while (len(home_manipulated_GA.columns) > regDropValue):
        regressionStepGA(home_manipulated_GA)
        
    for i in range(0, len(gamesPlayed)):
        predictionGA(curr_data_home_GA[i])
        
    resetBuild()
    
    # Away
    if (p): print("Correlating away data...")
    while (len(away_manipulated_GA.columns) > corrDropValue):
        correlationStepGA(away_manipulated_GA)
        lowerCutOffBy(cutOffValue)
        
    if (p): print("Regressing away data...")
    while (len(away_manipulated_GA.columns) > regDropValue):
        regressionStepGA(away_manipulated_GA)
        
    for i in range(0, len(gamesPlayed)):
        predictionGA(curr_data_away_GA[i])
        
    resetBuild()

# builds final data frame with current data and processed data
def buildFinalData(dfGF, dfGA):
    final_dataframe = pd.DataFrame(index = dfGF.index)
    
    xGFHome = dfGF['Predicted GF']
    xGAHome = dfGA['Predicted GA']
    xGFAway = dfGF['Predicted GF']
    xGAAway = dfGA['Predicted GA']
    
    final_dataframe['xGF Home'] = xGFHome
    final_dataframe['xGA Home'] = xGAHome
    final_dataframe['xGF Away'] = xGFAway
    final_dataframe['xGA Away'] = xGAAway
    
    final_dataframe = final_dataframe.append(pd.Series(
        [ 
            (final_dataframe['xGF Home'].sum()/31), 
            (final_dataframe['xGA Home'].sum()/31), 
            (final_dataframe['xGF Away'].sum()/31), 
            (final_dataframe['xGA Away'].sum()/31)
        ],
        index = final_dataframe.columns,
        name = 'Averages'), ignore_index=False)
    
    home_att_strength = []
    home_def_strength = []
    away_att_strength = []
    away_def_strength = []
    
    for row in final_dataframe.index:
        if (row != 'Averages'): 
            row = final_dataframe.loc[row]
            average = final_dataframe.loc['Averages']
            home_att_strength.append(row['xGF Home']/average['xGF Home'])
            home_def_strength.append(row['xGA Home']/average['xGA Home'])
            away_att_strength.append(row['xGF Away']/average['xGF Away'])
            away_def_strength.append(row['xGA Away']/average['xGA Away'])
        else:
            home_att_strength.append(np.NaN)
            home_def_strength.append(np.NaN)
            away_att_strength.append(np.NaN)
            away_def_strength.append(np.NaN)

    final_dataframe['Att Strength Home'] = home_att_strength
    final_dataframe['Def Strength Home'] = home_def_strength

    final_dataframe['Att Strength Away'] = away_att_strength
    final_dataframe['Def Strength Away'] = away_def_strength

    final_dataframe = final_dataframe.append(pd.Series(
        [
            'N/A',
            'N/A',
            'N/A',
            'N/A',
            (final_dataframe['Att Strength Home'].sum()/31), 
            (final_dataframe['Def Strength Home'].sum()/31), 
            (final_dataframe['Att Strength Away'].sum()/31), 
            (final_dataframe['Def Strength Away'].sum()/31)
        ],
        index = final_dataframe.columns,
        name = 'Average Strengths'), ignore_index=False)

    return(final_dataframe)

# [-- Results Step --]
# convert odds from decimal to american
def decToAmer(odds):
    if (odds == 2):
        american = 100
    if (odds > 2):
        american = int((odds - 1) * 100)
    elif (odds < 2):
        american = int(-100 / (odds - 1))
    
    return american

# from american odds to probability percentage
def amerToProb(odds):
    if  (odds > 0):
        prob = (100 / (odds + 100))
    elif (odds < 0):
        prob = ((-1 *  odds) / ((-1 * odds) + 100))
        
    return prob

# from probabilty to american odds
def probToAmer(prob):
    if (prob == .5):
        odds = 100
    elif (prob > .5):
        odds = ((prob*100) / (1 - prob)) * -1
    elif (prob < .5):
        odds = (100 / prob) -100
        
    return odds

# calculate an edge over a percentage
def calcEdge(myProb, prob):
    edge = 0
    
    if (myProb != prob):
        edge = round((myProb * 100) - (prob * 100), 2)
    
    if (edge < 0):
        edge = 0
        
    return edge

# calculate money won from american odds
def calcPayout(bet, odds):
    payout = bet
    
    if (odds < 0):
        payout = bet / (-1 * odds / 100)
    elif (odds > 0):
        payout = bet * odds / 100
    
    return payout

# calculate losses from american odds
def calcLosses(bet, odds):
    if (odds > 0):
        losses = bet
    elif (odds < 0):
        losses = ((-1 * odds) / 100) * bet
    
    return losses

# calculate an edge over american odds
def calcEdgeAmerican(myAmerican, american):
    myProb = amerToProb(myAmerican)
    prob = amerToProb(american)
        
    edge = calcEdge(myProb, prob)
        
    return edge

# removes juice from odds (book odds are weighted against bettors)
def removeJuice(awayAmericanOdds, homeAmericanOdds):
    # print("removing juice from odds...")
    # convert to probabilities (from american odds)
    awayProb = amerToProb(awayAmericanOdds)
    homeProb = amerToProb(homeAmericanOdds)
        
    # remove the juice (away IP  = away IP / (awap IP + home IP))
    awayProb = awayProb / (awayProb + homeProb)
    homeProb = homeProb / (homeProb + awayProb)
    
    # convert back to american odds (from prob.)
    awayOdds = int(probToAmer(awayProb))
    homeOdds = int(probToAmer(homeProb))
        
    return [awayOdds, homeOdds]

# converts utc to local timezone
def utc_to_local(utc_dt):
    datetime_obj = datetime.datetime.strptime(utc_dt, '%H:%M:%S%z')
    datetime_obj = datetime_obj + datetime.timedelta(hours=1)
    return datetime_obj.replace(tzinfo=timezone.utc).astimezone(tz=None)

# calculates the length of strings
def calcStringLength(x, y):
    if (not isinstance(x, str)):
        x = str(x)
    if (not isinstance(y, str)):
        y = str(y)
    return len(x) + len(y)
    
# using the expected gf & ga we determine expected results between two teams
def predictingResults(awayTeam, homeTeam, finalDf):
    global my_away_odds, my_home_odds
    
    # set att and def strengths
    awayTeam_att_strength = finalDf.loc[awayTeam, 'Att Strength Away']
    awayTeam_def_strength = finalDf.loc[awayTeam, 'Def Strength Away']
    homeTeam_att_strength = finalDf.loc[homeTeam, 'Att Strength Away']
    homeTeam_def_strength = finalDf.loc[homeTeam, 'Def Strength Away']
    
    # set averages
    away_GF_average = finalDf.loc['Averages', 'xGF Away']
    home_GF_average = finalDf.loc['Averages', 'xGF Home']
    
    # expected goals = (team attack * opponent defense) * average gf
    # this is done for home and away
    expected_goals_away = round((awayTeam_att_strength * homeTeam_def_strength) * away_GF_average, 2)
    expected_goals_home = round((homeTeam_att_strength * awayTeam_def_strength) * home_GF_average, 2)
    
    # win probabilty = (E[GF Away] / (E[GF Away] + E[GF Home])) * 100
    # win probabilty = (E[GF Away] / E[Total Goals]) * 100
    away_win_prob = round((expected_goals_away / (expected_goals_away+expected_goals_home)), 2)
    home_win_prob = round((expected_goals_home / (expected_goals_away+expected_goals_home)), 2)
    
    # converting the odds to decimal
    # decimal odds = (1 / win prob) * 100
    away_odds_decimal = (1 / away_win_prob)
    home_odds_decimal = (1 / home_win_prob)
    
    # converting to american odds
    away_odds_american = decToAmer(away_odds_decimal)
    home_odds_american = decToAmer(home_odds_decimal)
        
    # creating my odds (decimal)
    my_away_odds = round(away_odds_decimal, 2)
    my_home_odds = round(home_odds_decimal, 2)
    
    # a list of the data to return (expected goals, win prob, decimal odds)
    scores = [expected_goals_away, expected_goals_home, away_win_prob, home_win_prob, away_odds_decimal, home_odds_decimal]
    return scores
    

# tests a game using all dataframes (games played changes)
def testGame(awayTeam, homeTeam):
    result = [0, 0, 0, 0, 0, 0] # just so we can return results later
    results = []
    
    
    for i in range(0, len(gamesPlayed)): # loops thru all dataframes (diff. games played) and predicts results
        results.append(predictingResults(awayTeam, homeTeam, finalDataframe[i]))
    
    # expected goals
    awayEGF = []
    for i in range(0, len(gamesPlayed)):
        awayEGF.append(results[i][0])
    homeEGF = []
    for i in range(0, len(gamesPlayed)):
        homeEGF.append(results[i][1])
    result[0] = round(np.average(awayEGF, weights = weights), 2)
    result[1] = round(np.average(homeEGF, weights = weights), 2)
    
    # win probability
    awayWinProb = []
    for i in range(0, len(gamesPlayed)):
        awayWinProb.append(results[i][2])
    homeWinProb = []
    for i in range(0, len(gamesPlayed)):
        homeWinProb.append(results[i][3])
    result[2] = round(np.average(awayWinProb, weights = weights), 2)
    result[3] = round(np.average(homeWinProb, weights = weights), 2)
    
    # Odds
    awayOdds = []
    for i in range(0, len(gamesPlayed)):
        awayOdds.append(results[i][4])
    homeOdds = []
    for i in range(0, len(gamesPlayed)):
        homeOdds.append(results[i][5])
    result[4] = round(np.average(awayOdds, weights = weights), 3)
    result[5] = round(np.average(homeOdds, weights = weights), 3)
    
    return result

# [-- Backtesting Step --]
# backtesting through old games
def backTesting(df):
    correct = 0 # total correct 
    totalsCorrect = 0 # total correct totals (over vs under)
    wrong = 0 # total wrong
    total = 0 # total games tested
    
    for row in df.index: # loop  through games in backtest data
        correctPrediction = False
        date = df.loc[row, 'Date']
        if (p): print('backtesting game ' + str(date))
        homeWin = False
        predicted_home_win = False
        awayTeam = df.loc[row, "Visitor"]
        homeTeam = df.loc[row, "Home"]
        scoreA = df.loc[row, "ScoreA"]
        scoreH = df.loc[row, "ScoreH"]
        scoreT = float(scoreA) + float(scoreH)
            
        predicted_scores = testGame(awayTeam, homeTeam) # my models prediction
        totals = float(predicted_scores[0]) + float(predicted_scores[1]) # total expected goals
        
        if (int(scoreH) > int(scoreA)):
            homeWin = True
        elif (int(scoreA) > int(scoreH)):
            homeWin = False
        
        if (predicted_scores[3] > 50):
            predicted_home_win = True
            
        # Tallying
        if (homeWin == predicted_home_win): 
            correct += 1
            correctPrediction = True
        else:
            wrong += 1
        
        if (scoreT > 5.5):
            if (totals > 5.5):
                totalsCorrect += 1
        if (scoreT < 5.5):
            if (totals < 5.5):
                totalsCorrect += 1
                
        total += 1
        
        if (p):
            print(f'Prediction was {correctPrediction}')
            print(f'{awayTeam}: {scoreA} v.s. {homeTeam}: {scoreH}')
            print(f'My Prediction: {predicted_scores[0]} v.s. {predicted_scores[1]}')
            print("Correct: " + str(correct))
            print("Wrong: " + str(wrong))
            print("Total: " + str(total))
            print("Totals: " + str(totalsCorrect))
            print('\n\n')
        
        percentage = round(correct / total, 4)
        if (p): print(str(percentage) + '%')
        
def advancedBackTesting(df):
    global gamesPlayed, weights
    counter = 0
    counter2 = 0
    
    maxPercentage = 0
    listOfPossibleGamesPlayed = [3, 5, 10, 13, 17, 20, 23, 27, 30, 40]
    cComb = combinations(listOfPossibleGamesPlayed, 5)
        
    bestWeights = [0, 0, 0, 0, 0]
    bestGamesPlayed = [0, 0, 0, 0, 0]
    
    # while maxPercentage < 0.6: 
    for i in cComb:
        if (counter2 > 1): # code so that it skips every two (checks two, then skips two)
            counter2 += 1
            if (counter2 > 3):
                counter2 = 0
            continue
        pComb = permutations([10, 8, 6, 4, 2], 5)
        for j in pComb:
            correct = 0 # total correct 
            totalsCorrect = 0 # total correct totals (over vs under)
            wrong = 0 # total wrong
            total = 0 # total games tested
            percentage = 0 # percentage of games predicted correctly
            
            for row in df.index: # loop  through games in backtest data
                correctPrediction = False
                date = df.loc[row, 'Date']
                if (p): print('backtesting game ' + str(date))
                homeWin = False
                predicted_home_win = False
                awayTeam = df.loc[row, "Visitor"]
                homeTeam = df.loc[row, "Home"]
                scoreA = df.loc[row, "ScoreA"]
                scoreH = df.loc[row, "ScoreH"]
                scoreT = float(scoreA) + float(scoreH)
                    
                predicted_scores = testGame(awayTeam, homeTeam) # my models prediction
                totals = float(predicted_scores[0]) + float(predicted_scores[1]) # total expected goals
                
                if (int(scoreH) > int(scoreA)):
                    homeWin = True
                elif (int(scoreA) > int(scoreH)):
                    homeWin = False
                
                if (predicted_scores[3] > 50):
                    predicted_home_win = True
                    
                # Tallying
                if (homeWin == predicted_home_win): 
                    correct += 1
                    correctPrediction = True
                else:
                    wrong += 1
                
                if (scoreT > 5.5):
                    if (totals > 5.5):
                        totalsCorrect += 1
                if (scoreT < 5.5):
                    if (totals < 5.5):
                        totalsCorrect += 1
                        
                total += 1
                
                percentage = round(correct / total, 4)
                if (percentage > maxPercentage):
                    maxPercentage = percentage
                    bestWeights = j
                    bestGamesPlayed = i
                
                print(f'Prediction was {correctPrediction}')
                print(f'{awayTeam}: {scoreA} v.s. {homeTeam}: {scoreH}')
                print(f'My Prediction: {predicted_scores[0]} v.s. {predicted_scores[1]}')
                print("Correct: " + str(correct))
                print("Wrong: " + str(wrong))
                print("Total: " + str(total))
                print("Totals: " + str(totalsCorrect))
                print(str(percentage) + '%')
                print('\n')
            
            counter += 1
            weights = j # weights for the weighted average
            print(counter)
            print(f'Mas Percentage: {maxPercentage} using {bestWeights} weights (and {bestGamesPlayed} games played).')
        
        counter2 += 1
        gamesPlayed = i # how many games played the data should be
        print(counter)
        print(f'Mas Percentage: {maxPercentage} using {bestGamesPlayed} games played (and {bestWeights} weights).')
        
        resetBackTesting()
        currData(fromSeason, thruSeason, today) #  get current data
        buildData() # analysis of data (setting up data)
        for i in range(0, len(gamesPlayed)): # build current analysis (setting up current data)
            finalDataframe.append(buildFinalData(curr_data_away_GF[i], curr_data_away_GA[i]))
            
    print(f'Best percentage: {maxPercentage}')
    print(f'Games played used: {bestGamesPlayed}')
    print(f'Weights used: {bestWeights}')
    
def backTestWithOdds(df, lengthToSkip, awayEdgeCap, homeEdgeCap, minOddsA, minOddsH, maxOddsA, maxOddsH):
    if (p): print(f"backtesting with odds... {initialMoney}$")
    global backtest_odds_2021
    money = initialMoney # inital bank
    total = 0 # total games tested
    betsWon = 0
    betsLost = 0
    totalBets = 0
    
    wait = 1500
    
    
    teamOne = ""
    oddsOne = 0
    scoreOne = 0
    teamVH = ""
    onlyOneTeam = True
    
    for row in df.index[lengthToSkip:]: # loop  through games in backtest data
        if (onlyOneTeam):
            teamOne = df.loc[row, "Team"]
            oddsOne = df.loc[row, "Open"]
            scoreOne = df.loc[row, "Final"]
            teamVH = df.loc[row, "VH"]
        
        if (onlyOneTeam):
            onlyOneTeam = not onlyOneTeam
            continue
        
        correctPrediction = False
        homeWin = False
        predicted_home_win = False
        
        if (teamVH == "V"):
            awayTeam = teamOne
            homeTeam = df.loc[row, "Team"]
            scoreA = scoreOne
            scoreH = df.loc[row, "Final"]
            oddsA = oddsOne
            oddsH = df.loc[row, "Open"]
        elif (teamVH == "H"):
            awayTeam = df.loc[row, "Team"]
            homeTeam = teamOne
            scoreA = df.loc[row, "Final"]
            scoreH = scoreOne
            oddsA = df.loc[row, "Open"]
            oddsH = oddsOne
            
        
        predicted_scores = testGame(awayTeam, homeTeam) # my models prediction
        dejuiced_odds = removeJuice(oddsA, oddsH)
        
        my_away_odds = decToAmer(predicted_scores[4])
        my_home_odds = decToAmer(predicted_scores[5])
        
        awayEdge = calcEdgeAmerican(my_away_odds, oddsA) # dejuiced_odds[0]
        homeEdge = calcEdgeAmerican(my_home_odds, oddsH) # dejuiced_odds[1]
        
        if (scoreA > scoreH): # away win
            homeWin = False
        elif (scoreA < scoreH): # home win 
            homeWin = True
        elif (scoreA == scoreH): # tie
            draw = True
            
        predicted_home_win = False
        if (predicted_scores[3] > 50):
            predicted_home_win = True
        
        bet = 20
        # calculates bet to add
        if (awayEdge > homeEdge): # predicts away win
            if (awayEdge > awayEdgeCap and oddsA > minOddsA and oddsA < maxOddsA):
                if (not homeWin): # was correct
                    correctPrediction = True
                    betsWon += 1
                    totalBets += 1
                    money += calcPayout(bet, oddsA) # adds bet to current bank
                    if (p): print("current bet: " + str(calcPayout(bet, oddsA)) + ", book away odds: " + str(oddsA) + ", my away odds: " + str(my_away_odds) + ", home book odds: " + str(oddsH) + ", my home odds: " + str(my_home_odds))
                elif (homeWin): # was wrong
                    correctPrediction = False
                    betsLost += 1
                    totalBets += 1
                    money -= calcLosses(bet, oddsA) # adds bet to current bank
                    if (p): print("current bet: " + str(calcLosses(bet, oddsA)) + ", book away odds: " + str(oddsA) + ", my away odds: " + str(my_away_odds) + ", home book odds: " + str(oddsH) + ", my home odds: " + str(my_home_odds))
            else:
                if (p): print("no bet made")
        elif (homeEdge > awayEdge): # predicts home win
            if (homeEdge > homeEdgeCap and oddsH > minOddsH and oddsH < maxOddsH):
                if (homeWin): # was correct
                    correctPrediction = True
                    betsWon += 1
                    totalBets += 1
                    money += calcPayout(bet, oddsH) # adds bet to current bank
                    if (p): print("current bet: " + str(calcPayout(bet, oddsH)) + ", book away odds: " + str(oddsA) + ", my away odds: " + str(my_away_odds) + ", home book odds: " + str(oddsH) + ", my home odds: " + str(my_home_odds))
                elif (not homeWin): #  was wrong
                    correctPrediction = False
                    betsLost += 1
                    totalBets += 1
                    money -= calcLosses(bet, oddsH) # adds bet to current bank
                    if (p): print("current bet: " + str(calcLosses(bet, oddsH)) + ", book away odds: " + str(oddsA) + ", my away odds: " + str(my_away_odds) + ", home book odds: " + str(oddsH) + ", my home odds: " + str(my_home_odds))
            else:
                if (p): print("no bet made")
                
        total += 1
        money = round(money, 1)
        totalProfit = money - initialMoney
        
        if (p):
            print(f'Prediction was {correctPrediction}')
            print(f'{awayTeam}: {scoreA} v.s. {homeTeam}: {scoreH}')
            print(f'My Prediction: {predicted_scores[0]} v.s. {predicted_scores[1]}')
            print(f"Total: {total}")
            print(f"Bank: {money}$")
            print(f"Total profit: {totalProfit}$")
            print(f"Bets Won: {betsWon}, Bets Lost: {betsLost}, Total Bets: {totalBets}")
            print('\n\n')
            
        onlyOneTeam = not onlyOneTeam
        
    totalCorrectBets = 0
    try:
        totalCorrectBets = round(betsWon / (betsWon + betsLost), 2)
        print(f"Betting Percentage: {totalCorrectBets}")
    except ZeroDivisionError:
        print("0 bets made")
        
    return [totalProfit, totalCorrectBets]


def backTestBackTest(df):
    global p
    column_names = ["Edge", "Min Odds Away", "Min Odds Home", "Max Odds Away", "Max Odds Home", "Profit"]
    saveDataframe = pd.DataFrame(columns = column_names)
    p = False
    lengthToSkip = 1000
    edgeCaps = [4, 5]
    minOdds = [-1000, -600, -500, -400, -300, -200, -150, -125, 0]
    maxOdds = [1000, 600, 500, 400, 300, 200, 150, 125, 0]
    
    maxProfit = -1000
    maxBettingPercentage = 0
    counter = 0
    
    for edge in edgeCaps:
        for minA in minOdds:
            for minH in minOdds:
                for maxA in maxOdds:
                    for maxH in maxOdds:
                        # print(counter)
                        # counter += 1
                        currProfit = backTestWithOdds(df, lengthToSkip, edge, edge, minA, minH, maxA, maxH)[0]
                        currBettingPercentage = backTestWithOdds(df, lengthToSkip, edge, edge, minA, minH, maxA, maxH)[1]
                        
                        df2 = {'Edge': edge, 'Min Odds Away': minA, 'Min Odds Home': minH, 'Max Odds Away': maxA, 'Max Odds Home': maxH, 'Profit': currProfit, 'Pecentage': currBettingPercentage}
                        saveDataframe = saveDataframe.append(df2, ignore_index = True)
                        print(saveDataframe)
                        
                        # if (currProfit > maxProfit):
                        #     maxProfit = currProfit
                        #     bestEdge = edge
                        #     bestMinA = minA
                        #     bestMinH = minH
                        #     bestMaxA = maxA
                        #     bestMaxH = maxH
                        #     print(f"{maxProfit}$ best profit so far, using {lengthToSkip}, {edge}, {edge}, {minA}, {minH}, {maxA}, {maxH}")
                        
                        if (currBettingPercentage > maxBettingPercentage):
                            maxBettingPercentage = currBettingPercentage
                            bestEdge = edge
                            bestMinA = minA
                            bestMinH = minH
                            bestMaxA = maxA
                            bestMaxH = maxH
                            print(f"{maxBettingPercentage}% best betting percentage so far, using {lengthToSkip}, {edge}, {edge}, {minA}, {minH}, {maxA}, {maxH}")
                            
    # print(f"{maxProfit}$ best profit so far, using {lengthToSkip}, {bestEdge}, {bestEdge}, {bestMinA}, {bestMinH}, {bestMaxA}, {bestMaxH}")
    print(f"{maxBettingPercentage}% best betting percentage so far, using {lengthToSkip}, {bestEdge}, {bestEdge}, {bestMinA}, {bestMinH}, {bestMaxA}, {bestMaxH}")
    saveDataframe.to_csv('modelInputData.csv')
                    

# [-- Automation Step --]
def autoPredict():
    global textMessag, picks
    
    gameN = 1
    
    print(simple_json)
        
    for game in range(0, len(simple_json)):
        away_team = simple_json[game][0]
        home_team = simple_json[game][1]
        
        away_odds_decimal = simple_json[game][2]
        home_odds_decimal = simple_json[game][3]
        
        date = simple_json[game][4]
        
        result = testGame(away_team, home_team)
        
        # converting to american odds
        away_odds_american = decToAmer(away_odds_decimal)
        home_odds_american = decToAmer(home_odds_decimal)
        
        dejuiced_odds = removeJuice(away_odds_american, home_odds_american)
        
        # american
        my_away_odds = decToAmer(result[4])
        my_home_odds = decToAmer(result[5])
            
        total = result[0] + result[1]
        
        edgeAway = calcEdge(amerToProb(my_away_odds), amerToProb(away_odds_american))
        edgeHome = calcEdge(amerToProb(my_home_odds), amerToProb(home_odds_american))
        
        edge = max(edgeAway, edgeHome)
        if (edge < 5):
            continue
        # if (edge == edgeAway):
        #     if (away_odds_american < 0 or away_odds_american > 150):
        #         continue
        # elif (edge == edgeHome):
        #     if (home_odds_american < -125 or home_odds_american > 0):
        #         continue
            
        if (p):
            print('\n')
            print(f'{date}---------------------------------------------')
            print(f'Game {gameN}: {away_team} v.s. {home_team}')
            print(f'My Odds: {my_away_odds} | {my_home_odds}')
            print(f'Book Odds: {away_odds_american} | {home_odds_american}')
            print(f'{edgeAway} ' + str(round(result[2] * 100, 2)) + "% | " + str(round(result[3] * 100, 2)) + f'% {edgeHome}')
            print(f'{result[0]} | {result[1]} | = {total}')
            print('\n')
            
        commenceTime = simple_json[game][5]
        localTime = str(utc_to_local(commenceTime))[11:16]
        if (localTime[0] == '0'): localTime = localTime[1:]
        percentA = round(result[2] * 100, 2)
        percentH = round(result[3] * 100, 2)
        # space = ""
        # for i in range(0, calcStringLength(away_team, away_odds_american) - 1):
        #     space += "  "
        
        textMessage = f'\n🏒Pick {gameN}: {away_team} ({away_odds_american}) vs {home_team} ({home_odds_american})'
        textMessage += f'\n({edgeAway}%) {percentA}% | {percentH}% ({edgeHome}%)\n'
        textMessage += nhl_twitter_hashtags[away_team] + " " + nhl_twitter_hashtags[home_team] + "\n"
        
        picks.append(textMessage)
        
        gameN = gameN + 1
        
    print(picks)

# returns todays schedule (TIME: AWAYTEAM AWAYODDS vs HOMEODDS HOMETEAM)
def todaysGames():
    global textMessage
    textMessage = random.choice(greetings) + "\n"
    
    gameNumber = 1
    print(simple_json)
    for game in range(0, len(simple_json)):
        away_team = simple_json[game][0]
        home_team = simple_json[game][1]
        
        away_odds_decimal = simple_json[game][2]
        home_odds_decimal = simple_json[game][3]
        
        away_odds_american = decToAmer(away_odds_decimal)
        home_odds_american = decToAmer(home_odds_decimal)
        
        commenceTime = simple_json[game][5]
        localTime = str(utc_to_local(commenceTime))[11:16]
        if (localTime[0] == '0'): localTime = localTime[1:]
        textMessage += f"\n🏒{localTime}: {away_team} {away_odds_american} v.s. {home_odds_american} {home_team}\n"
        
        gameNumber += 1

# returns the current scores  
def scores():
    global textMessage
    textMessage = random.choice(score_greetings) + "\n"
    
    for game in odds_json_scores:
        awayTeam = game['away_team']
        homeTeam = game['home_team']
        
        try:
            if (game['scores'][0]['name'] == awayTeam):
                awayScore = game['scores'][0]['score']
                homeScore = game['scores'][1]['score']
            else:
                awayScore = game['scores'][1]['score']
                homeScore = game['scores'][0]['score']
        except:
            continue
        
        try:
            textMessage += f"{nhl_twitter_hashtags[awayTeam]} [{awayScore} - {homeScore}] {nhl_twitter_hashtags[homeTeam]}\n\n"
        except:
            return
        
# automatically tweets out current scores
def tweetScores():
    scores()
    twitter_api.update_status(textMessage)
    print(textMessage)
    print("Tweeted scores.")
    
# automatically tweet out todays schedule
def tweetSchedule():
    todaysGames()
    twitter_api.update_status(textMessage)
    print(textMessage)
    print("Tweeted schedule.")
    
# automatically tweet out todays picks
def tweetPicks():
    for pick in picks:
        tags = random.sample(hashtags, 3)
        tag = ""
        for i in tags:
            tag += i + " "
        twitter_api.update_status(pick + "\n" + tag)
        time.sleep(10)
        print(pick)
    print("Tweeted picks.")

# stores todays data into a text file      
def message():
    if (p): print("Saving: " + textMessage + "...")
    file = open('/Users/silasnevstad/Desktop/Everything/Programming/Python/BettingModels/Message.txt', 'a')
    file.truncate(0)
    file.write(textMessage)
    file.close()
    
def tweet():
    twitter_api.update_status(textMessage)

cleanOddsJson(True) # clean up the json file (upcoming games downloaded from online) (boolean decides whether or not to exit() if there are no games today)
currData(fromSeason, thruSeason, today) #  get current data
buildData() # analysis of data (setting up data)

for i in range(0, len(gamesPlayed)): # build current analysis (setting up current data)
    finalDataframe.append(buildFinalData(curr_data_away_GF[i], curr_data_away_GA[i]))

autoPredict()
# message()
# tweetScores()
# tweetSchedule()
# tweetPicks()

# print(testGame("Tampa Bay Lightning", "Colorado Avalanche"))

# scores()
# todaysGames()
# print(picks)

# print(rankByValue(multProfitPercentage(model_data), 'Profit'))
# print(rankByCorrectation(multProfitPercentage(model_data), 'Expected Profit'))

# inputDataframe = pd.read_csv('backtestingBacktest.csv')

# backTest1 = backTestWithOdds(backtest_odds_2021, 2000, 5, 5, -1000, -1000, 150, 150)
# print(backTest1)

# backTestBackTest(backtest_odds_2021)
# print(backTestWithOdds(backtest_odds_2021, 1000, 5, 5, 0, -300, 150, 0))

# backTesting(backtest_2021_2022_dataframe)

# advancedBackTesting(backtest_2021_2022_dataframe)

print("Code completed.")