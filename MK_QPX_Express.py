import matplotlib
import seaborn as sns
import datetime
import requests
import json
import datetime
import pandas as pd
import numpy as np
import os

#hi
__all__ = ['create_json_request', 'getjson_flight_prices', 'get_average_flight_price', 'parsejson_flight_prices', 'merge_queries_into_summary', 'NUMBER_API_KEYS']
__author__ = 'malikk'
API_KEYS = ['AIzaSyBPAhGun08oPp79XxnqfYkukaShqFL0iMs', 'AIzaSyBBZgOxX2NzQFE7ua_I9_Cym5i6N0NYf20', 'AIzaSyBtGnEG3rrv8wy-h4OOZMs0Az51xURTBuA', 'AIzaSyDeEZw0BkvoFgM11CVceitinBm_--Bo2g0', 'AIzaSyAZ4VudGpgcO6KWWANbNJe4yo8jU19jCo8', 'AIzaSyAIJ9xgn47tWcEg9vqq647ukTc_7b85_SM', 'AIzaSyBDyku0b3ZGeIZF4mDl1hu81WqXyVsXLa8', 'AIzaSyBZRdB2j8PvWbMTCrJPrZplNBh1NAwImbc', 'AIzaSyDbZ7eA5oErLVG9ZtkcA928kFuyVNIY-8s']
NUMBER_API_KEYS = len(API_KEYS)
def create_json_request(origin, destination, date, roundtrip=False, returndate=None, solutions=50):
    """
    Returns a json request for the API based on the inputs provided.
        Args:
            origin[str]: Example: SFO or JFK
            destination[str]: see origin
            date[datetime.datetime]: flight date
            roundtrip[boolean]: round trip flight or not
            returndate[datetime.datetime]: return date for round trip flight
            solutions[int]: number of solutions to fetch from API
    """
    if roundtrip:
        data = {
          "request": {
            "passengers": {
              "kind": "qpxexpress#passengerCounts",
              "adultCount": 1,
              "childCount": 0,
              "infantInLapCount": 0,
              "infantInSeatCount": 0,
              "seniorCount": 0
            },
            "slice": [
              {
                "kind": "qpxexpress#sliceInput",
                "origin": origin,
                "destination": destination,
                "date": date.strftime("%Y-%m-%d"),
                "maxStops": 0,
                "preferredCabin": "Coach",
                "permittedDepartureTime": {
                  "kind": "qpxexpress#timeOfDayRange",
                  "earliestTime": "05:00",
                  "latestTime": "12:00"
                }
              },
              {
                "kind": "qpxexpress#sliceInput",
                "origin": destination,
                "destination": origin,
                "date": returndate.strftime("%Y-%m-%d"),
                "maxStops": 0,
                "preferredCabin": "Coach",
                "permittedDepartureTime": {
                  "kind": "qpxexpress#timeOfDayRange",
                  "earliestTime": "05:00",
                  "latestTime": "12:00"
                }
              }
            ],
            "solutions": solutions,
            "saleCountry": "US"
          }
        }
    else:
        data = {
          "request": {
            "passengers": {
              "kind": "qpxexpress#passengerCounts",
              "adultCount": 1,
              "childCount": 0,
              "infantInLapCount": 0,
              "infantInSeatCount": 0,
              "seniorCount": 0
            },
            "slice": [
              {
                "kind": "qpxexpress#sliceInput",
                "origin": origin,
                "destination": destination,
                "date": date.strftime("%Y-%m-%d"),
                "maxStops": 0,
                "preferredCabin": "Coach",
                "permittedDepartureTime": {
                  "kind": "qpxexpress#timeOfDayRange",
                  "earliestTime": "05:00",
                  "latestTime": "12:00"
                }
              }
            ],
            "solutions": solutions,
            "saleCountry": "US"
          }
        }
    return data




def get_average_flight_price(df, precision=2, ignore_duplicate_flightno=True):
    '''
    Returns the average price by using the passed DataFrame.
    Equation = total prices / length of dataframe index
        Args:
            df(pandas.DataFrame) = the DataFrame
            precision(optional[int]) : how many decimals to display (default=2)
    '''
    if type(df) is not pd.DataFrame:
         raise TypeError('df must be a DataFrame. Passed type: ' + type(df))
    precisionstr = '{0:.' + str(precision) + 'f}'
    total = 0.0
    processed_flightno = {}
    # wow... you really like to dig deep into people's code huh. That makes two of us.
    for idx, row in df.iterrows():
        if not processed_flightno.get(row['FlightNumber'], False) or ignore_duplicate_flightno:
            processed_flightno[row['FlightNumber']] = True
            total += float(row['Price'])
    return float(precisionstr.format(float(total)/float(len(df.index))))


def merge_queries_into_summary(dataframes):
    '''
    Returns a summary dataframe with one row per origin/destination combo
    Each row contains traveldate, querydate, avg price, origin, destination
        Args:
            dataframes(list) = list of dataframes.
    '''
    if type(dataframes) is not list:
        raise TypeError('dataframes must be a list of DataFrames. Passed type: ' + type(dataframes))
    result = None
    for df in dataframes:
        avg_price = get_average_flight_price(df)
        onerow = df.head(1)
        onerow['Price'] = avg_price
        if result is None:
            result = onerow
        else:
            result = result.append(onerow, ignore_index=True)
    result.pop('Airline')
    return result


def getjson_flight_prices(request, apikey=1):
    '''
    Returns a Pandas DataFrame with the flight prices for given info.
    Source of flight price info = Google QPX Express API (ITA Software)
      Args:
        origin (str): The flight origin.
        destination (str): The flight destination.
        flightdate (datetime.datetime) : Date of flight departure. Datetime.datetime object.
        solutions(optional[int]) : How many ticket prices to fetch when calculating average ticket price. Default is 50.
        apikey(optional[int]): Which api key to use (1, 2, or 3)
    '''
    
    #Throw a TypeError if a datetime object is not passed.
    if apikey < 1 or apikey > 9:
        raise ValueError('apikey must be 1-9. Passed: {}'.format(str(apikey)))

    #Making Google give us their data >:D (forcibly, not by choice of course)
   #TODO -- make a stanford gmail just for querying the API. replace this
    url = "https://www.googleapis.com/qpxExpress/v1/trips/search?key={}".format(API_KEYS[apikey-1])
    response = requests.post(url, data=json.dumps(request), headers={'Content-Type' : 'application/json'})
    data = response.json()
    return data

def parsejson_flight_prices(jsonfile, origin, destination, flightdate, returndate=None, querydate=datetime.datetime.now()):
    data = jsonfile
    
    #Parse the JSON file. 
    trips = data['trips']
    trip_data = trips['data']

    carriers={}
    airports={}
    flight_options=[]

    for carrier in trip_data['carrier']:
        carriers[(carrier['code'])] = carrier['name']

    for airport in trip_data['airport']:
        airports[airport['code']] = airport['name']

    for option in trips['tripOption']:
        flight_options.append({'FlightNumber' : option['slice'][0]['segment'][0]['flight']['number'],
                               'Price' : option['saleTotal'], 
                               'Airline' : carriers[option['pricing'][0]['fare'][0]['carrier']]})

    querydate = querydate.strftime('%m/%d/%Y')
    
    for option in flight_options:
        option['Price'] = option['Price'].replace('USD', '') #Cleaning price string so we can cast it to a float later.
        option['FlightDate'] = flightdate.strftime('%m/%d/%Y') if type(flightdate) is datetime.datetime else flightdate
        option['Destination'] = destination
        option['Origin'] = origin
        option['QueryDate'] = querydate
        if returndate:
            option['ReturnDate'] = returndate.strftime('%m/%d/%Y') if type(returndate) is datetime.datetime else returndate

    #Helper function to sort flight options by price.
    def sortoptions(dict):
        return float(dict['Price'])

    #Remove duplicate data --> sort by price.
    flight_options = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in flight_options)]
    flight_options = sorted(flight_options, key=sortoptions)

    
    #The below code puts all query results into a dataFrame.
    df = pd.DataFrame(flight_options[0], index=np.arange(1))
    for i in range(1, len(flight_options)):
        df = df.append(flight_options[i], ignore_index=True)
    if returndate: 
        return df[['Price', 'Origin', 'Destination', 'QueryDate', 'FlightDate', 'ReturnDate', 'Airline', 'FlightNumber']]
    else:
         return df[['Price', 'Origin', 'Destination', 'QueryDate', 'FlightDate', 'Airline', 'FlightNumber']]

def get_percentage_savings_df(df, ticket_price_baseline=21):
    """
    Returns a pandas.DataFrame with days in advance as a column and percentage saved on ticket price as another.
        Args:
            df(pandas.DataFrame): input data
            ticket_price_baseline(int): how many days in advance to use as baseline for savings
    """
    d2 = df.copy(deep=True)
    averages = d2.groupby('days').mean()
    price_baseline = averages.ix[ticket_price_baseline]
    func = lambda new_cost : (1-(new_cost / price_baseline))*100
    averages = averages.apply(func=func, axis=1)
    cleanfloats = lambda number : float('{:.2f}'.format(float(number)))
    averages = averages.apply(func=cleanfloats, axis=1)
    df2 = pd.DataFrame(averages).rename(columns={0 : 'PercentageSavedOnTicketPriceRelTo{}'.format(str(ticket_price_baseline))})
    df2 = df2.reset_index()
    return df2 