import urllib2
from stockmarket import Stock


def floatify(list_):
    """Cast all members of the given list to float."""
    floatified = [float(e) for e in list_]
    return floatified

def stringify(list_):
    """Cast all members of the given list to string."""
    stringified = [str(e) for e in list_]
    return stringified

def mean(list_):
    """Calculate the mean of the values of the given list."""
    return sum(list_)/len(list_)

def point_mean(list_of_lists):
    """Given a list of lists with the same length, return a list where each value is a mean of the given ones, i.e::
    >>> list_ = [[1, 2], [3, 4]]
    >>> point_mean(list_) = [mean([1, 2], mean([3, 4])]
    """
    points = zip(*list_of_lists)
    return [mean(p) for p in points]

def contract(list_):
    """Calculate the product of all the elements in the list."""
    prod = 1
    for element in list_:
        prod *= element
    return prod

DATA_FOLDER = 'data' # folder where the CSV files from Yahoo! will end
CLOSE_COLUMN = 4 # the index of the column containing the close value
TICKER_COLUMN = 0 # the index of the column containing the ticker name
INDEX = '%5EGSPC' # ticker of the index

def get_tickers():
    """Get the Standard & Poor stock tickers from disk."""
    
    f = file('%s/tickers.txt' % DATA_FOLDER, 'r')
    data = f.read()
    f.close()
    tickers = []
    stocks = data.split('\r\n')
    for stock in stocks:
        try:
            ticker = stock.split(',')[TICKER_COLUMN]
            ticker = ticker.replace('"', '') # remove surrounding quotes
            if ticker: # not empty ticker
                tickers.append(ticker)
        except IndexError: # empty row
            pass
    return tickers

def download_sap_tickers():
    """Dump the list of s&p tickers to disk."""

    data = []
    for n in range(0, 500, 50):
        url = urllib2.urlopen("http://download.finance.yahoo.com/d/quotes.csv?s=@%5EGSPC&f=sl1d1t1c1ohgv&e=.csv&h=PAGE".replace('PAGE', str(n)))
        data.append(url.read())

    f = file('%s/tickers.txt' % DATA_FOLDER, 'w')
    f.write(''.join(data))
    f.close()

def download_historical_daily_data(ticker, year_start, year_end):
    """Download historical daily data for the given ticker in CSV."""
    print "getting data from ticker: %s" % ticker
    url = urllib2.urlopen("http://ichart.finance.yahoo.com/table.csv?s=%s&a=00&b=1&c=%d&d=00&e=1&f=%d&g=d&ignore=.csv" % (ticker, year_start, year_end))

    history = url.read()
    f = file('%s/%s.csv' % (DATA_FOLDER, ticker), 'w')
    f.write(history)
    f.close()

def download_historical_data(ticker):
    """Download historical monthly data for the given ticker in CSV."""
    print "getting data from ticker: %s" % ticker
    url = urllib2.urlopen("http://ichart.finance.yahoo.com/table.csv?s=%s&a=00&b=1&c=2000&d=00&e=1&f=2009&g=m&ignore=.csv" % ticker)

    history = url.read()
    f = file('%s/%s.csv' % (DATA_FOLDER, ticker), 'w')
    f.write(history)
    f.close()

def get_dates(ticker):
    """Return the list of dates with values for a certain ticker, in
    ascendent order. This is designed to be used in the X axis label
    of graphs."""

    f = file('%s/%s.csv' % (DATA_FOLDER, ticker), 'r')
    history = f.read()
    
    measures = history.split('\n')
    measures = measures[1:-1] # the last row is empty and the first
                              # one contains the labels

    date_column = 0  # dates are stored in the first column
    dates = [measure.split(',')[date_column] for measure in measures]

    dates.reverse()
    return dates
    

def get_closes(ticker):
    """Return a list of the the historical closing values for the
    stocks with the ticker provided, sorted by ascendent date.
    """

    f = file('%s/%s.csv' % (DATA_FOLDER, ticker), 'r')
    history = f.read()
    
    measures = history.split('\n')
    measures = measures[1:-1] # the last row is empty and the first
                              # one contains the labels
    
    closes = [float(measure.split(',')[CLOSE_COLUMN]) for measure in measures]

    closes.reverse()
    return closes

def get_stocks_from_tickerslist(tickerslist): 
    """Returns a list of Stocks with the tickers from the
    tickerslist. If the data for a ticker is not found or incomplete,
    its associated stock won't appear in the returned list.
    """
    
    stocks = []
    for ticker in tickerslist:
        try:
            values = get_closes(ticker)
            stocks.append(Stock(ticker, values))
        except IOError: # data for the ticker not found
            print "data not found for ticker: %s" % ticker

    # filter the stocks to remove the ones with incomplete values
    max_len = max([len(s.values) for s in stocks])
    valid_stocks = [s for s in stocks if len(s.values) == max_len]

    return valid_stocks

### START OBSOLETE CODE ###
def get_diffs(closes):
    """Return the velocity of the provided closes."""
    diffs = [(closes[i] - closes[i-1])/closes[i]*100 for i in range(1, len(closes))]
    return diffs

def get_deviations(closes, reference_closes):
    """Return the deviations of the given diffs from the given reference."""
    assert len(closes) == len(reference_closes)
    diffs = get_diffs(closes)
    reference_diffs = get_diffs(reference_closes)
    deviation = [diffs[i] - reference_diffs[i] for i in range(0, len(diffs))]
    return deviation

def get_abs_deviations(closes, reference_closes):
    deviations = get_deviations(closes, reference_closes)
    abs_deviation = [abs(val) for val in deviations]
    return abs_deviation

def get_acceleration(closes, reference_closes):
    """Return the acceleration of the given closes."""
    assert len(closes) == len(reference_closes)
    deviation = get_deviations(closes, reference_closes)
    acceleration = [deviation[i] - deviation[i-1] for i in range(1, len(deviation))]
    return acceleration

def get_abs_acceleration(closes, reference_closes):
    """Return the absolute acceleration of the given
    closes, i.e. deceleration is accounted as acceleration too."""
    assert len(closes) == len(reference_closes)
    deviation = get_abs_deviations(closes, reference_closes)
    acceleration = [deviation[i] - deviation[i-1] for i in range(1, len(deviation))]
    return acceleration

def get_mean_point_accelerations(closes_list, reference_closes, absolute=True):
    """Return the mean acceleration at each point as a mean among the
    given list of closes.
    """
    assert len(closes_list[0]) == len(reference_closes)
    if absolute:
        chosen_get_acceleration = get_abs_acceleration
    else:
        chosen_get_acceleration = get_acceleration
    accelerations = [chosen_get_acceleration(closes, reference_closes) for closes in closes_list]
    return point_mean(accelerations)
### END OBSOLETE CODE ###
